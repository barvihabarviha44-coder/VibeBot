from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database import db
from config import EMOJI
from utils.formatters import format_number
from keyboards.inline import get_market_menu, get_back_button

router = Router()


class MarketStates(StatesGroup):
    buy_amount = State()
    buy_price = State()
    sell_amount = State()
    sell_price = State()


@router.message(F.text.lower().in_(['рынок', 'маркет', 'market']))
async def market_command(message: Message):
    await show_market(message)


@router.callback_query(F.data == "menu_market")
async def market_callback(callback: CallbackQuery):
    await show_market(callback, edit=True)


async def show_market(target, edit: bool = False):
    vt_price = await db.get_vt_price()
    user = await db.get_user(target.from_user.id)
    
    text = f"""
{EMOJI['market']} <b>Рынок VibeTon</b>

{EMOJI['info']} Торгуйте VibeTon с другими игроками!

💱 <b>Текущий курс:</b> <b>{format_number(vt_price)} VC</b> за 1 VT
(обновляется каждый час)

{EMOJI['coin']} Ваш баланс: <b>{format_number(user['balance'])} VC</b>
{EMOJI['diamond']} Ваш VT: <b>{float(user['vt_balance']):.2f} VT</b>

Выберите операцию:
"""
    
    if edit:
        await target.message.edit_text(text, reply_markup=get_market_menu(), parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=get_market_menu(), parse_mode="HTML")


@router.callback_query(F.data == "market_buy")
async def market_buy(callback: CallbackQuery, state: FSMContext):
    vt_price = await db.get_vt_price()
    
    text = f"""
{EMOJI['market']} <b>Покупка VT</b>

💱 Рекомендуемая цена: <b>{format_number(vt_price)} VC</b>

Введите количество VT для покупки:
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_market"), parse_mode="HTML")
    await state.set_state(MarketStates.buy_amount)


@router.message(MarketStates.buy_amount)
async def buy_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
    except:
        await message.answer(f"{EMOJI['cross']} Неверное количество!")
        return
    
    if amount <= 0:
        await message.answer(f"{EMOJI['cross']} Количество должно быть положительным!")
        return
    
    await state.update_data(amount=amount)
    
    vt_price = await db.get_vt_price()
    
    text = f"""
{EMOJI['market']} <b>Покупка VT</b>

📊 Количество: <b>{amount} VT</b>
💱 Рекомендуемая цена: <b>{format_number(vt_price)} VC</b>

Введите вашу цену за 1 VT:
"""
    await message.answer(text, reply_markup=get_back_button("menu_market"), parse_mode="HTML")
    await state.set_state(MarketStates.buy_price)


@router.message(MarketStates.buy_price)
async def buy_price(message: Message, state: FSMContext):
    try:
        price_str = message.text.lower().replace('к', '000').replace('кк', '000000')
        price = int(float(price_str))
    except:
        await message.answer(f"{EMOJI['cross']} Неверная цена!")
        return
    
    data = await state.get_data()
    amount = data['amount']
    total_cost = int(price * amount)
    
    user = await db.get_user(message.from_user.id)
    
    if user['balance'] < total_cost:
        await message.answer(f"{EMOJI['cross']} Недостаточно средств! Нужно {format_number(total_cost)} VC")
        await state.clear()
        return
    
    # Резервируем средства
    await db.update_balance(message.from_user.id, total_cost, add=False)
    
    # Создаём ордер на покупку
    await db.create_market_order(message.from_user.id, 'buy', amount, price)
    
    await state.clear()
    
    text = f"""
{EMOJI['check']} <b>Ордер на покупку создан!</b>

📊 Количество: <b>{amount} VT</b>
💰 Цена: <b>{format_number(price)} VC</b> за 1 VT
💵 Итого: <b>{format_number(total_cost)} VC</b>

Ордер будет исполнен, когда найдётся продавец.
"""
    await message.answer(text, reply_markup=get_back_button("menu_market"), parse_mode="HTML")


@router.callback_query(F.data == "market_sell")
async def market_sell(callback: CallbackQuery, state: FSMContext):
    vt_price = await db.get_vt_price()
    user = await db.get_user(callback.from_user.id)
    
    text = f"""
{EMOJI['market']} <b>Продажа VT</b>

{EMOJI['diamond']} Ваш VT: <b>{float(user['vt_balance']):.2f} VT</b>
💱 Рекомендуемая цена: <b>{format_number(vt_price)} VC</b>

Введите количество VT для продажи:
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_market"), parse_mode="HTML")
    await state.set_state(MarketStates.sell_amount)


@router.message(MarketStates.sell_amount)
async def sell_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
    except:
        await message.answer(f"{EMOJI['cross']} Неверное количество!")
        return
    
    user = await db.get_user(message.from_user.id)
    
    if amount <= 0 or amount > float(user['vt_balance']):
        await message.answer(f"{EMOJI['cross']} Недостаточно VT!")
        return
    
    await state.update_data(amount=amount)
    
    vt_price = await db.get_vt_price()
    
    text = f"""
{EMOJI['market']} <b>Продажа VT</b>

📊 Количество: <b>{amount} VT</b>
💱 Рекомендуемая цена: <b>{format_number(vt_price)} VC</b>

Введите вашу цену за 1 VT:
"""
    await message.answer(text, reply_markup=get_back_button("menu_market"), parse_mode="HTML")
    await state.set_state(MarketStates.sell_price)


@router.message(MarketStates.sell_price)
async def sell_price(message: Message, state: FSMContext):
    try:
        price_str = message.text.lower().replace('к', '000').replace('кк', '000000')
        price = int(float(price_str))
    except:
        await message.answer(f"{EMOJI['cross']} Неверная цена!")
        return
    
    data = await state.get_data()
    amount = data['amount']
    
    # Резервируем VT
    await db.update_vt_balance(message.from_user.id, amount, add=False)
    
    # Создаём ордер на продажу
    await db.create_market_order(message.from_user.id, 'sell', amount, price)
    
    await state.clear()
    
    total = int(price * amount)
    
    text = f"""
{EMOJI['check']} <b>Ордер на продажу создан!</b>

📊 Количество: <b>{amount} VT</b>
💰 Цена: <b>{format_number(price)} VC</b> за 1 VT
💵 Ожидаемый доход: <b>{format_number(total)} VC</b>

Ордер будет исполнен, когда найдётся покупатель.
"""
    await message.answer(text, reply_markup=get_back_button("menu_market"), parse_mode="HTML")


@router.callback_query(F.data == "market_all_orders")
async def all_orders(callback: CallbackQuery):
    buy_orders = await db.get_market_orders('buy')
    sell_orders = await db.get_market_orders('sell')
    
    text = f"""
{EMOJI['market']} <b>Активные ордера</b>

📈 <b>Покупка (топ-5):</b>
"""
    
    for order in buy_orders[:5]:
        user = await db.get_user(order['user_id'])
        text += f"├ {float(order['amount']):.2f} VT по {format_number(order['price'])} VC — {user['first_name']}\n"
    
    if not buy_orders:
        text += "└ Нет ордеров\n"
    
    text += f"\n📉 <b>Продажа (топ-5):</b>\n"
    
    for order in sell_orders[:5]:
        user = await db.get_user(order['user_id'])
        text += f"├ {float(order['amount']):.2f} VT по {format_number(order['price'])} VC — {user['first_name']}\n"
    
    if not sell_orders:
        text += "└ Нет ордеров\n"
    
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_market"), parse_mode="HTML")
