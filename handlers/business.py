from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database import db
from config import EMOJI, ADMIN_USERNAME
from utils.formatters import format_number
from datetime import datetime

router = Router()

@router.message(F.text.lower().in_(['бизнес', 'бизнесы', 'business']))
async def business_command(message: Message):
    user = await db.get_user(message.from_user.id)
    user_businesses = await db.get_user_businesses(message.from_user.id)
    all_businesses = await db.get_all_businesses()
    
    total_profit_hour = 0
    for ub in user_businesses:
        profit = int(ub['base_profit'] * float(ub['profit_multiplier']))
        total_profit_hour += profit
    
    text = f"{EMOJI['business']} <b>Бизнесы</b>\n\n"
    text += f"📊 Ваших бизнесов: <b>{len(user_businesses)}/{user['business_slots']}</b>\n"
    text += f"💰 Доход: <b>{format_number(total_profit_hour)} VC/час</b>\n\n"
    
    if user_businesses:
        text += "<b>Ваши бизнесы:</b>\n"
        for ub in user_businesses:
            profit_hour = int(ub['base_profit'] * float(ub['profit_multiplier']))
            hours = (datetime.now() - ub['last_collect']).total_seconds() / 3600
            pending = int(hours * profit_hour)
            text += f"• {ub['emoji']} {ub['name']} — {format_number(pending)} VC накоплено\n"
        text += "\n"
    
    if all_businesses:
        text += "<b>Доступные бизнесы:</b>\n"
        owned_ids = [ub['business_id'] for ub in user_businesses]
        for biz in all_businesses:
            if biz['biz_id'] not in owned_ids:
                text += f"• {biz['emoji']} {biz['name']} — {format_number(biz['base_price'])} VC\n"
    else:
        text += "❌ Нет доступных бизнесов\n"
    
    text += f"\n💡 Слоты: {ADMIN_USERNAME}"
    
    builder = InlineKeyboardBuilder()
    for ub in user_businesses:
        builder.row(InlineKeyboardButton(text=f"💰 Собрать {ub['name']}", callback_data=f"biz_collect_{ub['ub_id']}"))
    
    if all_businesses:
        owned_ids = [ub['business_id'] for ub in user_businesses]
        for biz in all_businesses:
            if biz['biz_id'] not in owned_ids and len(user_businesses) < user['business_slots']:
                builder.row(InlineKeyboardButton(text=f"🛒 Купить {biz['name']}", callback_data=f"biz_buy_{biz['biz_id']}"))
    
    await message.answer(text, reply_markup=builder.as_markup() if builder._buttons else None, parse_mode="HTML")


@router.callback_query(F.data.startswith("biz_buy_"))
async def buy_business(callback: CallbackQuery):
    biz_id = int(callback.data.split("_")[2])
    business, error = await db.buy_business(callback.from_user.id, biz_id)
    if error:
        await callback.answer(f"❌ {error}", show_alert=True)
        return
    await callback.answer(f"✅ Бизнес «{business['name']}» куплен!", show_alert=True)
    await callback.message.delete()
    await business_command(callback.message)


@router.callback_query(F.data.startswith("biz_collect_"))
async def collect_business(callback: CallbackQuery):
    ub_id = int(callback.data.split("_")[2])
    profit = await db.collect_business_profit(callback.from_user.id, ub_id)
    if profit > 0:
        await callback.answer(f"✅ Собрано {format_number(profit)} VC!", show_alert=True)
    else:
        await callback.answer("ℹ️ Нечего собирать", show_alert=True)
    await callback.message.delete()
    await business_command(callback.message)
