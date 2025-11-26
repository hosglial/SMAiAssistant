# Используем официальный Python образ
FROM python:3.12-slim

# Обновляем пакеты (curl больше не нужен, Poetry устанавливается через pip)
RUN apt-get update && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry 2.1.1
ENV POETRY_VERSION=2.1.1
ENV POETRY_CACHE_DIR=/opt/poetry-cache

RUN pip install --no-cache-dir poetry==${POETRY_VERSION} \
    && poetry --version

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock ./

# Настраиваем Poetry: не создавать виртуальное окружение (используем системный Python)
RUN poetry config virtualenvs.create false

# Устанавливаем зависимости
RUN poetry install --no-interaction --no-ansi --no-root

# Копируем исходный код
COPY src/ ./src/

# Создаем непривилегированного пользователя
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Переменные окружения по умолчанию (можно переопределить при запуске)
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Команда запуска
CMD ["python", "src/bot.py"]

