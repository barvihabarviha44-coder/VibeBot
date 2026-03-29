from aiogram import Router, F
from aiogram.types import CallbackQuery
from config import EMOJI
from keyboards.inline import get_games_menu, get_back_button

router = Router()


@router.callback_query(F.data == "menu_games")
async def games_menu(callback: CallbackQuery):
    text = f"""
{EMOJI['slot']} <b>Игры VibeBet</b>

{EMOJI['info']} Выберите игру:

{EMOJI['gem']} <b>Алмазы</b> — найдите алмаз среди 4 ячеек
{EMOJI['bomb']} <b>Мины</b> — избегайте мин на поле 5x5
{EMOJI['rocket']} <b>Краш</b> — успейте забрать до краша
{EMOJI['slot']} <b>Рулетка</b> — классическая рулетка 0-36
{EMOJI['dice']} <b>Кости</b> — угадайте сумму двух кубиков
{EMOJI['football']} <b>Футбол</b> — гол или мимо
{EMOJI['basketball']} <b>Баскетбол</b> — попадёт или нет
{EMOJI['darts']} <b>Дартс</b> — в какой сектор попадёт
{EMOJI['bowling']} <b>Боулинг</b> — страйк или нет
🃏 <b>Блэкджек</b> — набери 21 очко
✊ <b>КНБ</b> — камень-ножницы-бумага
{EMOJI['door']} <b>Лабиринт</b> — выбери правильную дверь
⬆️ <b>Больше/Меньше</b> — угадай следующее число
"""
    await callback.message.edit_text(text, reply_markup=get_games_menu(), parse_mode="HTML")


# Callback для информации об играх
@router.callback_query(F.data == "game_diamonds")
async def game_diamonds_info(callback: CallbackQuery):
    text = f"""
{EMOJI['info']} <b>Алмазная лихорадка</b>

💎 Это игра, в которой необходимо угадать, в какой ячейке спрятан алмаз. Вам нужно открывать по одной ячейке на каждом из 16 уровней, чтобы найти алмаз.

{EMOJI['gem']} Чтобы начать игру, используй команду:

<code>алмазы [ставка] [сложность 1-2]</code>

<b>Пример:</b> <code>алмазы 100к 2</code>
<b>Пример:</b> <code>алмазы 100к</code>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")


@router.callback_query(F.data == "game_mines")
async def game_mines_info(callback: CallbackQuery):
    text = f"""
{EMOJI['info']} <b>Мины</b>

💣 Это игра, в которой вам нужно угадать пустые ячейки. Чем больше ячеек вы откроете, тем больше получите VC!

{EMOJI['bomb']} Чтобы начать игру, используй команду:

<code>мины [ставка] [мины 1-6]</code>

<b>Пример:</b> <code>мины 100к 3</code>
<b>Пример:</b> <code>мины 100к</code>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")


@router.callback_query(F.data == "game_crash")
async def game_crash_info(callback: CallbackQuery):
    text = f"""
{EMOJI['info']} <b>Краш</b>

🚀 Множитель растёт от x1.00 до x505! Успейте забрать выигрыш до того, как произойдёт краш.

{EMOJI['rocket']} Чтобы начать игру, используй команду:

<code>краш [ставка]</code>

<b>Пример:</b> <code>краш 100к</code>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")


@router.callback_query(F.data == "game_roulette")
async def game_roulette_info(callback: CallbackQuery):
    text = f"""
{EMOJI['info']} <b>Рулетка</b>

🎰 Классическая казино рулетка! Числа от 0 до 36.

<b>Коэффициенты:</b>
├ 🔴 Красное / ⚫ Чёрное: <b>2x</b>
├ 🟢 Зеро (0): <b>36x</b>
└ Диапазоны (1-12, 13-24, 25-36): <b>3x</b>

{EMOJI['slot']} Чтобы начать игру, используй команду:

<code>рулетка [ставка]</code>

<b>Пример:</b> <code>рулетка 100к</code>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")


