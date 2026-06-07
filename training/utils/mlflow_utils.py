"""
MLflow-интеграция для отслеживания обучения YOLOv8-seg.
Пытается подключиться к http://localhost:5000, иначе хранит локально.
"""

import os
import urllib.request

import mlflow

MLFLOW_TRACKING_URI    = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_EXPERIMENT_NAME = "birds-segmentation"


def setup_mlflow(experiment_name: str = MLFLOW_EXPERIMENT_NAME,
                 tracking_uri: str = MLFLOW_TRACKING_URI,
                 local_fallback_dir: str = None):
    """Настроить MLflow. Возвращает модуль mlflow с выставленным экспериментом."""
    uri = tracking_uri

    # Проверяем доступность сервера, иначе используем локальное хранилище
    try:
        urllib.request.urlopen(uri, timeout=2)
    except Exception:
        fallback = local_fallback_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "mlruns"
        )
        uri = fallback
        print(f"  MLflow: сервер недоступен, используем локальный путь: {fallback}")

    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(experiment_name)

    # Автологирование (без загрузки моделей — YOLO управляет этим сам)
    try:
        mlflow.autolog(log_models=False, silent=True)
    except Exception as e:
        print(f"  MLflow autolog: {e}")

    return mlflow
