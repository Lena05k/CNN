"""
Утилиты экспорта и проверки ONNX-моделей.
"""

import shutil
from pathlib import Path


def export_onnx_and_verify(model, export_dir: Path, dest_path: Path = None) -> Path:
    """
    Экспортировать best.pt → best.onnx через ultralytics и опционально скопировать.

    Args:
        model      : обученный YOLO-объект (после model.train())
        export_dir : папка с весами (weights/)
        dest_path  : путь назначения (например, frontend/public/models/best.onnx)

    Returns:
        Путь к созданному best.onnx
    """
    best_pt = export_dir / "best.pt"
    if not best_pt.exists():
        raise FileNotFoundError(f"Файл best.pt не найден: {best_pt}")

    from ultralytics import YOLO
    export_model = YOLO(str(best_pt))
    onnx_path = export_model.export(
        format="onnx",
        imgsz=640,
        simplify=True,
        opset=12,
        dynamic=False,
    )
    onnx_path = Path(onnx_path)
    print(f"  ✓ ONNX экспортирован: {onnx_path}  ({onnx_path.stat().st_size / 1e6:.1f} MB)")

    if dest_path is not None:
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(onnx_path, dest_path)
        print(f"  ✓ Скопирован во frontend: {dest_path}")

    return onnx_path
