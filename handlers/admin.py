from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import db
from config import ADMIN_IDS, EMOJI, CHAT_ID
from utils.formatters import format_number
import random

router = Router()


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    users_count = await db.get_all_users_count()
    jackpot = await db.get_jackpot()
    
    text = f"""
{EMOJI['crown']} <b>Админ-панель</b>

👥 Пользователей: <b>{users_count}</b>
💰 Джекпот: <b>{format_number(jackpot['amount'])} VC</b>

<b>Команды:</b>
/ban [ID] — забанить
/unban [ID] — разбанить
/give [ID] [сумма] — выдать VC
/givevt [ID] [сумма] — выдать VT
/userinfo [ID] — инфо о юзере
/promo [код] [vc/vt] [сумма] [макс] — промокод
/addbiz [название] [цена] [прибыль] — бизнес
/addslot [ID] — слот бизнеса
/broadcast [текст] — рассылка

<b>Принудительный запуск:</b>
/forcejackpot — розыгрыш джекпота
/forcepresident — выборы президента
/forcebonus — отправить бонус
"""
    await message.answer(text, parse_mode="HTML")


@router.message(Command("ban"))
async def ban_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ /ban [ID]")
        return
    
    try:
        user_id = int(args[1])
        await db.ban_user(user_id, True)
        await message.answer(f"✅ Пользователь {user_id} забанен!")
    except:
        await message.answer("❌ Неверный ID!")


@router.message(Command("unban"))
async def unban_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ /unban [ID]")
        return
    
    try:
        user_id = int(args[1])
        await db.ban_user(user_id, False)
        await message.answer(f"✅ Пользователь {user_id} разбанен!")
    except:
        await message.answer("❌ Неверный ID!")


