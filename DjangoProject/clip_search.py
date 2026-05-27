"""
CLIP-поиск похожих карточек (12 × 3 класса = 36 эталонов).

При первом вызове:
  - Загружает CLIP (openai/clip-vit-base-patch32, ~600 МБ — нужен интернет)
  - Вычисляет embeddings для эталонных изображений из data/dataset/
  - Копирует эталоны в media/cards/{class}/ для отдачи через Django

Все результаты кешируются в памяти процесса.
"""
from pathlib import Path

import numpy as np
from PIL import Image

_ROOT    = Path(__file__).resolve().parent.parent   # DjangoProject/
_DATASET = _ROOT / 'data' / 'dataset'

_CLASS_FOLDERS = {
    0: _DATASET / 'albatross' / 'images',
    1: _DATASET / 'Puffin'    / 'images',
    2: _DATASET / 'penguin'   / 'images',
}
_CLASS_NAMES   = ['Альбатрос', 'Тупик', 'Пингвин']
_CARDS_PER_CLASS = 12

_clip_model = None
_clip_proc  = None
_refs       = None   # list of {classId, className, url, emb: ndarray}


# ── CLIP model ────────────────────────────────────────────────────────────────

def _load_clip():
    global _clip_model, _clip_proc
    if _clip_model is None:
        from transformers import CLIPModel, CLIPProcessor
        print('[CLIP] загружаем openai/clip-vit-base-patch32 ...')
        _clip_model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
        _clip_proc  = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')
        _clip_model.eval()
        print('[CLIP] модель загружена.')
    return _clip_model, _clip_proc


def _embed(pil_img: Image.Image) -> np.ndarray:
    import torch
    model, proc = _load_clip()
    inputs = proc(images=pil_img, return_tensors='pt')
    with torch.no_grad():
        feat = model.get_image_features(**inputs)
        feat = feat / feat.norm(dim=-1, keepdim=True)
    return feat[0].cpu().numpy()


# ── Reference cards ───────────────────────────────────────────────────────────

def _build_refs(media_root: Path) -> list:
    """Build and cache reference card embeddings. Copies images to media/cards/."""
    global _refs
    refs = []

    for class_id, folder in _CLASS_FOLDERS.items():
        if not folder.exists():
            print(f'[CLIP] папка не найдена: {folder}')
            continue

        class_name = _CLASS_NAMES[class_id]
        card_dir   = media_root / 'cards' / class_name.lower()
        card_dir.mkdir(parents=True, exist_ok=True)

        imgs = sorted(p for p in folder.iterdir() if p.suffix.lower() in
                      ('.jpg', '.jpeg', '.png', '.webp'))[:_CARDS_PER_CLASS]

        for img_path in imgs:
            try:
                pil = Image.open(img_path).convert('RGB')
                pil.thumbnail((224, 224))
                emb = _embed(pil)

                dst = card_dir / img_path.name
                if not dst.exists():
                    pil.save(str(dst))

                url = f'/media/cards/{class_name.lower()}/{img_path.name}'
                refs.append({
                    'classId':   class_id,
                    'className': class_name,
                    'url':       url,
                    'emb':       emb,
                })
            except Exception as exc:
                print(f'[CLIP] пропускаем {img_path.name}: {exc}')

    print(f'[CLIP] эталонов загружено: {len(refs)}')
    _refs = refs
    return refs


def _get_refs(media_root: str) -> list:
    global _refs
    if _refs is None:
        _refs = _build_refs(Path(media_root))
    return _refs


# ── Public API ────────────────────────────────────────────────────────────────

def find_similar_by_text(query: str, media_root: str, top_k: int = 5) -> list:
    """Find reference cards most similar to a text description (CLIP text→image)."""
    import torch
    refs = _get_refs(media_root)
    if not refs:
        return []

    model, proc = _load_clip()
    inputs = proc(text=[query], return_tensors='pt', padding=True, truncation=True)
    with torch.no_grad():
        feat = model.get_text_features(**inputs)
        feat = feat / feat.norm(dim=-1, keepdim=True)
    text_emb = feat[0].cpu().numpy()

    sims = [(float(np.dot(text_emb, r['emb'])), r) for r in refs]
    sims.sort(key=lambda x: x[0], reverse=True)

    return [
        {
            'classId':   r['classId'],
            'className': r['className'],
            'url':       r['url'],
            'similarity': round(s, 4),
        }
        for s, r in sims[:top_k]
    ]


def find_similar(pil_crop: Image.Image, media_root: str, top_k: int = 3) -> list:
    """
    Find top_k reference cards most similar to the cropped bird region.
    Returns list of {classId, className, url, similarity}.
    """
    refs = _get_refs(media_root)
    if not refs:
        return []

    query = _embed(pil_crop)
    sims  = [(float(np.dot(query, r['emb'])), r) for r in refs]
    sims.sort(key=lambda x: x[0], reverse=True)

    return [
        {
            'classId':    r['classId'],
            'className':  r['className'],
            'url':        r['url'],
            'similarity': round(s, 4),
        }
        for s, r in sims[:top_k]
    ]
