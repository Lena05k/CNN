# ONNX Model

Поместите обученную модель сюда как `best.onnx`.

После обучения скрипт `training/train_all.py` скопирует файл автоматически.
Либо вручную:

```bash
cp yolo8_segment/<run_name>/weights/best.onnx frontend/public/models/best.onnx
```
