import asyncpg
import asyncio
from config import DATABASE_URL
from datetime import datetime, timedelta
import json

class Database:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
        await self.create_tables()
    
    async def create_tables(self):
        async with self.pool.acquire() as conn:
            # Пользователи
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    balance BIGINT DEFAULT 10000,
                    vt_balance DECIMAL(20,4) DEFAULT 0,
                    bank_balance BIGINT DEFAULT 0,
                    xp BIGINT DEFAULT 0,
                    level INT DEFAULT 1,
                    total_won BIGINT DEFAULT 0,
                    total_lost BIGINT DEFAULT 0,
                    games_played INT DEFAULT 0,
                    games_won INT DEFAULT 0,
                    registered_at TIMESTAMP DEFAULT NOW(),
                    last_activity TIMESTAMP DEFAULT NOW(),
                    is_banned BOOLEAN DEFAULT FALSE,
                    is_subscribed BOOLEAN DEFAULT FALSE,
                    jackpot_registered BOOLEAN DEFAULT FALSE,
                    president_bet BIGINT DEFAULT 0,
                    is_president BOOLEAN DEFAULT FALSE,
                    business_slots INT DEFAULT 1
                )
            ''')
            
            # Видеокарты пользователей
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_gpus (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    gpu_type TEXT,
                    count INT DEFAULT 0,
                    current_price BIGINT,
                    last_collect TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Рынок VibeTon
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS market_orders (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    order_type TEXT,
                    amount DECIMAL(20,4),
                    price BIGINT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Текущая цена VT
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS vt_price (
                    id SERIAL PRIMARY KEY,
                    price BIGINT,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Промокоды
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS promocodes (
                    id SERIAL PRIMARY KEY,
                    code TEXT UNIQUE,
                    reward_type TEXT,
                    reward_amount BIGINT,
                    max_uses INT,
                    current_uses INT DEFAULT 0,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Использованные промокоды
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS used_promocodes (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    promocode_id INT REFERENCES promocodes(id),
                    used_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Джекпот
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS jackpot (
                    id SERIAL PRIMARY KEY,
                    amount BIGINT DEFAULT 0,
                    last_winner BIGINT,
                    last_draw TIMESTAMP
                )
            ''')
            
            # Президент
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS president (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    profit BIGINT DEFAULT 0,
                    elected_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Ставки на президента
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS president_bets (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    bet_amount BIGINT,
                    bet_date DATE DEFAULT CURRENT_DATE
                )
            ''')
            
            # Бизнесы
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS businesses (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    base_price BIGINT,
                    base_profit BIGINT,
                    emoji TEXT DEFAULT '🏢'
                )
            ''')
            
            # Бизнесы пользователей
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_businesses (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    business_id INT REFERENCES businesses(id),
                    upgrade_level INT DEFAULT 1,
                    profit_multiplier DECIMAL(5,2) DEFAULT 1.0,
                    last_collect TIMESTAMP DEFAULT NOW(),
                    tax_paid_until DATE DEFAULT CURRENT_DATE
                )
            ''')
            
            # Задания
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_tasks (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    task_type TEXT,
                    task_target INT,
                    task_progress INT DEFAULT 0,
                    reward_vc BIGINT,
                    reward_vt DECIMAL(10,2),
                    task_date DATE DEFAULT CURRENT_DATE,
                    is_completed BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Активные игры
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS active_games (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    game_type TEXT,
                    bet_amount BIGINT,
                    game_data JSONB,
                    started_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # История игр
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS game_history (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    game_type TEXT,
                    bet_amount BIGINT,
                    win_amount BIGINT,
                    result TEXT,
                    played_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Переводы
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS transfers (
                    id SERIAL PRIMARY KEY,
                    from_user BIGINT,
                    to_user BIGINT,
                    amount BIGINT,
                    currency TEXT,
                    commission BIGINT,
                    transferred_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Бонусы в группе
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_bonus (
                    id SERIAL PRIMARY KEY,
                    bonus_amount BIGINT,
                    max_activations INT,
                    current_activations INT DEFAULT 0,
                    bonus_date DATE DEFAULT CURRENT_DATE
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS bonus_claims (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    bonus_id INT REFERENCES daily_bonus(id),
                    claimed_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Инициализация джекпота
            jackpot = await conn.fetchrow('SELECT * FROM jackpot WHERE id = 1')
            if not jackpot:
                await conn.execute('INSERT INTO jackpot (id, amount) VALUES (1, 1000000)')
            
            # Инициализация цены VT
            vt_price = await conn.fetchrow('SELECT * FROM vt_price ORDER BY id DESC LIMIT 1')
            if not vt_price:
                import random
                await conn.execute('INSERT INTO vt_price (price) VALUES ($1)', random.randint(1000, 15000))
    
    # ==================== USERS ====================
    
    async def get_user(self, user_id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
    
    async def create_user(self, user_id: int, username: str, first_name: str):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (user_id, username, first_name)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = $2,
                    first_name = $3,
                    last_activity = NOW()
            ''', user_id, username, first_name)
    
    async def update_balance(self, user_id: int, amount: int, add: bool = True):
        async with self.pool.acquire() as conn:
            if add:
                await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2', amount, user_id)
            else:
                await conn.execute('UPDATE users SET balance = balance - $1 WHERE user_id = $2', amount, user_id)
    
    async def update_vt_balance(self, user_id: int, amount: float, add: bool = True):
        async with self.pool.acquire() as conn:
            if add:
                await conn.execute('UPDATE users SET vt_balance = vt_balance + $1 WHERE user_id = $2', amount, user_id)
            else:
                await conn.execute('UPDATE users SET vt_balance = vt_balance - $1 WHERE user_id = $2', amount, user_id)
    
    async def update_bank(self, user_id: int, amount: int, add: bool = True):
        async with self.pool.acquire() as conn:
            if add:
                await conn.execute('UPDATE users SET bank_balance = bank_balance + $1 WHERE user_id = $2', amount, user_id)
            else:
                await conn.execute('UPDATE users SET bank_balance = bank_balance - $1 WHERE user_id = $2', amount, user_id)
    
    async def add_xp(self, user_id: int, amount: int):
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE users SET xp = xp + $1 WHERE user_id = $2', amount, user_id)
            user = await conn.fetchrow('SELECT xp, level FROM users WHERE user_id = $1', user_id)
            from config import get_level_from_xp
            new_level = get_level_from_xp(user['xp'])
            if new_level > user['level']:
                await conn.execute('UPDATE users SET level = $1 WHERE user_id = $2', new_level, user_id)
                return new_level
            return None
    
    async def update_stats(self, user_id: int, won: int = 0, lost: int = 0, played: int = 1, game_won: bool = False):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE users SET
                    total_won = total_won + $1,
                    total_lost = total_lost + $2,
                    games_played = games_played + $3,
                    games_won = games_won + $4,
                    last_activity = NOW()
                WHERE user_id = $5
            ''', won, lost, played, 1 if game_won else 0, user_id)
    
    async def set_subscribed(self, user_id: int, status: bool = True):
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE users SET is_subscribed = $1 WHERE user_id = $2', status, user_id)
    
    async def ban_user(self, user_id: int, ban: bool = True):
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE users SET is_banned = $1 WHERE user_id = $2', ban, user_id)
    
    async def get_top_by_balance(self, limit: int = 10):
        async with self.pool.acquire() as conn:
            return await conn.fetch('SELECT * FROM users ORDER BY balance DESC LIMIT $1', limit)
    
    async def get_top_by_vt(self, limit: int = 10):
        async with self.pool.acquire() as conn:
            return await conn.fetch('SELECT * FROM users ORDER BY vt_balance DESC LIMIT $1', limit)
    
    async def get_all_users_count(self):
        async with self.pool.acquire() as conn:
            return await conn.fetchval('SELECT COUNT(*) FROM users')
    
    # ==================== GPU FARM ====================
    
    async def get_user_gpus(self, user_id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetch('SELECT * FROM user_gpus WHERE user_id = $1', user_id)
    
    async def buy_gpu(self, user_id: int, gpu_type: str, price: int):
        async with self.pool.acquire() as conn:
            existing = await conn.fetchrow(
                'SELECT * FROM user_gpus WHERE user_id = $1 AND gpu_type = $2', 
                user_id, gpu_type
            )
            if existing:
                new_price = int(price * 1.2)
                await conn.execute('''
                    UPDATE user_gpus SET count = count + 1, current_price = $1
                    WHERE user_id = $2 AND gpu_type = $3
                ''', new_price, user_id, gpu_type)
            else:
                new_price = int(price * 1.2)
                await conn.execute('''
                    INSERT INTO user_gpus (user_id, gpu_type, count, current_price)
                    VALUES ($1, $2, 1, $3)
                ''', user_id, gpu_type, new_price)
    
    async def collect_vt(self, user_id: int):
        async with self.pool.acquire() as conn:
            gpus = await conn.fetch('SELECT * FROM user_gpus WHERE user_id = $1', user_id)
            from config import GPU_CONFIG
            total_vt = 0
            for gpu in gpus:
                config = GPU_CONFIG.get(gpu['gpu_type'])
                if config:
                    hours = (datetime.now() - gpu['last_collect']).total_seconds() / 3600
                    vt = hours * config['vt_per_hour'] * gpu['count']
                    total_vt += vt
            
            if total_vt > 0:
                await self.update_vt_balance(user_id, total_vt, add=True)
                await conn.execute(
                    'UPDATE user_gpus SET last_collect = NOW() WHERE user_id = $1',
                    user_id
                )
            return total_vt
    
    # ==================== MARKET ====================
    
    async def get_vt_price(self):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM vt_price ORDER BY updated_at DESC LIMIT 1')
            return row['price'] if row else 5000
    
    async def update_vt_price(self):
        import random
        async with self.pool.acquire() as conn:
            new_price = random.randint(1000, 15000)
            await conn.execute('INSERT INTO vt_price (price) VALUES ($1)', new_price)
            return new_price
    
    async def create_market_order(self, user_id: int, order_type: str, amount: float, price: int):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO market_orders (user_id, order_type, amount, price)
                VALUES ($1, $2, $3, $4)
            ''', user_id, order_type, amount, price)
    
    async def get_market_orders(self, order_type: str = None):
        async with self.pool.acquire() as conn:
            if order_type:
                return await conn.fetch(
                    'SELECT * FROM market_orders WHERE order_type = $1 AND is_active = TRUE ORDER BY price',
                    order_type
                )
            return await conn.fetch('SELECT * FROM market_orders WHERE is_active = TRUE ORDER BY created_at DESC')
    
    async def cancel_order(self, order_id: int, user_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute(
                'UPDATE market_orders SET is_active = FALSE WHERE id = $1 AND user_id = $2',
                order_id, user_id
            )
    
    async def execute_order(self, order_id: int, buyer_id: int):
        async with self.pool.acquire() as conn:
            order = await conn.fetchrow('SELECT * FROM market_orders WHERE id = $1 AND is_active = TRUE', order_id)
            if order:
                await conn.execute('UPDATE market_orders SET is_active = FALSE WHERE id = $1', order_id)
                return order
            return None
    
    # ==================== PROMOCODES ====================
    
    async def create_promocode(self, code: str, reward_type: str, reward_amount: int, max_uses: int, expires_days: int = 7):
        async with self.pool.acquire() as conn:
            expires = datetime.now() + timedelta(days=expires_days)
            await conn.execute('''
                INSERT INTO promocodes (code, reward_type, reward_amount, max_uses, expires_at)
                VALUES ($1, $2, $3, $4, $5)
            ''', code.upper(), reward_type, reward_amount, max_uses, expires)
    
    async def use_promocode(self, user_id: int, code: str):
        async with self.pool.acquire() as conn:
            promo = await conn.fetchrow(
                'SELECT * FROM promocodes WHERE code = $1 AND expires_at > NOW() AND current_uses < max_uses',
                code.upper()
            )
            if not promo:
                return None, "Промокод не найден или истёк"
            
            used = await conn.fetchrow(
                'SELECT * FROM used_promocodes WHERE user_id = $1 AND promocode_id = $2',
                user_id, promo['id']
            )
            if used:
                return None, "Вы уже использовали этот промокод"
            
            await conn.execute(
                'INSERT INTO used_promocodes (user_id, promocode_id) VALUES ($1, $2)',
                user_id, promo['id']
            )
            await conn.execute(
                'UPDATE promocodes SET current_uses = current_uses + 1 WHERE id = $1',
                promo['id']
            )
            
            if promo['reward_type'] == 'vc':
                await self.update_balance(user_id, promo['reward_amount'], add=True)
            elif promo['reward_type'] == 'vt':
                await self.update_vt_balance(user_id, promo['reward_amount'], add=True)
            
            return promo, None
    
    # ==================== JACKPOT ====================
    
    async def get_jackpot(self):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('SELECT * FROM jackpot WHERE id = 1')
    
    async def add_to_jackpot(self, amount: int):
        contribution = int(amount * 0.0001)  # 0.01%
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE jackpot SET amount = amount + $1 WHERE id = 1', contribution)
    
    async def register_for_jackpot(self, user_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE users SET jackpot_registered = TRUE WHERE user_id = $1', user_id)
    
    async def get_jackpot_participants(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch('SELECT * FROM users WHERE jackpot_registered = TRUE')
    
    async def draw_jackpot(self):
        import random
        async with self.pool.acquire() as conn:
            participants = await self.get_jackpot_participants()
            if not participants:
                return None
            
            winner = random.choice(participants)
            jackpot = await self.get_jackpot()
            
            await self.update_balance(winner['user_id'], jackpot['amount'], add=True)
            await conn.execute('''
                UPDATE jackpot SET amount = 1000000, last_winner = $1, last_draw = NOW() WHERE id = 1
            ''', winner['user_id'])
            await conn.execute('UPDATE users SET jackpot_registered = FALSE')
            
            return winner, jackpot['amount']
    
    # ==================== PRESIDENT ====================
    
    async def get_president(self):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('''
                SELECT p.*, u.username, u.first_name 
                FROM president p 
                JOIN users u ON p.user_id = u.user_id 
                ORDER BY p.elected_at DESC LIMIT 1
            ''')
    
    async def add_president_profit(self, amount: int):
        profit = int(amount * 0.0001)  # 0.01%
        async with self.pool.acquire() as conn:
            president = await self.get_president()
            if president:
                await conn.execute(
                    'UPDATE president SET profit = profit + $1 WHERE id = $2',
                    profit, president['id']
                )
                await self.update_balance(president['user_id'], profit, add=True)
    
    async def place_president_bet(self, user_id: int, amount: int):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO president_bets (user_id, bet_amount)
                VALUES ($1, $2)
                ON CONFLICT (user_id) WHERE bet_date = CURRENT_DATE
                DO UPDATE SET bet_amount = president_bets.bet_amount + $2
            ''', user_id, amount)
            await self.update_balance(user_id, amount, add=False)
    
    async def get_president_bets(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT pb.*, u.username, u.first_name
                FROM president_bets pb
                JOIN users u ON pb.user_id = u.user_id
                WHERE pb.bet_date = CURRENT_DATE
                ORDER BY pb.bet_amount DESC
            ''')
    
    async def elect_president(self):
        import random
        async with self.pool.acquire() as conn:
            bets = await self.get_president_bets()
            if not bets:
                return None
            
            current_president = await self.get_president()
            eligible_bets = [b for b in bets if not current_president or b['user_id'] != current_president['user_id']]
            
            if not eligible_bets:
                return None
            
            total_bets = sum(b['bet_amount'] for b in eligible_bets)
            rand = random.uniform(0, total_bets)
            cumulative = 0
            winner = None
            
            for bet in eligible_bets:
                cumulative += bet['bet_amount']
                if rand <= cumulative:
                    winner = bet
                    break
            
            if winner:
                # Возврат 50% проигравшим
                for bet in eligible_bets:
                    if bet['user_id'] != winner['user_id']:
                        refund = bet['bet_amount'] // 2
                        await self.update_balance(bet['user_id'], refund, add=True)
                
                # Новый президент
                await conn.execute('''
                    INSERT INTO president (user_id, profit) VALUES ($1, 0)
                ''', winner['user_id'])
                await conn.execute('UPDATE users SET is_president = FALSE')
                await conn.execute('UPDATE users SET is_president = TRUE WHERE user_id = $1', winner['user_id'])
                
                # Очистка ставок
                await conn.execute('DELETE FROM president_bets WHERE bet_date < CURRENT_DATE')
                
                return winner
            return None
    
    # ==================== BUSINESSES ====================
    
    async def add_business(self, name: str, base_price: int, base_profit: int, emoji: str = '🏢'):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO businesses (name, base_price, base_profit, emoji)
                VALUES ($1, $2, $3, $4)
            ''', name, base_price, base_profit, emoji)
    
    async def get_all_businesses(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch('SELECT * FROM businesses ORDER BY base_price')
    
    async def get_user_businesses(self, user_id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT ub.*, b.name, b.base_price, b.base_profit, b.emoji
                FROM user_businesses ub
                JOIN businesses b ON ub.business_id = b.id
                WHERE ub.user_id = $1
            ''', user_id)
    
    async def buy_business(self, user_id: int, business_id: int):
        async with self.pool.acquire() as conn:
            business = await conn.fetchrow('SELECT * FROM businesses WHERE id = $1', business_id)
            if not business:
                return None, "Бизнес не найден"
            
            user = await self.get_user(user_id)
            user_businesses = await self.get_user_businesses(user_id)
            
            if len(user_businesses) >= user['business_slots']:
                return None, f"У вас нет свободных слотов. Купите слот у {config.ADMIN_USERNAME}"
            
            if user['balance'] < business['base_price']:
                return None, "Недостаточно средств"
            
            await self.update_balance(user_id, business['base_price'], add=False)
            await conn.execute('''
                INSERT INTO user_businesses (user_id, business_id)
                VALUES ($1, $2)
            ''', user_id, business_id)
            
            return business, None
    
    async def collect_business_profit(self, user_id: int, user_business_id: int):
        async with self.pool.acquire() as conn:
            ub = await conn.fetchrow('''
                SELECT ub.*, b.base_profit
                FROM user_businesses ub
                JOIN businesses b ON ub.business_id = b.id
                WHERE ub.id = $1 AND ub.user_id = $2
            ''', user_business_id, user_id)
            
            if not ub:
                return 0
            
            hours = (datetime.now() - ub['last_collect']).total_seconds() / 3600
            profit = int(hours * ub['base_profit'] * float(ub['profit_multiplier']))
            
            await self.update_balance(user_id, profit, add=True)
            await conn.execute(
                'UPDATE user_businesses SET last_collect = NOW() WHERE id = $1',
                user_business_id
            )
            
            return profit
    
    async def upgrade_business(self, user_id: int, user_business_id: int, cost: int):
        async with self.pool.acquire() as conn:
            ub = await conn.fetchrow(
                'SELECT * FROM user_businesses WHERE id = $1 AND user_id = $2',
                user_business_id, user_id
            )
            if not ub:
                return False
            
            user = await self.get_user(user_id)
            if user['balance'] < cost:
                return False
            
            await self.update_balance(user_id, cost, add=False)
            new_multiplier = float(ub['profit_multiplier']) + 0.1
            await conn.execute(
                'UPDATE user_businesses SET profit_multiplier = $1, upgrade_level = upgrade_level + 1 WHERE id = $2',
                new_multiplier, user_business_id
            )
            return True
    
    async def sell_business(self, user_id: int, user_business_id: int):
        async with self.pool.acquire() as conn:
            ub = await conn.fetchrow('''
                SELECT ub.*, b.base_price
                FROM user_businesses ub
                JOIN businesses b ON ub.business_id = b.id
                WHERE ub.id = $1 AND ub.user_id = $2
            ''', user_business_id, user_id)
            
            if not ub:
                return 0
            
            sell_price = ub['base_price'] // 2
            await self.update_balance(user_id, sell_price, add=True)
            await conn.execute('DELETE FROM user_businesses WHERE id = $1', user_business_id)
            
            return sell_price
    
    async def pay_business_tax(self, user_id: int, user_business_id: int):
        async with self.pool.acquire() as conn:
            ub = await conn.fetchrow('''
                SELECT ub.*, b.base_price
                FROM user_businesses ub
                JOIN businesses b ON ub.business_id = b.id
                WHERE ub.id = $1 AND ub.user_id = $2
            ''', user_business_id, user_id)
            
            if not ub:
                return 0, "Бизнес не найден"
            
            tax = ub['base_price'] // 10  # 10% от стоимости в день
            user = await self.get_user(user_id)
            
            if user['balance'] < tax:
                return 0, "Недостаточно средств"
            
            await self.update_balance(user_id, tax, add=False)
            await conn.execute(
                'UPDATE user_businesses SET tax_paid_until = tax_paid_until + INTERVAL \'1 day\' WHERE id = $1',
                user_business_id
            )
            
            return tax, None
    
    # ==================== TASKS ====================
    
    async def generate_daily_tasks(self, user_id: int):
        import random
        async with self.pool.acquire() as conn:
            # Проверяем есть ли задания на сегодня
            existing = await conn.fetch(
                'SELECT * FROM daily_tasks WHERE user_id = $1 AND task_date = CURRENT_DATE',
                user_id
            )
            if existing:
                return existing
            
            task_types = [
                ('labyrinth_play', 'Сыграть в игру «Лабиринт»'),
                ('higher_lower_win', 'Выиграть в игре «Больше меньше»'),
                ('knb_play', 'Сыграть в игру «КНБ»'),
                ('crash_win', 'Выиграть в игре «Краш»'),
                ('mines_play', 'Сыграть в игру «Мины»'),
                ('diamonds_play', 'Сыграть в игру «Алмазы»'),
            ]
            
            selected = random.sample(task_types, 4)
            tasks = []
            
            for task_type, _ in selected:
                target = random.randint(3, 20)
                reward_vc = random.randint(500000, 1500000)
                reward_vt = random.randint(1, 50)
                
                await conn.execute('''
                    INSERT INTO daily_tasks (user_id, task_type, task_target, reward_vc, reward_vt)
                    VALUES ($1, $2, $3, $4, $5)
                ''', user_id, task_type, target, reward_vc, reward_vt)
            
            return await conn.fetch(
                'SELECT * FROM daily_tasks WHERE user_id = $1 AND task_date = CURRENT_DATE',
                user_id
            )
    
    async def update_task_progress(self, user_id: int, task_type: str, increment: int = 1):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE daily_tasks 
                SET task_progress = task_progress + $1
                WHERE user_id = $2 AND task_type = $3 AND task_date = CURRENT_DATE AND is_completed = FALSE
            ''', increment, user_id, task_type)
            
            # Проверяем выполнение
            task = await conn.fetchrow('''
                SELECT * FROM daily_tasks 
                WHERE user_id = $1 AND task_type = $2 AND task_date = CURRENT_DATE AND is_completed = FALSE
            ''', user_id, task_type)
            
            if task and task['task_progress'] >= task['task_target']:
                await conn.execute(
                    'UPDATE daily_tasks SET is_completed = TRUE WHERE id = $1',
                    task['id']
                )
                await self.update_balance(user_id, task['reward_vc'], add=True)
                await self.update_vt_balance(user_id, task['reward_vt'], add=True)
                return task
            return None
    
    # ==================== GAMES ====================
    
    async def start_game(self, user_id: int, game_type: str, bet: int, game_data: dict):
        async with self.pool.acquire() as conn:
            # Удаляем старую игру если есть
            await conn.execute(
                'DELETE FROM active_games WHERE user_id = $1 AND game_type = $2',
                user_id, game_type
            )
            await conn.execute('''
                INSERT INTO active_games (user_id, game_type, bet_amount, game_data)
                VALUES ($1, $2, $3, $4)
            ''', user_id, game_type, bet, json.dumps(game_data))
    
    async def get_active_game(self, user_id: int, game_type: str):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM active_games WHERE user_id = $1 AND game_type = $2',
                user_id, game_type
            )
            if row:
                return {**dict(row), 'game_data': json.loads(row['game_data'])}
            return None
    
    async def update_game(self, user_id: int, game_type: str, game_data: dict):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE active_games SET game_data = $1
                WHERE user_id = $2 AND game_type = $3
            ''', json.dumps(game_data), user_id, game_type)
    
    async def end_game(self, user_id: int, game_type: str, win_amount: int, result: str):
        async with self.pool.acquire() as conn:
            game = await self.get_active_game(user_id, game_type)
            if game:
                await conn.execute('''
                    INSERT INTO game_history (user_id, game_type, bet_amount, win_amount, result)
                    VALUES ($1, $2, $3, $4, $5)
                ''', user_id, game_type, game['bet_amount'], win_amount, result)
                await conn.execute(
                    'DELETE FROM active_games WHERE user_id = $1 AND game_type = $2',
                    user_id, game_type
                )
    
    # ==================== TRANSFERS ====================
    
    async def transfer(self, from_user: int, to_user: int, amount: int, currency: str, commission_rate: float):
        async with self.pool.acquire() as conn:
            commission = int(amount * commission_rate)
            net_amount = amount - commission
            
            if currency == 'vc':
                await self.update_balance(from_user, amount, add=False)
                await self.update_balance(to_user, net_amount, add=True)
            elif currency == 'vt':
                await self.update_vt_balance(from_user, amount, add=False)
                await self.update_vt_balance(to_user, net_amount, add=True)
            
            await conn.execute('''
                INSERT INTO transfers (from_user, to_user, amount, currency, commission)
                VALUES ($1, $2, $3, $4, $5)
            ''', from_user, to_user, amount, currency, commission)
            
            return net_amount, commission
    
    # ==================== BONUS ====================
    
    async def create_daily_bonus(self, amount: int, max_activations: int):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO daily_bonus (bonus_amount, max_activations)
                VALUES ($1, $2)
            ''', amount, max_activations)
            return await conn.fetchrow(
                'SELECT * FROM daily_bonus WHERE bonus_date = CURRENT_DATE ORDER BY id DESC LIMIT 1'
            )
    
    async def claim_bonus(self, user_id: int):
        async with self.pool.acquire() as conn:
            bonus = await conn.fetchrow('''
                SELECT * FROM daily_bonus 
                WHERE bonus_date = CURRENT_DATE AND current_activations < max_activations
                ORDER BY id DESC LIMIT 1
            ''')
            
            if not bonus:
                return None, "Бонус недоступен или уже закончился"
            
            claimed = await conn.fetchrow(
                'SELECT * FROM bonus_claims WHERE user_id = $1 AND bonus_id = $2',
                user_id, bonus['id']
            )
            
            if claimed:
                return None, "Вы уже получили этот бонус"
            
            await conn.execute(
                'INSERT INTO bonus_claims (user_id, bonus_id) VALUES ($1, $2)',
                user_id, bonus['id']
            )
            await conn.execute(
                'UPDATE daily_bonus SET current_activations = current_activations + 1 WHERE id = $1',
                bonus['id']
            )
            await self.update_balance(user_id, bonus['bonus_amount'], add=True)
            
            return bonus, None
    
    async def add_business_slot(self, user_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute(
                'UPDATE users SET business_slots = business_slots + 1 WHERE user_id = $1',
                user_id
            )


db = Database()
