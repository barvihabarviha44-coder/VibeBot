import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

CHANNEL_ID = "@nvibee_bet"
CHAT_ID = "@chatvibee_bet"
CHANNEL_LINK = "https://t.me/nvibee_bet"
CHAT_LINK = "https://t.me/chatvibee_bet"

ADMIN_IDS = [575621653]  # Добавьте свой ID
ADMIN_USERNAME = "@d066q"

# Эмодзи Premium
EMOJI = {
    "coin": "🪙",
    "diamond": "💎",
    "fire": "🔥",
    "star": "⭐",
    "crown": "👑",
    "money": "💰",
    "bank": "🏦",
    "chart": "📊",
    "rocket": "🚀",
    "bomb": "💣",
    "gem": "💠",
    "dice": "🎲",
    "football": "⚽",
    "basketball": "🏀",
    "darts": "🎯",
    "bowling": "🎳",
    "slot": "🎰",
    "trophy": "🏆",
    "gift": "🎁",
    "check": "✅",
    "cross": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "user": "👤",
    "users": "👥",
    "work": "💼",
    "farm": "🖥️",
    "gpu": "💻",
    "market": "🛒",
    "transfer": "💸",
    "level": "📈",
    "xp": "✨",
    "time": "🕐",
    "president": "👨‍💼",
    "business": "🏢",
    "tax": "📋",
    "jackpot": "🎰",
    "task": "📍",
    "help": "❓",
    "settings": "⚙️",
    "back": "◀️",
    "forward": "▶️",
    "up": "🔼",
    "down": "🔽",
    "play": "▶️",
    "stop": "⏹️",
    "refresh": "🔄",
    "lock": "🔒",
    "unlock": "🔓",
    "pin": "📌",
    "link": "🔗",
    "calendar": "📅",
    "bell": "🔔",
    "mute": "🔕",
    "speaker": "🔊",
    "eye": "👁️",
    "heart": "❤️",
    "broken_heart": "💔",
    "thumbs_up": "👍",
    "thumbs_down": "👎",
    "clap": "👏",
    "handshake": "🤝",
    "pray": "🙏",
    "muscle": "💪",
    "brain": "🧠",
    "eyes": "👀",
    "mouth": "👄",
    "ear": "👂",
    "nose": "👃",
    "foot": "🦶",
    "leg": "🦵",
    "bone": "🦴",
    "tooth": "🦷",
    "tongue": "👅",
    "lungs": "🫁",
    "anatomical_heart": "🫀",
    "mechanical_arm": "🦾",
    "mechanical_leg": "🦿",
    "door": "🚪",
    "key": "🔑",
    "hammer": "🔨",
    "axe": "🪓",
    "pick": "⛏️",
    "wrench": "🔧",
    "screwdriver": "🪛",
    "nut_bolt": "🔩",
    "gear": "⚙️",
    "chains": "⛓️",
    "magnet": "🧲",
    "ladder": "🪜",
    "scissors": "✂️",
    "card_box": "🗃️",
    "file_cabinet": "🗄️",
    "wastebasket": "🗑️",
    "closed_lock": "🔐",
    "green_circle": "🟢",
    "red_circle": "🔴",
    "blue_circle": "🔵",
    "yellow_circle": "🟡",
    "orange_circle": "🟠",
    "purple_circle": "🟣",
    "brown_circle": "🟤",
    "black_circle": "⚫",
    "white_circle": "⚪",
    "red_square": "🟥",
    "blue_square": "🟦",
    "green_square": "🟩",
    "yellow_square": "🟨",
    "orange_square": "🟧",
    "purple_square": "🟪",
    "brown_square": "🟫",
    "black_square": "⬛",
    "white_square": "⬜",
    "large_blue_diamond": "🔷",
    "large_orange_diamond": "🔶",
    "small_blue_diamond": "🔹",
    "small_orange_diamond": "🔸",
}

# Видеокарты для фермы
GPU_CONFIG = {
    "low": {
        "name": "NVIDIA GTX 1660 Super",
        "emoji": "🟢",
        "base_price": 150000,
        "vt_per_hour": 0.2,
        "max_count": 10
    },
    "medium": {
        "name": "NVIDIA RTX 3070",
        "emoji": "🟡", 
        "base_price": 200000,
        "vt_per_hour": 0.4,
        "max_count": 10
    },
    "high": {
        "name": "NVIDIA RTX 4090",
        "emoji": "🔴",
        "base_price": 250000,
        "vt_per_hour": 0.6,
        "max_count": 10
    }
}

# Работы
JOBS_CONFIG = [
    {"name": "Курьер", "emoji": "📦", "min_salary": 50000, "max_salary": 80000, "min_level": 1, "duration": 60},
    {"name": "Кассир", "emoji": "🛒", "min_salary": 70000, "max_salary": 100000, "min_level": 3, "duration": 90},
    {"name": "Официант", "emoji": "🍽️", "min_salary": 90000, "max_salary": 130000, "min_level": 5, "duration": 120},
    {"name": "Программист", "emoji": "💻", "min_salary": 150000, "max_salary": 250000, "min_level": 8, "duration": 180},
    {"name": "Дизайнер", "emoji": "🎨", "min_salary": 120000, "max_salary": 200000, "min_level": 10, "duration": 150},
    {"name": "Менеджер", "emoji": "📊", "min_salary": 200000, "max_salary": 350000, "min_level": 15, "duration": 240},
    {"name": "Инженер", "emoji": "⚙️", "min_salary": 250000, "max_salary": 400000, "min_level": 20, "duration": 300},
    {"name": "Врач", "emoji": "🩺", "min_salary": 350000, "max_salary": 550000, "min_level": 25, "duration": 360},
    {"name": "Адвокат", "emoji": "⚖️", "min_salary": 500000, "max_salary": 750000, "min_level": 30, "duration": 420},
    {"name": "Директор", "emoji": "👔", "min_salary": 700000, "max_salary": 1000000, "min_level": 40, "duration": 480},
]

# Уровни XP
def get_level_xp(level: int) -> int:
    return int(100 * (level ** 1.5))

def get_level_from_xp(xp: int) -> int:
    level = 1
    while get_level_xp(level) <= xp:
        level += 1
    return level - 1
