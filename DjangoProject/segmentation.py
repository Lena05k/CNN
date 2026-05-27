"""YOLOv8-seg ONNX inference — server-side postprocessing."""
import io
import base64

import numpy as np
from PIL import Image, ImageDraw, ImageFont

NC           = 3
CLASS_NAMES  = ['Альбатрос', 'Тупик', 'Пингвин']
CLASS_NAMES_LATIN = ['Albatros', 'Tupik', 'Pingvin']   # fallback when no Cyrillic font
CLASS_COLORS = [(249, 115, 22), (59, 130, 246), (34, 197, 94)]   # orange, blue, green
MASK_ALPHA   = 0.45


def _load_font(size: int):
    """
    Try to load a TrueType font that supports Cyrillic.
    Returns (font, cyrillic_ok).
    """
    paths = [
        # macOS
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
        '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        '/Library/Fonts/Arial Bold.ttf',
        # Linux — DejaVu (поддерживает кириллицу)
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
        # Linux — Liberation
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf',
        # Linux — Ubuntu / Noto
        '/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf',
        '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf',
        '/usr/share/fonts/noto/NotoSans-Bold.ttf',
        # Linux — FreeFonts
        '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
    ]
    for path in paths:
        try:
            return ImageFont.truetype(path, size), True
        except Exception:
            pass
    return ImageFont.load_default(), False

_seg_session = None


def _get_session(model_path: str):
    global _seg_session
    if _seg_session is None:
        import onnxruntime as ort
        _seg_session = ort.InferenceSession(str(model_path))
    return _seg_session


def _letterbox(img: Image.Image, size: int = 640):
    """Resize with grey padding to square. Returns (canvas, scale, pad_w, pad_h)."""
    w, h = img.size
    scale = size / max(w, h)
    nw, nh = int(w * scale), int(h * scale)
    resized = img.resize((nw, nh), Image.BILINEAR)
    canvas = Image.new('RGB', (size, size), (114, 114, 114))
    pad_w, pad_h = (size - nw) // 2, (size - nh) // 2
    canvas.paste(resized, (pad_w, pad_h))
    return canvas, scale, pad_w, pad_h


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -88, 88)))


def _iou(box, others):
    ix1 = np.maximum(box[0], others[:, 0])
    iy1 = np.maximum(box[1], others[:, 1])
    ix2 = np.minimum(box[2], others[:, 2])
    iy2 = np.minimum(box[3], others[:, 3])
    inter = np.maximum(0, ix2 - ix1) * np.maximum(0, iy2 - iy1)
    a1 = (box[2] - box[0]) * (box[3] - box[1])
    a2 = (others[:, 2] - others[:, 0]) * (others[:, 3] - others[:, 1])
    return inter / (a1 + a2 - inter + 1e-7)


def _nms(boxes, scores, iou_thresh=0.45):
    order = scores.argsort()[::-1]
    keep = []
    while order.size:
        i = order[0]
        keep.append(i)
        if order.size == 1:
            break
        order = order[1:][_iou(boxes[i], boxes[order[1:]]) < iou_thresh]
    return keep


