from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import db
from config import EMOJI
from utils.formatters import format_number
from utils.experience import maybe_add_xp
from keyboards.inline import (
    get_games_menu, get_dice_choice, get_football_choice,
    get_basketball_choice, get_darts_choice, get_bowling_choice
)
import asyncio

router = Router()


# ==================== КОСТИ ====================

@router.message(F.text.lower().startswith('кости'))
async def dice_game(message: Message):
    parts = message.text.lower().split()
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Кости</b> — это игра, в которой бросаются два кубика.

{EMOJI['dice']} Угадайте сумму: больше 7, меньше 7 или ровно 7.

<b>Коэффициенты:</b>
├ Больше 7: <b>2.3x</b>
├ Меньше 7: <b>2.3x</b>
└ Ровно 7: <b>5.8x</b>

<b>Использование:</b> <code>кости [ставка]</code>
<b>Пример:</b> <code>кости 100к</code>
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
{EMOJI['dice']} <b>Кости</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>

Выберите вашу ставку:
"""
    await message.answer(text, reply_markup=get_dice_choice(bet), parse_mode="HTML")


@router.callback_query(F.data.startswith("dice_"))
async def dice_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    choice = parts[1]
    bet = int(parts[2])
    
    user = await db.get_user(callback.from_user.id)
    if user['balance'] < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    await db.update_balance(callback.from_user.id, bet, add=False)
    
    # Бросаем два кубика
    dice1 = await callback.message.answer_dice(emoji="🎲")
    await asyncio.sleep(0.5)
    dice2 = await callback.message.answer_dice(emoji="🎲")
    
    await asyncio.sleep(4)
    
    total = dice1.dice.value + dice2.dice.value
    
    win = False
    multiplier = 0
    
    if choice == "more" and total > 7:
        win = True
        multiplier = 2.3
    elif choice == "less" and total < 7:
        win = True
        multiplier = 2.3
    elif choice == "equal" and total == 7:
        win = True
        multiplier = 5.8
    
    if win:
        winnings = int(bet * multiplier)
        await db.update_balance(callback.from_user.id, winnings, add=True)
        await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
        
        text = f"""
{EMOJI['check']} <b>Победа!</b>

{EMOJI['dice']} Сумма: <b>{total}</b>
{EMOJI['coin']} Выигрыш: <b>{format_number(winnings)} VC</b> (x{multiplier})
"""
    else:
        await db.update_stats(callback.from_user.id, lost=bet, played=1)
        await db.add_to_jackpot(bet)
        await db.add_president_profit(bet)
        
        text = f"""
{EMOJI['cross']} <b>Проигрыш!</b>

{EMOJI['dice']} Сумма: <b>{total}</b>
{EMOJI['coin']} Потеря: <b>{format_number(bet)} VC</b>
"""
    
    await maybe_add_xp(callback.from_user.id)
    await callback.message.answer(text, parse_mode="HTML")


# ==================== ФУТБОЛ ====================

@router.message(F.text.lower().startswith('футбол'))
async def football_game(message: Message):
    parts = message.text.lower().split()
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Футбол</b> — угадайте результат удара!

{EMOJI['football']} Выберите: гол или мимо.

<b>Коэффициенты:</b>
├ Гол: <b>1.8x</b>
└ Мимо: <b>3.7x</b>

<b>Использование:</b> <code>футбол [ставка]</code>
<b>Пример:</b> <code>футбол 100к</code>
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
{EMOJI['football']} <b>Футбол</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>

Выберите результат:
"""
    await message.answer(text, reply_markup=get_football_choice(bet), parse_mode="HTML")


@router.callback_query(F.data.startswith("football_"))
async def football_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    choice = parts[1]
    bet = int(parts[2])
    
    user = await db.get_user(callback.from_user.id)
    if user['balance'] < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    await db.update_balance(callback.from_user.id, bet, add=False)
    
    # Бросаем футбольный мяч
    football = await callback.message.answer_dice(emoji="⚽")
    
    await asyncio.sleep(4)
    
    # Значения 1,2 = мимо, 3,4,5 = гол
    is_goal = football.dice.value >= 3
    
    win = False
    multiplier = 0
    
    if choice == "goal" and is_goal:
        win = True
        multiplier = 1.8
    elif choice == "miss" and not is_goal:
        win = True
        multiplier = 3.7
    
    if win:
        winnings = int(bet * multiplier)
        await db.update_balance(callback.from_user.id, winnings, add=True)
        await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
        
        result_text = "⚽ Гол!" if is_goal else "❌ Мимо!"
        text = f"""
{EMOJI['check']} <b>Победа!</b>

{result_text}
{EMOJI['coin']} Выигрыш: <b>{format_number(winnings)} VC</b> (x{multiplier})
"""
    else:
        await db.update_stats(callback.from_user.id, lost=bet, played=1)
        await db.add_to_jackpot(bet)
        
        result_text = "⚽ Гол!" if is_goal else "❌ Мимо!"
        text = f"""
{EMOJI['cross']} <b>Проигрыш!</b>

{result_text}
{EMOJI['coin']} Потеря: <b>{format_number(bet)} VC</b>
"""
    
    await maybe_add_xp(callback.from_user.id)
    await callback.message.answer(text, parse_mode="HTML")


