#!/usr/bin/env python3
"""
ДЗ2 — Обучение YOLOv8-seg для сегментации птиц (Альбатрос / Тупик / Пингвин).

Запуск одного прогона:
    cd training/
    python train_all.py --run 1   # SGD,   yolov8n, 20 эпох
    python train_all.py --run 2   # Adam,  yolov8n, 20 эпох
    python train_all.py --run 3   # AdamW, yolov8n, 20 эпох
    python train_all.py --run 4   # SGD,   yolov8n, 50 эпох
    python train_all.py --run 5   # Adam,  yolov8n, 50 эпох
    python train_all.py --run 6   # AdamW, yolov8n, 50 эпох  ← обычно лучший
    python train_all.py --run 7   # AdamW, yolov8s, 50 эпох

Все 7 прогонов подряд:
    python train_all.py --all

Только экспорт уже обученной модели в ONNX:
    python train_all.py --export-only --run 6
"""

import argparse
import shutil
import sys
import urllib.request
from pathlib import Path

import torch
import mlflow
from ultralytics import YOLO
from ultralytics.utils import SETTINGS

SETTINGS["mlflow"] = False   # отключаем встроенный callback

# ── Пути ──────────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).resolve().parent.parent          # DjangoProject/
YAML_PATH    = ROOT / "training" / "data" / "birds.yaml"
OUTPUT_DIR   = ROOT / "yolo8_segment"
FRONTEND_DEST = ROOT / "frontend" / "public" / "models" / "best.onnx"

# ── 7 вариантов обучения ──────────────────────────────────────────────────────
RUNS = {
    1: dict(name="yolov8n-seg-sgd-e20",       weights="yolov8n-seg.pt", optimizer="SGD",   lr=0.010,  epochs=20, batch=8),
    2: dict(name="yolov8n-seg-adam-e20",      weights="yolov8n-seg.pt", optimizer="Adam",  lr=0.001,  epochs=20, batch=8),
    3: dict(name="yolov8n-seg-adamw-e20",     weights="yolov8n-seg.pt", optimizer="AdamW", lr=0.001,  epochs=20, batch=8),
    4: dict(name="yolov8n-seg-sgd-e50",       weights="yolov8n-seg.pt", optimizer="SGD",   lr=0.0005, epochs=50, batch=8),
    5: dict(name="yolov8n-seg-adam-e50",      weights="yolov8n-seg.pt", optimizer="Adam",  lr=0.0005, epochs=50, batch=8),
    6: dict(name="yolov8n-seg-adamw-e50",     weights="yolov8n-seg.pt", optimizer="AdamW", lr=0.0005, epochs=50, batch=8),  # обычно лучший
    7: dict(name="yolov8s-seg-adamw-e50",     weights="yolov8s-seg.pt", optimizer="AdamW", lr=0.0005, epochs=50, batch=8),
}


# ── MLflow ────────────────────────────────────────────────────────────────────
def setup_mlflow() -> mlflow:
    uri = "http://localhost:5000"
    try:
        urllib.request.urlopen(uri, timeout=2)
    except Exception:
        uri = str(ROOT / "mlruns")
        print(f"  MLflow: используем локальный путь {uri}")
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment("birds-segmentation")
    return mlflow


# ── Один тренировочный прогон ─────────────────────────────────────────────────
def train_run(run_id: int, device: str = "auto") -> dict:
    cfg      = RUNS[run_id]
    run_name = cfg["name"]                  # берём имя прямо из конфига
    run_dir  = OUTPUT_DIR / run_name

    if device == "auto":
        device_str = "0" if torch.cuda.is_available() else "cpu"
    else:
        device_str = device

    print(f"\n{'='*60}")
    print(f"  Запуск {run_id}: {run_name}")
    print(f"  opt={cfg['optimizer']}, lr={cfg['lr']}, "
          f"epochs={cfg['epochs']}, batch={cfg['batch']}")
    print(f"  Устройство: {device_str}")
    print(f"{'='*60}")

    mlf   = setup_mlflow()
    model = YOLO(cfg["weights"])

    with mlf.start_run(run_name=run_name):
        mlf.log_params({
            "run_id":    run_id,
            "model":     cfg["weights"],
            "optimizer": cfg["optimizer"],
            "lr":        cfg["lr"],
            "epochs":    cfg["epochs"],
            "batch":     cfg["batch"],
            "dataset":   "birds (albatross, puffin, penguin)",
            "nc":        3,
        })

        results = model.train(
            data=str(YAML_PATH),
            epochs=cfg["epochs"],
            imgsz=640,
            device=device_str,
            batch=cfg["batch"],
            optimizer=cfg["optimizer"],
            lr0=cfg["lr"],
            lrf=0.01,
            project=str(OUTPUT_DIR),
            name=run_name,
            exist_ok=False,
            verbose=True,
            amp=True,
            plots=True,
            save=True,
        )

        # Метрики в MLflow
        metrics = {}
        if hasattr(results, "results_dict"):
            for k, v in results.results_dict.items():
                if isinstance(v, (int, float)):
                    clean = (k.replace("[", "_").replace("]", "_")
                              .replace("/", "_").replace("(", "_").replace(")", "_"))
                    mlf.log_metric(clean, v)
                    metrics[clean] = v

        # Артефакты
        for fname in ("results.png", "confusion_matrix.png", "PR_curve.png",
                      "confusion_matrix_normalized.png"):
            p = run_dir / fname
            if p.exists():
                mlf.log_artifact(str(p), "artifacts")

        weights_dir = run_dir / "weights"
        for fname in ("best.pt", "last.pt"):
            p = weights_dir / fname
            if p.exists():
                mlf.log_artifact(str(p), "model")

    metrics["run_name"] = run_name
    metrics["run_dir"]  = str(run_dir)

    map50 = metrics.get("metrics_mAP50_B_", metrics.get("metrics_mAP50_", "—"))
    print(f"  ✓ Готово: {run_dir}")
    print(f"  mAP50 = {map50}")
    return metrics


