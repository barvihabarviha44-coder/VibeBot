from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database import db
from config import EMOJI, GPU_CONFIG
from utils.formatters import format_number

router = Router()

@router.message(F.text.lower().in_(['ферма', 'gpu', 'видеокарты']))
async def farm_command(message: Message):
    await show_farm(message)

async def show_farm(target, edit=False):
    user_id = target.from_user.id
    user = await db.get_user(user_id)
    gpus = await db.get_user_gpus(user_id)
    pending = await db.get_pending_vt(user_id)
    
    total_vt_per_hour = 0
    text = f"{EMOJI['farm']} <b>Ферма VibeTon</b>\n\n"
    text += f"{EMOJI['diamond']} VT: <b>{float(user['vt_balance']):.2f}</b>\n"
    text += f"⏳ Накоплено: <b>{pending:.4f} VT</b>\n\n"
    
    for gpu_type, config in GPU_CONFIG.items():
        user_gpu = next((g for g in gpus if g['gpu_type'] == gpu_type), None)
        count = user_gpu['count'] if user_gpu else 0
        vt_h = count * config['vt_per_hour']
        total_vt_per_hour += vt_h
        text += f"{config['emoji']} <b>{config['name']}</b>\n"
        text += f"   {count}/{config['max_count']} | {config['vt_per_hour']} VT/ч\n"
    
    text += f"\n⚡ Всего: <b>{total_vt_per_hour:.1f} VT/час</b>"
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💰 Собрать VT", callback_data="farm_collect"))
    builder.row(InlineKeyboardButton(text="🛒 Купить видеокарту", callback_data="farm_shop"))
    
    if edit:
        await target.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data == "farm_collect")
async def farm_collect(callback: CallbackQuery):
    collected = await db.collect_vt(callback.from_user.id)
    if collected > 0:
        await callback.answer(f"✅ Собрано {collected:.4f} VT!", show_alert=True)
    else:
        await callback.answer("ℹ️ Нечего собирать!", show_alert=True)
    await show_farm(callback, edit=True)

@router.callback_query(F.data == "farm_shop")
async def farm_shop(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    gpus = await db.get_user_gpus(callback.from_user.id)
    
    text = f"🛒 <b>Магазин видеокарт</b>\n\n💰 Баланс: <b>{format_number(user['balance'])} VC</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for gpu_type, config in GPU_CONFIG.items():
        user_gpu = next((g for g in gpus if g['gpu_type'] == gpu_type), None)
        count = user_gpu['count'] if user_gpu else 0
        price = user_gpu['current_price'] if user_gpu else config['base_price']
        text += f"{config['emoji']} <b>{config['name']}</b>\n"
        text += f"   Цена: {format_number(price)} VC | {count}/{config['max_count']}\n\n"
        if count < config['max_count']:
            builder.row(InlineKeyboardButton(
                text=f"{config['emoji']} Купить {config['name'].split()[-1]} ({format_number(price)})",
                callback_data=f"farm_buy_{gpu_type}"
            ))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="farm_back"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("farm_buy_"))
async def farm_buy(callback: CallbackQuery):
    gpu_type = callback.data.split("_")[2]
    config = GPU_CONFIG[gpu_type]
    user = await db.get_user(callback.from_user.id)
    gpus = await db.get_user_gpus(callback.from_user.id)
    
    user_gpu = next((g for g in gpus if g['gpu_type'] == gpu_type), None)
    count = user_gpu['count'] if user_gpu else 0
    price = user_gpu['current_price'] if user_gpu else config['base_price']
    
    if count >= config['max_count']:
        await callback.answer(f"❌ Максимум {config['max_count']}!", show_alert=True)
        return
    if user['balance'] < price:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    await db.update_balance(callback.from_user.id, price, add=False)
    await db.buy_gpu(callback.from_user.id, gpu_type, price)
    await callback.answer(f"✅ Куплена {config['name']}!", show_alert=True)
    await farm_shop(callback)

@router.callback_query(F.data == "farm_back")
async def farm_back(callback: CallbackQuery):
    await show_farm(callback, edit=True)
