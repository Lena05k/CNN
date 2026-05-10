from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import onnxruntime
import numpy as np
from PIL import Image
import os

imageClassList = {'0': 'Пингвин', '1': 'Тупик', '2': 'Альбатрос'}

# Key layers selected for UI display: normalization params, first conv,
# last feature conv, and the final classifier head (3 output classes).
_LAYERS_TO_SHOW = [
    ('normalization.mean',                     'Нормализация — среднее по каналам (RGB)'),
    ('normalization.std',                      'Нормализация — стандартное отклонение (RGB)'),
    ('resnet_feature_extractor.0.0.0.weight',  'Conv1 — первый свёрточный слой'),
    ('resnet_feature_extractor.0.18.0.weight', 'Conv18 — последний feature-блок'),
    ('classifier.1.weight',                    'Классификатор — матрица весов (3 × 1280)'),
    ('classifier.1.bias',                      'Классификатор — вектор смещений bias (3)'),
]

# Module-level singletons: initialised on first request, reused thereafter.
_ort_session = None
_weights_summary = None


def _model_path():
    return os.path.join(settings.MEDIA_ROOT, 'models', 'cifar100_CNN_RESNET20.onnx')


def _get_session():
    global _ort_session
    if _ort_session is None:
        _ort_session = onnxruntime.InferenceSession(_model_path())
    return _ort_session


def _get_weights_summary():
    """
    Parses the ONNX model once and returns a compact, UI-friendly summary
    of selected weight tensors. Result is cached for the process lifetime.
    onnx is imported lazily so the rest of the module works even if the
    package is absent (e.g. old Docker image).
    """
    global _weights_summary
    if _weights_summary is not None:
        return _weights_summary

    import onnx  # lazy import — onnxruntime (inference) is independent of this

    model = onnx.load(_model_path())
    init_map = {init.name: init for init in model.graph.initializer}

    result = []
    for name, role in _LAYERS_TO_SHOW:
        if name not in init_map:
            continue
        init = init_map[name]
        shape = list(init.dims)
        arr = (
            np.frombuffer(init.raw_data, dtype=np.float32).copy()
            if init.raw_data
            else np.array(init.float_data, dtype=np.float32)
        )

        entry = {
            'name': name,
            'role': role,
            'shape': shape,
            'numel': int(arr.size),
        }

        if arr.size <= 10:
            # Small tensors: expose every value directly.
            entry['values'] = [round(float(v), 6) for v in arr]
        else:
            # Large tensors: aggregate stats + 5-element sample.
            entry['min'] = round(float(arr.min()), 6)
            entry['max'] = round(float(arr.max()), 6)
            entry['mean'] = round(float(arr.mean()), 6)
            entry['std'] = round(float(arr.std()), 6)
            entry['sample'] = [round(float(v), 6) for v in arr.flat[:5]]

        result.append(entry)

    _weights_summary = result
    return _weights_summary


def scoreImagePage(request):
    return render(request, 'index.html')


@csrf_exempt
def predictImage(request):
    # Inference — must succeed for the response to be meaningful.
    try:
        fileObj = request.FILES['filePath']
        fs = FileSystemStorage()
        savedName = fs.save('images/' + fileObj.name, fileObj)
        filePath = fs.path(savedName)
        modelName = request.POST.get('modelName')
        scorePrediction = predictImageData(modelName, filePath)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    # Weights extraction is best-effort: if onnx package is missing or the
    # model file cannot be parsed, we return an empty list rather than 500.
    try:
        weightsSummary = _get_weights_summary()
    except Exception as e:
        weightsSummary = []

    return JsonResponse({'prediction': scorePrediction, 'weightsSummary': weightsSummary})


def predictImageData(modelName, filePath):
    img = Image.open(filePath).convert("RGB")
    img = np.asarray(img.resize((32, 32), Image.LANCZOS))
    sess = _get_session()
    outputOFModel = np.argmax(sess.run(None, {'input': np.asarray([img]).astype(np.float32)}))
    return imageClassList[str(outputOFModel)]
