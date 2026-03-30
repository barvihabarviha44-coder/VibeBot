from aiogram import Router, F
from aiogram.types import Message
from database import db

router = Router()


@router.message(F.text.lower().startswith('+реп'))
async def plus_rep(message: Message):
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение игрока")
        return

    target_id = message.reply_to_message.from_user.id
    target_name = message.reply_to_message.from_user.first_name

    success, error = await db.add_reputation(message.from_user.id, target_id, 'plus')
    if error:
        await message.answer(error)
        return

    rep = await db.get_reputation(target_id)
    await message.answer(
        f"👍 <b>{message.from_user.first_name}</b> повысил репутацию <b>{target_name}</b>\n⭐ Репутация: <b>{rep}</b>",
        parse_mode="HTML"
    )


@router.message(F.text.lower().startswith('-реп'))
async def minus_rep(message: Message):
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение игрока")
        return

    target_id = message.reply_to_message.from_user.id
    target_name = message.reply_to_message.from_user.first_name

    success, error = await db.add_reputation(message.from_user.id, target_id, 'minus')
    if error:
        await message.answer(error)
        return

    rep = await db.get_reputation(target_id)
    await message.answer(
        f"👎 <b>{message.from_user.first_name}</b> понизил репутацию <b>{target_name}</b>\n⭐ Репутация: <b>{rep}</b>",
        parse_mode="HTML"
    )
