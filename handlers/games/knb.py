from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import db
from config import EMOJI
from utils.formatters import format_number
from utils.experience import maybe_add_xp
from keyboards.inline import get_knb_choice, get_back_button
import random

router = Router()


@router.message(F.text.lower().startswith('кнб'))
async def knb_game(message: Message):
    parts = message.text.lower().split()
    
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Камень-Ножницы-Бумага</b>

✊ Классическая игра! Победите бота.

<b>Коэффициент победы:</b> <b>2x</b>

<b>Использование:</b> <code>кнб [ставка]</code>
<b>Пример:</b> <code>кнб 100к</code>
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
✊ <b>Камень-Ножницы-Бумага</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>

Выберите:
"""
    await message.answer(text, reply_markup=get_knb_choice(bet), parse_mode="HTML")


@router.callback_query(F.data.startswith("knb_"))
async def knb_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    player_choice = parts[1]
    bet = int(parts[2])
    
    user = await db.get_user(callback.from_user.id)
    if user['balance'] < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    await db.update_balance(callback.from_user.id, bet, add=False)
    
    choices = ['rock', 'scissors', 'paper']
    bot_choice = random.choice(choices)
    
    choice_emoji = {'rock': '🪨', 'scissors': '✂️', 'paper': '📄'}
    choice_name = {'rock': 'Камень', 'scissors': 'Ножницы', 'paper': 'Бумага'}
    
        # Определяем победителя
    if player_choice == bot_choice:
        # Ничья - возврат ставки
        await db.update_balance(callback.from_user.id, bet, add=True)
        await db.update_task_progress(callback.from_user.id, 'knb_play')
        
        text = f"""
🤝 <b>Ничья!</b>

Вы: {choice_emoji[player_choice]} {choice_name[player_choice]}
Бот: {choice_emoji[bot_choice]} {choice_name[bot_choice]}

{EMOJI['coin']} Ставка возвращена: <b>{format_number(bet)} VC</b>
"""
    elif (player_choice == 'rock' and bot_choice == 'scissors') or \
         (player_choice == 'scissors' and bot_choice == 'paper') or \
         (player_choice == 'paper' and bot_choice == 'rock'):
        # Победа
        winnings = bet * 2
        await db.update_balance(callback.from_user.id, winnings, add=True)
        await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
        await db.update_task_progress(callback.from_user.id, 'knb_play')
        
        text = f"""
{EMOJI['check']} <b>Победа!</b>

Вы: {choice_emoji[player_choice]} {choice_name[player_choice]}
Бот: {choice_emoji[bot_choice]} {choice_name[bot_choice]}

{EMOJI['coin']} Выигрыш: <b>{format_number(winnings)} VC</b> (x2)
"""
    else:
        # Проигрыш
        await db.update_stats(callback.from_user.id, lost=bet, played=1)
        await db.add_to_jackpot(bet)
        await db.update_task_progress(callback.from_user.id, 'knb_play')
        
        text = f"""
{EMOJI['cross']} <b>Проигрыш!</b>

Вы: {choice_emoji[player_choice]} {choice_name[player_choice]}
Бот: {choice_emoji[bot_choice]} {choice_name[bot_choice]}

{EMOJI['coin']} Потеря: <b>{format_number(bet)} VC</b>
"""
    
    await maybe_add_xp(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")
