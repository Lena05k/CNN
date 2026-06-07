#!/usr/bin/env python3
"""
Обучение YOLOv8-segment для сегментации птиц (ДЗ2).

Использование:
    cd training/
    python3 main.py --task segment --model yolov8n-seg-sgd   --epochs 20
    python3 main.py --task segment --model yolov8n-seg-adam  --epochs 20
    python3 main.py --task segment --model yolov8n-seg-adamw --epochs 50
    python3 main.py --task segment --model yolov8s-seg-adamw --epochs 50
"""

import shutil
from pathlib import Path

import torch
from ultralytics.utils import SETTINGS
SETTINGS["mlflow"] = False          # отключаем встроенный mlflow callback
from ultralytics import YOLO

from configs.config import Config, BASE_DIR as ROOT_DIR
from utils.mlflow_utils import setup_mlflow
from utils.export import export_onnx_and_verify


# ── Конфигурации 4-х обязательных запусков ─────────────────────────────────
# Название → (base_weights, optimizer, lr0, epochs, batch)
SEGMENT_CONFIGS = {
    "yolov8n-seg-sgd": {
        "weights":            "yolov8n-seg.pt",
        "default_optimizer":  "SGD",
        "default_lr":         0.01,
        "default_epochs":     20,
        "default_batch":      8,
    },
    "yolov8n-seg-adam": {
        "weights":            "yolov8n-seg.pt",
        "default_optimizer":  "Adam",
        "default_lr":         0.001,
        "default_epochs":     20,
        "default_batch":      8,
    },
    "yolov8n-seg-adamw": {
        "weights":            "yolov8n-seg.pt",
        "default_optimizer":  "AdamW",
        "default_lr":         0.0005,
        "default_epochs":     50,
        "default_batch":      8,
    },
    "yolov8s-seg-adamw": {
        "weights":            "yolov8s-seg.pt",
        "default_optimizer":  "AdamW",
        "default_lr":         0.0005,
        "default_epochs":     50,
        "default_batch":      8,
    },
}


def train_yolo_segment(
    model_name: str = "yolov8n-seg-adamw",
    optimizer:  str = None,
    lr:         float = None,
    epochs:     int   = None,
    imgsz:      int   = 640,
    batch:      int   = None,
    device:     str   = "cuda",
    export_to_frontend: bool = True,
) -> dict:
    """
    Запустить один обучающий прогон YOLOv8-seg с MLflow-трекингом.

    Returns:
        dict с метриками финального прогона (mAP50, precision, recall и др.)
    """
    cfg = SEGMENT_CONFIGS.get(model_name, SEGMENT_CONFIGS["yolov8n-seg-adamw"])

    optimizer = optimizer or cfg["default_optimizer"]
    lr        = lr        or cfg["default_lr"]
    epochs    = epochs    or cfg["default_epochs"]
    batch     = batch     or cfg["default_batch"]

    yaml_path  = ROOT_DIR / "training" / "data" / "birds.yaml"
    run_name   = f"{model_name}-e{epochs}-bs{batch}-{optimizer.lower()}"
    run_dir    = ROOT_DIR / "yolo8_segment" / run_name
    device_str = "cpu" if device == "cpu" or not torch.cuda.is_available() else "0"

    print(f"\n{'='*60}")
    print(f"  Запуск: {run_name}")
    print(f"  Оптимизатор: {optimizer}, LR: {lr}, Эпох: {epochs}, Batch: {batch}")
    print(f"  Устройство: {device_str}")
    print(f"{'='*60}")

    # MLflow
    mlflow = setup_mlflow(experiment_name="birds-segmentation")

    # Загружаем базовую модель
    model = YOLO(cfg["weights"])

    with mlflow.start_run(run_name=run_name):
        mlflow.log_params({
            "model":        model_name,
            "weights":      cfg["weights"],
            "optimizer":    optimizer,
            "learning_rate": lr,
            "epochs":       epochs,
            "imgsz":        imgsz,
            "batch":        batch,
            "device":       device_str,
            "dataset":      "birds_segmentation",
            "num_classes":  Config.NUM_CLASSES,
            "classes":      ", ".join(Config.CLASSES),
        })

        results = model.train(
            data=str(yaml_path),
            epochs=epochs,
            imgsz=imgsz,
            device=device_str,
            batch=batch,
            optimizer=optimizer,
            lr0=lr,
            lrf=0.01,
            project=str(ROOT_DIR / "yolo8_segment"),
            name=run_name,
            exist_ok=False,
            verbose=True,
            amp=True,
            plots=True,
            save=True,
            save_period=10,
        )

        # ── Логируем метрики ──────────────────────────────────────────────
        metrics = {}
        if hasattr(results, "results_dict"):
            for key, val in results.results_dict.items():
                if isinstance(val, (int, float)):
                    clean = (key.replace("[", "_").replace("]", "_")
                                .replace("(", "_").replace(")", "_")
                                .replace("/", "_"))
                    mlflow.log_metric(clean, val)
                    metrics[clean] = val

        # ── Логируем артефакты ────────────────────────────────────────────
        weights_dir = run_dir / "weights"
        for fname in ("best.pt", "last.pt"):
            p = weights_dir / fname
            if p.exists():
                mlflow.log_artifact(str(p), "model")

        for fname in ("results.png", "confusion_matrix.png",
                      "confusion_matrix_normalized.png", "PR_curve.png"):
            p = run_dir / fname
            if p.exists():
                mlflow.log_artifact(str(p), "artifacts")

        # ── ONNX экспорт ──────────────────────────────────────────────────
        frontend_dest = (
            ROOT_DIR / "frontend" / "public" / "models" / "best.onnx"
            if export_to_frontend else None
        )
        try:
            onnx_path = export_onnx_and_verify(
                model, weights_dir, dest_path=frontend_dest
            )
            mlflow.log_artifact(str(onnx_path), "onnx_model")
            # Сохраняем копию в data/models/
            models_dir = ROOT_DIR / "training" / "data" / "models"
            models_dir.mkdir(parents=True, exist_ok=True)
            safe = model_name.replace("-", "_")
            shutil.copy(onnx_path, models_dir / f"{safe}_e{epochs}.onnx")
        except Exception as e:
            print(f"  ⚠ ONNX экспорт: {e}")

        print(f"\n  ✓ Готово: {run_dir}")
        return metrics


def run_segment_from_args(args) -> dict:
    """CLI-обёртка: вызывается из main.py."""
    cfg = SEGMENT_CONFIGS.get(args.model, SEGMENT_CONFIGS["yolov8n-seg-adamw"])
    return train_yolo_segment(
        model_name=args.model,
        optimizer=args.optimizer or cfg["default_optimizer"],
        lr=args.lr or cfg["default_lr"],
        epochs=args.epochs or cfg["default_epochs"],
        imgsz=getattr(args, "imgsz", 640) or 640,
        batch=args.batch or cfg["default_batch"],
        device=getattr(args, "device", "cuda") or "cuda",
        export_to_frontend=not getattr(args, "no_export", False),
    )