def run_segmentation(pil_img: Image.Image, model_path: str,
                     conf_thresh: float = 0.25, iou_thresh: float = 0.45) -> list:
    """
    Run YOLOv8-seg ONNX inference.
    Returns list of dicts: {classId, className, score, bbox[x1,y1,x2,y2], mask(PIL L-image)}.
    """
    orig_w, orig_h = pil_img.size
    lb, scale, pad_w, pad_h = _letterbox(pil_img)

    arr = np.array(lb, dtype=np.float32) / 255.0
    tensor = arr.transpose(2, 0, 1)[np.newaxis]            # [1,3,640,640]

    sess = _get_session(model_path)
    outs = sess.run(None, {sess.get_inputs()[0].name: tensor})

    # output0: [1, 4+nc+32, 8400]   output1: [1, 32, 160, 160]
    preds  = outs[0][0]     # [features, 8400]
    protos = outs[1][0]     # [32, 160, 160]

    features, anchors = preds.shape
    nc = features - 4 - 32

    # Transpose → [8400, features]
    pt          = preds.T
    boxes_xywh  = pt[:, :4]
    class_scores = pt[:, 4:4 + nc]
    mask_coefs   = pt[:, 4 + nc:]

    scores    = class_scores.max(axis=1)
    class_ids = class_scores.argmax(axis=1)

    conf_mask = scores > conf_thresh
    if not conf_mask.any():
        return []

    boxes_xywh = boxes_xywh[conf_mask]
    scores     = scores[conf_mask]
    class_ids  = class_ids[conf_mask]
    mask_coefs = mask_coefs[conf_mask]

    # xywh → xyxy in 640×640 space
    b = np.empty_like(boxes_xywh)
    b[:, 0] = boxes_xywh[:, 0] - boxes_xywh[:, 2] / 2
    b[:, 1] = boxes_xywh[:, 1] - boxes_xywh[:, 3] / 2
    b[:, 2] = boxes_xywh[:, 0] + boxes_xywh[:, 2] / 2
    b[:, 3] = boxes_xywh[:, 1] + boxes_xywh[:, 3] / 2
    np.clip(b, 0, 640, out=b)

    kept = _nms(b, scores, iou_thresh)

    detections = []
    for idx in kept:
        x1 = float(max(0.0, (b[idx, 0] - pad_w) / scale))
        y1 = float(max(0.0, (b[idx, 1] - pad_h) / scale))
        x2 = float(min(orig_w, (b[idx, 2] - pad_w) / scale))
        y2 = float(min(orig_h, (b[idx, 3] - pad_h) / scale))

        # Reconstruct mask: sigmoid(coefs @ protos)
        mask_flat = _sigmoid(mask_coefs[idx] @ protos.reshape(32, -1))  # [25600]
        mask_160  = mask_flat.reshape(160, 160)

        # 160×160 → 640×640 → remove padding → original size
        m640 = Image.fromarray((mask_160 * 255).astype(np.uint8)).resize(
            (640, 640), Image.BILINEAR)
        m_arr = np.array(m640)
        nw, nh = int(orig_w * scale), int(orig_h * scale)
        m_crop = m_arr[pad_h: pad_h + nh, pad_w: pad_w + nw]
        mask_orig = Image.fromarray(m_crop).resize((orig_w, orig_h), Image.BILINEAR)

        cid = int(class_ids[idx])
        detections.append({
            'classId':   cid,
            'className': CLASS_NAMES[min(cid, NC - 1)],
            'score':     float(scores[idx]),
            'bbox':      [x1, y1, x2, y2],
            'mask':      mask_orig,   # PIL Image (L), removed before JSON serialisation
        })

    return detections


def render_detections(pil_img: Image.Image, detections: list) -> Image.Image:
    """Overlay semi-transparent masks, bboxes and labels. Returns RGB PIL Image."""
    base    = pil_img.convert('RGBA')
    overlay = Image.new('RGBA', base.size, (0, 0, 0, 0))

    for det in detections:
        r, g, b = CLASS_COLORS[det['classId'] % len(CLASS_COLORS)]
        mask_arr = (np.array(det['mask']) > 127).astype(np.uint8)
        rgba = np.zeros((*mask_arr.shape, 4), dtype=np.uint8)
        rgba[mask_arr == 1] = [r, g, b, int(255 * MASK_ALPHA)]
        overlay = Image.alpha_composite(overlay, Image.fromarray(rgba, 'RGBA'))

    result = Image.alpha_composite(base, overlay).convert('RGB')
    draw   = ImageDraw.Draw(result)

    # Шрифт — крупный, с поддержкой кириллицы
    fs = max(28, int(pil_img.width / 18))
    font, cyrillic_ok = _load_font(fs)

    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det['bbox']]
        r, g, b = CLASS_COLORS[det['classId'] % len(CLASS_COLORS)]

        # Рамка
        lw = max(3, int(pil_img.width / 180))
        draw.rectangle([x1, y1, x2, y2], outline=(r, g, b), width=lw)

        # Текст: кириллица или латинский транслит если шрифт не поддерживает
        name  = det['className'] if cyrillic_ok else CLASS_NAMES_LATIN[det['classId']]
        label = f"{name}  {det['score'] * 100:.0f}%"

        # Размер текстового блока
        try:
            bb = font.getbbox(label)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
        except AttributeError:
            tw, th = fs * len(label) // 2, fs

        pad = max(6, fs // 5)

        # Позиция фона: над рамкой, если есть место; иначе внутри сверху
        bg_x1 = x1
        bg_y1 = y1 - th - pad * 2
        if bg_y1 < 0:
            bg_y1 = y1
        bg_x2 = bg_x1 + tw + pad * 2
        bg_y2 = bg_y1 + th + pad * 2

        # Цветной прямоугольник-подложка
        draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=(r, g, b))

        # Белый текст поверх подложки
        draw.text((bg_x1 + pad, bg_y1 + pad), label, fill=(255, 255, 255), font=font)

    return result


def pil_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