@router.callback_query(F.data == "game_football")
async def game_football_info(callback: CallbackQuery):
    text = f"""
{EMOJI['info']} <b>Футбол</b>

⚽ Угадайте результат удара по воротам!

<b>Коэффициенты:</b>
├ ⚽ Гол: <b>1.8x</b>
└ ❌ Мимо: <b>3.7x</b>

Чтобы начать игру, используй команду:

<code>футбол [ставка]</code>

<b>Пример:</b> <code>футбол 100к</code>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")


@router.callback_query(F.data == "game_basketball")
async def game_basketball_info(callback: CallbackQuery):
    text = f"""
{EMOJI['info']} <b>Баскетбол</b>

🏀 Угадайте результат броска!

<b>Коэффициенты:</b>
├ 🏀 Попадание: <b>3.8x</b>
└ ❌ Мимо: <b>1.9x</b>

Чтобы начать игру, используй команду:

<code>баскетбол [ставка]</code>

<b>Пример:</b> <code>баскетбол 100к</code>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")


@router.callback_query(F.data == "game_darts")
async def game_darts_info(callback: CallbackQuery):
    text = f"""
{EMOJI['info']} <b>Дартс</b>

🎯 Угадайте в какой сектор попадёт дротик!

<b>Коэффициенты:</b>
├ 🎯 Центр: <b>5.8x</b>
├ ⚪ Белое: <b>1.9x</b>
├ 🔴 Красное: <b>1.9x</b>
└ ❌ Мимо: <b>5.8x</b>

Чтобы начать игру, используй команду:

<code>дартс [ставка]</code>

<b>Пример:</b> <code>дартс 100к</code>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")


@router.callback_query(F.data == "game_bowling")
async def game_bowling_info(callback: CallbackQuery):
    text = f"""
{EMOJI['info']} <b>Боулинг</b>

🎳 Угадайте результат броска шара!

<b>Коэффициенты:</b>
├ 🎳 Страйк: <b>5.3x</b>
├ ❌ Мимо: <b>5.3x</b>
└ 📍 1-5 кеглей: <b>1.9x</b>

Чтобы начать игру, используй команду:

<code>боулинг [ставка]</code>

<b>Пример:</b> <code>боулинг 100к</code>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")


@router.callback_query(F.data == "game_blackjack")
async def game_blackjack_info(callback: CallbackQuery):
    text = f"""
{EMOJI['info']} <b>Блэкджек</b>

🃏 Классическая карточная игра! Цель — набрать 21 очко или больше, чем дилер, но не более 21.

<b>Коэффициенты:</b>
├ Победа: <b>2x</b>
├ Блэкджек (21 с 2 карт): <b>2.5x</b>
└ Ничья: возврат ставки

Чтобы начать игру, используй команду:

<code>блэкджек [ставка]</code>

<b>Пример:</b> <code>блэкджек 100к</code>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")


@router.callback_query(F.data == "game_knb")
async def game_knb_info(callback: CallbackQuery):
    text = f"""
{EMOJI['info']} <b>Камень-Ножницы-Бумага</b>

✊ Классическая игра! Победите бота.

<b>Коэффициент победы:</b> <b>2x</b>
<b>Ничья:</b> возврат ставки

Чтобы начать игру, используй команду:

<code>кнб [ставка]</code>

<b>Пример:</b> <code>кнб 100к</code>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")


@router.callback_query(F.data == "game_labyrinth")
async def game_labyrinth_info(callback: CallbackQuery):
    text = f"""
{EMOJI['info']} <b>Лабиринт</b>

🚪 На первом этапе вам предстоит выбрать между двумя дверьми, за одной из которых находится приз.

• С каждым новым этапом количество дверей увеличивается
• Выигрыш умножается на количество дверей
• Вы можете забрать приз на любом этапе
• Чем больше дверей, тем выше риск и награда!

Чтобы начать игру, используй команду:

<code>лабиринт [ставка]</code>

<b>Пример:</b> <code>лабиринт 100к</code>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")


@router.callback_query(F.data == "game_higher_lower")
async def game_hl_info(callback: CallbackQuery):
    text = f"""
{EMOJI['info']} <b>Больше/Меньше</b>

⬆️ Игрок делает ставку и пытается предугадать, будет ли следующее число больше или меньше текущего, четным или нечетным.

• Чем выше число, указанное рядом с событием, тем ниже вероятность его выпадения.
• Можно забрать выигрыш в любой момент.

Чтобы начать игру, используй команду:

<code>больше [ставка]</code>

<b>Пример:</b> <code>больше 100к</code>
"""
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")
