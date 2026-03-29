from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import db
from config import EMOJI
from utils.formatters import format_number
from keyboards.inline import get_top_menu, get_back_button

router = Router()


@router.callback_query(F.data == "menu_top")
async def top_menu(callback: CallbackQuery):
    text = f"""
{EMOJI['trophy']} <b>Топ игроков</b>

Выберите категорию:
"""
    await callback.message.edit_text(text, reply_markup=get_top_menu(), parse_mode="HTML")


@router.callback_query(F.data == "top_vc")
async def top_vc(callback: CallbackQuery):
    top_users = await db.get_top_by_balance(10)
    
    text = f"""
{EMOJI['trophy']} <b>Топ-10 по VC</b>

"""
    
    medals = ["🥇", "🥈", "🥉"]
    
    for i, user in enumerate(top_users):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} <b>{user['first_name']}</b> — {format_number(user['balance'])} VC\n"
    
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_top"), parse_mode="HTML")


@router.callback_query(F.data == "top_vt")
async def top_vt(callback: CallbackQuery):
    top_users = await db.get_top_by_vt(10)
    
    text = f"""
{EMOJI['trophy']} <b>Топ-10 по VibeTon</b>

"""
    
    medals = ["🥇", "🥈", "🥉"]
    
    for i, user in enumerate(top_users):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} <b>{user['first_name']}</b> — {float(user['vt_balance']):.2f} VT\n"
    
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_top"), parse_mode="HTML")
