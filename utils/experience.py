import random
from database import db

async def maybe_add_xp(user_id: int):
    """Добавление XP с шансом 25%"""
    if random.random() < 0.25:
        xp_amount = random.randint(5, 25)
        new_level = await db.add_xp(user_id, xp_amount)
        return xp_amount, new_level
    return 0, None
