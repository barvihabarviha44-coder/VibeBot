import asyncio
import logging
import random
import pytz

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import BOT_TOKEN, CHANNEL_ID, EMOJI
from database import db
from utils.formatters import format_number

from handlers import (
    start, profile, help, promo, tasks, top,
    farm, jobs, bank, market, jackpot,
    president, business, admin, bonus,
    bonuses, reputation
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
    new_price = await db.update_vt_price()
    logger.info(f"VT price updated: {new_price}")


async def draw_jackpot():
    result = await db.draw_jackpot()
    if result:
        winner, amount = result
        try:
            await bot.send_message(
                CHANNEL_ID,
                f"""
🎰 <b>ДЖЕКПОТ СОРВАН!</b>

👤 Победитель: <b>{winner['first_name']}</b>
💰 Выигрыш: <b>{format_number(amount)} VC</b>
""",
                parse_mode="HTML"
            )
            try:
                await bot.send_message(
                    winner['user_id'],
                    f"🎉 <b>Вы выиграли ДжекПот!</b>\n💰 +{format_number(amount)} VC",
                    parse_mode="HTML"
                )
            except:
                pass
        except Exception as e:
            logger.error(f"Failed to send jackpot message: {e}")


async def elect_president():
    winner = await db.elect_president()
    if winner:
        try:
            await bot.send_message(
                CHANNEL_ID,
                f"""
👨‍💼 <b>НОВЫЙ ПРЕЗИДЕНТ!</b>

👤 <b>{winner['first_name']}</b>
💰 Ставка: <b>{format_number(winner['bet_amount'])} VC</b>

Президент получает 0.01% от всех операций!
""",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to send president message: {e}")


async def send_daily_bonus_post():
    bonus_amount = 15000000
    max_activations = random.randint(50, 500)

    await db.create_daily_bonus(bonus_amount, max_activations)

    try:
        await bot.send_message(
            CHANNEL_ID,
            f"""
🎁 <b>Бонус {format_number(bonus_amount)} VC</b>

🎁 Активаций: <b>{max_activations}</b>

🆘 Для получения напишите в комментариях: <b>Бонус</b>
🔔 Включите уведомления!
""",
            parse_mode="HTML"
        )
        logger.info("Daily bonus post sent")
    except Exception as e:
        logger.error(f"Failed to send daily bonus post: {e}")


async def on_startup():
    await db.connect()
    logger.info("Database connected")

    scheduler.add_job(update_vt_price, CronTrigger(minute=0))
    scheduler.add_job(draw_jackpot, CronTrigger(hour=0, minute=0))
    scheduler.add_job(elect_president, CronTrigger(hour=0, minute=7))
    scheduler.add_job(send_daily_bonus_post, CronTrigger(hour=16, minute=50))

    scheduler.start()
    logger.info("Scheduler started")

    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username}")


async def on_shutdown():
    scheduler.shutdown()
    logger.info("Bot shutdown")


async def main():
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(help.router)
    dp.include_router(promo.router)
    dp.include_router(tasks.router)
    dp.include_router(top.router)

    dp.include_router(farm.router)
    dp.include_router(jobs.router)
    dp.include_router(bank.router)
    dp.include_router(market.router)
    dp.include_router(jackpot.router)
    dp.include_router(president.router)
    dp.include_router(business.router)
    dp.include_router(admin.router)
    dp.include_router(bonus.router)
    dp.include_router(bonuses.router)
    dp.include_router(reputation.router)

    dp.include_router(mines.router)
    dp.include_router(diamonds.router)
    dp.include_router(crash.router)
    dp.include_router(roulette.router)
    dp.include_router(telegram_games.router)
    dp.include_router(blackjack.router)
    dp.include_router(knb.router)
    dp.include_router(labyrinth.router)
    dp.include_router(higher_lower.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
