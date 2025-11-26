"""
Сервис для работы с PostgreSQL базой данных
"""
import logging
import json
from typing import List, Dict, Any, Optional
import asyncpg
from config import Config

logger = logging.getLogger(__name__)


class DatabaseService:
    """Сервис для работы с PostgreSQL"""
    
    def __init__(self, config: Config):
        """
        Инициализация сервиса базы данных
        
        Args:
            config: Конфигурация приложения
        """
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self) -> None:
        """
        Инициализация пула соединений и создание таблицы
        """
        try:
            # Создаем пул соединений
            self.pool = await asyncpg.create_pool(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                user=self.config.postgres_user,
                password=self.config.postgres_password,
                database=self.config.postgres_database,
                min_size=1,
                max_size=self.config.postgres_db_pool_size,
            )
            logger.info(
                f"Пул соединений с PostgreSQL создан. "
                f"Хост: {self.config.postgres_host}:{self.config.postgres_port}, "
                f"БД: {self.config.postgres_database}"
            )
            
            # Создаем таблицу если её нет
            await self.initialize_db()
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}", exc_info=True)
            raise
    
    async def initialize_db(self) -> None:
        """
        Создание таблицы conversations если её нет
        """
        create_table_query = """
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            user_name TEXT,
            question TEXT NOT NULL,
            context_chunks JSONB NOT NULL,
            prompt TEXT NOT NULL,
            llm_response TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            telegram_message_id BIGINT,
            feedback BOOLEAN,
            feedback_timestamp TIMESTAMP,
            avg_context_score FLOAT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
        CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
        CREATE INDEX IF NOT EXISTS idx_conversations_success ON conversations(success);
        CREATE INDEX IF NOT EXISTS idx_conversations_telegram_message_id ON conversations(telegram_message_id);
        CREATE INDEX IF NOT EXISTS idx_conversations_avg_context_score ON conversations(avg_context_score);
        """
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(create_table_query)
                
                # Миграция: изменяем тип поля feedback с TEXT на BOOLEAN для существующих таблиц
                migration_query = """
                DO $$
                BEGIN
                    -- Проверяем, существует ли колонка feedback с типом TEXT
                    IF EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name = 'conversations' 
                        AND column_name = 'feedback' 
                        AND data_type = 'text'
                    ) THEN
                        -- Конвертируем существующие данные и изменяем тип
                        ALTER TABLE conversations 
                        ALTER COLUMN feedback TYPE BOOLEAN 
                        USING CASE 
                            WHEN feedback = 'yes' THEN true
                            WHEN feedback = 'no' THEN false
                            ELSE NULL
                        END;
                        
                        RAISE NOTICE 'Поле feedback успешно изменено на BOOLEAN';
                    END IF;
                END $$;
                """
                await conn.execute(migration_query)
                
            logger.info("Таблица conversations создана или уже существует")
        except Exception as e:
            logger.error(f"Ошибка при создании таблицы: {e}", exc_info=True)
            raise
    
    async def save_conversation(
        self,
        user_id: int,
        user_name: Optional[str],
        question: str,
        context_chunks: List[Dict[str, Any]],
        prompt: str,
        llm_response: str,
        success: bool,
        telegram_message_id: Optional[int] = None,
        avg_context_score: Optional[float] = None
    ) -> Optional[int]:
        """
        Сохранение данных о запросе в базу данных
        
        Args:
            user_id: ID пользователя Telegram
            user_name: Имя пользователя
            question: Вопрос клиента
            context_chunks: Найденные куски контекста из векторной БД
            prompt: Полный промпт, отправленный в LLM
            llm_response: Полный ответ от нейронной сети
            success: Флаг успешности из ответа LLM
            telegram_message_id: ID сообщения с ответом бота в Telegram
            avg_context_score: Средняя оценка релевантности найденных фрагментов
            
        Returns:
            ID созданной записи в БД или None при ошибке
        """
        if not self.pool:
            logger.warning("Пул соединений не инициализирован, пропускаем сохранение")
            return None
        
        try:
            insert_query = """
            INSERT INTO conversations 
            (user_id, user_name, question, context_chunks, prompt, llm_response, success, telegram_message_id, avg_context_score)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
            """
            
            async with self.pool.acquire() as conn:
                record_id = await conn.fetchval(
                    insert_query,
                    user_id,
                    user_name,
                    question,
                    json.dumps(context_chunks, ensure_ascii=False),
                    prompt,
                    llm_response,
                    success,
                    telegram_message_id,
                    avg_context_score
                )
            avg_score_str = f"{avg_context_score:.3f}" if avg_context_score is not None else "N/A"
            logger.debug(
                f"Данные о запросе сохранены в БД. User ID: {user_id}, Success: {success}, "
                f"Message ID: {telegram_message_id}, Avg Score: {avg_score_str}, "
                f"Record ID: {record_id}"
            )
            return record_id
            
        except Exception as e:
            # Не прерываем работу бота при ошибках БД
            logger.error(f"Ошибка при сохранении данных в БД: {e}", exc_info=True)
            return None
    
    async def update_feedback(
        self,
        telegram_message_id: int,
        feedback: str
    ) -> bool:
        """
        Обновление обратной связи для сообщения
        
        Args:
            telegram_message_id: ID сообщения с ответом бота в Telegram
            feedback: Значение обратной связи ('yes' или 'no')
            
        Returns:
            True если обновление прошло успешно, False при ошибке
        """
        if not self.pool:
            logger.warning("Пул соединений не инициализирован, пропускаем обновление feedback")
            return False
        
        # Конвертируем строку в boolean
        feedback_bool = True if feedback == 'yes' else False
        
        try:
            update_query = """
            UPDATE conversations 
            SET feedback = $1, feedback_timestamp = NOW()
            WHERE telegram_message_id = $2 AND feedback IS NULL
            RETURNING id
            """
            
            async with self.pool.acquire() as conn:
                record_id = await conn.fetchval(
                    update_query,
                    feedback_bool,
                    telegram_message_id
                )
            
            if record_id:
                logger.info(
                    f"Feedback обновлен для сообщения {telegram_message_id}. "
                    f"Значение: {feedback_bool} ('{feedback}'), Record ID: {record_id}"
                )
                return True
            else:
                logger.warning(
                    f"Не удалось обновить feedback для сообщения {telegram_message_id}. "
                    f"Возможно, feedback уже был установлен или запись не найдена."
                )
                return False
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении feedback в БД: {e}", exc_info=True)
            return False
    
    async def close(self) -> None:
        """
        Закрытие пула соединений
        """
        if self.pool:
            await self.pool.close()
            logger.info("Пул соединений с PostgreSQL закрыт")
            self.pool = None


# Экземпляр сервиса базы данных (синглтон на уровне модуля)
db_service: Optional[DatabaseService] = None

