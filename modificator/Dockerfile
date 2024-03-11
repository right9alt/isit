# Используем официальный образ Python в качестве родительского образа
FROM python:3.10-slim

# Установим переменные среды для Python и убедимся, что Python выводит все
# в stdout и stderr без буферизации (например, для журналов Docker)
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Установим рабочий каталог в контейнере на /app
WORKDIR /app

# Установим Poetry
RUN pip install poetry

# Скопируем только файлы зависимостей, чтобы избежать проблем с кэшированием
#COPY utils.py /app/modificator/
COPY modificator/poetry.lock modificator/pyproject.toml /app/

RUN poetry lock

# Установим зависимости проекта с помощью Poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

COPY ./modificator /app
