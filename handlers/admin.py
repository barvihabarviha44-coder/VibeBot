from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import db
from config import ADMIN_IDS, EMOJI
from utils.formatters import format_number

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    users_count = await db.get_all_users_count()
    jackpot = await db.get_jackpot()
    
    text = f"""
{EMOJI['crown']} <b>Админ-панель</b>

👥 Пользователей: <b>{users_count}</b>
💰 Джекпот: <b>{format_number(jackpot['amount'])} VC</b>

<b>Команды:</b>
/ban [ID] - забанить пользователя
/unban [ID] - разбанить пользователя
/give [ID] [сумма] - выдать VC
/givevt [ID] [сумма] - выдать VT
/userinfo [ID] - информация о пользователе
/promo [код] [тип] [сумма] [макс.исп] - создать промокод
/addbiz [название] [цена] [прибыль] - добавить бизнес
/addslot [ID] - добавить слот бизнеса
/broadcast [текст] - рассылка
"""
    await message.answer(text, parse_mode="HTML")


@router.message(Command("ban"))
async def ban_user(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /ban [ID]")
        return
    
    try:
        user_id = int(parts[1])
    except:
        await message.answer("Неверный ID!")
        return
    
    await db.ban_user(user_id, True)
    await message.answer(f"✅ Пользователь {user_id} забанен!")


@router.message(Command("unban"))
async def unban_user(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /unban [ID]")
        return
    
    try:
        user_id = int(parts[1])
    except:
        await message.answer("Неверный ID!")
        return
    
    await db.ban_user(user_id, False)
    await message.answer(f"✅ Пользователь {user_id} разбанен!")


@router.message(Command("give"))
async def give_vc(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Использование: /give [ID] [сумма]")
        return
    
    try:
        user_id = int(parts[1])
        amount_str = parts[2].lower().replace('к', '000').replace('кк', '000000')
        amount = int(float(amount_str))
    except:
        await message.answer("Неверные параметры!")
        return
    
    await db.update_balance(user_id, amount, add=True)
    await message.answer(f"✅ Выдано {format_number(amount)} VC пользователю {user_id}!")


@router.message(Command("givevt"))
async def give_vt(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Использование: /givevt [ID] [сумма]")
        return
    
    try:
        user_id = int(parts[1])
        amount = float(parts[2])
    except:
        await message.answer("Неверные параметры!")
        return
    
    await db.update_vt_balance(user_id, amount, add=True)
    await message.answer(f"✅ Выдано {amount} VT пользователю {user_id}!")


@router.message(Command("userinfo"))
async def user_info(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /userinfo [ID]")
        return
    
    try:
        user_id = int(parts[1])
    except:
        await message.answer("Неверный ID!")
        return
    
    user = await db.get_user(user_id)
    if not user:
        await message.answer("Пользователь не найден!")
        return
    
    text = f"""
{EMOJI['user']} <b>Информация о пользователе</b>

🆔 ID: <code>{user['user_id']}</code>
👤 Имя: {user['first_name']}
📝 Username: @{user['username'] or 'нет'}

{EMOJI['coin']} Баланс: <b>{format_number(user['balance'])} VC</b>
🏦 Банк: <b>{format_number(user['bank_balance'])} VC</b>
{EMOJI['diamond']} VT: <b>{float(user['vt_balance']):.2f}</b>

📊 Уровень: {user['level']}
✨ XP: {user['xp']}
🎮 Игр: {user['games_played']}
🏆 Побед: {user['games_won']}

📅 Регистрация: {user['registered_at'].strftime('%d.%m.%Y %H:%M')}
🔄 Активность: {user['last_activity'].strftime('%d.%m.%Y %H:%M')}
🚫 Бан: {'Да' if user['is_banned'] else 'Нет'}
"""
    await message.answer(text, parse_mode="HTML")


@router.message(Command("promo"))
async def create_promo(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) < 5:
        await message.answer("Использование: /promo [код] [vc/vt] [сумма] [макс.исп]")
        return
    
    try:
        code = parts[1]
        reward_type = parts[2].lower()
        amount_str = parts[3].lower().replace('к', '000').replace('кк', '000000')
        amount = int(float(amount_str))
        max_uses = int(parts[4])
    except:
        await message.answer("Неверные параметры!")
        return
    
    if reward_type not in ['vc', 'vt']:
        await message.answer("Тип награды: vc или vt")
        return
    
    await db.create_promocode(code, reward_type, amount, max_uses)
    await message.answer(f"✅ Промокод {code} создан!\nНаграда: {format_number(amount)} {reward_type.upper()}\nМакс. использований: {max_uses}")


@router.message(Command("addbiz"))
async def add_business(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.answer("Использование: /addbiz [название] [цена] [прибыль/час]")
        return
    
    try:
        name = parts[1]
        price_str = parts[2].lower().replace('к', '000').replace('кк', '000000')
        price = int(float(price_str))
        profit_str = parts[3].lower().replace('к', '000').replace('кк', '000000')
        profit = int(float(profit_str))
    except:
        await message.answer("Неверные параметры!")
        return
    
    await db.add_business(name, price, profit)
    await message.answer(f"✅ Бизнес «{name}» добавлен!\nЦена: {format_number(price)} VC\nПрибыль: {format_number(profit)} VC/час")


@router.message(Command("addslot"))
async def add_slot(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /addslot [ID]")
        return
    
    try:
        user_id = int(parts[1])
    except:
        await message.answer("Неверный ID!")
        return
    
    await db.add_business_slot(user_id)
    await message.answer(f"✅ Слот бизнеса добавлен пользователю {user_id}!")
