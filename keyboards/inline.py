from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import EMOJI

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['slot']} Игры", callback_data="menu_games"),
        InlineKeyboardButton(text=f"{EMOJI['user']} Профиль", callback_data="menu_profile")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['farm']} Ферма", callback_data="menu_farm"),
        InlineKeyboardButton(text=f"{EMOJI['work']} Работа", callback_data="menu_jobs")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['market']} Рынок", callback_data="menu_market"),
        InlineKeyboardButton(text=f"{EMOJI['bank']} Банк", callback_data="menu_bank")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['business']} Бизнес", callback_data="menu_business"),
        InlineKeyboardButton(text=f"{EMOJI['trophy']} Топ", callback_data="menu_top")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['jackpot']} Джекпот", callback_data="menu_jackpot"),
        InlineKeyboardButton(text=f"{EMOJI['president']} Президент", callback_data="menu_president")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['task']} Задания", callback_data="menu_tasks"),
        InlineKeyboardButton(text=f"{EMOJI['help']} Помощь", callback_data="menu_help")
    )
    return builder.as_markup()


def get_games_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['gem']} Алмазы", callback_data="game_diamonds"),
        InlineKeyboardButton(text=f"{EMOJI['bomb']} Мины", callback_data="game_mines")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['rocket']} Краш", callback_data="game_crash"),
        InlineKeyboardButton(text=f"{EMOJI['slot']} Рулетка", callback_data="game_roulette")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['dice']} Кости", callback_data="game_dice"),
        InlineKeyboardButton(text=f"{EMOJI['football']} Футбол", callback_data="game_football")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['basketball']} Баскетбол", callback_data="game_basketball"),
        InlineKeyboardButton(text=f"{EMOJI['darts']} Дартс", callback_data="game_darts")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['bowling']} Боулинг", callback_data="game_bowling"),
        InlineKeyboardButton(text="🃏 Блэкджек", callback_data="game_blackjack")
    )
    builder.row(
        InlineKeyboardButton(text="✊ КНБ", callback_data="game_knb"),
        InlineKeyboardButton(text=f"{EMOJI['door']} Лабиринт", callback_data="game_labyrinth")
    )
    builder.row(
        InlineKeyboardButton(text="⬆️ Больше/Меньше", callback_data="game_higher_lower")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Назад", callback_data="menu_main")
    )
    return builder.as_markup()


def get_dice_choice(bet: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📈 Больше 7 (2.3x)", callback_data=f"dice_more_{bet}"),
    )
    builder.row(
        InlineKeyboardButton(text="📉 Меньше 7 (2.3x)", callback_data=f"dice_less_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text="🎯 Ровно 7 (5.8x)", callback_data=f"dice_equal_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Отмена", callback_data="game_dice")
    )
    return builder.as_markup()


def get_football_choice(bet: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⚽ Гол (1.8x)", callback_data=f"football_goal_{bet}"),
        InlineKeyboardButton(text="❌ Мимо (3.7x)", callback_data=f"football_miss_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Отмена", callback_data="game_football")
    )
    return builder.as_markup()


def get_basketball_choice(bet: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🏀 Попадание (3.8x)", callback_data=f"basketball_goal_{bet}"),
        InlineKeyboardButton(text="❌ Мимо (1.9x)", callback_data=f"basketball_miss_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Отмена", callback_data="game_basketball")
    )
    return builder.as_markup()


def get_darts_choice(bet: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎯 Центр (5.8x)", callback_data=f"darts_center_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text="⚪ Белое (1.9x)", callback_data=f"darts_white_{bet}"),
        InlineKeyboardButton(text="🔴 Красное (1.9x)", callback_data=f"darts_red_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Мимо (5.8x)", callback_data=f"darts_miss_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Отмена", callback_data="game_darts")
    )
    return builder.as_markup()


def get_bowling_choice(bet: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎳 Страйк (5.3x)", callback_data=f"bowling_strike_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Мимо (5.3x)", callback_data=f"bowling_miss_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text="📍 1-5 кеглей (1.9x)", callback_data=f"bowling_partial_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Отмена", callback_data="game_bowling")
    )
    return builder.as_markup()


def get_knb_choice(bet: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🪨 Камень", callback_data=f"knb_rock_{bet}"),
        InlineKeyboardButton(text="✂️ Ножницы", callback_data=f"knb_scissors_{bet}"),
        InlineKeyboardButton(text="📄 Бумага", callback_data=f"knb_paper_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Отмена", callback_data="game_knb")
    )
    return builder.as_markup()


def get_crash_control(current_x: float):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"💰 Забрать ({current_x}x)", callback_data="crash_cashout")
    )
    return builder.as_markup()


def get_mines_grid(opened: list, mines_positions: list, revealed: bool = False):
    builder = InlineKeyboardBuilder()
    for i in range(25):
        row = i // 5
        col = i % 5
        if i in opened:
            if i in mines_positions:
                text = "💣"
            else:
                text = "💎"
        elif revealed and i in mines_positions:
            text = "💣"
        else:
            text = "⬜"
        builder.button(text=text, callback_data=f"mines_cell_{i}")
    builder.adjust(5)
    
    if not revealed:
        builder.row(
            InlineKeyboardButton(text="💰 Забрать", callback_data="mines_cashout")
        )
    return builder.as_markup()


