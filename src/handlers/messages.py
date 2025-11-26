"""
Обработчики текстовых сообщений.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from .utils import escape_markdown_v2
import db_service

logger = logging.getLogger(__name__)

# Глобальная переменная для RAG сервиса (будет установлена при инициализации)
rag_service = None


def set_rag_service(service):
    """
    Установить глобальный RAG сервис.
    
    Args:
        service: Экземпляр RAGService
    """
    global rag_service
    rag_service = service


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик текстовых сообщений с использованием RAG.
    
    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения
    """
    user_question = update.message.text
    user_id = update.effective_user.id
    
    # Получаем имя пользователя
    user_name = (
        update.effective_user.full_name 
        or update.effective_user.first_name 
        or None
    )
    
    logger.info(f"Получен вопрос от пользователя {user_id} ({user_name}): {user_question}")
    
    # Отправляем индикатор "печатает..."
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Получаем ответ от RAG сервиса
        answer, success, context_chunks, full_prompt, full_llm_response, avg_score = rag_service.answer_question(user_question)
        
        # Логируем ответ LLM для отладки
        logger.info(f"Ответ LLM (длина: {len(answer)} символов):\n{'-'*50}\n{answer}\n{'-'*50}")
        
        # Создаем inline-клавиатуру с кнопками обратной связи
        keyboard = [
            [
                InlineKeyboardButton("✅ Корректно", callback_data="feedback:yes"),
                InlineKeyboardButton("❌ Некорректно", callback_data="feedback:no")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Пытаемся отправить ответ с markdown форматированием
        try:
            sent_message = await update.message.reply_text(
                answer,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            logger.info(f"Сообщение отправлено с Markdown форматированием")
        except Exception as markdown_error:
            # Если ошибка парсинга markdown - пробуем MarkdownV2 с экранированием
            logger.error(f"Ошибка парсинга Markdown: {markdown_error}")
            logger.warning("Повторная отправка с экранированием специальных символов...")
            
            try:
                escaped_answer = escape_markdown_v2(answer)
                sent_message = await update.message.reply_text(
                    escaped_answer,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=reply_markup
                )
                logger.info("Сообщение отправлено с MarkdownV2 и экранированием")
            except Exception as v2_error:
                # Если и это не помогло - отправляем вообще без форматирования
                logger.error(f"Ошибка парсинга MarkdownV2: {v2_error}")
                logger.warning("Отправка вообще без форматирования...")
                
                sent_message = await update.message.reply_text(
                    answer,
                    reply_markup=reply_markup
                )
                logger.info("Сообщение отправлено без форматирования")
        
        telegram_message_id = sent_message.message_id
        status = "успешно" if success else "без результата"
        logger.info(f"Ответ отправлен пользователю {user_id} ({status}), Message ID: {telegram_message_id}")
        
        # Сохраняем данные в БД (не блокируем ответ пользователю при ошибках)
        if db_service.db_service:
            try:
                await db_service.db_service.save_conversation(
                    user_id=user_id,
                    user_name=user_name,
                    question=user_question,
                    context_chunks=context_chunks,
                    prompt=full_prompt,
                    llm_response=full_llm_response,
                    success=success,
                    telegram_message_id=telegram_message_id,
                    avg_context_score=avg_score
                )
            except Exception as db_error:
                logger.error(f"Ошибка при сохранении данных в БД: {db_error}", exc_info=True)
        
    except Exception as e:
        error_message = "⚠️ Извините, произошла ошибка при обработке вашего вопроса. Попробуйте позже."
        await update.message.reply_text(error_message)
        logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)

