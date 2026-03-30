from aiogram import Router, F
from aiogram.types import Message
from database import db
from config import EMOJI, CHAT_ID
from utils.formatters import format_number

router = Router()


@router.message(F.text.lower() == "бонус")
async def claim_bonus_chat(message: Message):
    chat_username = message.chat.username
    if not chat_username:
        return
    if f"@{chat_username}" != CHAT_ID and chat_username != CHAT_ID.replace("@", ""):
        return
    
    bonus, error = await db.claim_bonus(message.from_user.id)
    if error:
        await message.reply(f"❌ {error}")
        return
    
    remaining = bonus['max_activations'] - bonus['current_activations']
    text = f"✅ <b>Бонус получен!</b>\n\n💰 +{format_number(bonus['bonus_amount'])} VC\n📊 Осталось: {remaining} активаций"
    await message.reply(text, parse_mode="HTML")
