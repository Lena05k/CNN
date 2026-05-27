from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import onnxruntime
import numpy as np
from PIL import Image
import os
import json
from pathlib import Path

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


# ── ДЗ 2: сегментация ─────────────────────────────────────────────────────────

@csrf_exempt
def segment_image(request):
    """
    POST /api/segment
    Поля FormData: filePath (file), confThresh (float, default 0.25)

    Ответ JSON:
      rendered    — base64 PNG с масками
      detections  — [{classId, className, score, bbox, clipMatches}]
      clipEnabled — bool (False, если transformers/torch не установлен)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        file_obj    = request.FILES.get('filePath')
        conf_thresh = float(request.POST.get('confThresh', '0.25'))

        if not file_obj:
            return JsonResponse({'error': 'Поле filePath обязательно'}, status=400)

        pil_img = Image.open(file_obj).convert('RGB')

        from .segmentation import run_segmentation, render_detections, pil_to_b64
        dets         = run_segmentation(pil_img, str(settings.SEG_MODEL_PATH), conf_thresh)
        rendered_b64 = pil_to_b64(render_detections(pil_img, dets))

        # CLIP (опционально — если пакет не установлен, возвращаем пустые matches)
        clip_enabled = False
        try:
            from .clip_search import find_similar
            for det in dets:
                x1, y1, x2, y2 = (int(v) for v in det['bbox'])
                crop = pil_img.crop((
                    max(0, x1), max(0, y1),
                    min(pil_img.width, x2), min(pil_img.height, y2),
                ))
                det['clipMatches'] = (
                    find_similar(crop, str(settings.MEDIA_ROOT))
                    if crop.width > 10 and crop.height > 10
                    else []
                )
            clip_enabled = True
        except Exception:
            for det in dets:
                det.setdefault('clipMatches', [])

        for det in dets:
            det.pop('mask', None)   # PIL Image не сериализуется в JSON

        model_name = Path(str(settings.SEG_MODEL_PATH)).parent.parent.name

        return JsonResponse({
            'rendered':    rendered_b64,
            'detections':  dets,
            'clipEnabled': clip_enabled,
            'model':       model_name,
        })

    except Exception as exc:
        import traceback
        return JsonResponse(
            {'error': str(exc), 'trace': traceback.format_exc()},
            status=500,
        )


@csrf_exempt
def clip_card_search(request):
    """
    POST /api/clip-search   (FormData)
    Поля: classId (int), cropImage (file, опционально)

    Без cropImage / без CLIP: возвращает все карточки класса (similarity=null).
    С cropImage + CLIP: ранжирует карточки по сходству с вырезанным изображением.

    Ответ: { results: [{id, classId, name, desc, similarity}], clipEnabled: bool }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        class_id  = int(request.POST.get('classId', -1))
        crop_file = request.FILES.get('cropImage')

        # Карточки из frontend/src/constants/birdCards.js дублируем здесь
        ALL_CARDS = [
            # Альбатрос
            dict(id=1,  classId=0, name='Странствующий альбатрос',  desc='Wandering albatross gliding over Southern Ocean, massive 3.5m wingspan, white plumage with black wingtips'),
            dict(id=2,  classId=0, name='Чернобровый альбатрос',    desc='Black-browed albatross with yellow-orange bill and distinctive dark eyebrow stripe, soaring over Atlantic'),
            dict(id=3,  classId=0, name='Тёмноспинный альбатрос',   desc='Black-footed albatross with dark plumage and pale face near Hawaiian islands'),
            dict(id=4,  classId=0, name='Альбатрос Лайсана',        desc='Laysan albatross with white head and dark back nesting on Pacific atoll'),
            dict(id=5,  classId=0, name='Королевский альбатрос',    desc='Northern royal albatross landing on cliff edge with large pink-orange bill, New Zealand'),
            dict(id=6,  classId=0, name='Серый альбатрос',          desc='Grey-headed albatross with grey head and neck, yellow bill with black tip, sub-Antarctic'),
            # Тупик
            dict(id=7,  classId=1, name='Атлантический тупик',      desc='Atlantic puffin with colorful triangular orange bill standing on rocky cliff, Iceland'),
            dict(id=8,  classId=1, name='Тупик с уловом',           desc='Atlantic puffin holding row of small silver sand eels in bright orange beak'),
            dict(id=9,  classId=1, name='Топорок',                  desc='Tufted puffin with long golden plumes and massive red bill on Pacific rocky coast'),
            dict(id=10, classId=1, name='Ипатка',                   desc='Horned puffin standing on basalt rock, black and white plumage with orange-yellow bill base'),
            dict(id=11, classId=1, name='Гагарка',                  desc='Razorbill auk on sea cliff, closest living relative of puffin, thick blunt black bill'),
            dict(id=12, classId=1, name='Тупик в полёте',           desc='Atlantic puffin in fast flight over grey ocean, wings blurred, orange feet trailing'),
            # Пингвин
            dict(id=13, classId=2, name='Императорский пингвин',    desc='Emperor penguin colony on Antarctic sea ice, tallest and heaviest living penguin species'),
            dict(id=14, classId=2, name='Галстучный пингвин',       desc='Gentoo penguin running on sandy beach, recognized by orange beak and white head stripe'),
            dict(id=15, classId=2, name='Очковый пингвин',          desc='African penguin on South African rocky shore, black horseshoe marking on white chest'),
            dict(id=16, classId=2, name='Малый пингвин',            desc='Little blue penguin, smallest penguin species, walking on Australian beach at dusk'),
            dict(id=17, classId=2, name='Пингвин Адели',            desc='Adelie penguin marching across Antarctic ice, distinctive white eye ring on black cap'),
            dict(id=18, classId=2, name='Скальный пингвин',         desc='Rockhopper penguin with yellow spiky crest jumping between rocks on sub-Antarctic island'),
        ]

        cards = [c for c in ALL_CARDS if class_id < 0 or c['classId'] == class_id]

        # Попробуем CLIP-ранжирование если есть кроп
        clip_enabled = False
        if crop_file:
            try:
                import torch
                from transformers import CLIPModel, CLIPProcessor
                pil_crop = Image.open(crop_file).convert('RGB')
                model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
                proc  = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')
                model.eval()

                # Image embedding
                img_inputs = proc(images=pil_crop, return_tensors='pt')
                with torch.no_grad():
                    img_feat = model.get_image_features(**img_inputs)
                    img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
                img_emb = img_feat[0].cpu().numpy()

                # Text embeddings for each card
                import numpy as np
                texts = [c['desc'] for c in cards]
                txt_inputs = proc(text=texts, return_tensors='pt', padding=True, truncation=True)
                with torch.no_grad():
                    txt_feat = model.get_text_features(**txt_inputs)
                    txt_feat = txt_feat / txt_feat.norm(dim=-1, keepdim=True)
                txt_embs = txt_feat.cpu().numpy()

                sims = (txt_embs @ img_emb).tolist()
                for card, sim in zip(cards, sims):
                    card['similarity'] = round(float(sim), 4)
                cards.sort(key=lambda c: c.get('similarity', 0), reverse=True)
                clip_enabled = True
            except Exception:
                for card in cards:
                    card['similarity'] = None
        else:
            for card in cards:
                card['similarity'] = None

        return JsonResponse({'results': cards, 'clipEnabled': clip_enabled})

    except Exception as exc:
        import traceback
        return JsonResponse({'error': str(exc), 'trace': traceback.format_exc()}, status=500)


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
