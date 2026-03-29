import asyncio
import logging
from datetime import datetime, time
import pytz
import random

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import BOT_TOKEN, CHANNEL_ID, CHAT_ID, EMOJI
from database import db
from utils.formatters import format_number

# Импорт хендлеров
from handlers import (
    start, profile, help, promo, tasks, top,
    farm, jobs, bank, market,
    jackpot, president, business, admin,
    bonus, games_menu
)
from handlers.games import (
    mines, diamonds, crash, roulette,
    telegram_games, blackjack, knb,
    labyrinth, higher_lower
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

scheduler = AsyncIOScheduler(timezone=pytz.timezone('Europe/Moscow'))


async def update_vt_price():
    """Обновление цены VT каждый час"""
    new_price = await db.update_vt_price()
    logger.info(f"VT price updated: {new_price}")


async def draw_jackpot():
    """Розыгрыш джекпота раз в сутки"""
    result = await db.draw_jackpot()
    if result:
        winner, amount = result
        try:
            await bot.send_message(
                CHAT_ID,
                f"""
{EMOJI['jackpot']} <b>ДЖЕКПОТ СОРВАН!</b>

{EMOJI['trophy']} Победитель: <b>{winner['first_name']}</b>
{EMOJI['coin']} Выигрыш: <b>{format_number(amount)} VC</b>

🎉 Поздравляем!
""",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to send jackpot message: {e}")


async def elect_president():
    """Выборы президента раз в сутки в 00:07"""
    winner = await db.elect_president()
    if winner:
        try:
            await bot.send_message(
                CHAT_ID,
                f"""
{EMOJI['president']} <b>НОВЫЙ ПРЕЗИДЕНТ!</b>

👨‍💼 <b>{winner['first_name']}</b> избран президентом!
💰 Ставка: <b>{format_number(winner['bet_amount'])} VC</b>

Президент будет получать 0.01% от всех операций в боте!

📊 Проигравшим возвращено 50% ставок.
""",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to send president message: {e}")


async def send_daily_bonus():
    """Отправка ежедневного бонуса в группу в 16:50"""
    bonus_amount = 15000000
    max_activations = random.randint(50, 500)
    
    bonus = await db.create_daily_bonus(bonus_amount, max_activations)
    
    try:
        await bot.send_message(
            CHANNEL_ID,
            f"""
{EMOJI['gift']} <b>Бонус {format_number(bonus_amount)} VC</b> | от {max_activations} активаций

🆘 Для получения введи в комментариях слово <b>«Бонус»</b>
{EMOJI['bell']} Включи уведомления чтобы не пропустить раздачу!
""",
            parse_mode="HTML"
        )
        logger.info(f"Daily bonus sent: {bonus_amount} VC, {max_activations} activations")
    except Exception as e:
        logger.error(f"Failed to send bonus message: {e}")


async def reset_jackpot_registrations():
    """Сброс регистраций на джекпот после розыгрыша"""
    # Уже сбрасывается в draw_jackpot
    pass


async def on_startup():
    """Действия при запуске бота"""
    await db.connect()
    logger.info("Database connected")
    
    # Планировщик задач
    # Обновление цены VT каждый час
    scheduler.add_job(update_vt_price, CronTrigger(minute=0))
    
    # Розыгрыш джекпота в полночь
    scheduler.add_job(draw_jackpot, CronTrigger(hour=0, minute=0))
    
    # Выборы президента в 00:07
    scheduler.add_job(elect_president, CronTrigger(hour=0, minute=7))
    
    # Ежедневный бонус в 16:50
    scheduler.add_job(send_daily_bonus, CronTrigger(hour=16, minute=50))
    
    scheduler.start()
    logger.info("Scheduler started")
    
    # Информация о боте
    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username}")


async def on_shutdown():
    """Действия при остановке бота"""
    scheduler.shutdown()
    logger.info("Bot shutdown")


async def main():
    # Регистрация роутеров - базовые
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(help.router)
    dp.include_router(promo.router)
    dp.include_router(tasks.router)
    dp.include_router(top.router)
    
    # Функции
    dp.include_router(farm.router)
    dp.include_router(jobs.router)
    dp.include_router(bank.router)
    dp.include_router(market.router)
    dp.include_router(jackpot.router)
    dp.include_router(president.router)
    dp.include_router(business.router)
    dp.include_router(admin.router)
    dp.include_router(bonus.router)
    dp.include_router(games_menu.router)
    
    # Игры
    dp.include_router(mines.router)
    dp.include_router(diamonds.router)
    dp.include_router(crash.router)
    dp.include_router(roulette.router)
    dp.include_router(telegram_games.router)
    dp.include_router(blackjack.router)
    dp.include_router(knb.router)
    dp.include_router(labyrinth.router)
    dp.include_router(higher_lower.router)
    
    # События запуска/остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
