# CNN Classifier — Frontend

Vue 3 + Tailwind CSS SPA для классификации изображений через Django backend.

## Архитектура

```
frontend/
├── index.html                  # Entry point
├── vite.config.js              # Vite + proxy к Django
├── tailwind.config.js          # Tailwind тема (белые тона)
├── postcss.config.js
├── package.json
└── src/
    ├── main.js                 # Монтирование приложения
    ├── App.vue                 # Root-компонент
    ├── api/
    │   └── classifier.js       # Axios запрос к /predictImage
    ├── composables/
    │   └── useFileUpload.js    # Реюзабельная логика загрузки файла
    ├── assets/css/
    │   └── main.css            # Tailwind + кастомные утилиты
    └── components/
        ├── layout/
        │   ├── AppNav.vue      # Фиксированный навбар
        │   └── AppFooter.vue   # Футер
        ├── sections/
        │   ├── HeroSection.vue    # Заголовок страницы
        │   ├── ClassifierCard.vue # Основная карточка с формой
        │   └── FeaturesRow.vue    # Ряд из трёх фич-карточек
        ├── ui/
        │   ├── DropZone.vue       # Drag & Drop зона
        │   ├── FileChip.vue       # Чип с именем файла
        │   ├── BaseButton.vue     # Переиспользуемая кнопка
        │   ├── PredictionResult.vue # Блок результата
        │   └── FeatureCard.vue    # Одна фич-карточка
        └── icons/
            ├── IconBrain.vue
            ├── IconUpload.vue
            ├── IconImage.vue
            ├── IconClose.vue
            ├── IconSpinner.vue
            ├── IconSparkles.vue
            └── IconCheck.vue
```

## Запуск

```bash
cd frontend
npm install
npm run dev       # dev-сервер на :5173, proxy → Django :8000
npm run build     # сборка в ../templates/dist/
```

## Интеграция с Django

После `npm run build` статика попадает в `templates/dist/`.
Добавьте в `DjangoProject/urls.py`:

```python
from django.views.generic import TemplateView
urlpatterns = [
    path('', TemplateView.as_view(template_name='dist/index.html')),
    path('predictImage', views.predictImage, name='predictImage'),
]
```

В `settings.py` убедитесь что `TEMPLATES[0]['DIRS']` включает `templates/`.
