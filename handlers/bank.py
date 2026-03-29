from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from config import EMOJI
from utils.formatters import format_number
from keyboards.inline import get_bank_menu, get_back_button

router = Router()


class BankStates(StatesGroup):
    deposit_amount = State()
    withdraw_amount = State()
    transfer_vc_user = State()
    transfer_vc_amount = State()
    transfer_vt_user = State()
    transfer_vt_amount = State()


@router.message(F.text.lower().in_(['банк', 'bank']))
async def bank_command(message: Message):
    await show_bank(message)


@router.callback_query(F.data == "menu_bank")
async def bank_callback(callback: CallbackQuery):
    await show_bank(callback, edit=True)


async def show_bank(target, edit: bool = False):
    user = await db.get_user(target.from_user.id)
    
    text = f"""
{EMOJI['bank']} <b>Банк VibeBet</b>

{EMOJI['coin']} Баланс: <b>{format_number(user['balance'])} VC</b>
🏦 В банке: <b>{format_number(user['bank_balance'])} VC</b>
{EMOJI['diamond']} VibeTon: <b>{float(user['vt_balance']):.2f} VT</b>

{EMOJI['info']} <b>Комиссии:</b>
├ Переводы через банк: <b>2%</b>
└ Переводы командой: <b>6%</b>

Выберите операцию:
"""
    
    if edit:
        await target.message.edit_text(text, reply_markup=get_bank_menu(), parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=get_bank_menu(), parse_mode="HTML")


@router.callback_query(F.data == "bank_deposit")
async def bank_deposit(callback: CallbackQuery, state: FSMContext):
    text = f"""
{EMOJI['bank']} <b>Депозит</b>

Введите сумму для депозита:
(например: 100к или 1000000)
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_bank"), parse_mode="HTML")
    await state.set_state(BankStates.deposit_amount)


@router.message(BankStates.deposit_amount)
async def process_deposit(message: Message, state: FSMContext):
    try:
        amount_str = message.text.lower().replace('к', '000').replace('кк', '000000')
        amount = int(float(amount_str))
    except:
        await message.answer(f"{EMOJI['cross']} Неверная сумма!")
        return
    
    user = await db.get_user(message.from_user.id)
    
    if amount <= 0:
        await message.answer(f"{EMOJI['cross']} Сумма должна быть положительной!")
        return
    
    if user['balance'] < amount:
        await message.answer(f"{EMOJI['cross']} Недостаточно средств!")
        return
    
    await db.update_balance(message.from_user.id, amount, add=False)
    await db.update_bank(message.from_user.id, amount, add=True)
    
    await state.clear()
    
    text = f"""
{EMOJI['check']} <b>Депозит успешен!</b>

💰 Внесено: <b>{format_number(amount)} VC</b>
🏦 В банке: <b>{format_number(user['bank_balance'] + amount)} VC</b>
"""
    await message.answer(text, reply_markup=get_back_button("menu_bank"), parse_mode="HTML")


@router.callback_query(F.data == "bank_withdraw")
async def bank_withdraw(callback: CallbackQuery, state: FSMContext):
    text = f"""
{EMOJI['bank']} <b>Снятие</b>

Введите сумму для снятия:
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_bank"), parse_mode="HTML")
    await state.set_state(BankStates.withdraw_amount)


@router.message(BankStates.withdraw_amount)
async def process_withdraw(message: Message, state: FSMContext):
    try:
        amount_str = message.text.lower().replace('к', '000').replace('кк', '000000')
        amount = int(float(amount_str))
    except:
        await message.answer(f"{EMOJI['cross']} Неверная сумма!")
        return
    
    user = await db.get_user(message.from_user.id)
    
    if amount <= 0:
        await message.answer(f"{EMOJI['cross']} Сумма должна быть положительной!")
        return
    
    if user['bank_balance'] < amount:
        await message.answer(f"{EMOJI['cross']} Недостаточно средств в банке!")
        return
    
    await db.update_bank(message.from_user.id, amount, add=False)
    await db.update_balance(message.from_user.id, amount, add=True)
    
    await state.clear()
    
    text = f"""
{EMOJI['check']} <b>Снятие успешно!</b>

💰 Снято: <b>{format_number(amount)} VC</b>
{EMOJI['coin']} Баланс: <b>{format_number(user['balance'] + amount)} VC</b>
"""
    await message.answer(text, reply_markup=get_back_button("menu_bank"), parse_mode="HTML")