@router.message(Command("give"))
async def give_vc(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ /give [ID] [сумма]")
        return
    
    try:
        from utils.formatters import parse_bet
        user_id = int(args[1])
        amount = parse_bet(args[2])
        
        target_user = await db.get_user(user_id)
        if not target_user:
            await message.answer("❌ Пользователь не найден!")
            return
        
        await db.update_balance(user_id, amount, add=True)
        await message.answer(f"✅ Выдано {format_number(amount)} VC пользователю {user_id}!")
    except:
        await message.answer("❌ Ошибка!")


@router.message(Command("givevt"))
async def give_vt(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ /givevt [ID] [сумма]")
        return
    
    try:
        user_id = int(args[1])
        amount = float(args[2])
        
        target_user = await db.get_user(user_id)
        if not target_user:
            await message.answer("❌ Пользователь не найден!")
            return
        
        await db.update_vt_balance(user_id, amount, add=True)
        await message.answer(f"✅ Выдано {amount} VT пользователю {user_id}!")
    except:
        await message.answer("❌ Ошибка!")


@router.message(Command("userinfo"))
async def user_info(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ /userinfo [ID]")
        return
    
    try:
        user_id = int(args[1])
        user = await db.get_user(user_id)
        
        if not user:
            await message.answer("❌ Пользователь не найден!")
            return
        
        text = f"""
👤 <b>Пользователь {user_id}</b>

Имя: {user['first_name']}
Username: @{user['username'] or 'нет'}
Баланс: {format_number(user['balance'])} VC
Банк: {format_number(user['bank_balance'])} VC
VT: {float(user['vt_balance']):.2f}
Уровень: {user['level']}
Игр: {user['games_played']}
Бан: {'Да' if user['is_banned'] else 'Нет'}
"""
        await message.answer(text, parse_mode="HTML")
    except:
        await message.answer("❌ Ошибка!")


@router.message(Command("promo"))
async def create_promo(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    if len(args) < 5:
        await message.answer("❌ /promo [код] [vc/vt] [сумма] [макс]")
        return
    
    try:
        from utils.formatters import parse_bet
        code = args[1].upper()
        reward_type = args[2].lower()
        amount = parse_bet(args[3])
        max_uses = int(args[4])
        
        if reward_type not in ['vc', 'vt']:
            await message.answer("❌ Тип: vc или vt")
            return
        
        await db.create_promocode(code, reward_type, amount, max_uses)
        await message.answer(f"✅ Промокод <code>{code}</code> создан!\n💰 {format_number(amount)} {reward_type.upper()}\n👥 Макс: {max_uses}", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("addbiz"))
async def add_business(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    if len(args) < 4:
        await message.answer("❌ /addbiz [название] [цена] [прибыль]")
        return
    
    try:
        from utils.formatters import parse_bet
        name = args[1]
        price = parse_bet(args[2])
        profit = parse_bet(args[3])
        
        await db.add_business(name, price, profit)
        await message.answer(f"✅ Бизнес «{name}» добавлен!\n💰 Цена: {format_number(price)} VC\n📈 Прибыль: {format_number(profit)} VC/час", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("addslot"))
async def add_slot(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ /addslot [ID]")
        return
    
    try:
        user_id = int(args[1])
        await db.add_business_slot(user_id)
        await message.answer(f"✅ Слот добавлен пользователю {user_id}!")
    except:
        await message.answer("❌ Ошибка!")


@router.message(Command("broadcast"))
async def broadcast(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("❌ /broadcast [текст]")
        return
    
    async with db.pool.acquire() as conn:
        users = await conn.fetch("SELECT user_id FROM users WHERE is_banned = FALSE")
    
    sent = 0
    for user in users:
        try:
            await message.bot.send_message(user['user_id'], text, parse_mode="HTML")
            sent += 1
        except:
            pass
    
    await message.answer(f"✅ Отправлено: {sent}")


# ==================== ПРИНУДИТЕЛЬНЫЙ ЗАПУСК ====================

@router.message(Command("forcejackpot"))
async def force_jackpot(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    result = await db.draw_jackpot()
    
    if not result:
        await message.answer("❌ Нет участников джекпота!")
        return
    
    winner, amount = result
    
    try:
        await message.bot.send_message(
            CHAT_ID,
            f"""
{EMOJI['jackpot']} <b>ДЖЕКПОТ СОРВАН!</b>

👤 Победитель: <b>{winner['first_name']}</b>
💰 Выигрыш: <b>{format_number(amount)} VC</b>
""",
            parse_mode="HTML"
        )
        
        await message.bot.send_message(
            winner['user_id'],
            f"🎉 Вы выиграли ДжекПот! +{format_number(amount)} VC",
            parse_mode="HTML"
        )
    except:
        pass
    
    await message.answer(f"✅ Джекпот разыгран!\nПобедитель: {winner['first_name']} ({winner['user_id']})\nСумма: {format_number(amount)} VC")


@router.message(Command("forcepresident"))
async def force_president(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    winner = await db.elect_president()
    
    if not winner:
        await message.answer("❌ Нет ставок на президента!")
        return
    
    try:
        await message.bot.send_message(
            CHAT_ID,
            f"""
{EMOJI['president']} <b>НОВЫЙ ПРЕЗИДЕНТ!</b>

👤 <b>{winner['first_name']}</b>
💰 Ставка: <b>{format_number(winner['bet_amount'])} VC</b>
""",
            parse_mode="HTML"
        )
    except:
        pass
    
    await message.answer(f"✅ Президент избран!\n{winner['first_name']} ({winner['user_id']})")


@router.message(Command("forcebonus"))
async def force_bonus(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    bonus_amount = 15000000
    max_activations = random.randint(50, 500)
    
    await db.create_daily_bonus(bonus_amount, max_activations)
    
    try:
        await message.bot.send_message(
            CHAT_ID,
            f"""
{EMOJI['gift']} <b>Бонус {format_number(bonus_amount)} VC</b>

🎁 Активаций: <b>{max_activations}</b>

🆘 Напишите: <b>Бонус</b>
""",
            parse_mode="HTML"
        )
        await message.answer(f"✅ Бонус отправлен в чат!\n{format_number(bonus_amount)} VC, {max_activations} активаций")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}\n\nПроверьте:\n1. Бот добавлен в чат {CHAT_ID}\n2. Бот админ чата")
