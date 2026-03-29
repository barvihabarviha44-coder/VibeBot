from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database import db
from config import EMOJI
from utils.formatters import format_number, parse_bet
from utils.experience import maybe_add_xp
import random

router = Router()


def get_mines_grid(opened: list, mines_positions: list, revealed: bool = False):
    builder = InlineKeyboardBuilder()
    for i in range(25):
        if i in opened:
            if i in mines_positions:
                text = "💥"
            else:
                text = "💎"
        elif revealed and i in mines_positions:
            text = "💣"
        else:
            text = "⬜"
        builder.button(text=text, callback_data=f"mines_cell_{i}")
    builder.adjust(5)
    
    if not revealed and len([x for x in opened if x not in mines_positions]) > 0:
        builder.row(InlineKeyboardButton(text="💰 Забрать", callback_data="mines_cashout"))
    
    return builder.as_markup()


@router.message(F.text.lower().startswith('мины'))
async def mines_game(message: Message):
    parts = message.text.split()
    
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Мины</b> — откройте ячейки, избегая мин!

<b>Использование:</b> <code>мины [ставка] [мины 1-6]</code>

<b>Пример:</b> <code>мины 100к 3</code>
<b>Пример:</b> <code>мины 1.5кк</code>
"""
        await message.answer(text, parse_mode="HTML")
        return
    
    bet = parse_bet(parts[1])
    mines_count = int(parts[2]) if len(parts) > 2 else 3
    mines_count = max(1, min(6, mines_count))
    
    if bet <= 0:
        await message.answer(f"{EMOJI['cross']} Неверная ставка!")
        return
    
    user = await db.get_user(message.from_user.id)
    if user['balance'] < bet:
        await message.answer(f"{EMOJI['cross']} Недостаточно средств!")
        return
    
    await db.update_balance(message.from_user.id, bet, add=False)
    
    mines_positions = random.sample(range(25), mines_count)
    
    game_data = {
        'mines_positions': mines_positions,
        'opened': [],
        'multiplier': 1.0,
        'mines_count': mines_count
    }
    await db.start_game(message.from_user.id, 'mines', bet, game_data)
    
    text = f"""
{EMOJI['bomb']} <b>Мины</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>
💣 Мин: <b>{mines_count}</b>
📈 Множитель: <b>x1.0</b>
"""
    await message.answer(text, reply_markup=get_mines_grid([], []), parse_mode="HTML")


@router.callback_query(F.data.startswith("mines_cell_"))
async def mines_cell(callback: CallbackQuery):
    cell = int(callback.data.split("_")[2])
    
    game = await db.get_active_game(callback.from_user.id, 'mines')
    if not game:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    game_data = game['game_data']
    mines_positions = game_data['mines_positions']
    opened = game_data['opened']
    
    if cell in opened:
        await callback.answer("Уже открыто!")
        return
    
    opened.append(cell)
    
    if cell in mines_positions:
        await db.end_game(callback.from_user.id, 'mines', 0, 'lose')
        await db.update_stats(callback.from_user.id, lost=game['bet_amount'], played=1)
        await db.add_to_jackpot(game['bet_amount'])
        await db.update_task_progress(callback.from_user.id, 'mines_play')
        
        text = f"""
{EMOJI['cross']} <b>БУМ!</b>

💣 Вы нашли мину!
{EMOJI['coin']} Потеря: <b>-{format_number(game['bet_amount'])} VC</b>
"""
        await callback.message.edit_text(
            text,
            reply_markup=get_mines_grid(opened, mines_positions, revealed=True),
            parse_mode="HTML"
        )
    else:
        opened_safe = len([x for x in opened if x not in mines_positions])
        base_multi = 1 + (game_data['mines_count'] * 0.1)
        multiplier = round(base_multi * (1 + opened_safe * 0.2), 2)
        game_data['multiplier'] = multiplier
        game_data['opened'] = opened
        
        await db.update_game(callback.from_user.id, 'mines', game_data)
        
        current_win = int(game['bet_amount'] * multiplier)
        
        text = f"""
{EMOJI['gem']} <b>Мины</b>

{EMOJI['coin']} Ставка: <b>{format_number(game['bet_amount'])} VC</b>
💣 Мин: <b>{game_data['mines_count']}</b>
💎 Открыто: <b>{opened_safe}</b>
📈 Множитель: <b>x{multiplier}</b>
💰 Выигрыш: <b>{format_number(current_win)} VC</b>
"""
        await callback.message.edit_text(
            text,
            reply_markup=get_mines_grid(opened, []),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "mines_cashout")
async def mines_cashout(callback: CallbackQuery):
    game = await db.get_active_game(callback.from_user.id, 'mines')
    if not game:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    game_data = game['game_data']
    winnings = int(game['bet_amount'] * game_data['multiplier'])
    
    await db.update_balance(callback.from_user.id, winnings, add=True)
    await db.end_game(callback.from_user.id, 'mines', winnings, 'win')
    await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
    await db.update_task_progress(callback.from_user.id, 'mines_play')
    await maybe_add_xp(callback.from_user.id)
    
    text = f"""
{EMOJI['check']} <b>Выигрыш!</b>

📈 Множитель: <b>x{game_data['multiplier']}</b>
{EMOJI['coin']} Выигрыш: <b>+{format_number(winnings)} VC</b>
"""
    await callback.message.edit_text(
        text,
        reply_markup=get_mines_grid(game_data['opened'], game_data['mines_positions'], revealed=True),
        parse_mode="HTML"
    )
