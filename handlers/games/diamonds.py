from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import db
from config import EMOJI
from utils.formatters import format_number
from utils.experience import maybe_add_xp
from keyboards.inline import get_diamonds_grid, get_back_button
import random

router = Router()


@router.message(F.text.lower().startswith('алмазы'))
async def diamonds_game(message: Message):
    parts = message.text.lower().split()
    
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Алмазная лихорадка</b> — это игра, в которой необходимо угадать, в какой ячейке спрятан алмаз. Вам нужно открывать по одной ячейке на каждом из 16 уровней, чтобы найти алмаз.

{EMOJI['gem']} Чтобы начать игру, используй команду:

<code>алмазы [ставка] [сложность 1-2]</code>

<b>Пример:</b> <code>алмазы 100к 2</code>
<b>Пример:</b> <code>алмазы 100к</code>
"""
        await message.answer(text, parse_mode="HTML")
        return
    
    try:
        bet_str = parts[1].lower().replace('к', '000').replace('кк', '000000')
        bet = int(float(bet_str))
        difficulty = int(parts[2]) if len(parts) > 2 else 1
        difficulty = max(1, min(2, difficulty))
    except:
        await message.answer(f"{EMOJI['cross']} Неверные параметры!")
        return
    
    user = await db.get_user(message.from_user.id)
    if user['balance'] < bet:
        await message.answer(f"{EMOJI['cross']} Недостаточно средств!")
        return
    
    await db.update_balance(message.from_user.id, bet, add=False)
    
    # Генерируем позицию алмаза для первого уровня
    diamond_pos = random.randint(0, 3)
    
    game_data = {
        'difficulty': difficulty,
        'current_level': 1,
        'max_levels': 16,
        'diamond_positions': [diamond_pos],
        'opened': [],
        'multiplier': 1.0
    }
    await db.start_game(message.from_user.id, 'diamonds', bet, game_data)
    
    text = f"""
{EMOJI['gem']} <b>Алмазная лихорадка</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>
📊 Уровень: <b>1/16</b>
📈 Множитель: <b>x1.0</b>

Выберите ячейку с алмазом:

🔷🔷🔷🔷
"""
    await message.answer(text, reply_markup=get_diamonds_grid(1, []), parse_mode="HTML")


@router.callback_query(F.data.startswith("diamond_cell_"))
async def diamond_cell(callback: CallbackQuery):
    parts = callback.data.split("_")
    level = int(parts[2])
    cell = int(parts[3])
    
    game = await db.get_active_game(callback.from_user.id, 'diamonds')
    if not game:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    game_data = game['game_data']
    
    if level != game_data['current_level']:
        await callback.answer("Неверный уровень!")
        return
    
    diamond_pos = game_data['diamond_positions'][level - 1]
    
    if cell == diamond_pos:
        # Нашли алмаз, переходим на следующий уровень
        game_data['opened'].append(cell)
        game_data['current_level'] += 1
        game_data['multiplier'] = round(1 + (level * 0.3), 2)
        
        if game_data['current_level'] > game_data['max_levels']:
            # Победа на всех уровнях!
            winnings = int(game['bet_amount'] * game_data['multiplier'])
            await db.update_balance(callback.from_user.id, winnings, add=True)
            await db.end_game(callback.from_user.id, 'diamonds', winnings, 'win')
            await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
            await db.update_task_progress(callback.from_user.id, 'diamonds_play')
            
            text = f"""
{EMOJI['trophy']} <b>ПОБЕДА! Все уровни пройдены!</b>

{EMOJI['coin']} Ставка: <b>{format_number(game['bet_amount'])} VC</b>
📈 Множитель: <b>x{game_data['multiplier']}</b>
💰 Выигрыш: <b>{format_number(winnings)} VC</b>
"""
            await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")
            return
        
        # Генерируем позицию для следующего уровня
        new_diamond_pos = random.randint(0, 3)
        game_data['diamond_positions'].append(new_diamond_pos)
        game_data['opened'] = []
        
        await db.update_game(callback.from_user.id, 'diamonds', game_data)
        
        current_win = int(game['bet_amount'] * game_data['multiplier'])
        
        text = f"""
{EMOJI['gem']} <b>Алмазная лихорадка</b>

{EMOJI['check']} Алмаз найден!

{EMOJI['coin']} Ставка: <b>{format_number(game['bet_amount'])} VC</b>
📊 Уровень: <b>{game_data['current_level']}/16</b>
📈 Множитель: <b>x{game_data['multiplier']}</b>
💰 Текущий выигрыш: <b>{format_number(current_win)} VC</b>

Выберите ячейку с алмазом:
"""
        await callback.message.edit_text(
            text,
            reply_markup=get_diamonds_grid(game_data['current_level'], []),
            parse_mode="HTML"
        )
    else:
        # Проигрыш
        await db.end_game(callback.from_user.id, 'diamonds', 0, 'lose')
        await db.update_stats(callback.from_user.id, lost=game['bet_amount'], played=1)
        await db.add_to_jackpot(game['bet_amount'])
        await db.update_task_progress(callback.from_user.id, 'diamonds_play')
        
        text = f"""
{EMOJI['cross']} <b>Проигрыш!</b>

💎 Алмаз был в ячейке {diamond_pos + 1}
{EMOJI['coin']} Потеря: <b>{format_number(game['bet_amount'])} VC</b>
"""
        await callback.message.edit_text(
            text,
            reply_markup=get_diamonds_grid(level, [], diamond_pos, revealed=True),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "diamond_cashout")
async def diamond_cashout(callback: CallbackQuery):
    game = await db.get_active_game(callback.from_user.id, 'diamonds')
    if not game:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    game_data = game['game_data']
    winnings = int(game['bet_amount'] * game_data['multiplier'])
    
    await db.update_balance(callback.from_user.id, winnings, add=True)
    await db.end_game(callback.from_user.id, 'diamonds', winnings, 'win')
    await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
    await db.update_task_progress(callback.from_user.id, 'diamonds_play')
    
    await maybe_add_xp(callback.from_user.id)
    
    text = f"""
{EMOJI['check']} <b>Выигрыш забран!</b>

📊 Уровень: <b>{game_data['current_level'] - 1}/16</b>
{EMOJI['coin']} Ставка: <b>{format_number(game['bet_amount'])} VC</b>
📈 Множитель: <b>x{game_data['multiplier']}</b>
💰 Выигрыш: <b>{format_number(winnings)} VC</b>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")
