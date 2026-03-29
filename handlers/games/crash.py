from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import db
from config import EMOJI
from utils.formatters import format_number
from utils.experience import maybe_add_xp
from keyboards.inline import get_crash_control, get_back_button
import random
import asyncio

router = Router()


@router.message(F.text.lower().startswith('краш'))
async def crash_game(message: Message):
    parts = message.text.lower().split()
    
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Краш</b> — игра, в которой множитель растёт до случайной точки. 

{EMOJI['rocket']} Успейте забрать выигрыш до краша!

<b>Множитель:</b> от <b>1.01x</b> до <b>505x</b>

<b>Использование:</b> <code>краш [ставка]</code>
<b>Пример:</b> <code>краш 100к</code>
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
    
    await db.update_balance(message.from_user.id, bet, add=False)
    
    # Генерируем точку краша
    crash_point = round(random.uniform(1.01, 505), 2)
    
    game_data = {
        'crash_point': crash_point,
        'current_x': 1.0,
        'cashed_out': False
    }
    await db.start_game(message.from_user.id, 'crash', bet, game_data)
    
    text = f"""
{EMOJI['rocket']} <b>Краш</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>

📈 Множитель: <b>x1.00</b>
💰 Выигрыш: <b>{format_number(bet)} VC</b>

🚀 Игра началась...
"""
    msg = await message.answer(text, reply_markup=get_crash_control(1.0), parse_mode="HTML")
    
    # Запускаем анимацию роста
    current_x = 1.0
    while current_x < crash_point:
        await asyncio.sleep(0.5)
        
        # Проверяем, не забрал ли игрок выигрыш
        game = await db.get_active_game(message.from_user.id, 'crash')
        if not game or game['game_data'].get('cashed_out'):
            return
        
        current_x = round(current_x + random.uniform(0.05, 0.3), 2)
        current_x = min(current_x, crash_point)
        
        game_data['current_x'] = current_x
        await db.update_game(message.from_user.id, 'crash', game_data)
        
        current_win = int(bet * current_x)
        
        try:
            await msg.edit_text(
                f"""
{EMOJI['rocket']} <b>Краш</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>

📈 Множитель: <b>x{current_x}</b>
💰 Выигрыш: <b>{format_number(current_win)} VC</b>

🚀 Растёт...
""",
                reply_markup=get_crash_control(current_x),
                parse_mode="HTML"
            )
        except:
            pass
    
    # Краш!
    game = await db.get_active_game(message.from_user.id, 'crash')
    if game and not game['game_data'].get('cashed_out'):
        await db.end_game(message.from_user.id, 'crash', 0, 'lose')
        await db.update_stats(message.from_user.id, lost=bet, played=1)
        await db.add_to_jackpot(bet)
        await db.update_task_progress(message.from_user.id, 'crash_play')
        
        await msg.edit_text(
            f"""
{EMOJI['cross']} <b>КРАШ!</b>

💥 Краш на: <b>x{crash_point}</b>
{EMOJI['coin']} Потеря: <b>{format_number(bet)} VC</b>
""",
            reply_markup=get_back_button("menu_games"),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "crash_cashout")
async def crash_cashout(callback: CallbackQuery):
    game = await db.get_active_game(callback.from_user.id, 'crash')
    if not game:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    if game['game_data'].get('cashed_out'):
        await callback.answer("Вы уже забрали выигрыш!")
        return
    
    game_data = game['game_data']
    game_data['cashed_out'] = True
    await db.update_game(callback.from_user.id, 'crash', game_data)
    
    current_x = game_data['current_x']
    winnings = int(game['bet_amount'] * current_x)
    
    await db.update_balance(callback.from_user.id, winnings, add=True)
    await db.end_game(callback.from_user.id, 'crash', winnings, 'win')
    await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
    await db.update_task_progress(callback.from_user.id, 'crash_win')
    
    await maybe_add_xp(callback.from_user.id)
    
    text = f"""
{EMOJI['check']} <b>Выигрыш забран!</b>

📈 Забрано на: <b>x{current_x}</b>
💥 Краш был бы на: <b>x{game_data['crash_point']}</b>
{EMOJI['coin']} Ставка: <b>{format_number(game['bet_amount'])} VC</b>
💰 Выигрыш: <b>{format_number(winnings)} VC</b>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")
