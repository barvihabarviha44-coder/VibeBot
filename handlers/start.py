from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from database import db
from config import CHANNEL_ID, EMOJI
from keyboards.inline import get_subscription_keyboard

router = Router()


async def check_subscription(bot: Bot, user_id: int) -> bool:
    try:
        channel_member = await bot.get_chat_member(CHANNEL_ID, user_id)
        if channel_member.status in ['left', 'kicked']:
            return False
    except:
        pass
    return True


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await db.get_user(message.from_user.id)
    
    if not user:
        await db.create_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name
        )
        user = await db.get_user(message.from_user.id)
    
    is_subscribed = await check_subscription(message.bot, message.from_user.id)
    
    if not is_subscribed:
        text = f"""
{EMOJI['star']} <b>Добро пожаловать в VibeBet!</b>

{EMOJI['info']} Для использования бота подпишитесь на канал.
{EMOJI['gift']} После подписки вы получите <b>10.000 VC</b>!
"""
        await message.answer(text, reply_markup=get_subscription_keyboard(), parse_mode="HTML")
        return
    
    await db.set_subscribed(message.from_user.id, True)
    
    text = f"""
{EMOJI['check']} <b>Вы в игре!</b>

Напишите <code>помощь</code> для списка команд.
"""
    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: CallbackQuery):
    is_subscribed = await check_subscription(callback.bot, callback.from_user.id)
    
    if is_subscribed:
        await db.set_subscribed(callback.from_user.id, True)
        
        text = f"""
{EMOJI['check']} <b>Подписка подтверждена!</b>

{EMOJI['gift']} Вам начислено <b>10.000 VC</b>!

Напишите <code>помощь</code> для списка команд.
"""
        await callback.message.edit_text(text, parse_mode="HTML")
    else:
        await callback.answer("❌ Вы не подписаны на канал!", show_alert=True)
