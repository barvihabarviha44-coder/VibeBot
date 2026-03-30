from aiogram import Router, F
from aiogram.types import Message
from database import db
from utils.formatters import format_number

router = Router()

PROFILE_COMMANDS = ['я', 'б', 'проф', 'профиль', 'п']


@router.message(F.text.lower().in_(PROFILE_COMMANDS))
async def show_profile(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        user = await db.get_user(message.from_user.id)

    rep = await db.get_reputation(message.from_user.id)
    ref_count = await db.get_referral_count(message.from_user.id)

    me = await message.bot.get_me()
    ref_link = f"https://t.me/{me.username}?start={message.from_user.id}"

    text = f"""
👤 <b>Профиль</b>

🆔 ID: <code>{user['user_id']}</code>
📊 Уровень: <b>{user['level']}</b> ({user['xp']} XP)
⭐ Репутация: <b>{rep}</b>

🪙 Баланс: <b>{format_number(user['balance'])} VC</b>
💎 VibeTon: <b>{float(user['vt_balance']):.2f} VT</b>

🎮 Игр: <b>{user['games_played']}</b>
✅ Выиграно: <b>{format_number(user['total_won'])} VC</b>
❌ Проиграно: <b>{format_number(user['total_lost'])} VC</b>

👥 Рефералов: <b>{ref_count}</b>
🔗 Ссылка: <code>{ref_link}</code>

📅 Регистрация: <b>{user['registered_at'].strftime('%d.%m.%Y')}</b>
"""
    await message.answer(text, parse_mode="HTML")
