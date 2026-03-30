import asyncpg
from datetime import datetime, timedelta
import json
import random
from config import DATABASE_URL


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10, command_timeout=60)
        await self.create_tables()

    async def create_tables(self):
        async with self.pool.acquire() as conn:
            await conn.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY, username TEXT DEFAULT '', first_name TEXT DEFAULT 'Игрок',
                balance BIGINT DEFAULT 10000, vt_balance DECIMAL(20,4) DEFAULT 0, bank_balance BIGINT DEFAULT 0,
                xp BIGINT DEFAULT 0, level INT DEFAULT 1, total_won BIGINT DEFAULT 0, total_lost BIGINT DEFAULT 0,
                games_played INT DEFAULT 0, games_won INT DEFAULT 0, registered_at TIMESTAMP DEFAULT NOW(),
                last_activity TIMESTAMP DEFAULT NOW(), last_work TIMESTAMP DEFAULT NULL,
                is_banned BOOLEAN DEFAULT FALSE, is_subscribed BOOLEAN DEFAULT FALSE,
                jackpot_registered BOOLEAN DEFAULT FALSE, is_president BOOLEAN DEFAULT FALSE, business_slots INT DEFAULT 1)''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS businesses (
                biz_id SERIAL PRIMARY KEY, name TEXT NOT NULL, base_price BIGINT NOT NULL,
                base_profit BIGINT NOT NULL, emoji TEXT DEFAULT '🏢')''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS promocodes (
                promo_id SERIAL PRIMARY KEY, code TEXT UNIQUE NOT NULL, reward_type TEXT NOT NULL,
                reward_amount BIGINT NOT NULL, max_uses INT NOT NULL, current_uses INT DEFAULT 0,
                expires_at TIMESTAMP, created_at TIMESTAMP DEFAULT NOW())''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS jackpot (
                jp_id INT PRIMARY KEY DEFAULT 1, amount BIGINT DEFAULT 1000000, last_winner BIGINT, last_draw TIMESTAMP)''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS president (
                pres_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, profit BIGINT DEFAULT 0, elected_at TIMESTAMP DEFAULT NOW())''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS vt_price (
                vtp_id SERIAL PRIMARY KEY, price BIGINT NOT NULL, updated_at TIMESTAMP DEFAULT NOW())''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS daily_bonus (
                db_id SERIAL PRIMARY KEY, bonus_amount BIGINT NOT NULL, max_activations INT NOT NULL,
                current_activations INT DEFAULT 0, bonus_date DATE DEFAULT CURRENT_DATE)''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS user_gpus (
                gpu_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, gpu_type TEXT NOT NULL,
                count INT DEFAULT 0, current_price BIGINT NOT NULL, last_collect TIMESTAMP DEFAULT NOW(), UNIQUE(user_id, gpu_type))''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS market_orders (
                order_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, order_type TEXT NOT NULL,
                amount DECIMAL(20,4) NOT NULL, price BIGINT NOT NULL, created_at TIMESTAMP DEFAULT NOW(), is_active BOOLEAN DEFAULT TRUE)''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS used_promocodes (
                up_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, promocode_id INT NOT NULL,
                used_at TIMESTAMP DEFAULT NOW(), UNIQUE(user_id, promocode_id))''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS president_bets (
                pb_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, bet_amount BIGINT NOT NULL, bet_date DATE DEFAULT CURRENT_DATE)''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS user_businesses (
                ub_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, business_id INT NOT NULL,
                upgrade_level INT DEFAULT 1, profit_multiplier DECIMAL(5,2) DEFAULT 1.0,
                last_collect TIMESTAMP DEFAULT NOW(), tax_paid_until DATE DEFAULT CURRENT_DATE, UNIQUE(user_id, business_id))''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS daily_tasks (
                dt_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, task_type TEXT NOT NULL,
                task_target INT NOT NULL, task_progress INT DEFAULT 0, reward_vc BIGINT NOT NULL,
                reward_vt DECIMAL(10,2) NOT NULL, task_date DATE DEFAULT CURRENT_DATE, is_completed BOOLEAN DEFAULT FALSE)''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS active_games (
                ag_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, game_type TEXT NOT NULL,
                bet_amount BIGINT NOT NULL, game_data JSONB NOT NULL DEFAULT '{}', started_at TIMESTAMP DEFAULT NOW(), UNIQUE(user_id, game_type))''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS game_history (
                gh_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, game_type TEXT NOT NULL,
                bet_amount BIGINT NOT NULL, win_amount BIGINT DEFAULT 0, result TEXT, played_at TIMESTAMP DEFAULT NOW())''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS transfers (
                tr_id SERIAL PRIMARY KEY, from_user BIGINT NOT NULL, to_user BIGINT NOT NULL,
                amount BIGINT NOT NULL, currency TEXT NOT NULL, commission BIGINT DEFAULT 0, transferred_at TIMESTAMP DEFAULT NOW())''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS bonus_claims (
                bc_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, bonus_id INT NOT NULL,
                claimed_at TIMESTAMP DEFAULT NOW(), UNIQUE(user_id, bonus_id))''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS referrals (
                ref_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL UNIQUE, referred_by BIGINT NOT NULL,
                bonus_given BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT NOW())''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS reputation (
                rep_id SERIAL PRIMARY KEY, from_user BIGINT NOT NULL, to_user BIGINT NOT NULL,
                rep_type TEXT NOT NULL, created_at TIMESTAMP DEFAULT NOW())''')

            await conn.execute('''CREATE TABLE IF NOT EXISTS cooldowns (
                cd_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, cd_type TEXT NOT NULL,
                last_used TIMESTAMP DEFAULT NOW(), UNIQUE(user_id, cd_type))''')

            jp = await conn.fetchrow('SELECT * FROM jackpot WHERE jp_id = 1')
            if not jp:
                await conn.execute('INSERT INTO jackpot (jp_id, amount) VALUES (1, 1000000)')
            vtp = await conn.fetchrow('SELECT * FROM vt_price ORDER BY vtp_id DESC LIMIT 1')
            if not vtp:
                await conn.execute('INSERT INTO vt_price (price) VALUES ($1)', random.randint(1000, 15000))

    # ===== USERS =====
    async def get_user(self, uid):
        async with self.pool.acquire() as c:
            return await c.fetchrow('SELECT * FROM users WHERE user_id=$1', uid)

    async def create_user(self, uid, uname, fname):
        async with self.pool.acquire() as c:
            await c.execute('INSERT INTO users(user_id,username,first_name) VALUES($1,$2,$3) ON CONFLICT(user_id) DO UPDATE SET username=EXCLUDED.username,first_name=EXCLUDED.first_name,last_activity=NOW()', uid, uname or '', fname or 'Игрок')

    async def update_balance(self, uid, amt, add=True):
        async with self.pool.acquire() as c:
            if add: await c.execute('UPDATE users SET balance=balance+$1 WHERE user_id=$2', amt, uid)
            else: await c.execute('UPDATE users SET balance=GREATEST(balance-$1,0) WHERE user_id=$2', amt, uid)

    async def update_vt_balance(self, uid, amt, add=True):
        async with self.pool.acquire() as c:
            if add: await c.execute('UPDATE users SET vt_balance=vt_balance+$1 WHERE user_id=$2', amt, uid)
            else: await c.execute('UPDATE users SET vt_balance=GREATEST(vt_balance-$1,0) WHERE user_id=$2', amt, uid)

    async def update_bank(self, uid, amt, add=True):
        async with self.pool.acquire() as c:
            if add: await c.execute('UPDATE users SET bank_balance=bank_balance+$1 WHERE user_id=$2', amt, uid)
            else: await c.execute('UPDATE users SET bank_balance=GREATEST(bank_balance-$1,0) WHERE user_id=$2', amt, uid)

    async def add_xp(self, uid, amt):
        from config import get_level_from_xp
        async with self.pool.acquire() as c:
            await c.execute('UPDATE users SET xp=xp+$1 WHERE user_id=$2', amt, uid)
            u = await c.fetchrow('SELECT xp,level FROM users WHERE user_id=$1', uid)
            if not u: return None
            nl = get_level_from_xp(u['xp'])
            if nl > u['level']:
                await c.execute('UPDATE users SET level=$1 WHERE user_id=$2', nl, uid)
                return nl
            return None

    async def update_stats(self, uid, won=0, lost=0, played=1, game_won=False):
        async with self.pool.acquire() as c:
            await c.execute('UPDATE users SET total_won=total_won+$1,total_lost=total_lost+$2,games_played=games_played+$3,games_won=games_won+$4,last_activity=NOW() WHERE user_id=$5', won, lost, played, 1 if game_won else 0, uid)

    async def set_subscribed(self, uid, s=True):
        async with self.pool.acquire() as c: await c.execute('UPDATE users SET is_subscribed=$1 WHERE user_id=$2', s, uid)

    async def ban_user(self, uid, b=True):
        async with self.pool.acquire() as c: await c.execute('UPDATE users SET is_banned=$1 WHERE user_id=$2', b, uid)

    async def get_top_by_balance(self, n=10):
        async with self.pool.acquire() as c: return await c.fetch('SELECT * FROM users WHERE is_banned=FALSE ORDER BY balance DESC LIMIT $1', n)

    async def get_top_by_vt(self, n=10):
        async with self.pool.acquire() as c: return await c.fetch('SELECT * FROM users WHERE is_banned=FALSE ORDER BY vt_balance DESC LIMIT $1', n)

    async def get_all_users_count(self):
        async with self.pool.acquire() as c: return await c.fetchval('SELECT COUNT(*) FROM users')

    async def get_user_by_username(self, u):
        async with self.pool.acquire() as c: return await c.fetchrow('SELECT * FROM users WHERE LOWER(username)=LOWER($1)', u.replace('@',''))

    async def get_user_position_in_top(self, uid, field='balance'):
        if field not in ('balance','vt_balance','xp'): field='balance'
        async with self.pool.acquire() as c:
            r = await c.fetchval(f'SELECT COUNT(*)+1 FROM users WHERE {field}>(SELECT COALESCE({field},0) FROM users WHERE user_id=$1) AND is_banned=FALSE', uid)
            return r or 1

    async def add_business_slot(self, uid):
        async with self.pool.acquire() as c: await c.execute('UPDATE users SET business_slots=business_slots+1 WHERE user_id=$1', uid)

    # ===== GPU =====
    async def get_user_gpus(self, uid):
        async with self.pool.acquire() as c: return await c.fetch('SELECT * FROM user_gpus WHERE user_id=$1', uid)

    async def buy_gpu(self, uid, gtype, price):
        async with self.pool.acquire() as c:
            np = int(price*1.2)
            e = await c.fetchrow('SELECT * FROM user_gpus WHERE user_id=$1 AND gpu_type=$2', uid, gtype)
            if e: await c.execute('UPDATE user_gpus SET count=count+1,current_price=$1 WHERE user_id=$2 AND gpu_type=$3', np, uid, gtype)
            else: await c.execute('INSERT INTO user_gpus(user_id,gpu_type,count,current_price) VALUES($1,$2,1,$3)', uid, gtype, np)

    async def collect_vt(self, uid):
        from config import GPU_CONFIG
        async with self.pool.acquire() as c:
            gpus = await c.fetch('SELECT * FROM user_gpus WHERE user_id=$1', uid)
            t = 0.0
            for g in gpus:
                cfg = GPU_CONFIG.get(g['gpu_type'])
                if cfg and g['count'] > 0:
                    h = (datetime.now()-g['last_collect']).total_seconds()/3600
                    t += h*cfg['vt_per_hour']*g['count']
            if t > 0:
                await self.update_vt_balance(uid, t, True)
                await c.execute('UPDATE user_gpus SET last_collect=NOW() WHERE user_id=$1', uid)
            return t

    async def get_pending_vt(self, uid):
        from config import GPU_CONFIG
        async with self.pool.acquire() as c:
            gpus = await c.fetch('SELECT * FROM user_gpus WHERE user_id=$1', uid)
            t = 0.0
            for g in gpus:
                cfg = GPU_CONFIG.get(g['gpu_type'])
                if cfg and g['count'] > 0:
                    h = (datetime.now()-g['last_collect']).total_seconds()/3600
                    t += h*cfg['vt_per_hour']*g['count']
            return t

    # ===== MARKET =====
    async def get_vt_price(self):
        async with self.pool.acquire() as c:
            r = await c.fetchrow('SELECT price FROM vt_price ORDER BY vtp_id DESC LIMIT 1')
            return r['price'] if r else 5000

    async def update_vt_price(self):
        async with self.pool.acquire() as c:
            p = random.randint(1000, 15000)
            await c.execute('INSERT INTO vt_price(price) VALUES($1)', p)
            return p

    async def create_market_order(self, uid, otype, amt, price):
        async with self.pool.acquire() as c:
            await c.execute('INSERT INTO market_orders(user_id,order_type,amount,price) VALUES($1,$2,$3,$4)', uid, otype, amt, price)

    async def get_market_orders(self, otype=None, uid=None):
        async with self.pool.acquire() as c:
            if uid: return await c.fetch('SELECT * FROM market_orders WHERE user_id=$1 AND is_active=TRUE ORDER BY created_at DESC', uid)
            if otype: return await c.fetch('SELECT * FROM market_orders WHERE order_type=$1 AND is_active=TRUE ORDER BY price', otype)
            return await c.fetch('SELECT * FROM market_orders WHERE is_active=TRUE ORDER BY created_at DESC LIMIT 20')

    async def cancel_order(self, oid, uid):
        async with self.pool.acquire() as c:
            o = await c.fetchrow('SELECT * FROM market_orders WHERE order_id=$1 AND user_id=$2 AND is_active=TRUE', oid, uid)
            if o:
                await c.execute('UPDATE market_orders SET is_active=FALSE WHERE order_id=$1', oid)
                if o['order_type']=='buy': await self.update_balance(uid, int(o['price']*float(o['amount'])), True)
                else: await self.update_vt_balance(uid, float(o['amount']), True)
                return o

    # ===== PROMO =====
    async def create_promocode(self, code, rtype, ramt, muses, days=7):
        async with self.pool.acquire() as c:
            exp = datetime.now()+timedelta(days=days)
            await c.execute('INSERT INTO promocodes(code,reward_type,reward_amount,max_uses,expires_at) VALUES($1,$2,$3,$4,$5) ON CONFLICT(code) DO UPDATE SET reward_type=EXCLUDED.reward_type,reward_amount=EXCLUDED.reward_amount,max_uses=EXCLUDED.max_uses,expires_at=EXCLUDED.expires_at', code.upper(), rtype, ramt, muses, exp)

    async def use_promocode(self, uid, code):
        async with self.pool.acquire() as c:
            p = await c.fetchrow('SELECT * FROM promocodes WHERE UPPER(code)=UPPER($1) AND expires_at>NOW() AND current_uses<max_uses', code)
            if not p: return None, "Промокод не найден или истёк"
            u = await c.fetchrow('SELECT * FROM used_promocodes WHERE user_id=$1 AND promocode_id=$2', uid, p['promo_id'])
            if u: return None, "Уже использован"
            await c.execute('INSERT INTO used_promocodes(user_id,promocode_id) VALUES($1,$2)', uid, p['promo_id'])
            await c.execute('UPDATE promocodes SET current_uses=current_uses+1 WHERE promo_id=$1', p['promo_id'])
            if p['reward_type']=='vc': await self.update_balance(uid, p['reward_amount'], True)
            elif p['reward_type']=='vt': await self.update_vt_balance(uid, float(p['reward_amount']), True)
            return p, None

    # ===== JACKPOT =====
    async def get_jackpot(self):
        async with self.pool.acquire() as c: return await c.fetchrow('SELECT * FROM jackpot WHERE jp_id=1')

    async def add_to_jackpot(self, amt):
        ct = max(int(amt*0.0001), 1)
        async with self.pool.acquire() as c: await c.execute('UPDATE jackpot SET amount=amount+$1 WHERE jp_id=1', ct)

    async def register_for_jackpot(self, uid):
        async with self.pool.acquire() as c: await c.execute('UPDATE users SET jackpot_registered=TRUE WHERE user_id=$1', uid)

    async def get_jackpot_participants_count(self):
        async with self.pool.acquire() as c: return await c.fetchval('SELECT COUNT(*) FROM users WHERE jackpot_registered=TRUE AND is_banned=FALSE')

    async def draw_jackpot(self):
        async with self.pool.acquire() as c:
            parts = await c.fetch('SELECT * FROM users WHERE jackpot_registered=TRUE AND is_banned=FALSE')
            if not parts: return None
            w = random.choice(parts)
            jp = await self.get_jackpot()
            await self.update_balance(w['user_id'], jp['amount'], True)
            await c.execute('UPDATE jackpot SET amount=1000000,last_winner=$1,last_draw=NOW() WHERE jp_id=1', w['user_id'])
            await c.execute('UPDATE users SET jackpot_registered=FALSE')
            return w, jp['amount']

    # ===== PRESIDENT =====
    async def get_president(self):
        async with self.pool.acquire() as c:
            return await c.fetchrow('SELECT p.*,u.username,u.first_name FROM president p JOIN users u ON p.user_id=u.user_id ORDER BY p.elected_at DESC LIMIT 1')

    async def add_president_profit(self, amt):
        pr = max(int(amt*0.0001), 1)
        async with self.pool.acquire() as c:
            p = await self.get_president()
            if p:
                await c.execute('UPDATE president SET profit=profit+$1 WHERE pres_id=$2', pr, p['pres_id'])
                await self.update_balance(p['user_id'], pr, True)

    async def place_president_bet(self, uid, amt):
        async with self.pool.acquire() as c:
            e = await c.fetchrow('SELECT * FROM president_bets WHERE user_id=$1 AND bet_date=CURRENT_DATE', uid)
            if e: await c.execute('UPDATE president_bets SET bet_amount=bet_amount+$1 WHERE user_id=$2 AND bet_date=CURRENT_DATE', amt, uid)
            else: await c.execute('INSERT INTO president_bets(user_id,bet_amount) VALUES($1,$2)', uid, amt)
            await self.update_balance(uid, amt, False)

    async def get_president_bets(self):
        async with self.pool.acquire() as c:
            return await c.fetch('SELECT pb.*,u.username,u.first_name FROM president_bets pb JOIN users u ON pb.user_id=u.user_id WHERE pb.bet_date=CURRENT_DATE ORDER BY pb.bet_amount DESC')

    async def elect_president(self):
        async with self.pool.acquire() as c:
            bets = await self.get_president_bets()
            if not bets: return None
            cp = await self.get_president()
            eligible = [b for b in bets if not cp or b['user_id']!=cp['user_id']]
            if not eligible: return None
            total = sum(b['bet_amount'] for b in eligible)
            r = random.uniform(0, total); cum = 0; w = eligible[-1]
            for b in eligible:
                cum += b['bet_amount']
                if r <= cum: w = b; break
            for b in eligible:
                if b['user_id'] != w['user_id']:
                    await self.update_balance(b['user_id'], b['bet_amount']//2, True)
            if cp: await c.execute('UPDATE users SET is_president=FALSE WHERE user_id=$1', cp['user_id'])
            await c.execute('INSERT INTO president(user_id,profit) VALUES($1,0)', w['user_id'])
            await c.execute('UPDATE users SET is_president=TRUE WHERE user_id=$1', w['user_id'])
            await c.execute('DELETE FROM president_bets WHERE bet_date<=CURRENT_DATE')
            return w

    # ===== BUSINESS =====
    async def add_business(self, name, price, profit, emoji='🏢'):
        async with self.pool.acquire() as c:
            await c.execute('INSERT INTO businesses(name,base_price,base_profit,emoji) VALUES($1,$2,$3,$4)', name, price, profit, emoji)

    async def get_all_businesses(self):
        async with self.pool.acquire() as c: return await c.fetch('SELECT * FROM businesses ORDER BY base_price')

    async def get_user_businesses(self, uid):
        async with self.pool.acquire() as c:
            return await c.fetch('SELECT ub.*,b.name,b.base_price,b.base_profit,b.emoji FROM user_businesses ub JOIN businesses b ON ub.business_id=b.biz_id WHERE ub.user_id=$1', uid)

    async def buy_business(self, uid, bid):
        async with self.pool.acquire() as c:
            biz = await c.fetchrow('SELECT * FROM businesses WHERE biz_id=$1', bid)
            if not biz: return None, "Не найден"
            u = await self.get_user(uid); ubs = await self.get_user_businesses(uid)
            if any(ub['business_id']==bid for ub in ubs): return None, "Уже есть"
            if len(ubs) >= u['business_slots']: return None, "Нет слотов"
            if u['balance'] < biz['base_price']: return None, "Нет средств"
            await self.update_balance(uid, biz['base_price'], False)
            await c.execute('INSERT INTO user_businesses(user_id,business_id) VALUES($1,$2)', uid, bid)
            return biz, None

    async def collect_business_profit(self, uid, ubid):
        async with self.pool.acquire() as c:
            ub = await c.fetchrow('SELECT ub.*,b.base_profit FROM user_businesses ub JOIN businesses b ON ub.business_id=b.biz_id WHERE ub.ub_id=$1 AND ub.user_id=$2', ubid, uid)
            if not ub: return 0
            h = (datetime.now()-ub['last_collect']).total_seconds()/3600
            pr = int(h*ub['base_profit']*float(ub['profit_multiplier']))
            if pr > 0:
                await self.update_balance(uid, pr, True)
                await c.execute('UPDATE user_businesses SET last_collect=NOW() WHERE ub_id=$1', ubid)
            return pr

    async def sell_business(self, uid, ubid):
        async with self.pool.acquire() as c:
            ub = await c.fetchrow('SELECT ub.*,b.base_price FROM user_businesses ub JOIN businesses b ON ub.business_id=b.biz_id WHERE ub.ub_id=$1 AND ub.user_id=$2', ubid, uid)
            if not ub: return 0
            sp = ub['base_price']//2
            await self.update_balance(uid, sp, True)
            await c.execute('DELETE FROM user_businesses WHERE ub_id=$1', ubid)
            return sp

    async def upgrade_business(self, uid, ubid, cost):
        async with self.pool.acquire() as c:
            ub = await c.fetchrow('SELECT * FROM user_businesses WHERE ub_id=$1 AND user_id=$2', ubid, uid)
            if not ub: return False
            u = await self.get_user(uid)
            if u['balance'] < cost: return False
            await self.update_balance(uid, cost, False)
            nm = float(ub['profit_multiplier'])+0.1
            await c.execute('UPDATE user_businesses SET profit_multiplier=$1,upgrade_level=upgrade_level+1 WHERE ub_id=$2', nm, ubid)
            return True

    # ===== TASKS =====
    async def generate_daily_tasks(self, uid):
        async with self.pool.acquire() as c:
            e = await c.fetch('SELECT * FROM daily_tasks WHERE user_id=$1 AND task_date=CURRENT_DATE', uid)
            if e: return e
            types = ['labyrinth_play','higher_lower_win','knb_play','crash_win','mines_play','diamonds_play','roulette_play','blackjack_play']
            for t in random.sample(types, 4):
                await c.execute('INSERT INTO daily_tasks(user_id,task_type,task_target,reward_vc,reward_vt) VALUES($1,$2,$3,$4,$5)', uid, t, random.randint(3,20), random.randint(500000,1500000), random.randint(1,50))
            return await c.fetch('SELECT * FROM daily_tasks WHERE user_id=$1 AND task_date=CURRENT_DATE', uid)

    async def update_task_progress(self, uid, ttype, inc=1):
        async with self.pool.acquire() as c:
            t = await c.fetchrow('SELECT * FROM daily_tasks WHERE user_id=$1 AND task_type=$2 AND task_date=CURRENT_DATE AND is_completed=FALSE', uid, ttype)
            if not t: return None
            np = t['task_progress']+inc
            await c.execute('UPDATE daily_tasks SET task_progress=$1 WHERE dt_id=$2', np, t['dt_id'])
            if np >= t['task_target']:
                await c.execute('UPDATE daily_tasks SET is_completed=TRUE WHERE dt_id=$1', t['dt_id'])
                await self.update_balance(uid, t['reward_vc'], True)
                await self.update_vt_balance(uid, float(t['reward_vt']), True)
                return t
            return None

    # ===== GAMES =====
    async def start_game(self, uid, gtype, bet, gdata):
        async with self.pool.acquire() as c:
            await c.execute('DELETE FROM active_games WHERE user_id=$1 AND game_type=$2', uid, gtype)
            await c.execute('INSERT INTO active_games(user_id,game_type,bet_amount,game_data) VALUES($1,$2,$3,$4)', uid, gtype, bet, json.dumps(gdata))

    async def get_active_game(self, uid, gtype):
        async with self.pool.acquire() as c:
            r = await c.fetchrow('SELECT * FROM active_games WHERE user_id=$1 AND game_type=$2', uid, gtype)
            if r:
                d = dict(r); gd = d['game_data']
                if isinstance(gd, str): d['game_data'] = json.loads(gd)
                return d
            return None

    async def update_game(self, uid, gtype, gdata):
        async with self.pool.acquire() as c:
            await c.execute('UPDATE active_games SET game_data=$1 WHERE user_id=$2 AND game_type=$3', json.dumps(gdata), uid, gtype)

    async def end_game(self, uid, gtype, wamt, result):
        async with self.pool.acquire() as c:
            g = await self.get_active_game(uid, gtype)
            if g:
                await c.execute('INSERT INTO game_history(user_id,game_type,bet_amount,win_amount,result) VALUES($1,$2,$3,$4,$5)', uid, gtype, g['bet_amount'], wamt, result)
                await c.execute('DELETE FROM active_games WHERE user_id=$1 AND game_type=$2', uid, gtype)
                return g
            return None

    # ===== TRANSFERS =====
    async def transfer(self, fuser, tuser, amt, cur, rate):
        async with self.pool.acquire() as c:
            com = int(amt*rate); net = amt-com
            if cur=='vc': await self.update_balance(fuser, amt, False); await self.update_balance(tuser, net, True)
            elif cur=='vt': await self.update_vt_balance(fuser, float(amt), False); await self.update_vt_balance(tuser, float(net), True)
            await c.execute('INSERT INTO transfers(from_user,to_user,amount,currency,commission) VALUES($1,$2,$3,$4,$5)', fuser, tuser, amt, cur, com)
            return net, com

    # ===== BONUS =====
    async def create_daily_bonus(self, amt, maxact):
        async with self.pool.acquire() as c:
            e = await c.fetchrow('SELECT * FROM daily_bonus WHERE bonus_date=CURRENT_DATE')
            if e: return e
            await c.execute('INSERT INTO daily_bonus(bonus_amount,max_activations) VALUES($1,$2)', amt, maxact)
            return await c.fetchrow('SELECT * FROM daily_bonus WHERE bonus_date=CURRENT_DATE ORDER BY db_id DESC LIMIT 1')

    async def get_active_bonus(self):
        async with self.pool.acquire() as c:
            return await c.fetchrow('SELECT * FROM daily_bonus WHERE bonus_date=CURRENT_DATE AND current_activations<max_activations ORDER BY db_id DESC LIMIT 1')

    async def claim_bonus(self, uid):
        async with self.pool.acquire() as c:
            b = await self.get_active_bonus()
            if not b: return None, "Бонус недоступен"
            cl = await c.fetchrow('SELECT * FROM bonus_claims WHERE user_id=$1 AND bonus_id=$2', uid, b['db_id'])
            if cl: return None, "Уже получен"
            await c.execute('INSERT INTO bonus_claims(user_id,bonus_id) VALUES($1,$2)', uid, b['db_id'])
            await c.execute('UPDATE daily_bonus SET current_activations=current_activations+1 WHERE db_id=$1', b['db_id'])
            await self.update_balance(uid, b['bonus_amount'], True)
            return await c.fetchrow('SELECT * FROM daily_bonus WHERE db_id=$1', b['db_id']), None

    # ===== REFERRALS =====
    async def set_referrer(self, uid, ref_by):
        async with self.pool.acquire() as c:
            if uid == ref_by: return False
            e = await c.fetchrow('SELECT * FROM referrals WHERE user_id=$1', uid)
            if e: return False
            await c.execute('INSERT INTO referrals(user_id,referred_by) VALUES($1,$2) ON CONFLICT DO NOTHING', uid, ref_by)
            return True

    async def get_referrer(self, uid):
        async with self.pool.acquire() as c:
            r = await c.fetchrow('SELECT referred_by FROM referrals WHERE user_id=$1', uid)
            return r['referred_by'] if r else None

    async def get_referral_count(self, uid):
        async with self.pool.acquire() as c:
            return await c.fetchval('SELECT COUNT(*) FROM referrals WHERE referred_by=$1', uid)

    async def give_referral_bonus(self, uid):
        async with self.pool.acquire() as c:
            ref = await c.fetchrow('SELECT * FROM referrals WHERE user_id=$1 AND bonus_given=FALSE', uid)
            if not ref: return False
            await self.update_balance(uid, 50000, True)
            await self.update_balance(ref['referred_by'], 25000, True)
            await self.update_vt_balance(ref['referred_by'], 1.0, True)
            await c.execute('UPDATE referrals SET bonus_given=TRUE WHERE ref_id=$1', ref['ref_id'])
            return True

    async def add_referral_profit(self, uid, lost_amt):
        ref = await self.get_referrer(uid)
        if ref:
            pr = int(lost_amt*0.02)
            if pr > 0: await self.update_balance(ref, pr, True)

    # ===== REPUTATION =====
    async def add_reputation(self, fuser, tuser, rtype):
        async with self.pool.acquire() as c:
            if fuser == tuser: return None, "❌ Нельзя себе"
            last = await c.fetchrow('SELECT * FROM reputation WHERE from_user=$1 AND to_user=$2 AND created_at>NOW()-INTERVAL \'1 hour\'', fuser, tuser)
            if last: return None, "⏳ Раз в час"
            await c.execute('INSERT INTO reputation(from_user,to_user,rep_type) VALUES($1,$2,$3)', fuser, tuser, rtype)
            return True, None

    async def get_reputation(self, uid):
        async with self.pool.acquire() as c:
            plus = await c.fetchval("SELECT COUNT(*) FROM reputation WHERE to_user=$1 AND rep_type='plus'", uid) or 0
            minus = await c.fetchval("SELECT COUNT(*) FROM reputation WHERE to_user=$1 AND rep_type='minus'", uid) or 0
            return plus - (minus*2)

    # ===== COOLDOWNS =====
    async def check_cooldown(self, uid, ctype, hours=1.0):
        async with self.pool.acquire() as c:
            r = await c.fetchrow('SELECT last_used FROM cooldowns WHERE user_id=$1 AND cd_type=$2', uid, ctype)
            if not r: return True
            return datetime.now()-r['last_used'] > timedelta(hours=hours)

    async def set_cooldown(self, uid, ctype):
        async with self.pool.acquire() as c:
            await c.execute('INSERT INTO cooldowns(user_id,cd_type,last_used) VALUES($1,$2,NOW()) ON CONFLICT(user_id,cd_type) DO UPDATE SET last_used=NOW()', uid, ctype)

    async def get_cooldown_remaining(self, uid, ctype, hours=1.0):
        async with self.pool.acquire() as c:
            r = await c.fetchrow('SELECT last_used FROM cooldowns WHERE user_id=$1 AND cd_type=$2', uid, ctype)
            if not r: return 0
            elapsed = (datetime.now()-r['last_used']).total_seconds()
            return max(0, int(hours*3600-elapsed))


db = Database()