@router.callback_query(F.data == "bank_transfer_vc")
async def bank_transfer_vc(callback: CallbackQuery, state: FSMContext):
    text = f"""
{EMOJI['transfer']} <b>Перевод VC</b>

Введите ID или @username получателя:
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_bank"), parse_mode="HTML")
    await state.set_state(BankStates.transfer_vc_user)


@router.message(BankStates.transfer_vc_user)
async def transfer_vc_user(message: Message, state: FSMContext):
    target_input = message.text.strip()
    
    # Пытаемся найти пользователя
    try:
        if target_input.startswith('@'):
            # По юзернейму - нужно искать в базе
            await state.update_data(target_username=target_input)
        else:
            target_id = int(target_input)
            target_user = await db.get_user(target_id)
            if not target_user:
                await message.answer(f"{EMOJI['cross']} Пользователь не найден!")
                return
            await state.update_data(target_id=target_id)
    except ValueError:
        await message.answer(f"{EMOJI['cross']} Неверный ID!")
        return
    
    text = f"""
{EMOJI['transfer']} <b>Перевод VC</b>

Получатель: <b>{target_input}</b>
💸 Комиссия: <b>2%</b>

Введите сумму перевода:
"""
    await message.answer(text, reply_markup=get_back_button("menu_bank"), parse_mode="HTML")
    await state.set_state(BankStates.transfer_vc_amount)


@router.message(BankStates.transfer_vc_amount)
async def transfer_vc_amount(message: Message, state: FSMContext):
    try:
        amount_str = message.text.lower().replace('к', '000').replace('кк', '000000')
        amount = int(float(amount_str))
    except:
        await message.answer(f"{EMOJI['cross']} Неверная сумма!")
        return
    
    user = await db.get_user(message.from_user.id)
    data = await state.get_data()
    
    if amount <= 0:
        await message.answer(f"{EMOJI['cross']} Сумма должна быть положительной!")
        return
    
    if user['balance'] < amount:
        await message.answer(f"{EMOJI['cross']} Недостаточно средств!")
        return
    
    target_id = data.get('target_id')
    
    if not target_id:
        await message.answer(f"{EMOJI['cross']} Получатель не найден!")
        await state.clear()
        return
    
    if target_id == message.from_user.id:
        await message.answer(f"{EMOJI['cross']} Нельзя переводить себе!")
        return
    
    net_amount, commission = await db.transfer(
        message.from_user.id, target_id, amount, 'vc', 0.02
    )
    
    await state.clear()
    
    text = f"""
{EMOJI['check']} <b>Перевод успешен!</b>

💸 Отправлено: <b>{format_number(amount)} VC</b>
📤 Комиссия: <b>{format_number(commission)} VC</b>
📥 Получено: <b>{format_number(net_amount)} VC</b>
"""
    await message.answer(text, reply_markup=get_back_button("menu_bank"), parse_mode="HTML")


# Команда перевода
@router.message(F.text.lower().startswith('перевод'))
async def transfer_command(message: Message):
    parts = message.text.split()
    
    if len(parts) < 3:
        text = f"""
{EMOJI['info']} <b>Перевод</b>

<b>Использование:</b>
<code>перевод [ID] [сумма]</code>
<code>перевод [ID] [сумма] vt</code>

<b>Примеры:</b>
<code>перевод 123456789 100к</code>
<code>перевод 123456789 10 vt</code>

💸 Комиссия командой: <b>6%</b>
"""
        await message.answer(text, parse_mode="HTML")
        return
    
    try:
        target_id = int(parts[1])
        amount_str = parts[2].lower().replace('к', '000').replace('кк', '000000')
        amount = int(float(amount_str))
        currency = parts[3].lower() if len(parts) > 3 else 'vc'
    except:
        await message.answer(f"{EMOJI['cross']} Неверные параметры!")
        return
    
    if currency not in ['vc', 'vt']:
        await message.answer(f"{EMOJI['cross']} Неверная валюта! Используйте vc или vt")
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target_id)
    
    if not target_user:
        await message.answer(f"{EMOJI['cross']} Получатель не найден!")
        return
    
    if target_id == message.from_user.id:
        await message.answer(f"{EMOJI['cross']} Нельзя переводить себе!")
        return
    
    if currency == 'vc':
        if user['balance'] < amount:
            await message.answer(f"{EMOJI['cross']} Недостаточно средств!")
            return
    else:
        if float(user['vt_balance']) < amount:
            await message.answer(f"{EMOJI['cross']} Недостаточно VT!")
            return
    
    net_amount, commission = await db.transfer(
        message.from_user.id, target_id, amount, currency, 0.06
    )
    
    currency_name = "VC" if currency == 'vc' else "VT"
    
    text = f"""
{EMOJI['check']} <b>Перевод успешен!</b>

👤 Получатель: <b>{target_user['first_name']}</b>
💸 Отправлено: <b>{format_number(amount)} {currency_name}</b>
📤 Комиссия (6%): <b>{format_number(commission)} {currency_name}</b>
📥 Получено: <b>{format_number(net_amount)} {currency_name}</b>
"""
    await message.answer(text, parse_mode="HTML")
