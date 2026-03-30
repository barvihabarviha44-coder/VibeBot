from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text.lower().in_(['помощь', 'команды', 'help', '?']))
async def help_command(message: Message):
    text = """
❓ <b>Все команды VibeBet</b>

👤 <b>Профиль и бонусы:</b>
<code>профиль</code> / <code>я</code> — профиль
<code>бонус</code> — ежедневный бонус (500к VC)
<code>час</code> — ежечасный бонус (10-150к VC)
<code>+реп</code> — +1 реп (ответом)
<code>-реп</code> — -2 реп (ответом)

🎮 <b>Игры:</b>
<code>мины [ставка] [мины]</code> / <code>мн</code>
<code>алмазы [ставка]</code> / <code>ал</code>
<code>краш [ставка]</code> / <code>крш</code>
<code>рулетка [ставка] [выбор]</code> / <code>рл</code>
<code>кости [ставка]</code> / <code>кс</code>
<code>футбол [ставка]</code> / <code>фб</code>
<code>баскетбол [ставка]</code> / <code>бс</code>
<code>дартс [ставка]</code> / <code>др</code>
<code>боулинг [ставка]</code> / <code>бл</code>
<code>блэкджек [ставка]</code> / <code>бд</code>
<code>кнб [ставка]</code>
<code>лабиринт [ставка]</code> / <code>лб</code>
<code>больше [ставка]</code> / <code>бм</code>

💼 <b>Экономика:</b>
<code>работа</code> / <code>раб</code>
<code>ферма</code>
<code>банк</code>
<code>рынок</code>
<code>бизнес</code>

📋 <b>Другое:</b>
<code>задания</code>
<code>топ</code>
<code>джекпот</code>
<code>президент</code>
<code>промокод [код]</code>
<code>перевод [ID] [сумма]</code>

💡 <b>Поддержка сумм:</b>
<code>1к</code>, <code>1.5к</code>, <code>2кк</code>, <code>all</code>, <code>все</code>, <code>пол</code>, <code>половина</code>
"""
    await message.answer(text, parse_mode="HTML")
