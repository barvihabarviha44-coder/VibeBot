from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import db
from config import EMOJI
from utils.formatters import format_number
from keyboards.inline import get_back_button

router = Router()

TASK_NAMES = {
    'labyrinth_play': 'Сыграть в игру «Лабиринт»',
    'higher_lower_win': 'Выиграть в игре «Больше меньше»',
    'knb_play': 'Сыграть в игру «КНБ»',
    'crash_win': 'Выиграть в игре «Краш»',
    'mines_play': 'Сыграть в игру «Мины»',
    'diamonds_play': 'Сыграть в игру «Алмазы»',
    'crash_play': 'Сыграть в игру «Краш»',
}


@router.message(F.text.lower().in_(['задания', 'задачи', 'квесты']))
async def tasks_command(message: Message):
    await show_tasks(message)


@router.callback_query(F.data == "menu_tasks")
async def tasks_callback(callback: CallbackQuery):
    await show_tasks(callback, edit=True)


async def show_tasks(target, edit: bool = False):
    tasks = await db.generate_daily_tasks(target.from_user.id)
    
    text = f"""
{EMOJI['task']} <b>Ежедневные задания</b>

"""
    
    total_vc = 0
    total_vt = 0
    
    for task in tasks:
        status = "✅" if task['is_completed'] else "📋"
        task_name = TASK_NAMES.get(task['task_type'], task['task_type'])
        text += f"""• {task_name}
{status} Прогресс: [{task['task_progress']}/{task['task_target']}]

"""
        total_vc += task['reward_vc']
        total_vt += task['reward_vt']
    
    text += f"""──────────
{EMOJI['trophy']} <b>Призы за выполнение:</b>
• {format_number(total_vc)} VC
• {total_vt} VT

❗ Задания обновляются в 00:00 по МСК.
"""
    
    if edit:
        await target.message.edit_text(text, reply_markup=get_back_button(), parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=get_back_button(), parse_mode="HTML")
