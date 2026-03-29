from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database import db
from config import EMOJI, ADMIN_USERNAME
from utils.formatters import format_number
from keyboards.inline import get_back_button
from datetime import datetime

router = Router()


class BusinessStates(StatesGroup):
    upgrade_confirm = State()


def get_business_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🏢 Мои бизнесы", callback_data="business_my")
    )
    builder.row(
        InlineKeyboardButton(text="🛒 Купить бизнес", callback_data="business_shop")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Назад", callback_data="menu_main")
    )
    return builder.as_markup()


@router.message(F.text.lower().in_(['бизнес', 'бизнесы', 'business']))
async def business_command(message: Message):
    await show_business(message)


@router.callback_query(F.data == "menu_business")
async def business_callback(callback: CallbackQuery):
    await show_business(callback, edit=True)


async def show_business(target, edit: bool = False):
    user = await db.get_user(target.from_user.id)
    user_businesses = await db.get_user_businesses(target.from_user.id)
    
    total_profit_hour = 0
    for ub in user_businesses:
        profit = int(ub['base_profit'] * float(ub['profit_multiplier']))
        total_profit_hour += profit
    
    text = f"""
{EMOJI['business']} <b>Бизнесы</b>

{EMOJI['info']} Покупайте бизнесы и получайте пассивный доход!

📊 <b>Ваша статистика:</b>
├ Бизнесов: <b>{len(user_businesses)}/{user['business_slots']}</b>
├ Доход/час: <b>{format_number(total_profit_hour)} VC</b>
└ Слоты: <b>{user['business_slots']}</b>

💡 Для покупки дополнительных слотов обратитесь к {ADMIN_USERNAME}

Выберите действие:
"""
    
    if edit:
        await target.message.edit_text(text, reply_markup=get_business_menu(), parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=get_business_menu(), parse_mode="HTML")


@router.callback_query(F.data == "business_shop")
async def business_shop(callback: CallbackQuery):
    businesses = await db.get_all_businesses()
    user = await db.get_user(callback.from_user.id)
    user_businesses = await db.get_user_businesses(callback.from_user.id)
    
    owned_ids = [ub['business_id'] for ub in user_businesses]
    
    if not businesses:
        text = f"""
{EMOJI['business']} <b>Магазин бизнесов</b>

{EMOJI['info']} Пока нет доступных бизнесов.
Администраторы скоро добавят новые!
"""
        await callback.message.edit_text(text, reply_markup=get_back_button("menu_business"), parse_mode="HTML")
        return
    
    text = f"""
{EMOJI['business']} <b>Магазин бизнесов</b>

{EMOJI['coin']} Ваш баланс: <b>{format_number(user['balance'])} VC</b>
📦 Слотов: <b>{len(user_businesses)}/{user['business_slots']}</b>

<b>Доступные бизнесы:</b>
"""
    
    builder = InlineKeyboardBuilder()
    
    for biz in businesses:
        owned = biz['id'] in owned_ids
        status = "✅" if owned else ""
        tax_daily = biz['base_price'] // 10
        
        text += f"""
{biz['emoji']} <b>{biz['name']}</b> {status}
├ Цена: <b>{format_number(biz['base_price'])} VC</b>
├ Прибыль: <b>{format_number(biz['base_profit'])} VC/час</b>
└ Налог: <b>{format_number(tax_daily)} VC/день</b>
"""
        
        if not owned:
            builder.row(
                InlineKeyboardButton(
                    text=f"{biz['emoji']} Купить {biz['name']}",
                    callback_data=f"business_buy_{biz['id']}"
                )
            )
    
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Назад", callback_data="menu_business")
    )
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("business_buy_"))
async def business_buy(callback: CallbackQuery):
    business_id = int(callback.data.split("_")[2])
    
    business, error = await db.buy_business(callback.from_user.id, business_id)
    
    if error:
        await callback.answer(f"❌ {error}", show_alert=True)
        return
    
    await callback.answer(f"✅ Бизнес «{business['name']}» куплен!", show_alert=True)
    await business_shop(callback)


