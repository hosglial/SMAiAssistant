"""
Утилиты для обработчиков.
"""


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

