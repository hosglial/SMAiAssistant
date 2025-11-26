"""
Обработчики команд бота.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start.
    
    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения
    """
    welcome_message = (
        "Привет! Я RAG-ассистент по документации UEM SafeMobile.\n\n"
        "Задайте мне любой вопрос о системе, и я постараюсь найти ответ в документации."
    )
    await update.message.reply_text(welcome_message)
    logger.info(f"Пользователь {update.effective_user.id} запустил бота")