@router.callback_query(F.data == "business_my")
async def my_businesses(callback: CallbackQuery):
    user_businesses = await db.get_user_businesses(callback.from_user.id)
    
    if not user_businesses:
        text = f"""
{EMOJI['business']} <b>Мои бизнесы</b>

У вас пока нет бизнесов.
Купите первый бизнес в магазине!
"""
        await callback.message.edit_text(text, reply_markup=get_back_button("menu_business"), parse_mode="HTML")
        return
    
    text = f"""
{EMOJI['business']} <b>Мои бизнесы</b>

"""
    
    builder = InlineKeyboardBuilder()
    
    for ub in user_businesses:
        profit_hour = int(ub['base_profit'] * float(ub['profit_multiplier']))
        hours_since = (datetime.now() - ub['last_collect']).total_seconds() / 3600
        pending_profit = int(hours_since * profit_hour)
        tax_daily = ub['base_price'] // 10
        
        # Проверка налогов
        tax_status = "✅" if ub['tax_paid_until'] >= datetime.now().date() else "⚠️ Нужно оплатить!"
        
        text += f"""
{ub['emoji']} <b>{ub['name']}</b>
├ Уровень: <b>{ub['upgrade_level']}</b> (x{float(ub['profit_multiplier']):.1f})
├ Прибыль: <b>{format_number(profit_hour)} VC/час</b>
├ Накоплено: <b>{format_number(pending_profit)} VC</b>
├ Налог: <b>{format_number(tax_daily)} VC/день</b>
└ Статус: {tax_status}
"""
        
        builder.row(
            InlineKeyboardButton(
                text=f"💰 Собрать ({format_number(pending_profit)})",
                callback_data=f"business_collect_{ub['id']}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=f"⬆️ Улучшить",
                callback_data=f"business_upgrade_{ub['id']}"
            ),
            InlineKeyboardButton(
                text=f"💸 Продать",
                callback_data=f"business_sell_{ub['id']}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=f"📋 Оплатить налог",
                callback_data=f"business_tax_{ub['id']}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Назад", callback_data="menu_business")
    )
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("business_collect_"))
async def business_collect(callback: CallbackQuery):
    ub_id = int(callback.data.split("_")[2])
    
    profit = await db.collect_business_profit(callback.from_user.id, ub_id)
    
    if profit > 0:
        await callback.answer(f"✅ Собрано {format_number(profit)} VC!", show_alert=True)
    else:
        await callback.answer("ℹ️ Нечего собирать!", show_alert=True)
    
    await my_businesses(callback)


@router.callback_query(F.data.startswith("business_upgrade_"))
async def business_upgrade(callback: CallbackQuery):
    ub_id = int(callback.data.split("_")[2])
    
    # Получаем информацию о бизнесе
    user_businesses = await db.get_user_businesses(callback.from_user.id)
    ub = next((b for b in user_businesses if b['id'] == ub_id), None)
    
    if not ub:
        await callback.answer("❌ Бизнес не найден!", show_alert=True)
        return
    
    # Стоимость улучшения = базовая цена * уровень * 0.2
    upgrade_cost = int(ub['base_price'] * ub['upgrade_level'] * 0.2)
    new_multiplier = float(ub['profit_multiplier']) + 0.1
    new_profit = int(ub['base_profit'] * new_multiplier)
    
    text = f"""
⬆️ <b>Улучшение бизнеса</b>

{ub['emoji']} <b>{ub['name']}</b>

Текущий уровень: <b>{ub['upgrade_level']}</b>
Текущий множитель: <b>x{float(ub['profit_multiplier']):.1f}</b>

После улучшения:
├ Уровень: <b>{ub['upgrade_level'] + 1}</b>
├ Множитель: <b>x{new_multiplier:.1f}</b>
└ Прибыль: <b>{format_number(new_profit)} VC/час</b>

💰 Стоимость: <b>{format_number(upgrade_cost)} VC</b>
"""
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"✅ Улучшить за {format_number(upgrade_cost)} VC",
            callback_data=f"business_upgrade_confirm_{ub_id}_{upgrade_cost}"
        )
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Отмена", callback_data="business_my")
    )
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("business_upgrade_confirm_"))
async def business_upgrade_confirm(callback: CallbackQuery):
    parts = callback.data.split("_")
    ub_id = int(parts[3])
    cost = int(parts[4])
    
    success = await db.upgrade_business(callback.from_user.id, ub_id, cost)
    
    if success:
        await callback.answer("✅ Бизнес улучшен!", show_alert=True)
    else:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
    
    await my_businesses(callback)


