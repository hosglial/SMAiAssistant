# Telegram RAG Assistant

RAG (Retrieval-Augmented Generation) ассистент для документации UEM SafeMobile. Бот использует векторный поиск в Qdrant и генерацию ответов через OpenRouter API для предоставления точной информации из документации.

## Архитектура

- **Telegram Bot**: обработка сообщений пользователей
- **Qdrant**: векторная БД для хранения эмбеддингов документации
- **OpenRouter API**: генерация ответов через LLM модели
- **Ollama**: векторизация запросов (модель qwen3-embedding:0.6b по умолчанию)

## Предварительные требования

1. Python 3.12+
2. Docker (для Qdrant)
3. Ollama с установленной моделью для эмбеддингов (по умолчанию `qwen3-embedding:0.6b`)
4. Токен Telegram бота от [@BotFather](https://t.me/BotFather)
5. API ключ от [OpenRouter](https://openrouter.ai/)

## Установка

### 1. Установка зависимостей

```bash
poetry install
```

### 2. Запуск Qdrant

Запустите Qdrant в Docker контейнере:

```bash
docker run -d -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

### 3. Установка Ollama и модели эмбеддингов

Установите Ollama:
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

Загрузите модель для эмбеддингов (или другую, указанную в `.env`):
```bash
ollama pull qwen3-embedding:0.6b
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корневой директории проекта:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-3.5-turbo

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=safemobile_docs

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

**Важно:** Эмбеддинги должны быть загружены в Qdrant отдельным сервисом перед запуском бота.

## Запуск

1. Убедитесь, что запущены Qdrant и Ollama:
```bash
# Проверка Qdrant
curl http://localhost:6333/health

# Проверка Ollama
curl http://localhost:11434/api/tags
```

2. Убедитесь, что в Qdrant загружена коллекция с эмбеддингами документации

3. Запустите бота:
```bash
poetry run python src/bot.py
```

## Использование

1. Найдите вашего бота в Telegram по имени, которое вы указали при создании
2. Отправьте команду `/start` для приветствия
3. Задайте любой вопрос о системе UEM SafeMobile
4. Бот найдет релевантную информацию в документации и сгенерирует ответ

## Конфигурация RAG параметров

Вы можете настроить параметры RAG через переменные окружения:

- `RAG_TOP_K` - количество документов для поиска (по умолчанию: 15)
- `RAG_SCORE_THRESHOLD` - минимальный порог релевантности (по умолчанию: 0.5)

## Структура проекта

```
AIAssistantBot/
├── src/
│   ├── bot.py           # Основной файл Telegram бота
│   ├── config.py        # Конфигурация приложения
│   └── rag_service.py   # RAG сервис (векторный поиск + генерация)
├── pyproject.toml       # Конфигурация Poetry и зависимости
├── poetry.lock          # Заблокированные версии зависимостей
└── README.md            # Документация
```

## Troubleshooting

### Бот не находит ответы
- Проверьте, что коллекция в Qdrant заполнена данными
- Убедитесь, что название коллекции в `.env` совпадает с фактическим
- Попробуйте уменьшить `RAG_SCORE_THRESHOLD`

### Ошибки при векторизации
- Убедитесь, что Ollama запущен: `ollama serve`
- Проверьте, что модель установлена: `ollama list | grep qwen3-embedding`
- Убедитесь, что название модели в `.env` совпадает с установленной

### Ошибки OpenRouter
- Проверьте правильность API ключа
- Убедитесь, что на балансе достаточно средств
- Проверьте доступность модели в вашем регионе
