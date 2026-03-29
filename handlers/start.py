from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import db
from config import CHANNEL_ID, CHAT_ID, EMOJI
from keyboards.inline import get_main_menu, get_subscription_keyboard

router = Router()


async def check_subscription(bot, user_id: int) -> bool:
    try:
        channel_member = await bot.get_chat_member(CHANNEL_ID, user_id)
        chat_member = await bot.get_chat_member(CHAT_ID, user_id)
        return channel_member.status not in ['left', 'kicked'] and chat_member.status not in ['left', 'kicked']
    except:
        return False


@router.message(Command("start"))
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
            text = f"""
{EMOJI['star']} <b>Добро пожаловать в VibeBet!</b>

{EMOJI['info']} Для использования бота необходимо подписаться на наш канал и вступить в чат.

{EMOJI['gift']} После подписки вы получите <b>10.000 VC</b> на счёт!
"""
            await message.answer(text, reply_markup=get_subscription_keyboard(), parse_mode="HTML")
            return
        else:
            await db.set_subscribed(message.from_user.id, True)
    
    text = f"""
{EMOJI['crown']} <b>VibeBet — Игровой бот</b>

{EMOJI['coin']} Ваш баланс: <b>{user['balance'] if user else 10000:,} VC</b>

{EMOJI['fire']} Выберите действие из меню ниже:
"""
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")


@router.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: CallbackQuery):
    is_subscribed = await check_subscription(callback.bot, callback.from_user.id)
    
    if is_subscribed:
        await db.set_subscribed(callback.from_user.id, True)
        
        user = await db.get_user(callback.from_user.id)
        
        text = f"""
{EMOJI['check']} <b>Подписка подтверждена!</b>

{EMOJI['gift']} Вам начислено <b>10.000 VC</b>!

{EMOJI['crown']} <b>VibeBet — Игровой бот</b>

{EMOJI['coin']} Ваш баланс: <b>{user['balance']:,} VC</b>

{EMOJI['fire']} Выберите действие из меню ниже:
"""
        await callback.message.edit_text(text, reply_markup=get_main_menu(), parse_mode="HTML")
    else:
        await callback.answer("❌ Вы не подписаны на канал или не вступили в чат!", show_alert=True)


@router.callback_query(F.data == "menu_main")
async def menu_main(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    
    text = f"""
{EMOJI['crown']} <b>VibeBet — Игровой бот</b>

{EMOJI['coin']} Ваш баланс: <b>{user['balance']:,} VC</b>
{EMOJI['diamond']} VibeTon: <b>{float(user['vt_balance']):.2f} VT</b>

{EMOJI['fire']} Выберите действие из меню ниже:
"""
    await callback.message.edit_text(text, reply_markup=get_main_menu(), parse_mode="HTML")
