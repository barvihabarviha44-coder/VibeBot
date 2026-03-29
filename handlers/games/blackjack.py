from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import db
from config import EMOJI
from utils.formatters import format_number
from utils.experience import maybe_add_xp
from keyboards.inline import get_blackjack_controls, get_back_button
import random

router = Router()

CARD_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}
CARD_SUITS = ['♠️', '♥️', '♦️', '♣️']
CARD_NAMES = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']


def create_deck():
    deck = []
    for suit in CARD_SUITS:
        for name in CARD_NAMES:
            deck.append({'name': name, 'suit': suit, 'value': CARD_VALUES[name]})
    random.shuffle(deck)
    return deck


def calculate_hand(cards):
    total = sum(card['value'] for card in cards)
    aces = sum(1 for card in cards if card['name'] == 'A')
    
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    
    return total


def format_cards(cards, hide_first=False):
    if hide_first:
        return f"🂠 {cards[1]['name']}{cards[1]['suit']}"
    return ' '.join(f"{card['name']}{card['suit']}" for card in cards)


@router.message(F.text.lower().startswith('блэкджек'))
async def blackjack_game(message: Message):
    parts = message.text.lower().split()
    
    if len(parts) < 2:
        text = f"""
{EMOJI['info']} <b>Блэкджек</b> — классическая карточная игра!

🃏 Цель: набрать 21 очко или больше, чем дилер, но не более 21.

<b>Коэффициенты:</b>
├ Победа: <b>2x</b>
├ Блэкджек (21 с 2 карт): <b>2.5x</b>
└ Ничья: возврат ставки

<b>Использование:</b> <code>блэкджек [ставка]</code>
<b>Пример:</b> <code>блэкджек 100к</code>
"""
        await message.answer(text, parse_mode="HTML")
        return
    
    try:
        bet_str = parts[1].lower().replace('к', '000').replace('кк', '000000')
        bet = int(float(bet_str))
    except:
        await message.answer(f"{EMOJI['cross']} Неверная ставка!")
        return
    
    user = await db.get_user(message.from_user.id)
    if user['balance'] < bet:
        await message.answer(f"{EMOJI['cross']} Недостаточно средств!")
        return
    
    await db.update_balance(message.from_user.id, bet, add=False)
    
    deck = create_deck()
    player_cards = [deck.pop(), deck.pop()]
    dealer_cards = [deck.pop(), deck.pop()]
    
    player_total = calculate_hand(player_cards)
    
    game_data = {
        'deck': deck,
        'player_cards': player_cards,
        'dealer_cards': dealer_cards,
        'doubled': False
    }
    await db.start_game(message.from_user.id, 'blackjack', bet, game_data)
    
    # Проверка на блэкджек
    if player_total == 21:
        dealer_total = calculate_hand(dealer_cards)
        if dealer_total == 21:
            # Ничья
            await db.update_balance(message.from_user.id, bet, add=True)
            await db.end_game(message.from_user.id, 'blackjack', bet, 'push')
            
            text = f"""
🃏 <b>Блэкджек — Ничья!</b>

Ваши карты: {format_cards(player_cards)} = <b>{player_total}</b>
Карты дилера: {format_cards(dealer_cards)} = <b>{dealer_total}</b>

{EMOJI['coin']} Ставка возвращена: <b>{format_number(bet)} VC</b>
"""
            await message.answer(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")
            return
        else:
            # Блэкджек!
            winnings = int(bet * 2.5)
            await db.update_balance(message.from_user.id, winnings, add=True)
            await db.end_game(message.from_user.id, 'blackjack', winnings, 'blackjack')
            await db.update_stats(message.from_user.id, won=winnings, played=1, game_won=True)
            
            text = f"""
🎰 <b>БЛЭКДЖЕК!</b>

Ваши карты: {format_cards(player_cards)} = <b>{player_total}</b>
Карты дилера: {format_cards(dealer_cards)} = <b>{dealer_total}</b>

{EMOJI['coin']} Выигрыш: <b>{format_number(winnings)} VC</b> (x2.5)
"""
            await message.answer(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")
            return
    
    text = f"""
🃏 <b>Блэкджек</b>

{EMOJI['coin']} Ставка: <b>{format_number(bet)} VC</b>

Ваши карты: {format_cards(player_cards)} = <b>{player_total}</b>
Карты дилера: {format_cards(dealer_cards, hide_first=True)}

Выберите действие:
"""
    await message.answer(text, reply_markup=get_blackjack_controls(), parse_mode="HTML")


@router.callback_query(F.data == "bj_hit")
async def blackjack_hit(callback: CallbackQuery):
    game = await db.get_active_game(callback.from_user.id, 'blackjack')
    if not game:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    game_data = game['game_data']
    deck = game_data['deck']
    player_cards = game_data['player_cards']
    dealer_cards = game_data['dealer_cards']
    
    # Берём карту
    player_cards.append(deck.pop())
    player_total = calculate_hand(player_cards)
    
    game_data['player_cards'] = player_cards
    game_data['deck'] = deck
    await db.update_game(callback.from_user.id, 'blackjack', game_data)
    
    if player_total > 21:
        # Перебор
        await db.end_game(callback.from_user.id, 'blackjack', 0, 'bust')
        await db.update_stats(callback.from_user.id, lost=game['bet_amount'], played=1)
        await db.add_to_jackpot(game['bet_amount'])
        
        text = f"""
{EMOJI['cross']} <b>Перебор!</b>

Ваши карты: {format_cards(player_cards)} = <b>{player_total}</b>
Карты дилера: {format_cards(dealer_cards)}

{EMOJI['coin']} Потеря: <b>{format_number(game['bet_amount'])} VC</b>
"""
        await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")
    elif player_total == 21:
        # Автоматически стоим
        await blackjack_stand_logic(callback, game)
    else:
        text = f"""
🃏 <b>Блэкджек</b>

{EMOJI['coin']} Ставка: <b>{format_number(game['bet_amount'])} VC</b>

Ваши карты: {format_cards(player_cards)} = <b>{player_total}</b>
Карты дилера: {format_cards(dealer_cards, hide_first=True)}

Выберите действие:
"""
        await callback.message.edit_text(text, reply_markup=get_blackjack_controls(), parse_mode="HTML")


@router.callback_query(F.data == "bj_stand")
async def blackjack_stand(callback: CallbackQuery):
    game = await db.get_active_game(callback.from_user.id, 'blackjack')
    if not game:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    await blackjack_stand_logic(callback, game)


async def blackjack_stand_logic(callback, game):
    game_data = game['game_data']
    deck = game_data['deck']
    player_cards = game_data['player_cards']
    dealer_cards = game_data['dealer_cards']
    bet = game['bet_amount']
    
    if game_data.get('doubled'):
        bet *= 2
    
    player_total = calculate_hand(player_cards)
    
    # Дилер берёт карты до 17
    dealer_total = calculate_hand(dealer_cards)
    while dealer_total < 17:
        dealer_cards.append(deck.pop())
        dealer_total = calculate_hand(dealer_cards)
    
    # Определяем победителя
    if dealer_total > 21:
        # Дилер перебрал
        winnings = bet * 2
        await db.update_balance(callback.from_user.id, winnings, add=True)
        await db.end_game(callback.from_user.id, 'blackjack', winnings, 'win')
        await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
        
        text = f"""
{EMOJI['check']} <b>Победа! Дилер перебрал!</b>

Ваши карты: {format_cards(player_cards)} = <b>{player_total}</b>
Карты дилера: {format_cards(dealer_cards)} = <b>{dealer_total}</b>

{EMOJI['coin']} Выигрыш: <b>{format_number(winnings)} VC</b>
"""
    elif player_total > dealer_total:
        # Победа игрока
        winnings = bet * 2
        await db.update_balance(callback.from_user.id, winnings, add=True)
        await db.end_game(callback.from_user.id, 'blackjack', winnings, 'win')
        await db.update_stats(callback.from_user.id, won=winnings, played=1, game_won=True)
        
        text = f"""
{EMOJI['check']} <b>Победа!</b>

Ваши карты: {format_cards(player_cards)} = <b>{player_total}</b>
Карты дилера: {format_cards(dealer_cards)} = <b>{dealer_total}</b>

{EMOJI['coin']} Выигрыш: <b>{format_number(winnings)} VC</b>
"""
    elif player_total < dealer_total:
        # Проигрыш
        await db.end_game(callback.from_user.id, 'blackjack', 0, 'lose')
        await db.update_stats(callback.from_user.id, lost=bet, played=1)
        await db.add_to_jackpot(bet)
        
        text = f"""
{EMOJI['cross']} <b>Проигрыш!</b>

Ваши карты: {format_cards(player_cards)} = <b>{player_total}</b>
Карты дилера: {format_cards(dealer_cards)} = <b>{dealer_total}</b>

{EMOJI['coin']} Потеря: <b>{format_number(bet)} VC</b>
"""
    else:
        # Ничья
        await db.update_balance(callback.from_user.id, bet, add=True)
        await db.end_game(callback.from_user.id, 'blackjack', bet, 'push')
        
        text = f"""
🤝 <b>Ничья!</b>

Ваши карты: {format_cards(player_cards)} = <b>{player_total}</b>
Карты дилера: {format_cards(dealer_cards)} = <b>{dealer_total}</b>

{EMOJI['coin']} Ставка возвращена: <b>{format_number(bet)} VC</b>
"""
    
    await maybe_add_xp(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")


@router.callback_query(F.data == "bj_double")
async def blackjack_double(callback: CallbackQuery):
    game = await db.get_active_game(callback.from_user.id, 'blackjack')
    if not game:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    user = await db.get_user(callback.from_user.id)
    if user['balance'] < game['bet_amount']:
        await callback.answer("❌ Недостаточно средств для удвоения!", show_alert=True)
        return
    
    # Удваиваем ставку
    await db.update_balance(callback.from_user.id, game['bet_amount'], add=False)
    
    game_data = game['game_data']
    game_data['doubled'] = True
    deck = game_data['deck']
    player_cards = game_data['player_cards']
    
    # Берём одну карту и стоим
    player_cards.append(deck.pop())
    game_data['player_cards'] = player_cards
    game_data['deck'] = deck
    
    await db.update_game(callback.from_user.id, 'blackjack', game_data)
    
    player_total = calculate_hand(player_cards)
    
    if player_total > 21:
        # Перебор
        total_loss = game['bet_amount'] * 2
        await db.end_game(callback.from_user.id, 'blackjack', 0, 'bust')
        await db.update_stats(callback.from_user.id, lost=total_loss, played=1)
        await db.add_to_jackpot(total_loss)
        
        text = f"""
{EMOJI['cross']} <b>Перебор!</b>

Ваши карты: {format_cards(player_cards)} = <b>{player_total}</b>
Карты дилера: {format_cards(game_data['dealer_cards'])}

{EMOJI['coin']} Потеря: <b>{format_number(total_loss)} VC</b> (удвоено)
"""
        await callback.message.edit_text(text, reply_markup=get_back_button("menu_games"), parse_mode="HTML")
    else:
        game['bet_amount'] *= 2
        await blackjack_stand_logic(callback, game)
