"""
Константы и вспомогательные функции для CLI (main.py).
"""

from scripts.train_yolo_seg import SEGMENT_CONFIGS

YOLO_MODELS = list(SEGMENT_CONFIGS.keys())


def get_segment_config(model_name: str) -> dict:
    return SEGMENT_CONFIGS.get(model_name, SEGMENT_CONFIGS["yolov8n-seg-adamw"])


def print_segment_summary(results_list: list) -> None:
    """Вывести таблицу результатов всех запусков."""
    print("\n" + "=" * 70)
    print("ИТОГИ ОБУЧЕНИЯ YOLOv8-SEG")
    print("=" * 70)
    print(f"{'Запуск':<35} {'mAP50':>8} {'Precision':>10} {'Recall':>8}")
    print("-" * 70)
    for r in results_list:
        name   = r.get("name", "—")
        map50  = r.get("metrics_mAP50_B_", r.get("metrics_mAP50_", 0.0))
        prec   = r.get("metrics_precision_B_", r.get("metrics_precision_", 0.0))
        rec    = r.get("metrics_recall_B_", r.get("metrics_recall_", 0.0))
        print(f"  {name:<33} {map50:>8.4f} {prec:>10.4f} {rec:>8.4f}")
    print("=" * 70)
    if results_list:
        best = max(
            results_list,
            key=lambda x: x.get("metrics_mAP50_B_", x.get("metrics_mAP50_", 0.0))
        )
        bmap = best.get("metrics_mAP50_B_", best.get("metrics_mAP50_", 0.0))
        print(f"\n  🏆  Лучший запуск: {best['name']}  (mAP50 = {bmap:.4f})")
