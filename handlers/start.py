from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, CommandObject
from database import db
from config import CHANNEL_ID, EMOJI
from keyboards.inline import get_subscription_keyboard

router = Router()


async def check_subscription(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['left', 'kicked']:
            return False
    except:
        pass
    return True


@router.message(CommandStart(deep_link=True))
async def cmd_start_ref(message: Message, command: CommandObject):
    user = await db.get_user(message.from_user.id)
    is_new = user is None

    if not user:
        await db.create_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name
        )

    if is_new and command.args:
        try:
            ref_id = int(command.args)
            if ref_id != message.from_user.id:
                success = await db.set_referrer(message.from_user.id, ref_id)
                if success:
                    await db.give_referral_bonus(message.from_user.id)
                    await message.answer(
                        "🎁 <b>Реферальный бонус активирован!</b>\n\n"
                        "Вам: <b>+50к VC</b>\n"
                        "Пригласившему: <b>+25к VC + 1 VT</b>",
                        parse_mode="HTML"
                    )
                    try:
                        await message.bot.send_message(
                            ref_id,
                            f"👥 <b>{message.from_user.first_name}</b> зарегистрировался по вашей ссылке!\n"
                            f"💰 +25к VC\n💎 +1 VT",
                            parse_mode="HTML"
                        )
                    except:
                        pass
        except:
            pass

    is_subscribed = await check_subscription(message.bot, message.from_user.id)
    if not is_subscribed:
        await message.answer(
            f"{EMOJI['star']} <b>Добро пожаловать в VibeBet!</b>\n\nПодпишитесь на канал для начала!",
            reply_markup=get_subscription_keyboard(),
            parse_mode="HTML"
        )
        return

    await db.set_subscribed(message.from_user.id, True)
    await message.answer(
        f"{EMOJI['check']} <b>Вы в игре!</b>\n\nНапишите <code>помощь</code>",
        parse_mode="HTML"
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.create_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name
        )

    is_subscribed = await check_subscription(message.bot, message.from_user.id)
    if not is_subscribed:
        await message.answer(
            f"{EMOJI['star']} <b>Добро пожаловать в VibeBet!</b>\n\nПодпишитесь на канал!",
            reply_markup=get_subscription_keyboard(),
            parse_mode="HTML"
        )
        return

    await db.set_subscribed(message.from_user.id, True)
    await message.answer(
        f"{EMOJI['check']} <b>Вы в игре!</b>\n\nНапишите <code>помощь</code>",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: CallbackQuery):
    is_subscribed = await check_subscription(callback.bot, callback.from_user.id)
    if is_subscribed:
        await db.set_subscribed(callback.from_user.id, True)
        await callback.message.edit_text(
            f"{EMOJI['check']} <b>Подписка подтверждена!</b>\n\nНапишите <code>помощь</code>",
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Вы не подписаны!", show_alert=True)
