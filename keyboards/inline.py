from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import CHANNEL_LINK


def get_subscription_keyboard():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK))
    b.row(InlineKeyboardButton(text="✅ Проверить", callback_data="check_subscription"))
    return b.as_markup()
