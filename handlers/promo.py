from aiogram import Router, F
from aiogram.types import Message
from database import db
from config import EMOJI
from utils.formatters import format_number

router = Router()


@router.message(F.text.lower().startswith('промокод'))
async def use_promocode(message: Message):
    parts = message.text.split()
    
    if len(parts) < 2:
        text = f"""
{EMOJI['gift']} <b>Промокоды</b>

{EMOJI['info']} Для активации введите:
<code>промокод [код]</code>

<b>Пример:</b> <code>промокод BONUS2024</code>
"""
        await message.answer(text, parse_mode="HTML")
        return
    
    code = parts[1]
    promo, error = await db.use_promocode(message.from_user.id, code)
    
    if error:
        await message.answer(f"{EMOJI['cross']} {error}")
        return
    
    currency = "VC" if promo['reward_type'] == 'vc' else "VT"
    
    text = f"""
{EMOJI['check']} <b>Промокод активирован!</b>

{EMOJI['gift']} Код: <b>{code.upper()}</b>
💰 Награда: <b>{format_number(promo['reward_amount'])} {currency}</b>
"""
    await message.answer(text, parse_mode="HTML")
