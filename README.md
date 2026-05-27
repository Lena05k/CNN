# 🐦 Bird Vision — классификация и сегментация птиц

**Веб-приложение на Django + Vue.js** для распознавания птиц с помощью нейронных сетей.
Два независимых модуля: классификация изображений (CNN ResNet) и сегментация объектов (YOLOv8-seg).

🌐 **Живое демо:** [https://cnn-production-cd13.up.railway.app](https://cnn-production-cd13.up.railway.app)

---

## 📋 Содержание

- [Описание задач](#описание-задач)
- [Результаты обучения](#результаты-обучения)
- [Технологии](#технологии)
- [Архитектура](#архитектура)
- [Запуск проекта](#запуск-проекта)
- [Деплой](#деплой)

---

## Описание задач

### ДЗ 1 — Классификация изображений

Обучена свёрточная нейронная сеть на базе **ResNet** для классификации изображений птиц из трёх классов подмножества CIFAR-100:

| Класс | Описание |
|---|---|
| 🐧 Пингвин (*Spheniscidae*) | Нелетающие морские птицы Южного полушария |
| 🐦 Тупик (*Fratercula arctica*) | Морские птицы с ярким оранжевым клювом |
| 🦅 Альбатрос (*Diomedeidae*) | Крупные птицы с размахом крыльев до 3,5 м |

**Что делает модуль:**
- Загрузка изображения через drag-and-drop
- Классификация через ONNX Runtime на сервере
- Отображение результата: название, латинское имя, масса, описание
- Вывод весовых коэффициентов ключевых слоёв модели (нормализация, Conv1, Conv18, классификатор)

### ДЗ 2 — Сегментация объектов

Обучена модель **YOLOv8n-seg** для сегментации птиц на изображениях с пиксельными масками.

**Что делает модуль:**
- Загрузка изображения, настройка порога уверенности (5–95%)
- Сегментация через серверный ONNX Runtime
- Отображение масок, ограничивающих рамок с подписями и процентом уверенности
- Поиск похожих карточек по классу (CLIP-ранжирование, если доступно)
- История обработанных изображений

---

## Результаты обучения

Проведено обучение **7 конфигураций** YOLOv8n/s-seg с разными оптимизаторами и количеством эпох:

| Модель | mAP50 | Precision | Recall |
|---|:---:|:---:|:---:|
| yolov8n-seg-sgd-e20 | **0.9903** | 0.9467 | 0.9928 |
| yolov8n-seg-adam-e20 | 0.9584 | 0.9293 | 0.9060 |
| yolov8n-seg-adamw-e20 | 0.9716 | 0.9655 | 0.9787 |
| yolov8n-seg-sgd-e50 | 0.9692 | 0.9176 | 0.9250 |
| yolov8n-seg-adam-e50 | 0.9886 | 0.9944 | 0.9306 |
| yolov8n-seg-adamw-e50 | 0.9738 | 0.9853 | 0.9583 |
| yolov8s-seg-adamw-e50 | 0.9776 | 0.9554 | 0.9515 |

### 🏆 Лучшая модель: `yolov8n-seg-sgd-e20`

**mAP50 = 0.9903** — наивысший результат среди всех конфигураций.

**Вывод:** несмотря на меньшее число эпох (20 vs 50), модель с оптимизатором SGD показала лучший результат. SGD с моментумом лучше обобщается на данном датасете — более медленная, но стабильная сходимость дала более качественные веса. Увеличение числа эпох до 50 у SGD привело к переобучению (mAP50 упал с 0.9903 до 0.9692). Более сложная архитектура yolov8s при тех же условиях не превзошла лёгкую yolov8n.

---

## Технологии

**Backend**
- Python 3.11, Django 4.2
- ONNX Runtime — инференс без PyTorch
- Pillow — рендеринг масок на изображениях
- Gunicorn — продакшн-сервер

**Frontend**
- Vue 3 (Composition API)
- Vite + Tailwind CSS
- Axios

**ML**
- Ultralytics YOLOv8-seg (обучение)
- CNN ResNet (обучение через PyTorch, экспорт в ONNX)
- MLflow — трекинг экспериментов

**Инфраструктура**
- Docker / Docker Compose
- Railway (деплой)
- WhiteNoise (раздача статики)

---

## Архитектура

```
├── DjangoProject/          # Django-приложение
│   ├── views.py            # API: /predictImage, /api/segment, /api/clip-search
│   ├── segmentation.py     # YOLOv8-seg инференс + рендеринг масок
│   └── clip_search.py      # CLIP-поиск похожих карточек
├── frontend/               # Vue 3 + Vite
│   └── src/
│       ├── components/
│       │   ├── sections/   # ClassifierCard, SegmenterCard, HeroSection
│       │   └── ui/         # DropZone, BaseButton, PredictionResult, FileChip
│       └── constants/      # birdMeta, segmentMeta, birdCards
├── media/
│   └── models/             # cifar100_CNN_RESNET20.onnx (372 KB)
├── yolo8_segment/
│   └── yolov8n-seg-sgd-e20/weights/best.onnx  (13 MB)
├── training/               # скрипты обучения
├── Dockerfile              # продакшн multi-stage сборка
└── docker-compose.yml      # локальная разработка
```

**Поток запроса (классификация):**
```
Браузер → POST /predictImage (FormData) → Django view
→ ONNX Runtime (ResNet) → argmax + softmax → класс + уверенность
→ JSON { prediction, weightsSummary } → Vue → PredictionResult
```

**Поток запроса (сегментация):**
```
Браузер → POST /api/segment (FormData) → Django view
→ letterbox → ONNX Runtime (YOLOv8) → NMS → маски
→ Pillow render (маски + подписи) → base64 PNG
→ JSON { rendered, detections } → Vue → SegmenterCard
```

---

## Запуск проекта

### Через Docker Compose (рекомендуется)

```bash
# Клонировать репозиторий
git clone <repo-url>
cd DjangoProject

# Собрать и запустить
make build
make up

# Приложение доступно:
# Frontend: http://localhost:5173
# Backend:  http://localhost:8001
```

Доступные команды:

```bash
make help          # список всех команд
make up            # запустить в фоне
make down          # остановить
make logs          # логи всех контейнеров
make logs-backend  # логи Django
make rebuild       # пересобрать с нуля
make shell-backend # shell внутри backend-контейнера
```

### Без Docker (локально)

```bash
# Backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend (в отдельном терминале)
cd frontend
npm install
npm run dev
```

Frontend будет на `http://localhost:5173`, запросы к API проксируются на Django (`http://localhost:8000`).

---

## Деплой

Проект задеплоен на **Railway** через Docker.

Переменные окружения на сервере:

| Переменная | Значение |
|---|---|
| `SECRET_KEY` | случайная строка 50+ символов |
| `DEBUG` | `False` |

Пересборка происходит автоматически при каждом `git push origin master`.