# ── ONNX экспорт ──────────────────────────────────────────────────────────────
def export_onnx(run_dir: Path) -> Path:
    best_pt = run_dir / "weights" / "best.pt"
    if not best_pt.exists():
        raise FileNotFoundError(f"best.pt не найден: {best_pt}")

    print(f"\n  Экспорт ONNX из {best_pt} ...")
    export_model = YOLO(str(best_pt))
    onnx_path = Path(export_model.export(
        format="onnx", imgsz=640, simplify=True, opset=12, dynamic=False
    ))
    print(f"  ✓ ONNX: {onnx_path}  ({onnx_path.stat().st_size / 1e6:.1f} MB)")

    FRONTEND_DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(onnx_path, FRONTEND_DEST)
    print(f"  ✓ Скопирован во frontend: {FRONTEND_DEST}")
    return onnx_path


# ── Сравнение результатов ─────────────────────────────────────────────────────
def print_summary(all_results: list):
    def get(d, *keys, default=0.0):
        for k in keys:
            if k in d: return d[k]
        return default

    print(f"\n{'='*72}")
    print("  ИТОГИ")
    print(f"{'='*72}")
    print(f"  {'Запуск':<45} {'mAP50':>7} {'Precision':>10} {'Recall':>8}")
    print(f"  {'-'*70}")
    for r in all_results:
        name = r.get("run_name", "—")
        m50  = get(r, "metrics_mAP50_B_",     "metrics_mAP50_")
        prec = get(r, "metrics_precision_B_",  "metrics_precision_")
        rec  = get(r, "metrics_recall_B_",     "metrics_recall_")
        print(f"  {name:<45} {m50:>7.4f} {prec:>10.4f} {rec:>8.4f}")
    print(f"{'='*72}")

    best = max(all_results,
               key=lambda x: get(x, "metrics_mAP50_B_", "metrics_mAP50_"))
    bmap = get(best, "metrics_mAP50_B_", "metrics_mAP50_")
    print(f"\n  🏆  Лучший: {best['run_name']}  (mAP50 = {bmap:.4f})")
    return best


# ── Главный блок ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run",         type=int, choices=[1, 2, 3, 4, 5, 6, 7],
                        help="Номер прогона (1–7)")
    parser.add_argument("--all",         action="store_true",
                        help="Запустить все 7 прогонов последовательно")
    parser.add_argument("--export-only", action="store_true",
                        help="Только экспорт ONNX (пропустить обучение)")
    parser.add_argument("--device",      type=str, default="auto",
                        help="Устройство: auto | cuda | cpu")
    args = parser.parse_args()

    if not args.run and not args.all:
        parser.print_help()
        sys.exit(0)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print("  ДЗ2 — YOLOv8-seg Birds (Albatross / Puffin / Penguin)")
    print(f"{'='*60}")
    print(f"  PyTorch: {torch.__version__}")
    print(f"  CUDA   : {torch.cuda.is_available()}")
    print(f"  YAML   : {YAML_PATH}")
    print(f"  Output : {OUTPUT_DIR}")

    run_ids = list(RUNS.keys()) if args.all else [args.run]
    all_results = []

    for run_id in run_ids:
        if args.export_only:
            cfg     = RUNS[run_id]
            run_dir = OUTPUT_DIR / cfg["name"]
            export_onnx(run_dir)
        else:
            try:
                metrics = train_run(run_id, device=args.device)
                all_results.append(metrics)
            except Exception as e:
                print(f"\n  ✗ Ошибка в запуске {run_id}: {e}")
                if not args.all:
                    sys.exit(1)

    if len(all_results) > 1:
        best = print_summary(all_results)
        print("\n  Экспортируем лучшую модель в ONNX...")
        export_onnx(Path(best["run_dir"]))
    elif len(all_results) == 1 and not args.export_only:
        print("\n  Экспортируем модель в ONNX...")
        export_onnx(Path(all_results[0]["run_dir"]))


if __name__ == "__main__":
    main()
