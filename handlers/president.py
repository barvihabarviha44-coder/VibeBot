from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database import db
from config import EMOJI, ADMIN_USERNAME
from utils.formatters import format_number, format_time
from keyboards.inline import get_president_menu, get_back_button
from datetime import datetime, timedelta
import pytz

router = Router()

MSK = pytz.timezone('Europe/Moscow')


class PresidentStates(StatesGroup):
    bet_amount = State()


@router.message(F.text.lower().in_(['президент', 'выборы']))
async def president_command(message: Message):
    await show_president(message)


@router.callback_query(F.data == "menu_president")
async def president_callback(callback: CallbackQuery):
    await show_president(callback, edit=True)


async def show_president(target, edit: bool = False):
    president = await db.get_president()
    user = await db.get_user(target.from_user.id)
    bets = await db.get_president_bets()
    
    # Вычисляем время до конца выборов
    now = datetime.now(MSK)
    end_time = now.replace(hour=23, minute=59, second=59)
    if now.hour >= 23 and now.minute >= 59:
        end_time = end_time + timedelta(days=1)
    remaining = (end_time - now).total_seconds()
    
    # Находим ставку пользователя
    user_bet = next((b for b in bets if b['user_id'] == target.from_user.id), None)
    
    # Общая сумма ставок
    total_bets = sum(b['bet_amount'] for b in bets)
    
    # Шанс пользователя
    user_chance = (user_bet['bet_amount'] / total_bets * 100) if user_bet and total_bets > 0 else 0
    
    president_name = f"{president['first_name']}" if president else "Нет"
    president_profit = president['profit'] if president else 0
    
    text = f"""
{EMOJI['president']} <b>Президент</b>

👨‍💼 Текущий президент: <b>{president_name}</b>
💰 Прибыль президента: <b>{format_number(president_profit)} VC</b>

{EMOJI['info']} <b>Информация:</b>
• Президент получает 0.01% от всех операций
• Ставки принимаются с 00:10 до 23:59
• Результаты в 00:07 по МСК
• Победитель выбирается случайно среди участников
• Шанс победы зависит от размера ставки
• Проигравшие получают 50% ставки назад
• Текущий президент не может участвовать

──────────

➡️ Твоя ставка: <b>{format_number(user_bet['bet_amount']) if user_bet else 'нет'} VC</b>
📊 Твой шанс: <b>{user_chance:.2f}%</b>
🕐 До конца выборов: <b>~{format_time(int(remaining))}</b>

👥 Участников: <b>{len(bets)}</b>
💰 Общий банк: <b>{format_number(total_bets)} VC</b>
"""
    
    # Проверяем, может ли пользователь участвовать
    can_participate = True
    if president and president['user_id'] == target.from_user.id:
        can_participate = False
        text += "\n⚠️ <i>Вы текущий президент и не можете участвовать</i>"
    
    keyboard = get_president_menu_custom(can_participate)
    
    if edit:
        await target.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=keyboard, parse_mode="HTML")


def get_president_menu_custom(can_participate: bool):
    builder = InlineKeyboardBuilder()
    if can_participate:
        builder.row(
            InlineKeyboardButton(text="💰 Сделать ставку", callback_data="president_bet")
        )
    builder.row(
        InlineKeyboardButton(text="📊 Все кандидаты", callback_data="president_candidates")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Назад", callback_data="menu_main")
    )
    return builder.as_markup()


@router.callback_query(F.data == "president_bet")
async def president_bet_start(callback: CallbackQuery, state: FSMContext):
    president = await db.get_president()
    
    if president and president['user_id'] == callback.from_user.id:
        await callback.answer("❌ Вы текущий президент!", show_alert=True)
        return
    
    text = f"""
{EMOJI['president']} <b>Ставка на выборы</b>

Введите сумму ставки:
(чем больше ставка, тем выше шанс победить)

<b>Пример:</b> <code>100к</code> или <code>1000000</code>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_president"), parse_mode="HTML")
    await state.set_state(PresidentStates.bet_amount)


@router.message(PresidentStates.bet_amount)
async def president_bet_process(message: Message, state: FSMContext):
    try:
        amount_str = message.text.lower().replace('к', '000').replace('кк', '000000')
        amount = int(float(amount_str))
    except:
        await message.answer(f"{EMOJI['cross']} Неверная сумма!")
        return
    
    if amount <= 0:
        await message.answer(f"{EMOJI['cross']} Сумма должна быть положительной!")
        return
    
    user = await db.get_user(message.from_user.id)
    
    if user['balance'] < amount:
        await message.answer(f"{EMOJI['cross']} Недостаточно средств!")
        return
    
    await db.place_president_bet(message.from_user.id, amount)
    await state.clear()
    
    text = f"""
{EMOJI['check']} <b>Ставка принята!</b>

💰 Сумма: <b>{format_number(amount)} VC</b>

Удачи на выборах! Результаты в 00:07 по МСК.
"""
    await message.answer(text, reply_markup=get_back_button("menu_president"), parse_mode="HTML")


@router.callback_query(F.data == "president_candidates")
async def president_candidates(callback: CallbackQuery):
    bets = await db.get_president_bets()
    total_bets = sum(b['bet_amount'] for b in bets)
    
    text = f"""
{EMOJI['president']} <b>Кандидаты на выборах</b>

👥 Всего участников: <b>{len(bets)}</b>
💰 Общий банк: <b>{format_number(total_bets)} VC</b>

<b>Топ кандидатов:</b>
"""
    
    sorted_bets = sorted(bets, key=lambda x: x['bet_amount'], reverse=True)
    
    for i, bet in enumerate(sorted_bets[:10], 1):
        chance = (bet['bet_amount'] / total_bets * 100) if total_bets > 0 else 0
        text += f"\n{i}. <b>{bet['first_name']}</b>\n"
        text += f"   💰 {format_number(bet['bet_amount'])} VC ({chance:.1f}%)\n"
    
    if not bets:
        text += "\nПока нет кандидатов"
    
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_president"), parse_mode="HTML")
