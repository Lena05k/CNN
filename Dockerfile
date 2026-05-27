# ── Stage 1: сборка Vue-фронтенда ─────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
# vite.config.js: outDir = '../templates/dist'  →  /templates/dist
RUN npm run build


# ── Stage 2: Django + Gunicorn ────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Системные зависимости: ONNX, Pillow, шрифты для Pillow (кириллица в масках)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Исходный код Django
COPY manage.py .
COPY DjangoProject/ ./DjangoProject/

# ML-модели
COPY media/ ./media/
COPY yolo8_segment/ ./yolo8_segment/

# Собранный Vue-фронтенд из stage 1
COPY --from=frontend-builder /templates/dist ./templates/dist

# Папка для загружаемых изображений
RUN mkdir -p media/images

# Миграции и сбор статики
RUN python manage.py migrate --noinput
RUN python manage.py collectstatic --noinput

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=DjangoProject.settings

EXPOSE 8000

CMD ["gunicorn", "DjangoProject.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "120"]
