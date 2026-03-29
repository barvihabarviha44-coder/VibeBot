from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import db
from config import EMOJI
from utils.formatters import format_number
from utils.experience import maybe_add_xp
from keyboards.inline import get_higher_lower_choice, get_back_button
import random

router = Router()


@router.message(F.text.lower().startswith('больше') or F.text.lower().startswith('бм'))
async def higher_lower_game(message: Message):
    parts = message.text.lower().split()
    
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Больше/Меньше</b>

⬆️ Игрок делает ставку и пытается предугадать, будет ли следующее число больше или меньше текущего, четным или нечетным.

<b>Коэффициенты (примерные):</b>
├ Больше/Меньше: <b>~2x</b>
├ Чётное/Нечётное: <b>~2x</b>
└ Чем выше число, тем ниже шанс на "больше"

<b>Использование:</b> <code>больше [ставка]</code>
<b>Пример:</b> <code>больше 100к</code>
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
    
    current_number = random.randint(1, 100)
    
    game_data = {
        'current_number': current_number,
        'multiplier': 1.0,
        'rounds': 0
    }
    await db.start_game(message.from_user.id, 'higher_lower', bet, game_data)
    
    text = f"""
⬆️ <b>Больше/Меньше</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>
🔢 Текущее число: <b>{current_number}</b>
📈 Множитель: <b>x1.0</b>

Выберите:
"""
    await message.answer(text, reply_markup=get_higher_lower_choice(current_number, bet), parse_mode="HTML")


@router.callback_query(F.data.startswith("hl_"))
async def higher_lower_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    choice = parts[1]
    
    if choice == "cashout":
        await higher_lower_cashout(callback)
        return
    
    bet = int(parts[2])
    
    game = await db.get_active_game(callback.from_user.id, 'higher_lower')
    if not game:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    game_data = game['game_data']
    current_number = game_data['current_number']
    new_number = random.randint(1, 100)
    
    win = False
    
    if choice == "higher" and new_number > current_number:
        win = True
    elif choice == "lower" and new_number < current_number:
        win = True
    elif choice == "even" and new_number % 2 == 0:
        win = True
    elif choice == "odd" and new_number % 2 != 0:
        win = True
    
    if win:
        # Рассчитываем множитель в зависимости от сложности угадывания
        if choice in ["higher", "lower"]:
            if choice == "higher":
                multiplier_add = (100 - current_number) / 100 * 2
            else:
                multiplier_add = current_number / 100 * 2
        else:
            multiplier_add = 0.5
        
        game_data['multiplier'] = round(game_data['multiplier'] + multiplier_add, 2)
        game_data['current_number'] = new_number
        game_data['rounds'] += 1
        
        await db.update_game(callback.from_user.id, 'higher_lower', game_data)
        await db.update_task_progress(callback.from_user.id, 'higher_lower_win')
        
        current_win = int(game['bet_amount'] * game_data['multiplier'])
        
        choice_text = {"higher": "⬆️ Больше", "lower": "⬇️ Меньше", "even": "Чётное", "odd": "Нечётное"}
        
        text = f"""
{EMOJI['check']} <b>Правильно!</b>

Было: <b>{current_number}</b> → Стало: <b>{new_number}</b>
Ваш выбор: <b>{choice_text[choice]}</b>

⬆️ <b>Больше/Меньше</b>

{EMOJI['coin']} Ставка: <b>{format_number(game['bet_amount'])} VC</b>
🔢 Текущее число: <b>{new_number}</b>
📈 Множитель: <b>x{game_data['multiplier']}</b>
💰 Текущий выигрыш: <b>{format_number(current_win)} VC</b>

Продолжить или забрать?
"""
        await callback.message.edit_text(
            text, 
            reply_markup=get_higher_lower_choice(new_number, bet),
            parse_mode="HTML"
        )
    else:
        # Проигрыш
        await db.end_game(callback.from_user.id, 'higher_lower', 0, 'lose')
        await db.update_stats(callback.from_user.id, lost=game['bet_amount'], played=1)
        await db.add_to_jackpot(game['bet_amount'])
        
        choice_text = {"higher": "⬆️ Больше", "lower": "⬇️ Меньше", "even": "Чётное", "odd": "Нечётное"}
        
        text = f"""
{EMOJI['cross']} <b>Неправильно!</b>

Было: <b>{current_number}</b> → Стало: <b>{new_number}</b>
Ваш выбор: <b>{choice_text[choice]}</b>

{EMOJI['coin']} Потеря: <b>{format_number(game['bet_amount'])} VC</b>
"""
        await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")


async def higher_lower_cashout(callback: CallbackQuery):
    game = await db.get_active_game(callback.from_user.id, 'higher_lower')
    if not game:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    game_data = game['game_data']
    winnings = int(game['bet_amount'] * game_data['multiplier'])
    
    await db.update_balance(callback.from_user.id, winnings, add=True)
    await db.end_game(callback.from_user.id, 'higher_lower', winnings, 'win')
    await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
    
    await maybe_add_xp(callback.from_user.id)
    
    text = f"""
{EMOJI['check']} <b>Выигрыш забран!</b>

🔄 Раундов: <b>{game_data['rounds']}</b>
{EMOJI['coin']} Ставка: <b>{format_number(game['bet_amount'])} VC</b>
📈 Множитель: <b>x{game_data['multiplier']}</b>
💰 Выигрыш: <b>{format_number(winnings)} VC</b>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")
