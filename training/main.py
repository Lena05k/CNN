#!/usr/bin/env python3
"""
Главный скрипт обучения YOLOv8-seg (ДЗ2 — Сегментация птиц).

Запустить один из 4 обязательных прогонов:
    python main.py --model yolov8n-seg-sgd
    python main.py --model yolov8n-seg-adam
    python main.py --model yolov8n-seg-adamw
    python main.py --model yolov8s-seg-adamw

Все 4 прогона подряд:
    python main.py --all

Переопределить гиперпараметры:
    python main.py --model yolov8n-seg-adamw --epochs 100 --batch 4 --lr 0.0003
"""

import argparse
import sys

import torch

from options import YOLO_MODELS, get_segment_config, print_segment_summary
from scripts.train_yolo_seg import train_yolo_segment


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Обучение YOLOv8-seg для сегментации птиц",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--model",     type=str, default="yolov8n-seg-adamw",
                   choices=YOLO_MODELS, help="Конфигурация модели")
    p.add_argument("--all",       action="store_true",
                   help="Последовательно запустить все 4 обязательных прогона")
    p.add_argument("--optimizer", type=str, default=None,
                   help="Оптимизатор (SGD | Adam | AdamW)")
    p.add_argument("--lr",        type=float, default=None, help="Learning rate")
    p.add_argument("--epochs",    type=int,   default=None, help="Количество эпох")
    p.add_argument("--batch",     type=int,   default=None, help="Batch size")
    p.add_argument("--imgsz",     type=int,   default=640,  help="Размер изображения")
    p.add_argument("--device",    type=str,   default="cuda",
                   choices=["cuda", "cpu"], help="Устройство")
    p.add_argument("--no-export", action="store_true",
                   help="Не копировать ONNX в frontend/public/models/")
    return p


def main():
    args = build_parser().parse_args()

    print("\n" + "=" * 60)
    print("  ДЗ2 — Сегментация птиц (YOLOv8-seg + ONNX)")
    print("=" * 60)
    print(f"  PyTorch : {torch.__version__}")
    print(f"  CUDA    : {torch.cuda.is_available()}")
    print(f"  Устройство: {args.device}")
    print("=" * 60)

    models_to_run = YOLO_MODELS if args.all else [args.model]
    all_results = []

    for model_name in models_to_run:
        cfg = get_segment_config(model_name)
        try:
            metrics = train_yolo_segment(
                model_name=model_name,
                optimizer=args.optimizer or cfg["default_optimizer"],
                lr=args.lr       or cfg["default_lr"],
                epochs=args.epochs or cfg["default_epochs"],
                imgsz=args.imgsz,
                batch=args.batch or cfg["default_batch"],
                device=args.device,
                export_to_frontend=not args.no_export,
            )
            metrics["name"] = model_name
            all_results.append(metrics)
        except Exception as e:
            print(f"\n  ✗ Ошибка при обучении {model_name}: {e}")
            if not args.all:
                sys.exit(1)

    if all_results:
        print_segment_summary(all_results)


if __name__ == "__main__":
    main()
