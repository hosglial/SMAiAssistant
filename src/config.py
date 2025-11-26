"""
Конфигурация для Telegram RAG бота
"""
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Класс конфигурации приложения на основе Pydantic"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Telegram Bot
    telegram_bot_token: str = Field(
        ...,
        description="Токен Telegram бота от @BotFather"
    )
    
    # OpenRouter API
    openrouter_api_key: str = Field(
        ...,
        description="API ключ от OpenRouter"
    )
    openrouter_model: str = Field(
        default="openai/gpt-3.5-turbo",
        description="Модель для генерации ответов"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="Базовый URL OpenRouter API"
    )
    
    # Qdrant
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="URL Qdrant сервера"
    )
    qdrant_collection: str = Field(
        default="safemobile_docs",
        description="Название коллекции в Qdrant"
    )
    
    # Ollama
    ollama_url: str = Field(
        default="http://localhost:11434",
        description="URL Ollama сервера"
    )
    ollama_embedding_model: str = Field(
        default="qwen3-embedding:0.6b",
        description="Модель для генерации эмбеддингов"
    )
    
    # RAG параметры
    rag_top_k: int = Field(
        default=15,
        ge=1,
        le=50,
        description="Количество документов для поиска"
    )
    rag_score_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Минимальный порог релевантности (0.3-0.5 оптимально)"
    )
    
    # PostgreSQL
    postgres_host: str = Field(
        default="localhost",
        description="Хост PostgreSQL сервера"
    )
    postgres_port: int = Field(
        default=5432,
        ge=1,
        le=65535,
        description="Порт PostgreSQL сервера"
    )
    postgres_user: str = Field(
        default="postgres",
        description="Пользователь PostgreSQL"
    )
    postgres_password: str = Field(
        ...,
        description="Пароль PostgreSQL"
    )
    postgres_database: str = Field(
        default="aiassistant",
        description="Название базы данных"
    )
    postgres_db_pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Размер пула соединений с БД"
    )
    
    @field_validator("telegram_bot_token", "openrouter_api_key", "postgres_password")
    @classmethod
    def validate_not_empty(cls, v: str, info) -> str:
        """Проверяет, что обязательные поля не пустые"""
        if not v or v.strip() == "":
            raise ValueError(f"{info.field_name} не может быть пустым")
        return v.strip()
    
    @property
    def top_k(self) -> int:
        """Алиас для обратной совместимости"""
        return self.rag_top_k
    
    @property
    def score_threshold(self) -> float:
        """Алиас для обратной совместимости"""
        return self.rag_score_threshold
    
    @classmethod
    def from_env(cls) -> "Config":
        """Создает конфигурацию из переменных окружения
        
        Этот метод оставлен для обратной совместимости.
        В Pydantic можно просто использовать Config()
        """
        return cls()

