from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import db
from config import EMOJI
from utils.formatters import format_number
from keyboards.inline import get_jackpot_menu, get_back_button

router = Router()


@router.callback_query(F.data == "menu_jackpot")
async def jackpot_menu(callback: CallbackQuery):
    jackpot = await db.get_jackpot()
    user = await db.get_user(callback.from_user.id)
    participants = await db.get_jackpot_participants()
    
    text = f"""
{EMOJI['jackpot']} <b>ДжекПот</b>

💰 Сумма: <b>{format_number(jackpot['amount'])} VC</b>
👥 Участников: <b>{len(participants)}</b>

{EMOJI['info']} <b>Информация:</b>
• Для участия нажмите "Участвовать"
• 0.01% от проигрышей попадает в ДжекПот
• Розыгрыш раз в сутки среди зарегистрированных
• Победитель определяется случайно

{'✅ Вы участвуете!' if user['jackpot_registered'] else '❌ Вы не участвуете'}
"""
    
    await callback.message.edit_text(
        text, 
        reply_markup=get_jackpot_menu(user['jackpot_registered']),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "jackpot_register")
async def jackpot_register(callback: CallbackQuery):
    await db.register_for_jackpot(callback.from_user.id)
    await callback.answer("✅ Вы зарегистрированы в розыгрыше!", show_alert=True)
    await jackpot_menu(callback)
