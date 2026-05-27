/**
 * YOLOv8-seg ONNX inference в браузере (onnxruntime-web).
 *
 * Модель: frontend/public/models/best.onnx
 * Вход:   images  [1, 3, 640, 640]
 * Выход:  output0 [1, 4+C+32, 8400]  — боксы + скоры + коэф. масок
 *         output1 [1, 32, 160, 160]  — прототипы масок
 */
import * as ort from 'onnxruntime-web'

// WASM-файлы с CDN — не требует дополнительных настроек сборки
ort.env.wasm.wasmPaths = 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.18.0/dist/'

const INPUT_SIZE    = 640
const PROTO_SIZE    = 160
const NUM_MASK_COEF = 32

let _session = null

// ─── Сессия ───────────────────────────────────────────────────────────────────

export async function getSession(modelPath = '/models/best.onnx') {
  if (!_session) {
    _session = await ort.InferenceSession.create(modelPath, {
      executionProviders: ['wasm'],
    })
  }
  return _session
}

export function resetSession() { _session = null }

// ─── Препроцессинг ────────────────────────────────────────────────────────────

/** Letterbox-ресайз картинки на 640×640 с серыми полями. */
function letterbox(img) {
  const canvas = document.createElement('canvas')
  canvas.width  = INPUT_SIZE
  canvas.height = INPUT_SIZE
  const ctx = canvas.getContext('2d')

  const scale = Math.min(INPUT_SIZE / img.naturalWidth, INPUT_SIZE / img.naturalHeight)
  const w = Math.round(img.naturalWidth  * scale)
  const h = Math.round(img.naturalHeight * scale)
  const padX = (INPUT_SIZE - w) / 2
  const padY = (INPUT_SIZE - h) / 2

  ctx.fillStyle = '#808080'
  ctx.fillRect(0, 0, INPUT_SIZE, INPUT_SIZE)
  ctx.drawImage(img, padX, padY, w, h)

  return { canvas640: canvas, scale, padX, padY }
}

/** Canvas → Float32Array NCHW [1, 3, H, W]. */
function canvasToTensor(canvas) {
  const { width: W, height: H } = canvas
  const rgba = canvas.getContext('2d').getImageData(0, 0, W, H).data
  const n    = W * H
  const data = new Float32Array(3 * n)
  for (let i = 0; i < n; i++) {
    data[i]         = rgba[i * 4]     / 255
    data[n + i]     = rgba[i * 4 + 1] / 255
    data[2 * n + i] = rgba[i * 4 + 2] / 255
  }
  return new ort.Tensor('float32', data, [1, 3, H, W])
}

// ─── NMS ──────────────────────────────────────────────────────────────────────

function iou(a, b) {
  const ix1 = Math.max(a[0], b[0]), iy1 = Math.max(a[1], b[1])
  const ix2 = Math.min(a[2], b[2]), iy2 = Math.min(a[3], b[3])
  const inter = Math.max(0, ix2 - ix1) * Math.max(0, iy2 - iy1)
  const ua = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - inter
  return ua > 0 ? inter / ua : 0
}

function nms(boxes, scores, iouThresh = 0.45) {
  const order      = [...scores.keys()].sort((a, b) => scores[b] - scores[a])
  const suppressed = new Uint8Array(scores.length)
  const keep = []
  for (const i of order) {
    if (suppressed[i]) continue
    keep.push(i)
    for (const j of order) {
      if (!suppressed[j] && j !== i && iou(boxes[i], boxes[j]) > iouThresh)
        suppressed[j] = 1
    }
  }
  return keep
}

// ─── Маска ────────────────────────────────────────────────────────────────────

/**
 * Строит canvas размером origW×origH с бинарной маской для одного объекта.
 * Использует цепочку: 160×160 → 640×640 → кроп паддинга → origW×origH.
 */
function buildMaskCanvas(maskCoefs, proto, padX, padY, scale, origW, origH) {
  const P  = PROTO_SIZE
  const PP = P * P

  // sigmoid(coefs @ proto)
  const id = new ImageData(P, P)
  for (let p = 0; p < PP; p++) {
    let v = 0
    for (let m = 0; m < NUM_MASK_COEF; m++) v += maskCoefs[m] * proto[m * PP + p]
    id.data[p * 4 + 3] = 1 / (1 + Math.exp(-v)) > 0.5 ? 255 : 0
  }

  const mc = document.createElement('canvas')
  mc.width = P; mc.height = P
  mc.getContext('2d').putImageData(id, 0, 0)

  // Масштаб до 640×640
  const big = document.createElement('canvas')
  big.width = INPUT_SIZE; big.height = INPUT_SIZE
  big.getContext('2d').drawImage(mc, 0, 0, INPUT_SIZE, INPUT_SIZE)

  // Убираем letterbox и масштабируем к оригинальному размеру
  const cropW = Math.round(origW * scale)
  const cropH = Math.round(origH * scale)
  const out = document.createElement('canvas')
  out.width = origW; out.height = origH
  out.getContext('2d').drawImage(big, padX, padY, cropW, cropH, 0, 0, origW, origH)

  return out
}