def get_diamonds_grid(current_level: int, opened: list, diamond_pos: int = None, revealed: bool = False):
    builder = InlineKeyboardBuilder()
    cells_per_level = 4
    
    for i in range(cells_per_level):
        if i in opened:
            if diamond_pos is not None and i == diamond_pos:
                text = "💎"
            else:
                text = "⬛"
        elif revealed and diamond_pos is not None and i == diamond_pos:
            text = "💎"
        else:
            text = "🔷"
        builder.button(text=text, callback_data=f"diamond_cell_{current_level}_{i}")
    builder.adjust(4)
    
    if not revealed and len(opened) > 0:
        builder.row(
            InlineKeyboardButton(text="💰 Забрать", callback_data="diamond_cashout")
        )
    return builder.as_markup()


def get_labyrinth_doors(level: int, num_doors: int):
    builder = InlineKeyboardBuilder()
    for i in range(num_doors):
        builder.button(text=f"🚪 Дверь {i+1}", callback_data=f"labyrinth_door_{level}_{i}")
    builder.adjust(min(num_doors, 4))
    
    if level > 1:
        builder.row(
            InlineKeyboardButton(text="💰 Забрать", callback_data="labyrinth_cashout")
        )
    return builder.as_markup()


def get_higher_lower_choice(current_number: int, bet: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⬆️ Больше", callback_data=f"hl_higher_{bet}"),
        InlineKeyboardButton(text="⬇️ Меньше", callback_data=f"hl_lower_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text="🔢 Чётное", callback_data=f"hl_even_{bet}"),
        InlineKeyboardButton(text="🔢 Нечётное", callback_data=f"hl_odd_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Забрать", callback_data="hl_cashout")
    )
    return builder.as_markup()


def get_blackjack_controls():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🃏 Ещё", callback_data="bj_hit"),
        InlineKeyboardButton(text="✋ Хватит", callback_data="bj_stand")
    )
    builder.row(
        InlineKeyboardButton(text="✖️ Удвоить", callback_data="bj_double")
    )
    return builder.as_markup()


def get_farm_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🟢 GTX 1660 Super", callback_data="farm_buy_low"),
    )
    builder.row(
        InlineKeyboardButton(text="🟡 RTX 3070", callback_data="farm_buy_medium"),
    )
    builder.row(
        InlineKeyboardButton(text="🔴 RTX 4090", callback_data="farm_buy_high"),
    )
    builder.row(
        InlineKeyboardButton(text="💰 Собрать VibeTon", callback_data="farm_collect")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Назад", callback_data="menu_main")
    )
    return builder.as_markup()


def get_bank_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📥 Депозит", callback_data="bank_deposit"),
        InlineKeyboardButton(text="📤 Снять", callback_data="bank_withdraw")
    )
    builder.row(
        InlineKeyboardButton(text="💸 Перевод VC", callback_data="bank_transfer_vc"),
        InlineKeyboardButton(text="💸 Перевод VT", callback_data="bank_transfer_vt")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Налоги", callback_data="bank_taxes")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Назад", callback_data="menu_main")
    )
    return builder.as_markup()


def get_market_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📈 Купить VT", callback_data="market_buy"),
        InlineKeyboardButton(text="📉 Продать VT", callback_data="market_sell")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Мои ордера", callback_data="market_my_orders")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Все ордера", callback_data="market_all_orders")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Назад", callback_data="menu_main")
    )
    return builder.as_markup()


def get_top_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🪙 Топ по VC", callback_data="top_vc"),
        InlineKeyboardButton(text="💎 Топ по VT", callback_data="top_vt")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Назад", callback_data="menu_main")
    )
    return builder.as_markup()


def get_jackpot_menu(registered: bool):
    builder = InlineKeyboardBuilder()
    if not registered:
        builder.row(
            InlineKeyboardButton(text="🎰 Участвовать", callback_data="jackpot_register")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="✅ Вы участвуете", callback_data="jackpot_info")
        )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Назад", callback_data="menu_main")
    )
    return builder.as_markup()


def get_president_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Сделать ставку", callback_data="president_bet")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Все кандидаты", callback_data="president_candidates")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Назад", callback_data="menu_main")
    )
    return builder.as_markup()


def get_back_button(callback: str = "menu_main"):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Назад", callback_data=callback)
    )
    return builder.as_markup()


def get_subscription_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📢 Канал", url="https://t.me/nvibee_bet"),
        InlineKeyboardButton(text="💬 Чат", url="https://t.me/chatvibee_bet")
    )
    builder.row(
        InlineKeyboardButton(text="✅ Я подписался", callback_data="check_subscription")
    )
    return builder.as_markup()


def get_roulette_choice(bet: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔴 Красное (2x)", callback_data=f"roulette_red_{bet}"),
        InlineKeyboardButton(text="⚫ Чёрное (2x)", callback_data=f"roulette_black_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text="🟢 Зеро (36x)", callback_data=f"roulette_zero_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text="1️⃣ 1-12 (3x)", callback_data=f"roulette_1-12_{bet}"),
        InlineKeyboardButton(text="2️⃣ 13-24 (3x)", callback_data=f"roulette_13-24_{bet}"),
        InlineKeyboardButton(text="3️⃣ 25-36 (3x)", callback_data=f"roulette_25-36_{bet}")
    )
    builder.row(
        InlineKeyboardButton(text=f"{EMOJI['back']} Отмена", callback_data="game_roulette")
    )
    return builder.as_markup()
