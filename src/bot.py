"""
Telegram RAG бот для документации UEM SafeMobile.
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from telegram.constants import ParseMode

from config import Config
from rag_service import RAGService

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Глобальная переменная для RAG сервиса
rag_service = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    welcome_message = (
        "Привет! Я RAG-ассистент по документации UEM SafeMobile.\n\n"
        "Задайте мне любой вопрос о системе, и я постараюсь найти ответ в документации."
    )
    await update.message.reply_text(welcome_message)
    logger.info(f"Пользователь {update.effective_user.id} запустил бота")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений с использованием RAG"""
    user_question = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"Получен вопрос от пользователя {user_id}: {user_question}")
    
    # Отправляем индикатор "печатает..."
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Получаем ответ от RAG сервиса
        answer, success = rag_service.answer_question(user_question)
        
        # Отправляем ответ пользователю с markdown форматированием
        await update.message.reply_text(
            answer,
            parse_mode=ParseMode.MARKDOWN
        )
        
        status = "успешно" if success else "без результата"
        logger.info(f"Ответ отправлен пользователю {user_id} ({status})")
        
    except Exception as e:
        error_message = "⚠️ Извините, произошла ошибка при обработке вашего вопроса. Попробуйте позже."
        await update.message.reply_text(error_message)
        logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)


def main() -> None:
    """Главная функция запуска бота."""
    global rag_service
    
    try:
        # Загружаем конфигурацию
        config = Config.from_env()
        logger.info("Конфигурация загружена")
        
        # Инициализируем RAG сервис
        rag_service = RAGService(config)
        logger.info("RAG сервис инициализирован")
        
        # Создаем приложение
        application = Application.builder().token(config.telegram_bot_token).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Регистрируем обработчик ошибок
        application.add_error_handler(error_handler)
        
        # Запускаем бота
        logger.info("Бот запущен и готов к работе...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
