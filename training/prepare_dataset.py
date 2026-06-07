#!/usr/bin/env python3
"""
Конвертация CVAT XML (bbox) → YOLO segmentation format.

Структура входных данных:
    data/dataset/
    ├── albatross/images/*.jpg  +  annotations.xml
    ├── Puffin/images/*.jpg     +  annotations.xml
    └── penguin/images/*.jpg    +  annotations.xml

Результат (data/yolo_birds/):
    images/train/  images/val/
    labels/train/  labels/val/
    birds.yaml

Запуск:
    cd training/
    python prepare_dataset.py
    python prepare_dataset.py --val-split 0.15   # изменить долю val
"""

import argparse
import os
import random
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

# ── Настройки ─────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent.parent   # DjangoProject/
SRC_DIR  = ROOT / "data" / "dataset"
DST_DIR  = ROOT / "data" / "yolo_birds"
YAML_OUT = ROOT / "training" / "data" / "birds.yaml"

# Имена папок → class id
CLASS_MAP = {
    "albatross": 0,
    "puffin":    1,    # папка называется Puffin (case-insensitive)
    "penguin":   2,
}

CLASS_NAMES = {0: "albatross", 1: "puffin", 2: "penguin"}


def bbox_to_yolo_polygon(xtl, ytl, xbr, ybr, img_w, img_h) -> str:
    """
    Прямоугольный bbox → нормализованный YOLO polygon (4 угла, 8 координат).
    Формат: x1 y1 x2 y2 x3 y3 x4 y4 (по часовой стрелке).
    """
    x1, y1 = xtl / img_w, ytl / img_h
    x2, y2 = xbr / img_w, ytl / img_h
    x3, y3 = xbr / img_w, ybr / img_h
    x4, y4 = xtl / img_w, ybr / img_h
    # Клипуем в [0, 1]
    coords = [max(0.0, min(1.0, v)) for v in [x1, y1, x2, y2, x3, y3, x4, y4]]
    return " ".join(f"{v:.6f}" for v in coords)


def parse_cvat_xml(xml_path: Path, class_id: int):
    """
    Парсим annotations.xml (CVAT 1.1).
    Возвращаем dict: filename → list of YOLO polygon strings.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    records = {}

    for img_elem in root.findall("image"):
        fname = img_elem.get("name")
        w = int(img_elem.get("width"))
        h = int(img_elem.get("height"))
        lines = []

        for box in img_elem.findall("box"):
            xtl = float(box.get("xtl"))
            ytl = float(box.get("ytl"))
            xbr = float(box.get("xbr"))
            ybr = float(box.get("ybr"))
            poly = bbox_to_yolo_polygon(xtl, ytl, xbr, ybr, w, h)
            lines.append(f"{class_id} {poly}")

        if lines:                         # пропускаем кадры без аннотаций
            records[fname] = lines

    return records


def prepare(val_split: float = 0.1, seed: int = 42):
    random.seed(seed)

    all_records = []  # list of (src_img_path, filename, label_lines)

    # Ищем все три класса
    for folder in SRC_DIR.iterdir():
        if not folder.is_dir():
            continue
        class_id = CLASS_MAP.get(folder.name.lower())
        if class_id is None:
            print(f"  Пропускаем неизвестную папку: {folder.name}")
            continue

        xml_path   = folder / "annotations.xml"
        images_dir = folder / "images"

        if not xml_path.exists():
            print(f"  ⚠ Нет annotations.xml в {folder.name}/")
            continue

        print(f"  Читаем {folder.name}/ (class {class_id}) ...")
        records = parse_cvat_xml(xml_path, class_id)

        for fname, lines in records.items():
            src_img = images_dir / fname
            if src_img.exists():
                all_records.append((src_img, fname, lines, class_id))
            else:
                # Ищем файл без расширения (случай расхождения расширений)
                stem = Path(fname).stem
                found = list(images_dir.glob(f"{stem}.*"))
                if found:
                    all_records.append((found[0], found[0].name, lines, class_id))

        print(f"    → {len(records)} аннотированных изображений")

    if not all_records:
        print("ОШИБКА: не найдено ни одного аннотированного изображения!")
        return

    # ── Перемешиваем и делим на train/val ──────────────────────────────────
    random.shuffle(all_records)
    val_n  = max(1, int(len(all_records) * val_split))
    val_set   = all_records[:val_n]
    train_set = all_records[val_n:]

    print(f"\n  Всего: {len(all_records)}  →  train: {len(train_set)}, val: {val_n}")

    # ── Записываем ──────────────────────────────────────────────────────────
    DST_DIR.mkdir(parents=True, exist_ok=True)

    split_stat = {0: 0, 1: 0, 2: 0}

    for split_name, split_data in [("train", train_set), ("val", val_set)]:
        (DST_DIR / "images" / split_name).mkdir(parents=True, exist_ok=True)
        (DST_DIR / "labels" / split_name).mkdir(parents=True, exist_ok=True)

        for src_img, fname, lines, class_id in split_data:
            dst_img   = DST_DIR / "images" / split_name / fname
            label_name = Path(fname).stem + ".txt"
            dst_label  = DST_DIR / "labels" / split_name / label_name

            shutil.copy(src_img, dst_img)
            dst_label.write_text("\n".join(lines))

            if split_name == "train":
                split_stat[class_id] += 1

    print(f"\n  Train по классам:")
    for cid, cnt in split_stat.items():
        print(f"    {CLASS_NAMES[cid]:12s} (class {cid}): {cnt}")

    # ── Создаём birds.yaml ──────────────────────────────────────────────────
    yaml_content = f"""# Датасет для YOLOv8-seg — Птицы (ДЗ2)
# Сгенерировано prepare_dataset.py

path: {DST_DIR}
train: images/train
val:   images/val

nc: 3
names:
  0: albatross
  1: puffin
  2: penguin
"""
    YAML_OUT.write_text(yaml_content)
    print(f"\n  ✓ birds.yaml обновлён: {YAML_OUT}")
    print(f"  ✓ Датасет готов:       {DST_DIR}")
    print("\nТеперь запускайте обучение:")
    print("    python train_all.py --all")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--val-split", type=float, default=0.1,
                        help="Доля val (default: 0.1 = 10%%)")
    parser.add_argument("--seed",      type=int,   default=42)
    args = parser.parse_args()

    print("=" * 55)
    print("  Подготовка датасета: CVAT XML → YOLO polygon")
    print("=" * 55)
    prepare(val_split=args.val_split, seed=args.seed)
