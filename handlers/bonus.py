from aiogram import Router, F
from aiogram.types import Message
from database import db
from config import EMOJI, CHAT_ID
from utils.formatters import format_number

router = Router()


@router.message(F.text.lower() == "бонус")
async def claim_bonus(message: Message):
    # Проверяем, что сообщение в чате
    if str(message.chat.id) != CHAT_ID.replace("@", ""):
        # Пробуем проверить по username чата
        if message.chat.username and f"@{message.chat.username}" != CHAT_ID:
            return
    
    bonus, error = await db.claim_bonus(message.from_user.id)
    
    if error:
        await message.reply(f"{EMOJI['cross']} {error}")
        return
    
    text = f"""
{EMOJI['check']} <b>Бонус получен!</b>

💰 +{format_number(bonus['bonus_amount'])} VC

Осталось активаций: {bonus['max_activations'] - bonus['current_activations']}
"""
    await message.reply(text, parse_mode="HTML")
