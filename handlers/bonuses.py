from aiogram import Router, F
from aiogram.types import Message
from database import db
from utils.formatters import format_number, format_time
import random

router = Router()


@router.message(F.text.lower().in_(['бонус', 'ежедневный', 'daily']))
async def daily_bonus(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала напишите /start")
        return

    can_use = await db.check_cooldown(message.from_user.id, 'daily_bonus', 24.0)
    if not can_use:
        remaining = await db.get_cooldown_remaining(message.from_user.id, 'daily_bonus', 24.0)
        await message.answer(
            f"⏳ <b>Ежедневный бонус</b>\n\nСледующий через: <b>{format_time(remaining)}</b>",
            parse_mode="HTML"
        )
        return

    amount = 500000
    await db.update_balance(message.from_user.id, amount, add=True)
    await db.set_cooldown(message.from_user.id, 'daily_bonus')

    await message.answer(
        f"🎁 <b>Ежедневный бонус!</b>\n\n💰 +{format_number(amount)} VC",
        parse_mode="HTML"
    )


@router.message(F.text.lower().in_(['час', 'часовой', 'hour', 'hourly']))
async def hourly_bonus(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала напишите /start")
        return

    can_use = await db.check_cooldown(message.from_user.id, 'hourly_bonus', 1.0)
    if not can_use:
        remaining = await db.get_cooldown_remaining(message.from_user.id, 'hourly_bonus', 1.0)
        await message.answer(
            f"⏳ <b>Часовой бонус</b>\n\nСледующий через: <b>{format_time(remaining)}</b>",
            parse_mode="HTML"
        )
        return

    amount = random.randint(10000, 150000)
    await db.update_balance(message.from_user.id, amount, add=True)
    await db.set_cooldown(message.from_user.id, 'hourly_bonus')

    await message.answer(
        f"🎁 <b>Часовой бонус!</b>\n\n💰 +{format_number(amount)} VC",
        parse_mode="HTML"
    )
