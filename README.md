# Telegram RAG Assistant

RAG (Retrieval-Augmented Generation) ассистент для документации UEM SafeMobile. Бот использует векторный поиск в Qdrant и генерацию ответов через OpenRouter API для предоставления точной информации из документации.

## Архитектура

- **Telegram Bot**: обработка сообщений пользователей
- **Qdrant**: векторная БД для хранения эмбеддингов документации
- **PostgreSQL**: база данных для логирования запросов и ответов
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
OLLAMA_EMBEDDING_MODEL=qwen3-embedding:0.6b

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password_here
POSTGRES_DATABASE=aiassistant
POSTGRES_DB_POOL_SIZE=10
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

## Docker

### Сборка образа локально

```bash
docker build -t aiassistant-bot:latest .
```

### Запуск контейнера

```bash
docker run -d \
  --name aiassistant-bot \
  --env-file .env \
  -e QDRANT_URL=http://host.docker.internal:6333 \
  -e OLLAMA_URL=http://host.docker.internal:11434 \
  aiassistant-bot:latest
```

**Примечание:** Если Qdrant и Ollama запущены на хосте, используйте `host.docker.internal` для доступа к ним из контейнера. Для Linux может потребоваться `--network host` или использование IP адреса хоста.

### Запуск через Docker Compose

Самый простой способ запуска - использовать Docker Compose. Все переменные из `.env` файла автоматически загружаются:

**Вариант 1: Только бот (Qdrant и Ollama на хосте)**
```bash
docker-compose up -d
```

**Вариант 2: Бот + PostgreSQL (Qdrant и Ollama на хосте)**
```bash
docker-compose -f docker-compose.full.yml up -d
```

**Управление:**
```bash
# Просмотр логов
docker-compose logs -f bot

# Остановка
docker-compose down

# Пересборка и перезапуск
docker-compose up -d --build
```

**Как работает с .env:**
- Docker Compose автоматически загружает все переменные из `.env` файла через `env_file: .env`
- Не нужно перепечатывать переменные - просто создайте `.env` файл и запустите `docker-compose up`
- Переменные из `.env` можно переопределить через `environment:` секцию в compose файле

### Использование образа из GitHub Container Registry

После сборки через GitHub Actions образ будет доступен в `ghcr.io`:

```bash
docker pull ghcr.io/<your-username>/<repo-name>:latest
docker run -d --name aiassistant-bot --env-file .env ghcr.io/<your-username>/<repo-name>:latest
```

## GitHub Actions

При пуше в ветку `main` или создании тега автоматически запускается сборка Docker образа и публикация в GitHub Container Registry (ghcr.io).

**Триггеры:**
- Push в ветку `main` → образ с тегом `main` и `latest`
- Создание тега `v*` → образ с тегом версии (например, `v1.0.0`)
- Pull Request → сборка без публикации

**Использование образа:**
```bash
# Вход в GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Запуск образа
docker run -d --name aiassistant-bot --env-file .env \
  ghcr.io/<your-username>/<repo-name>:latest
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
│   ├── rag_service.py   # RAG сервис (векторный поиск + генерация)
│   └── db_service.py    # Сервис для работы с PostgreSQL
├── .github/
│   └── workflows/
│       └── docker-build.yml  # GitHub Actions workflow для сборки образа
├── Dockerfile            # Dockerfile для сборки образа
├── docker-compose.yml    # Docker Compose для запуска бота
├── docker-compose.full.yml  # Docker Compose с Qdrant
├── .dockerignore         # Исключения для Docker сборки
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
