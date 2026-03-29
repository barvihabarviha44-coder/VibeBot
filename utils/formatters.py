import re


def format_number(num) -> str:
    """Форматирование чисел в к, кк, ккк"""
    if num is None:
        return "0"
    
    num = float(num)
    
    if abs(num) < 1000:
        return str(int(num))
    
    suffixes = ['', 'к', 'кк', 'ккк', 'кккк']
    magnitude = 0
    
    while abs(num) >= 1000 and magnitude < len(suffixes) - 1:
        magnitude += 1
        num /= 1000.0
    
    if num == int(num):
        return f"{int(num)}{suffixes[magnitude]}"
    else:
        return f"{num:.2f}{suffixes[magnitude]}".rstrip('0').rstrip('.')


def parse_bet(text: str) -> int:
    """Парсинг ставки из текста: 1к, 1.5к, 1кк, 1.5кк и т.д."""
    text = text.lower().strip().replace(' ', '').replace(',', '.')
    
    # Паттерн для чисел с суффиксами
    match = re.match(r'^(\d+\.?\d*)(к+|кк+|ккк+)?$', text)
    
    if not match:
        # Пробуем просто число
        try:
            return int(float(text))
        except:
            return 0
    
    number = float(match.group(1))
    suffix = match.group(2) or ''
    
    # Считаем множитель по количеству 'к'
    multiplier = 1000 ** len(suffix) if suffix else 1
    
    result = int(number * multiplier)
    return result


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
