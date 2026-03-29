from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import db
from config import EMOJI, get_level_xp
from utils.formatters import format_number, create_progress_bar
from keyboards.inline import get_back_button

router = Router()

PROFILE_COMMANDS = ['я', 'б', 'проф', 'профиль', 'п']


@router.message(F.text.lower().in_(PROFILE_COMMANDS))
async def show_profile(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        user = await db.get_user(message.from_user.id)
    
    await send_profile(message, user)


@router.callback_query(F.data == "menu_profile")
async def profile_callback(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    await send_profile(callback, user, edit=True)


async def send_profile(target, user, edit: bool = False):
    current_xp = user['xp']
    current_level = user['level']
    next_level_xp = get_level_xp(current_level + 1)
    xp_progress = create_progress_bar(current_xp, next_level_xp)
    
    winrate = (user['games_won'] / user['games_played'] * 100) if user['games_played'] > 0 else 0
    
    text = f"""
{EMOJI['user']} <b>Профиль игрока</b>

{EMOJI['crown']} <b>{user['first_name'] or 'Игрок'}</b>
├ {EMOJI['level']} Уровень: <b>{current_level}</b>
├ {EMOJI['xp']} Опыт: <b>{current_xp}/{next_level_xp}</b>
└ {xp_progress}

{EMOJI['coin']} <b>Финансы:</b>
├ Баланс: <b>{format_number(user['balance'])} VC</b>
├ Банк: <b>{format_number(user['bank_balance'])} VC</b>
└ VibeTon: <b>{float(user['vt_balance']):.2f} VT</b>

{EMOJI['chart']} <b>Статистика:</b>
├ Игр сыграно: <b>{user['games_played']}</b>
├ Побед: <b>{user['games_won']}</b>
├ Винрейт: <b>{winrate:.1f}%</b>
├ Всего выиграно: <b>{format_number(user['total_won'])} VC</b>
└ Всего проиграно: <b>{format_number(user['total_lost'])} VC</b>

{EMOJI['calendar']} Регистрация: <b>{user['registered_at'].strftime('%d.%m.%Y')}</b>
"""
    
    if edit:
        await target.message.edit_text(text, reply_markup=get_back_button(), parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=get_back_button(), parse_mode="HTML")
