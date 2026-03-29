from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database import db
from config import EMOJI, JOBS_CONFIG
from utils.formatters import format_number, create_progress_bar
from keyboards.inline import get_back_button
import random
import asyncio
from datetime import datetime, timedelta

router = Router()

# Хранение активных работ пользователей
active_jobs = {}


def get_jobs_menu(user_level: int):
    builder = InlineKeyboardBuilder()
    
    for i, job in enumerate(JOBS_CONFIG):
        if user_level >= job['min_level']:
            builder.row(
                InlineKeyboardButton(
                    text=f"{job['emoji']} {job['name']} (Ур.{job['min_level']}+)",
                    callback_data=f"job_start_{i}"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text=f"🔒 {job['name']} (Ур.{job['min_level']})",
                    callback_data=f"job_locked_{i}"
                )
            )
    
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Назад", callback_data="menu_main")
    )
    return builder.as_markup()


@router.message(F.text.lower().in_(['работа', 'работать', 'раб']))
async def jobs_command(message: Message):
    await show_jobs(message)


@router.callback_query(F.data == "menu_jobs")
async def jobs_callback(callback: CallbackQuery):
    await show_jobs(callback, edit=True)


async def show_jobs(target, edit: bool = False):
    user = await db.get_user(target.from_user.id)
    
    # Проверяем активную работу
    if target.from_user.id in active_jobs:
        job_data = active_jobs[target.from_user.id]
        remaining = (job_data['end_time'] - datetime.now()).total_seconds()
        if remaining > 0:
            job = JOBS_CONFIG[job_data['job_index']]
            progress = 1 - (remaining / job_data['duration'])
            
            text = f"""
{EMOJI['work']} <b>Работа</b>

{job['emoji']} Вы работаете: <b>{job['name']}</b>

{create_progress_bar(int(progress * 100), 100, 15)} {int(progress * 100)}%

⏱ Осталось: <b>{int(remaining // 60)} мин. {int(remaining % 60)} сек.</b>
💰 Зарплата: <b>{format_number(job_data['salary'])} VC</b>
"""
            if edit:
                await target.message.edit_text(text, reply_markup=get_back_button("menu_main"), parse_mode="HTML")
            else:
                await target.answer(text, reply_markup=get_back_button("menu_main"), parse_mode="HTML")
            return
        else:
            # Работа завершена
            salary = job_data['salary']
            await db.update_balance(target.from_user.id, salary, add=True)
            del active_jobs[target.from_user.id]
            
            if edit:
                await target.answer(f"✅ Работа завершена! Получено {format_number(salary)} VC")
    
    text = f"""
{EMOJI['work']} <b>Работа</b>

{EMOJI['level']} Ваш уровень: <b>{user['level']}</b>

{EMOJI['info']} Выберите работу. Чем выше уровень, тем лучше работа доступна!

<b>Доступные работы:</b>
"""
    
    for job in JOBS_CONFIG:
        status = "✅" if user['level'] >= job['min_level'] else "🔒"
        text += f"\n{status} {job['emoji']} <b>{job['name']}</b> — {format_number(job['min_salary'])}-{format_number(job['max_salary'])} VC"
    
    if edit:
        await target.message.edit_text(text, reply_markup=get_jobs_menu(user['level']), parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=get_jobs_menu(user['level']), parse_mode="HTML")


@router.callback_query(F.data.startswith("job_start_"))
async def start_job(callback: CallbackQuery):
    job_index = int(callback.data.split("_")[2])
    job = JOBS_CONFIG[job_index]
    
    user = await db.get_user(callback.from_user.id)
    
    if user['level'] < job['min_level']:
        await callback.answer(f"❌ Требуется уровень {job['min_level']}!", show_alert=True)
        return
    
    if callback.from_user.id in active_jobs:
        await callback.answer("❌ Вы уже работаете!", show_alert=True)
        return
    
    salary = random.randint(job['min_salary'], job['max_salary'])
    duration = job['duration']
    
    active_jobs[callback.from_user.id] = {
        'job_index': job_index,
        'salary': salary,
        'duration': duration,
        'end_time': datetime.now() + timedelta(seconds=duration),
        'start_time': datetime.now()
    }
    
    text = f"""
{EMOJI['check']} <b>Вы начали работу!</b>

{job['emoji']} Работа: <b>{job['name']}</b>
⏱ Длительность: <b>{duration // 60} мин.</b>
💰 Зарплата: <b>{format_number(salary)} VC</b>

{create_progress_bar(0, 100, 15)} 0%
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_jobs"), parse_mode="HTML")
    
    # Запускаем обновление прогресса
    asyncio.create_task(update_job_progress(callback, job, salary, duration))


async def update_job_progress(callback, job, salary, duration):
    start_time = datetime.now()
    msg = callback.message
    
    while callback.from_user.id in active_jobs:
        await asyncio.sleep(10)
        
        if callback.from_user.id not in active_jobs:
            break
        
        elapsed = (datetime.now() - start_time).total_seconds()
        remaining = duration - elapsed
        
        if remaining <= 0:
            # Работа завершена
            await db.update_balance(callback.from_user.id, salary, add=True)
            del active_jobs[callback.from_user.id]
            
            text = f"""
{EMOJI['check']} <b>Работа завершена!</b>

{job['emoji']} Работа: <b>{job['name']}</b>
💰 Получено: <b>{format_number(salary)} VC</b>
"""
            try:
                await msg.edit_text(text, reply_markup=get_back_button("menu_jobs"), parse_mode="HTML")
            except:
                pass
            break
        
        progress = elapsed / duration
        
        text = f"""
{EMOJI['work']} <b>Работа</b>

{job['emoji']} Вы работаете: <b>{job['name']}</b>

{create_progress_bar(int(progress * 100), 100, 15)} {int(progress * 100)}%

⏱ Осталось: <b>{int(remaining // 60)} мин. {int(remaining % 60)} сек.</b>
💰 Зарплата: <b>{format_number(salary)} VC</b>
"""
        try:
            await msg.edit_text(text, reply_markup=get_back_button("menu_main"), parse_mode="HTML")
        except:
            pass


@router.callback_query(F.data.startswith("job_locked_"))
async def job_locked(callback: CallbackQuery):
    job_index = int(callback.data.split("_")[2])
    job = JOBS_CONFIG[job_index]
    await callback.answer(f"🔒 Требуется уровень {job['min_level']}!", show_alert=True)
