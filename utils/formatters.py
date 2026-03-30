def format_number(num) -> str:
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
    return f"{num:.2f}{suffixes[magnitude]}".rstrip('0').rstrip('.')


def parse_bet(text: str) -> int:
    text = text.lower().strip().replace(' ', '').replace(',', '.')
    k_count = 0
    while text.endswith('к'):
        k_count += 1
        text = text[:-1]
    try:
        number = float(text)
    except:
        return 0
    result = int(number * (1000 ** k_count))
    return max(0, result)


def parse_amount_special(text: str, current_amount: int) -> int:
    """
    Поддержка:
    - 1к / 1.5к / 2кк
    - all / все
    - пол / половина
    """
    raw = text.lower().strip().replace(' ', '')
    if raw in ('all', 'все', 'всё'):
        return max(0, int(current_amount))
    if raw in ('пол', 'половина', 'half'):
        return max(0, int(current_amount // 2))
    return parse_bet(raw)


def format_time(seconds: int) -> str:
    if seconds < 0:
        seconds = 0
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    parts = []
    if h > 0:
        parts.append(f"{h}ч.")
    if m > 0:
        parts.append(f"{m}мин.")
    if s > 0 or not parts:
        parts.append(f"{s}сек.")
    return " ".join(parts)


def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    if total <= 0:
        return "░" * length
    filled = int(length * min(current, total) / total)
    return "▓" * filled + "░" * (length - filled)
