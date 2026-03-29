def format_number(num: int | float) -> str:
    """Форматирование чисел в к, кк, ккк и т.д."""
    if num is None:
        return "0"
    
    num = float(num)
    
    if num < 1000:
        return str(int(num))
    
    suffixes = ['', 'к', 'кк', 'ккк', 'кккк', 'ккккк']
    magnitude = 0
    
    while abs(num) >= 1000 and magnitude < len(suffixes) - 1:
        magnitude += 1
        num /= 1000.0
    
    if num == int(num):
        return f"{int(num)}{suffixes[magnitude]}"
    else:
        return f"{num:.2f}{suffixes[magnitude]}"


def format_time(seconds: int) -> str:
    """Форматирование времени"""
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
    filled = int(length * current / total) if total > 0 else 0
    empty = length - filled
    return "▓" * filled + "░" * empty