// ─── Публичный API ────────────────────────────────────────────────────────────

/**
 * Запустить YOLOv8-seg инференс на HTMLImageElement.
 * Возвращает массив объектов: { classId, score, box[x1,y1,x2,y2], maskCanvas }
 */
export async function runSegmentation(imgElement, {
  confThresh = 0.25,
  iouThresh  = 0.45,
  modelPath  = '/models/best.onnx',
} = {}) {
  const session = await getSession(modelPath)
  const origW   = imgElement.naturalWidth
  const origH   = imgElement.naturalHeight

  const { canvas640, scale, padX, padY } = letterbox(imgElement)
  const inputTensor = canvasToTensor(canvas640)
  const results     = await session.run({ [session.inputNames[0]]: inputTensor })

  const out0 = results[session.outputNames[0]]  // [1, features, 8400]
  const out1 = results[session.outputNames[1]]  // [1, 32, 160, 160]

  const [, features, anchors] = out0.dims
  const nc  = features - 4 - NUM_MASK_COEF      // число классов из модели
  const d0  = out0.data
  const d1  = out1.data

  const boxes = [], scores = [], classIds = [], coefsList = []

  for (let a = 0; a < anchors; a++) {
    let maxScore = 0, classId = 0
    for (let c = 0; c < nc; c++) {
      const s = d0[(4 + c) * anchors + a]
      if (s > maxScore) { maxScore = s; classId = c }
    }
    if (maxScore < confThresh) continue

    const cx = d0[0 * anchors + a], cy = d0[1 * anchors + a]
    const bw = d0[2 * anchors + a], bh = d0[3 * anchors + a]

    boxes.push([
      Math.max(0, Math.min(origW, (cx - bw / 2 - padX) / scale)),
      Math.max(0, Math.min(origH, (cy - bh / 2 - padY) / scale)),
      Math.max(0, Math.min(origW, (cx + bw / 2 - padX) / scale)),
      Math.max(0, Math.min(origH, (cy + bh / 2 - padY) / scale)),
    ])
    scores.push(maxScore)
    classIds.push(classId)

    const coefs = new Float32Array(NUM_MASK_COEF)
    for (let m = 0; m < NUM_MASK_COEF; m++) coefs[m] = d0[(4 + nc + m) * anchors + a]
    coefsList.push(coefs)
  }

  return nms(boxes, scores, iouThresh).map(i => ({
    classId:    classIds[i],
    score:      scores[i],
    box:        boxes[i],
    maskCanvas: buildMaskCanvas(coefsList[i], d1, padX, padY, scale, origW, origH),
  }))
}

/**
 * Нарисовать все детекции (маски + боксы + подписи) на canvas.
 */
export function drawDetections(canvas, imgElement, detections, classNames, classColors) {
  canvas.width  = imgElement.naturalWidth
  canvas.height = imgElement.naturalHeight
  const ctx = canvas.getContext('2d')
  ctx.drawImage(imgElement, 0, 0)

  for (const det of detections) {
    const [r, g, b] = classColors[det.classId % classColors.length]

    // Полупрозрачная маска
    const mCtx  = det.maskCanvas.getContext('2d')
    const mData = mCtx.getImageData(0, 0, det.maskCanvas.width, det.maskCanvas.height)

    const ov  = document.createElement('canvas')
    ov.width  = canvas.width
    ov.height = canvas.height
    const ovCtx = ov.getContext('2d')
    const ovPx  = ovCtx.createImageData(canvas.width, canvas.height)

    for (let i = 0; i < mData.data.length / 4; i++) {
      if (mData.data[i * 4 + 3] > 128) {
        ovPx.data[i * 4]     = r
        ovPx.data[i * 4 + 1] = g
        ovPx.data[i * 4 + 2] = b
        ovPx.data[i * 4 + 3] = 115   // ~45% прозрачность
      }
    }
    ovCtx.putImageData(ovPx, 0, 0)
    ctx.drawImage(ov, 0, 0)

    // Бокс
    const [x1, y1, x2, y2] = det.box
    const lw = Math.max(2, Math.round(canvas.width / 400))
    ctx.strokeStyle = `rgb(${r},${g},${b})`
    ctx.lineWidth   = lw
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)

    // Подпись
    const name  = classNames[det.classId] ?? `Класс ${det.classId}`
    const label = `${name}  ${(det.score * 100).toFixed(1)}%`
    const fs    = Math.max(13, Math.round(canvas.width / 45))
    ctx.font    = `bold ${fs}px Inter, system-ui, sans-serif`
    const tw    = ctx.measureText(label).width
    const lh    = fs + 6

    ctx.fillStyle = `rgb(${r},${g},${b})`
    ctx.fillRect(x1, y1 - lh, tw + 10, lh)
    ctx.fillStyle = '#ffffff'
    ctx.fillText(label, x1 + 5, y1 - 4)
  }
}