@router.callback_query(F.data.startswith("business_sell_"))
async def business_sell(callback: CallbackQuery):
    ub_id = int(callback.data.split("_")[2])
    
    user_businesses = await db.get_user_businesses(callback.from_user.id)
    ub = next((b for b in user_businesses if b['id'] == ub_id), None)
    
    if not ub:
        await callback.answer("❌ Бизнес не найден!", show_alert=True)
        return
    
    sell_price = ub['base_price'] // 2
    
    text = f"""
💸 <b>Продажа бизнеса</b>

{ub['emoji']} <b>{ub['name']}</b>

⚠️ Вы уверены, что хотите продать бизнес?

💰 Вы получите: <b>{format_number(sell_price)} VC</b>
(50% от изначальной стоимости)
"""
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"✅ Продать за {format_number(sell_price)} VC",
            callback_data=f"business_sell_confirm_{ub_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Отмена", callback_data="business_my")
    )
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("business_sell_confirm_"))
async def business_sell_confirm(callback: CallbackQuery):
    ub_id = int(callback.data.split("_")[3])
    
    sell_price = await db.sell_business(callback.from_user.id, ub_id)
    
    if sell_price > 0:
        await callback.answer(f"✅ Бизнес продан за {format_number(sell_price)} VC!", show_alert=True)
    else:
        await callback.answer("❌ Ошибка при продаже!", show_alert=True)
    
    await my_businesses(callback)


@router.callback_query(F.data.startswith("business_tax_"))
async def business_tax(callback: CallbackQuery):
    ub_id = int(callback.data.split("_")[2])
    
    tax, error = await db.pay_business_tax(callback.from_user.id, ub_id)
    
    if error:
        await callback.answer(f"❌ {error}", show_alert=True)
    else:
        await callback.answer(f"✅ Налог {format_number(tax)} VC оплачен!", show_alert=True)
    
    await my_businesses(callback)


# Налоги в банке
@router.callback_query(F.data == "bank_taxes")
async def bank_taxes(callback: CallbackQuery):
    user_businesses = await db.get_user_businesses(callback.from_user.id)
    
    if not user_businesses:
        text = f"""
{EMOJI['tax']} <b>Налоги</b>

У вас нет бизнесов, налоги не требуются.
"""
        await callback.message.edit_text(text, reply_markup=get_back_button("menu_bank"), parse_mode="HTML")
        return
    
    text = f"""
{EMOJI['tax']} <b>Налоги на бизнесы</b>

{EMOJI['info']} Налог = 10% от стоимости бизнеса в день

<b>Ваши бизнесы:</b>
"""
    
    builder = InlineKeyboardBuilder()
    total_tax = 0
    
    for ub in user_businesses:
        tax = ub['base_price'] // 10
        total_tax += tax
        status = "✅" if ub['tax_paid_until'] >= datetime.now().date() else "⚠️"
        
        text += f"""
{ub['emoji']} <b>{ub['name']}</b>
├ Налог: <b>{format_number(tax)} VC/день</b>
├ Оплачено до: <b>{ub['tax_paid_until'].strftime('%d.%m.%Y')}</b>
└ Статус: {status}
"""
        
        builder.row(
            InlineKeyboardButton(
                text=f"💳 Оплатить {ub['name']} ({format_number(tax)})",
                callback_data=f"business_tax_{ub['id']}"
            )
        )
    
    text += f"\n💰 <b>Всего налогов:</b> {format_number(total_tax)} VC/день"
    
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Назад", callback_data="menu_bank")
    )
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
