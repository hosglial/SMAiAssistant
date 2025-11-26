"""
Telegram RAG бот для документации UEM SafeMobile.
"""
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler, CallbackQueryHandler

from config import Config
from rag_service import RAGService
import db_service
from handlers import start, handle_message, handle_feedback_callback, error_handler
from handlers.messages import set_rag_service

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """
    Инициализация сервисов после создания приложения.
    
    Args:
        application: Экземпляр Application
    """
    from db_service import DatabaseService
    
    config = application.bot_data.get('config')
    if not config:
        logger.error("Конфигурация не найдена в bot_data")
        return
    
    # Инициализируем RAG сервис
    rag_service = RAGService(config)
    set_rag_service(rag_service)
    logger.info("RAG сервис инициализирован")
    
    # Инициализируем сервис базы данных
    db_service.db_service = DatabaseService(config)
    await db_service.db_service.initialize()
    logger.info("Сервис базы данных инициализирован")


async def post_shutdown(application: Application) -> None:
    """
    Закрытие соединений при завершении работы бота.
    
    Args:
        application: Экземпляр Application
    """
    if db_service.db_service:
        await db_service.db_service.close()


def main() -> None:
    """Главная функция запуска бота."""
    try:
        # Загружаем конфигурацию
        config = Config.from_env()
        logger.info("Конфигурация загружена")
        
        # Создаем приложение с post_init и post_shutdown через ApplicationBuilder
        application = (
            Application.builder()
            .token(config.telegram_bot_token)
            .post_init(post_init)
            .post_shutdown(post_shutdown)
            .build()
        )
        
        # Сохраняем конфигурацию в bot_data для использования в post_init
        application.bot_data['config'] = config
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(handle_feedback_callback))
        
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
