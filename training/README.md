# ДЗ2 — Обучение YOLOv8-seg (Сегментация птиц)

## Требования

```bash
pip install ultralytics mlflow onnx onnxruntime torch torchvision
```

## Датасет

Уже аннотирован в формате YOLO polygon (Roboflow).  
Путь настраивается в `data/birds.yaml` → поле `path:`.

**Структура датасета:**
```
obj_train_data/
├── train/images/   (271 изображение)
├── train/labels/
├── valid/images/   (40 изображений)
├── valid/labels/
└── test/images/
```

**Классы:** `0 = albatross`, `1 = puffin`

## Запуск

```bash
cd training/

# Один прогон
python train_all.py --run 1   # SGD,   yolov8n, 20 эпох
python train_all.py --run 2   # Adam,  yolov8n, 20 эпох
python train_all.py --run 3   # AdamW, yolov8n, 50 эпох
python train_all.py --run 4   # AdamW, yolov8s, 50 эпох

# Все 4 прогона подряд (рекомендуется)
python train_all.py --all

# На CPU (если нет GPU)
python train_all.py --run 3 --device cpu

# Только экспорт ONNX (если модель уже обучена)
python train_all.py --export-only --run 3
```

## Результаты

После обучения:
- Веса и графики → `yolo8_segment/<run_name>/`
- ONNX-модель   → `frontend/public/models/best.onnx` (автоматически)
- MLflow runs   → `mlruns/` (или `http://localhost:5000`)

## Конфигурации прогонов

| # | Модель      | Опт.  | LR     | Эпох |
|---|-------------|-------|--------|------|
| 1 | yolov8n-seg | SGD   | 0.010  | 20   |
| 2 | yolov8n-seg | Adam  | 0.001  | 20   |
| 3 | yolov8n-seg | AdamW | 0.0005 | 50   |
| 4 | yolov8s-seg | AdamW | 0.0005 | 50   |
