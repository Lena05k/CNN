"""
Конфигурация обучения для сегментации птиц (ДЗ2).
"""

from pathlib import Path

# Корень проекта — папка DjangoProject/ (на 2 уровня выше configs/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Config:
    """Базовая конфигурация"""

    CLASSES        = ["albatross", "puffin"]
    NUM_CLASSES    = 2

    DATA_DIR       = BASE_DIR / "training" / "data"
    DATASET_YAML   = DATA_DIR / "birds.yaml"
    OUTPUT_DIR     = BASE_DIR / "yolo8_segment"
    MODELS_DIR     = BASE_DIR / "training" / "data" / "models"

    BATCH_SIZE     = 8
    EPOCHS         = 50
    LEARNING_RATE  = 0.001
    IMGSZ          = 640

    @classmethod
    def setup_dirs(cls):
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.MODELS_DIR.mkdir(parents=True, exist_ok=True)
