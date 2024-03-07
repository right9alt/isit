# Используем официальный образ Python в качестве родительского образа
FROM python:3.12-slim

# Установим переменные среды для Python и убедимся, что Python выводит все
# в stdout и stderr без буферизации (например, для журналов Docker)
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Установим рабочий каталог в контейнере на /app
WORKDIR /app

# Скопируем только файлы зависимостей, чтобы избежать проблем с кэшированием
#COPY utils.py /app/scrapper/
COPY scrapper/poetry.lock scrapper/pyproject.toml /app/

# Установим Poetry
RUN pip install poetry
RUN poetry lock

# Установим зависимости проекта с помощью Poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

COPY ./scrapper /app