# ==================== БАСКЕТБОЛ ====================

@router.message(F.text.lower().startswith('баскетбол'))
async def basketball_game(message: Message):
    parts = message.text.lower().split()
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Баскетбол</b> — угадайте результат броска!

{EMOJI['basketball']} Выберите: попадание или мимо.

<b>Коэффициенты:</b>
├ Попадание: <b>3.8x</b>
└ Мимо: <b>1.9x</b>

<b>Использование:</b> <code>баскетбол [ставка]</code>
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
{EMOJI['basketball']} <b>Баскетбол</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>

Выберите результат:
"""
    await message.answer(text, reply_markup=get_basketball_choice(bet), parse_mode="HTML")


@router.callback_query(F.data.startswith("basketball_"))
async def basketball_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    choice = parts[1]
    bet = int(parts[2])
    
    user = await db.get_user(callback.from_user.id)
    if user['balance'] < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    await db.update_balance(callback.from_user.id, bet, add=False)
    
    ball = await callback.message.answer_dice(emoji="🏀")
    
    await asyncio.sleep(4)
    
    # 4,5 = попадание
    is_goal = ball.dice.value >= 4
    
    win = False
    multiplier = 0
    
    if choice == "goal" and is_goal:
        win = True
        multiplier = 3.8
    elif choice == "miss" and not is_goal:
        win = True
        multiplier = 1.9
    
    if win:
        winnings = int(bet * multiplier)
        await db.update_balance(callback.from_user.id, winnings, add=True)
        await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
        
        text = f"""
{EMOJI['check']} <b>Победа!</b>

{'🏀 Попадание!' if is_goal else '❌ Мимо!'}
{EMOJI['coin']} Выигрыш: <b>{format_number(winnings)} VC</b> (x{multiplier})
"""
    else:
        await db.update_stats(callback.from_user.id, lost=bet, played=1)
        await db.add_to_jackpot(bet)
        
        text = f"""
{EMOJI['cross']} <b>Проигрыш!</b>

{'🏀 Попадание!' if is_goal else '❌ Мимо!'}
{EMOJI['coin']} Потеря: <b>{format_number(bet)} VC</b>
"""
    
    await maybe_add_xp(callback.from_user.id)
    await callback.message.answer(text, parse_mode="HTML")


# ==================== ДАРТС ====================

@router.message(F.text.lower().startswith('дартс'))
async def darts_game(message: Message):
    parts = message.text.lower().split()
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Дартс</b> — угадайте результат броска!

{EMOJI['darts']} Выберите сектор.

<b>Коэффициенты:</b>
├ Центр: <b>5.8x</b>
├ Белое/Красное: <b>1.9x</b>
└ Мимо: <b>5.8x</b>

<b>Использование:</b> <code>дартс [ставка]</code>
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
{EMOJI['darts']} <b>Дартс</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>

Выберите сектор:
"""
    await message.answer(text, reply_markup=get_darts_choice(bet), parse_mode="HTML")


