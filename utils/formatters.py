def format_number(num: int | float) -> str:
    """Форматирование чисел в к, кк, ккк и т.д."""
    if num is None:
        return "0"
    
    num = float(num)
    
    if abs(num) < 1000:
        return str(int(num))
    
    suffixes = ['', 'к', 'кк', 'ккк', 'кккк', 'ккккк']
    magnitude = 0
    
    original = num
    while abs(num) >= 1000 and magnitude < len(suffixes) - 1:
        magnitude += 1
        num /= 1000.0
    
    # Форматируем с нужной точностью
    if num == int(num):
        return f"{int(num)}{suffixes[magnitude]}"
    elif abs(original) >= 100000000:  # 100кк+
        return f"{num:.1f}{suffixes[magnitude]}"
    else:
        return f"{num:.2f}{suffixes[magnitude]}"


def format_time(seconds: int) -> str:
    """Форматирование времени"""
    if seconds < 0:
        seconds = 0
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}ч.")
    if minutes > 0:
        parts.append(f"{minutes}мин.")
    if secs > 0 or not parts:
        parts.append(f"{secs}сек.")
    
    return " ".join(parts)


def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    """Создание прогресс-бара"""
    if total <= 0:
        return "░" * length
    
    filled = int(length * min(current, total) / total)
    empty = length - filled
    return "▓" * filled + "░" * empty


def parse_amount(text: str) -> int:
    """Парсинг суммы из текста (100к -> 100000)"""
    text = text.lower().strip()
    
    multipliers = {
        'к': 1000,
        'кк': 1000000,
        'ккк': 1000000000,
        'кккк': 1000000000000,
    }
    
    for suffix, mult in sorted(multipliers.items(), key=lambda x: -len(x[0])):
        if text.endswith(suffix):
            try:
                return int(float(text[:-len(suffix)]) * mult)
            except:
                pass
    
    try:
        return int(float(text))
    except:
        return 0
