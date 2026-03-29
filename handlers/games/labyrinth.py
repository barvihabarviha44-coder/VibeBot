from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import db
from config import EMOJI
from utils.formatters import format_number
from utils.experience import maybe_add_xp
from keyboards.inline import get_labyrinth_doors, get_back_button
import random

router = Router()


@router.message(F.text.lower().startswith('лабиринт'))
async def labyrinth_game(message: Message):
    parts = message.text.lower().split()
    
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Лабиринт</b> — игра с дверьми!

{EMOJI['door']} На первом этапе вам предстоит выбрать между двумя дверьми, за одной из которых находится приз.

• С каждым новым этапом количество дверей увеличивается
• Выигрыш умножается на количество дверей
• Вы можете забрать приз на любом этапе
• Чем больше дверей, тем выше риск и награда!

<b>Использование:</b> <code>лабиринт [ставка]</code>
<b>Пример:</b> <code>лабиринт 100к</code>
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
    
    # Первый уровень - 2 двери
    correct_door = random.randint(0, 1)
    
    game_data = {
        'current_level': 1,
        'num_doors': 2,
        'correct_door': correct_door,
        'multiplier': 1.0
    }
    await db.start_game(message.from_user.id, 'labyrinth', bet, game_data)
    
    text = f"""
{EMOJI['door']} <b>Лабиринт</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>
📊 Уровень: <b>1</b>
🚪 Дверей: <b>2</b>
📈 Множитель: <b>x1.0</b>

Выберите дверь:
"""
    await message.answer(text, reply_markup=get_labyrinth_doors(1, 2), parse_mode="HTML")


@router.callback_query(F.data.startswith("labyrinth_door_"))
async def labyrinth_door(callback: CallbackQuery):
    parts = callback.data.split("_")
    level = int(parts[2])
    door = int(parts[3])
    
    game = await db.get_active_game(callback.from_user.id, 'labyrinth')
    if not game:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    game_data = game['game_data']
    
    if level != game_data['current_level']:
        await callback.answer("Неверный уровень!")
        return
    
    correct_door = game_data['correct_door']
    
    if door == correct_door:
        # Правильная дверь!
        game_data['multiplier'] = round(game_data['multiplier'] * game_data['num_doors'], 2)
        game_data['current_level'] += 1
        game_data['num_doors'] = min(game_data['num_doors'] + 1, 6)  # Максимум 6 дверей
        game_data['correct_door'] = random.randint(0, game_data['num_doors'] - 1)
        
        await db.update_game(callback.from_user.id, 'labyrinth', game_data)
        await db.update_task_progress(callback.from_user.id, 'labyrinth_play')
        
        current_win = int(game['bet_amount'] * game_data['multiplier'])
        
        text = f"""
{EMOJI['check']} <b>Правильно!</b>

{EMOJI['door']} <b>Лабиринт</b>

{EMOJI['coin']} Ставка: <b>{format_number(game['bet_amount'])} VC</b>
📊 Уровень: <b>{game_data['current_level']}</b>
🚪 Дверей: <b>{game_data['num_doors']}</b>
📈 Множитель: <b>x{game_data['multiplier']}</b>
💰 Текущий выигрыш: <b>{format_number(current_win)} VC</b>

Выберите следующую дверь:
"""
        await callback.message.edit_text(
            text,
            reply_markup=get_labyrinth_doors(game_data['current_level'], game_data['num_doors']),
            parse_mode="HTML"
        )
    else:
        # Неправильная дверь
        await db.end_game(callback.from_user.id, 'labyrinth', 0, 'lose')
        await db.update_stats(callback.from_user.id, lost=game['bet_amount'], played=1)
        await db.add_to_jackpot(game['bet_amount'])
        await db.update_task_progress(callback.from_user.id, 'labyrinth_play')
        
        text = f"""
{EMOJI['cross']} <b>Неправильная дверь!</b>

🚪 Правильная дверь была: <b>{correct_door + 1}</b>
{EMOJI['coin']} Потеря: <b>{format_number(game['bet_amount'])} VC</b>
"""
        await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")


@router.callback_query(F.data == "labyrinth_cashout")
async def labyrinth_cashout(callback: CallbackQuery):
    game = await db.get_active_game(callback.from_user.id, 'labyrinth')
    if not game:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    game_data = game['game_data']
    winnings = int(game['bet_amount'] * game_data['multiplier'])
    
    await db.update_balance(callback.from_user.id, winnings, add=True)
    await db.end_game(callback.from_user.id, 'labyrinth', winnings, 'win')
    await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
    
    await maybe_add_xp(callback.from_user.id)
    
    text = f"""
{EMOJI['check']} <b>Выигрыш забран!</b>

📊 Пройдено уровней: <b>{game_data['current_level'] - 1}</b>
{EMOJI['coin']} Ставка: <b>{format_number(game['bet_amount'])} VC</b>
📈 Множитель: <b>x{game_data['multiplier']}</b>
💰 Выигрыш: <b>{format_number(winnings)} VC</b>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")