@router.callback_query(F.data.startswith("darts_"))
async def darts_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    choice = parts[1]
    bet = int(parts[2])
    
    user = await db.get_user(callback.from_user.id)
    if user['balance'] < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    await db.update_balance(callback.from_user.id, bet, add=False)
    
    dart = await callback.message.answer_dice(emoji="🎯")
    
    await asyncio.sleep(4)
    
    # 1 = мимо, 2,3 = белое/красное внешнее, 4,5 = внутреннее, 6 = центр
    value = dart.dice.value
    result = "miss" if value == 1 else ("center" if value == 6 else ("white" if value in [2, 4] else "red"))
    
    win = False
    multiplier = 0
    
    if choice == "center" and result == "center":
        win = True
        multiplier = 5.8
    elif choice == "miss" and result == "miss":
        win = True
        multiplier = 5.8
    elif choice in ["white", "red"] and result in ["white", "red"]:
        win = True
        multiplier = 1.9
    
    result_emoji = {"center": "🎯 Центр!", "miss": "❌ Мимо!", "white": "⚪ Белое!", "red": "🔴 Красное!"}
    
    if win:
        winnings = int(bet * multiplier)
        await db.update_balance(callback.from_user.id, winnings, add=True)
        await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
        
        text = f"""
{EMOJI['check']} <b>Победа!</b>

{result_emoji[result]}
{EMOJI['coin']} Выигрыш: <b>{format_number(winnings)} VC</b> (x{multiplier})
"""
    else:
        await db.update_stats(callback.from_user.id, lost=bet, played=1)
        await db.add_to_jackpot(bet)
        
        text = f"""
{EMOJI['cross']} <b>Проигрыш!</b>

{result_emoji[result]}
{EMOJI['coin']} Потеря: <b>{format_number(bet)} VC</b>
"""
    
    await maybe_add_xp(callback.from_user.id)
    await callback.message.answer(text, parse_mode="HTML")


# ==================== БОУЛИНГ ====================

@router.message(F.text.lower().startswith('боулинг'))
async def bowling_game(message: Message):
    parts = message.text.lower().split()
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Боулинг</b> — угадайте результат броска!

{EMOJI['bowling']} Выберите результат.

<b>Коэффициенты:</b>
├ Страйк: <b>5.3x</b>
├ Мимо: <b>5.3x</b>
└ 1-5 кеглей: <b>1.9x</b>

<b>Использование:</b> <code>боулинг [ставка]</code>
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
{EMOJI['bowling']} <b>Боулинг</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>

Выберите результат:
"""
    await message.answer(text, reply_markup=get_bowling_choice(bet), parse_mode="HTML")


@router.callback_query(F.data.startswith("bowling_"))
async def bowling_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    choice = parts[1]
    bet = int(parts[2])
    
    user = await db.get_user(callback.from_user.id)
    if user['balance'] < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    await db.update_balance(callback.from_user.id, bet, add=False)
    
    bowl = await callback.message.answer_dice(emoji="🎳")
    
    await asyncio.sleep(4)
    
    # 1 = мимо, 6 = страйк, 2-5 = частичное
    value = bowl.dice.value
    result = "miss" if value == 1 else ("strike" if value == 6 else "partial")
    
    win = False
    multiplier = 0
    
    if choice == "strike" and result == "strike":
        win = True
        multiplier = 5.3
    elif choice == "miss" and result == "miss":
        win = True
        multiplier = 5.3
    elif choice == "partial" and result == "partial":
        win = True
        multiplier = 1.9
    
    result_emoji = {"strike": "🎳 Страйк!", "miss": "❌ Мимо!", "partial": f"📍 {value} кеглей!"}
    
    if win:
        winnings = int(bet * multiplier)
        await db.update_balance(callback.from_user.id, winnings, add=True)
        await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
        
        text = f"""
{EMOJI['check']} <b>Победа!</b>

{result_emoji[result]}
{EMOJI['coin']} Выигрыш: <b>{format_number(winnings)} VC</b> (x{multiplier})
"""
    else:
        await db.update_stats(callback.from_user.id, lost=bet, played=1)
        await db.add_to_jackpot(bet)
        
        text = f"""
{EMOJI['cross']} <b>Проигрыш!</b>

{result_emoji[result]}
{EMOJI['coin']} Потеря: <b>{format_number(bet)} VC</b>
"""
    
    await maybe_add_xp(callback.from_user.id)
    await callback.message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "game_dice")
async def game_dice_menu(callback: CallbackQuery):
    text = f"""
{EMOJI['info']} <b>Кости</b> — это игра, в которой бросаются два кубика.

{EMOJI['dice']} Угадайте сумму: больше 7, меньше 7 или ровно 7.

<b>Коэффициенты:</b>
├ Больше 7: <b>2.3x</b>
├ Меньше 7: <b>2.3x</b>
└ Ровно 7: <b>5.8x</b>

<b>Использование:</b> <code>кости [ставка]</code>
<b>Пример:</b> <code>кости 100к</code>
"""
    await callback.message.edit_text(text, reply_markup=get_games_menu(), parse_mode="HTML")
