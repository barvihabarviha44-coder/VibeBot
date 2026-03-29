from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from config import EMOJI
from keyboards.inline import get_back_button

router = Router()


@router.message(F.text.lower().in_(['помощь', 'команды', 'help']))
async def help_command(message: Message):
    await show_help(message)


@router.callback_query(F.data == "menu_help")
async def help_callback(callback: CallbackQuery):
    await show_help(callback, edit=True)


async def show_help(target, edit: bool = False):
    text = f"""
{EMOJI['help']} <b>Центр помощи VibeBet</b>

{EMOJI['user']} <b>Профиль:</b>
<code>я</code>, <code>б</code>, <code>проф</code>, <code>профиль</code>, <code>п</code>

{EMOJI['slot']} <b>Игры:</b>
<code>мины [ставка] [мины 1-6]</code>
<code>алмазы [ставка]</code>
<code>краш [ставка]</code>
<code>рулетка [ставка]</code>
<code>кости [ставка]</code>
<code>футбол [ставка]</code>
<code>баскетбол [ставка]</code>
<code>боулинг [ставка]</code>
<code>дартс [ставка]</code>
<code>блэкджек [ставка]</code>
<code>кнб [ставка]</code>
<code>лабиринт [ставка]</code>
<code>больше [ставка]</code>

{EMOJI['work']} <b>Работа:</b>
<code>работа</code> - список работ

{EMOJI['farm']} <b>Ферма:</b>
<code>ферма</code> - управление фермой VT

{EMOJI['bank']} <b>Банк:</b>
<code>банк</code> - депозиты и переводы
<code>перевод [ID] [сумма]</code> - быстрый перевод

{EMOJI['market']} <b>Рынок:</b>
<code>рынок</code> - торговля VibeTon

{EMOJI['gift']} <b>Промокоды:</b>
<code>промокод [код]</code> - активировать промокод

{EMOJI['info']} <b>Форматы сумм:</b>
<code>100к</code> = 100,000
<code>1кк</code> = 1,000,000
"""
    
    if edit:
        await target.message.edit_text(text, reply_markup=get_back_button(), parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=get_back_button(), parse_mode="HTML")
