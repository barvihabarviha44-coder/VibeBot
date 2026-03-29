from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import db
from config import EMOJI, GPU_CONFIG
from utils.formatters import format_number
from keyboards.inline import get_farm_menu, get_back_button

router = Router()


@router.message(F.text.lower().in_(['ферма', 'видеокарты', 'gpu']))
async def farm_command(message: Message):
    await show_farm(message)


@router.callback_query(F.data == "menu_farm")
async def farm_callback(callback: CallbackQuery):
    await show_farm(callback, edit=True)


async def show_farm(target, edit: bool = False):
    user_id = target.from_user.id
    user = await db.get_user(user_id)
    gpus = await db.get_user_gpus(user_id)
    
    # Подсчёт добычи в час
    total_vt_per_hour = 0
    gpu_info = []
    
    for gpu_type, config in GPU_CONFIG.items():
        user_gpu = next((g for g in gpus if g['gpu_type'] == gpu_type), None)
        count = user_gpu['count'] if user_gpu else 0
        current_price = user_gpu['current_price'] if user_gpu else config['base_price']
        vt_per_hour = count * config['vt_per_hour']
        total_vt_per_hour += vt_per_hour
        
        gpu_info.append({
            'name': config['name'],
            'emoji': config['emoji'],
            'count': count,
            'max': config['max_count'],
            'price': current_price,
            'vt_per_hour': config['vt_per_hour']
        })
    
    text = f"""
{EMOJI['farm']} <b>Ферма VibeTon</b>

{EMOJI['info']} Покупайте видеокарты и добывайте VibeTon!

{EMOJI['diamond']} Ваш VT: <b>{float(user['vt_balance']):.2f} VT</b>
⚡ Добыча: <b>{total_vt_per_hour:.2f} VT/час</b>

<b>Видеокарты:</b>
"""
    
    for gpu in gpu_info:
        text += f"""
{gpu['emoji']} <b>{gpu['name']}</b>
├ Количество: <b>{gpu['count']}/{gpu['max']}</b>
├ Добыча: <b>{gpu['vt_per_hour']} VT/час</b>
└ Цена: <b>{format_number(gpu['price'])} VC</b>
"""
    
    if edit:
        await target.message.edit_text(text, reply_markup=get_farm_menu(), parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=get_farm_menu(), parse_mode="HTML")


@router.callback_query(F.data.startswith("farm_buy_"))
async def buy_gpu(callback: CallbackQuery):
    gpu_type = callback.data.split("_")[2]
    
    if gpu_type not in GPU_CONFIG:
        await callback.answer("❌ Неизвестная видеокарта!", show_alert=True)
        return
    
    config = GPU_CONFIG[gpu_type]
    user = await db.get_user(callback.from_user.id)
    gpus = await db.get_user_gpus(callback.from_user.id)
    
    user_gpu = next((g for g in gpus if g['gpu_type'] == gpu_type), None)
    count = user_gpu['count'] if user_gpu else 0
    current_price = user_gpu['current_price'] if user_gpu else config['base_price']
    
    if count >= config['max_count']:
        await callback.answer(f"❌ Максимум {config['max_count']} видеокарт этого типа!", show_alert=True)
        return
    
    if user['balance'] < current_price:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    await db.update_balance(callback.from_user.id, current_price, add=False)
    await db.buy_gpu(callback.from_user.id, gpu_type, current_price)
    
    await callback.answer(f"✅ Куплена {config['name']}!", show_alert=True)
    await show_farm(callback, edit=True)


@router.callback_query(F.data == "farm_collect")
async def collect_vt(callback: CallbackQuery):
    collected = await db.collect_vt(callback.from_user.id)
    
    if collected > 0:
        await callback.answer(f"✅ Собрано {collected:.4f} VT!", show_alert=True)
    else:
        await callback.answer("ℹ️ Нечего собирать!", show_alert=True)
    
    await show_farm(callback, edit=True)
