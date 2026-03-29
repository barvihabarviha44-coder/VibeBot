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
    
    #
