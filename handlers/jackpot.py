from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database import db
from config import EMOJI
from utils.formatters import format_number

router = Router()

@router.message(F.text.lower().in_(['джекпот', 'jackpot', 'жп']))
async def jackpot_command(message: Message):
    jackpot = await db.get_jackpot()
    user = await db.get_user(message.from_user.id)
    participants_count = await db.get_jackpot_participants_count()
    
    status = "✅ Вы участвуете" if user['jackpot_registered'] else "❌ Вы не участвуете"
    
    text = f"""
{EMOJI['jackpot']} <b>ДжекПот</b>

💰 Сумма: <b>{format_number(jackpot['amount'])} VC</b>
👥 Участников: <b>{participants_count}</b>

{status}

ℹ️ <b>Информация:</b>
• 0.01% от проигрышей попадает в ДжекПот
• Розыгрыш раз в сутки в 00:00 МСК
"""
    builder = InlineKeyboardBuilder()
    if not user['jackpot_registered']:
        builder.row(InlineKeyboardButton(text="🎰 Участвовать", callback_data="jackpot_register"))
    
    await message.answer(text, reply_markup=builder.as_markup() if builder._buttons else None, parse_mode="HTML")

@router.callback_query(F.data == "jackpot_register")
async def jackpot_register(callback: CallbackQuery):
    await db.register_for_jackpot(callback.from_user.id)
    await callback.answer("✅ Вы зарегистрированы в розыгрыше!", show_alert=True)
    await callback.message.delete()
    await jackpot_command(callback.message)
