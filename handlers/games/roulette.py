from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import db
from config import EMOJI
from utils.formatters import format_number
from utils.experience import maybe_add_xp
from keyboards.inline import get_roulette_choice, get_back_button
import random

router = Router()

RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
BLACK_NUMBERS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]


@router.message(F.text.lower().startswith('рулетка'))
async def roulette_game(message: Message):
    parts = message.text.lower().split()
    
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Рулетка</b> — классическая казино игра!

{EMOJI['slot']} Выберите ставку и сектор.

<b>Коэффициенты:</b>
├ 🔴 Красное / ⚫ Чёрное: <b>2x</b>
├ 🟢 Зеро (0): <b>36x</b>
└ Диапазоны (1-12, 13-24, 25-36): <b>3x</b>

<b>Использование:</b> <code>рулетка [ставка]</code>
<b>Пример:</b> <code>рулетка 100к</code>
"""
        await message.answer(text, parse_mode="HTML")
        return
    
    try:
        bet_str = parts[1].lower().replace('к', '000').replace('кк', '000000')
        bet = int(float(bet_str))
    except:
        await message.answer(f"{EMOJI['cross']} Неверная ставка!")
        return
    
    user = await db.get_user(message.from_user.id)
    if user['balance'] < bet:
        await message.answer(f"{EMOJI['cross']} Недостаточно средств!")
        return
    
    text = f"""
{EMOJI['slot']} <b>Рулетка</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>

Выберите ставку:
"""
    await message.answer(text, reply_markup=get_roulette_choice(bet), parse_mode="HTML")


@router.callback_query(F.data.startswith("roulette_"))
async def roulette_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    choice = parts[1]
    bet = int(parts[2])
    
    user = await db.get_user(callback.from_user.id)
    if user['balance'] < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    await db.update_balance(callback.from_user.id, bet, add=False)
    
    # Крутим рулетку
    result = random.randint(0, 36)
    
    win = False
    multiplier = 0
    
    if choice == "red" and result in RED_NUMBERS:
        win = True
        multiplier = 2
    elif choice == "black" and result in BLACK_NUMBERS:
        win = True
        multiplier = 2
    elif choice == "zero" and result == 0:
        win = True
        multiplier = 36
    elif choice == "1-12" and 1 <= result <= 12:
        win = True
        multiplier = 3
    elif choice == "13-24" and 13 <= result <= 24:
        win = True
        multiplier = 3
    elif choice == "25-36" and 25 <= result <= 36:
        win = True
        multiplier = 3
    
    # Определяем цвет выпавшего числа
    if result == 0:
        result_color = "🟢"
    elif result in RED_NUMBERS:
        result_color = "🔴"
    else:
        result_color = "⚫"
    
    if win:
        winnings = int(bet * multiplier)
        await db.update_balance(callback.from_user.id, winnings, add=True)
        await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
        
        text = f"""
{EMOJI['check']} <b>Победа!</b>

{EMOJI['slot']} Выпало: {result_color} <b>{result}</b>
{EMOJI['coin']} Выигрыш: <b>{format_number(winnings)} VC</b> (x{multiplier})
"""
    else:
        await db.update_stats(callback.from_user.id, lost=bet, played=1)
        await db.add_to_jackpot(bet)
        
        text = f"""
{EMOJI['cross']} <b>Проигрыш!</b>

{EMOJI['slot']} Выпало: {result_color} <b>{result}</b>
{EMOJI['coin']} Потеря: <b>{format_number(bet)} VC</b>
"""
    
    await maybe_add_xp(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")
