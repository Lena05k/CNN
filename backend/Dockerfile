FROM python:3.11-slim

WORKDIR /app

# Системные зависимости для ONNX Runtime и Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода Django
COPY manage.py .
COPY DjangoProject/ ./DjangoProject/
COPY media/ ./media/

# Копирование frontend для templates
COPY frontend/index.html ./frontend/index.html

# Создание папки для загруженных изображений и БД
RUN mkdir -p media/images

# Выполнение миграций при сборке
RUN python manage.py migrate --noinput

# Переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=DjangoProject.settings

EXPOSE 8000

# Запуск Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
