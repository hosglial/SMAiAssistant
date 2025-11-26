"""
Обработчик ошибок бота.
"""
import logging
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Глобальный обработчик ошибок.
    
    Args:
        update: Объект Update от Telegram (может быть None)
        context: Контекст выполнения с информацией об ошибке
    """
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)

