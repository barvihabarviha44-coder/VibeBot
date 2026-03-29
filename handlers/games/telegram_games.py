from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database import db
from config import EMOJI
from utils.formatters import format_number, parse_bet
from utils.experience import maybe_add_xp
import asyncio

router = Router()


# ==================== КОСТИ ====================

def get_dice_keyboard(bet: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📈 Больше 7 (2.3x)", callback_data=f"dice_more_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text="📉 Меньше 7 (2.3x)", callback_data=f"dice_less_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text="🎯 Ровно 7 (5.8x)", callback_data=f"dice_equal_{bet}")
    )
    return builder.as_markup()


@router.message(F.text.lower().startswith('кости'))
async def dice_game(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Кости</b> — бросаются два кубика.

<b>Коэффициенты:</b>
• Больше 7: <b>2.3x</b>
• Меньше 7: <b>2.3x</b>
• Ровно 7: <b>5.8x</b>

<b>Пример:</b> <code>кости 100к</code>
"""
        await message.answer(text, parse_mode="HTML")
        return
    
    bet = parse_bet(parts[1])
    if bet <= 0:
        await message.answer(f"{EMOJI['cross']} Неверная ставка!")
        return
    
    user = await db.get_user(message.from_user.id)
    if user['balance'] < bet:
        await message.answer(f"{EMOJI['cross']} Недостаточно средств!")
        return
    
    text = f"""
{EMOJI['dice']} <b>Кости</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>

Выберите:
"""
    await message.answer(text, reply_markup=get_dice_keyboard(bet), parse_mode="HTML")


@router.callback_query(F.data.startswith("dice_"))
async def dice_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    choice = parts[1]
    bet = int(parts[2])
    
    user = await db.get_user(callback.from_user.id)
    if user['balance'] < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    # Сразу отключаем кнопки
    await callback.message.edit_reply_markup(reply_markup=None)
    
    await db.update_balance(callback.from_user.id, bet, add=False)
    
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
{EMOJI['coin']} Выигрыш: <b>+{format_number(winnings)} VC</b> (x{multiplier})
"""
    else:
        await db.update_stats(callback.from_user.id, lost=bet, played=1)
        await db.add_to_jackpot(bet)
        await db.add_president_profit(bet)
        
        text = f"""
{EMOJI['cross']} <b>Проигрыш!</b>

{EMOJI['dice']} Сумма: <b>{total}</b>
{EMOJI['coin']} Потеря: <b>-{format_number(bet)} VC</b>
"""
    
    await maybe_add_xp(callback.from_user.id)
    await callback.message.answer(text, parse_mode="HTML")


# ==================== ФУТБОЛ ====================

def get_football_keyboard(bet: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⚽ Гол (1.8x)", callback_data=f"football_goal_{bet}"),
        InlineKeyboardButton(text="❌ Мимо (3.7x)", callback_data=f"football_miss_{bet}")
    )
    return builder.as_markup()


@router.message(F.text.lower().startswith('футбол'))
async def football_game(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Футбол</b> — угадайте результат!

<b>Коэффициенты:</b>
• Гол: <b>1.8x</b>
• Мимо: <b>3.7x</b>

<b>Пример:</b> <code>футбол 100к</code>
"""
        await message.answer(text, parse_mode="HTML")
        return
    
    bet = parse_bet(parts[1])
    if bet <= 0:
        await message.answer(f"{EMOJI['cross']} Неверная ставка!")
        return
    
    user = await db.get_user(message.from_user.id)
    if user['balance'] < bet:
        await message.answer(f"{EMOJI['cross']} Недостаточно средств!")
        return
    
    text = f"""
{EMOJI['football']} <b>Футбол</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>

Выберите:
"""
    await message.answer(text, reply_markup=get_football_keyboard(bet), parse_mode="HTML")


@router.callback_query(F.data.startswith("football_"))
async def football_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    choice = parts[1]
    bet = int(parts[2])
    
    user = await db.get_user(callback.from_user.id)
    if user['balance'] < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await db.update_balance(callback.from_user.id, bet, add=False)
    
    football = await callback.message.answer_dice(emoji="⚽")
    await asyncio.sleep(4)
    
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
        
        text = f"""
{EMOJI['check']} <b>Победа!</b>

{'⚽ Гол!' if is_goal else '❌ Мимо!'}
{EMOJI['coin']} Выигрыш: <b>+{format_number(winnings)} VC</b>
"""
    else:
        await db.update_stats(callback.from_user.id, lost=bet, played=1)
        await db.add_to_jackpot(bet)
        
        text = f"""
{EMOJI['cross']} <b>Проигрыш!</b>

{'⚽ Гол!' if is_goal else '❌ Мимо!'}
{EMOJI['coin']} Потеря: <b>-{format_number(bet)} VC</b>
"""
    
    await maybe_add_xp(callback.from_user.id)
    await callback.message.answer(text, parse_mode="HTML")


# ==================== БАСКЕТБОЛ ====================

def get_basketball_keyboard(bet: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🏀 Попадание (3.8x)", callback_data=f"basketball_goal_{bet}"),
        InlineKeyboardButton(text="❌ Мимо (1.9x)", callback_data=f"basketball_miss_{bet}")
    )
    return builder.as_markup()


@router.message(F.text.lower().startswith('баскетбол'))
async def basketball_game(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Баскетбол</b>

<b>Коэффициенты:</b>
• Попадание: <b>3.8x</b>
• Мимо: <b>1.9x</b>

<b>Пример:</b> <code>баскетбол 100к</code>
"""
        await message.answer(text, parse_mode="HTML")
        return
    
    bet = parse_bet(parts[1])
    if bet <= 0:
        await message.answer(f"{EMOJI['cross']} Неверная ставка!")
        return
    
    user = await db.get_user(message.from_user.id)
    if user['balance'] < bet:
        await message.answer(f"{EMOJI['cross']} Недостаточно средств!")
        return
    
    text = f"""
{EMOJI['basketball']} <b>Баскетбол</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>

Выберите:
"""
    await message.answer(text, reply_markup=get_basketball_keyboard(bet), parse_mode="HTML")


@router.callback_query(F.data.startswith("basketball_"))
async def basketball_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    choice = parts[1]
    bet = int(parts[2])
    
    user = await db.get_user(callback.from_user.id)
    if user['balance'] < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await db.update_balance(callback.from_user.id, bet, add=False)
    
    ball = await callback.message.answer_dice(emoji="🏀")
    await asyncio.sleep(4)
    
    is_goal = ball.dice.value >= 4
    
    win = (choice == "goal" and is_goal) or (choice == "miss" and not is_goal)
    multiplier = 3.8 if choice == "goal" else 1.9
    
    if win:
        winnings = int(bet * multiplier)
        await db.update_balance(callback.from_user.id, winnings, add=True)
        await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
        
        text = f"{EMOJI['check']} <b>Победа!</b>\n\n{'🏀 Попадание!' if is_goal else '❌ Мимо!'}\n{EMOJI['coin']} Выигрыш: <b>+{format_number(winnings)} VC</b>"
    else:
        await db.update_stats(callback.from_user.id, lost=bet, played=1)
        await db.add_to_jackpot(bet)
        text = f"{EMOJI['cross']} <b>Проигрыш!</b>\n\n{'🏀 Попадание!' if is_goal else '❌ Мимо!'}\n{EMOJI['coin']} Потеря: <b>-{format_number(bet)} VC</b>"
    
    await maybe_add_xp(callback.from_user.id)
    await callback.message.answer(text, parse_mode="HTML")


# ==================== ДАРТС ====================

def get_darts_keyboard(bet: int):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎯 Центр (5.8x)", callback_data=f"darts_center_{bet}"))
    builder.row(
        InlineKeyboardButton(text="⚪ Белое (1.9x)", callback_data=f"darts_white_{bet}"),
        InlineKeyboardButton(text="🔴 Красное (1.9x)", callback_data=f"darts_red_{bet}")
    )
    builder.row(InlineKeyboardButton(text="❌ Мимо (5.8x)", callback_data=f"darts_miss_{bet}"))
    return builder.as_markup()


@router.message(F.text.lower().startswith('дартс'))
async def darts_game(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Дартс</b>

<b>Коэффициенты:</b>
• Центр: <b>5.8x</b>
• Белое/Красное: <b>1.9x</b>
• Мимо: <b>5.8x</b>

<b>Пример:</b> <code>дартс 100к</code>
"""
        await message.answer(text, parse_mode="HTML")
        return
    
    bet = parse_bet(parts[1])
    if bet <= 0:
        await message.answer(f"{EMOJI['cross']} Неверная ставка!")
        return
    
    user = await db.get_user(message.from_user.id)
    if user['balance'] < bet:
        await message.answer(f"{EMOJI['cross']} Недостаточно средств!")
        return
    
    text = f"""
{EMOJI['darts']} <b>Дартс</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>

Выберите:
"""
    await message.answer(text, reply_markup=get_darts_keyboard(bet), parse_mode="HTML")


@router.callback_query(F.data.startswith("darts_"))
async def darts_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    choice = parts[1]
    bet = int(parts[2])
    
    user = await db.get_user(callback.from_user.id)
    if user['balance'] < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await db.update_balance(callback.from_user.id, bet, add=False)
    
    dart = await callback.message.answer_dice(emoji="🎯")
    await asyncio.sleep(4)
    
    value = dart.dice.value
    # 1=мимо, 2,4=белое, 3,5=красное, 6=центр
    if value == 1:
        result = "miss"
    elif value == 6:
        result = "center"
    elif value in [2, 4]:
        result = "white"
    else:
        result = "red"
    
    win = (choice == result) or (choice in ["white", "red"] and result in ["white", "red"])
    
    if choice == "center" and result == "center":
        multiplier = 5.8
        win = True
    elif choice == "miss" and result == "miss":
        multiplier = 5.8
        win = True
    elif choice in ["white", "red"] and result in ["white", "red"]:
        multiplier = 1.9
        win = True
    else:
        win = False
        multiplier = 0
    
    result_text = {"center": "🎯 Центр!", "miss": "❌ Мимо!", "white": "⚪ Белое!", "red": "🔴 Красное!"}
    
    if win:
        winnings = int(bet * multiplier)
        await db.update_balance(callback.from_user.id, winnings, add=True)
        await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
        text = f"{EMOJI['check']} <b>Победа!</b>\n\n{result_text[result]}\n{EMOJI['coin']} Выигрыш: <b>+{format_number(winnings)} VC</b>"
    else:
        await db.update_stats(callback.from_user.id, lost=bet, played=1)
        await db.add_to_jackpot(bet)
        text = f"{EMOJI['cross']} <b>Проигрыш!</b>\n\n{result_text[result]}\n{EMOJI['coin']} Потеря: <b>-{format_number(bet)} VC</b>"
    
    await maybe_add_xp(callback.from_user.id)
    await callback.message.answer(text, parse_mode="HTML")


# ==================== БОУЛИНГ ====================

def get_bowling_keyboard(bet: int):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎳 Страйк (5.3x)", callback_data=f"bowling_strike_{bet}"))
    builder.row(InlineKeyboardButton(text="❌ Мимо (5.3x)", callback_data=f"bowling_miss_{bet}"))
    builder.row(InlineKeyboardButton(text="📍 1-5 кеглей (1.9x)", callback_data=f"bowling_partial_{bet}"))
    return builder.as_markup()


@router.message(F.text.lower().startswith('боулинг'))
async def bowling_game(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Боулинг</b>

<b>Коэффициенты:</b>
• Страйк: <b>5.3x</b>
• Мимо: <b>5.3x</b>
• 1-5 кеглей: <b>1.9x</b>

<b>Пример:</b> <code>боулинг 100к</code>
"""
        await message.answer(text, parse_mode="HTML")
        return
    
    bet = parse_bet(parts[1])
    if bet <= 0:
        await message.answer(f"{EMOJI['cross']} Неверная ставка!")
        return
    
    user = await db.get_user(message.from_user.id)
    if user['balance'] < bet:
        await message.answer(f"{EMOJI['cross']} Недостаточно средств!")
        return
    
    text = f"""
{EMOJI['bowling']} <b>Боулинг</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>

Выберите:
"""
    await message.answer(text, reply_markup=get_bowling_keyboard(bet), parse_mode="HTML")


@router.callback_query(F.data.startswith("bowling_"))
async def bowling_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    choice = parts[1]
    bet = int(parts[2])
    
    user = await db.get_user(callback.from_user.id)
    if user['balance'] < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await db.update_balance(callback.from_user.id, bet, add=False)
    
    bowl = await callback.message.answer_dice(emoji="🎳")
    await asyncio.sleep(4)
    
    value = bowl.dice.value
    result = "miss" if value == 1 else ("strike" if value == 6 else "partial")
    
    win = (choice == result)
    multiplier = 5.3 if choice in ["strike", "miss"] else 1.9
    
    result_text = {"strike": "🎳 Страйк!", "miss": "❌ Мимо!", "partial": f"📍 {value} кеглей!"}
    
    if win:
        winnings = int(bet * multiplier)
        await db.update_balance(callback.from_user.id, winnings, add=True)
        await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
        text = f"{EMOJI['check']} <b>Победа!</b>\n\n{result_text[result]}\n{EMOJI['coin']} Выигрыш: <b>+{format_number(winnings)} VC</b>"
    else:
        await db.update_stats(callback.from_user.id, lost=bet, played=1)
        await db.add_to_jackpot(bet)
        text = f"{EMOJI['cross']} <b>Проигрыш!</b>\n\n{result_text[result]}\n{EMOJI['coin']} Потеря: <b>-{format_number(bet)} VC</b>"
    
    await maybe_add_xp(callback.from_user.id)
    await callback.message.answer(text, parse_mode="HTML")
