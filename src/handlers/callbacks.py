"""
Обработчики callback-запросов от inline-кнопок.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

import db_service

logger = logging.getLogger(__name__)


async def handle_feedback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатий на кнопки обратной связи.
    
    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения
    """
    query = update.callback_query
    
    try:
        # Подтверждаем получение callback
        await query.answer("Спасибо за отзыв!")
        
        # Парсим callback_data для получения feedback
        if not query.data or ":" not in query.data:
            logger.error(f"Некорректный формат callback_data: {query.data}")
            return
        
        feedback_value = query.data.split(":")[1]
        message_id = query.message.message_id
        user_id = update.effective_user.id
        
        logger.info(
            f"Получен feedback от пользователя {user_id} для сообщения {message_id}: {feedback_value}"
        )
        
        # Сохраняем feedback в БД
        if db_service.db_service:
            try:
                success = await db_service.db_service.update_feedback(
                    telegram_message_id=message_id,
                    feedback=feedback_value
                )
                
                if success:
                    # Удаляем кнопки после успешного сохранения
                    await query.edit_message_reply_markup(reply_markup=None)
                    logger.info(f"Кнопки удалены для сообщения {message_id}")
                else:
                    logger.warning(f"Не удалось сохранить feedback для сообщения {message_id}")
                    
            except Exception as db_error:
                logger.error(f"Ошибка при сохранении feedback в БД: {db_error}", exc_info=True)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке feedback callback: {e}", exc_info=True)

