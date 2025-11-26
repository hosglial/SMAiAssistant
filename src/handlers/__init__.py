"""
Модуль обработчиков Telegram бота.
"""
from .commands import start
from .messages import handle_message
from .callbacks import handle_feedback_callback
from .errors import error_handler

__all__ = [
    'start',
    'handle_message',
    'handle_feedback_callback',
    'error_handler',
]

