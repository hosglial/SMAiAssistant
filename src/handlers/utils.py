"""
Утилиты для обработчиков.
"""

# Максимальная длина сообщения в Telegram (с запасом для безопасности)
MAX_MESSAGE_LENGTH = 4000  # Оставляем запас от 4096


def escape_markdown_v2(text: str) -> str:
    """
    Экранирование специальных символов Markdown V2.
    
    Args:
        text: Исходный текст
        
    Returns:
        Текст с экранированными специальными символами
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def split_long_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """
    Разбивает длинное сообщение на части, стараясь сохранить целостность абзацев.
    
    Args:
        text: Исходный текст для разбиения
        max_length: Максимальная длина одной части (по умолчанию 4000 символов)
        
    Returns:
        Список частей текста
    """
    if len(text) <= max_length:
        return [text]
    
    parts = []
    remaining_text = text
    
    while len(remaining_text) > max_length:
        # Пытаемся найти место разрыва по абзацам (двойной перенос строки)
        split_pos = remaining_text.rfind('\n\n', 0, max_length)
        
        # Если не нашли абзац, ищем по одинарному переносу строки
        if split_pos == -1:
            split_pos = remaining_text.rfind('\n', 0, max_length)
        
        # Если не нашли перенос строки, ищем по точке с пробелом
        if split_pos == -1:
            split_pos = remaining_text.rfind('. ', 0, max_length)
            if split_pos != -1:
                split_pos += 1  # Включаем точку
        
        # Если ничего не нашли, разрываем по пробелу
        if split_pos == -1:
            split_pos = remaining_text.rfind(' ', 0, max_length)
        
        # Если даже пробела нет, разрываем принудительно
        if split_pos == -1:
            split_pos = max_length
        
        # Добавляем часть в список
        part = remaining_text[:split_pos].strip()
        if part:
            parts.append(part)
        
        # Обновляем оставшийся текст
        remaining_text = remaining_text[split_pos:].strip()
    
    # Добавляем последнюю часть, если она есть
    if remaining_text:
        parts.append(remaining_text)
    
    return parts

