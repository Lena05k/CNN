<template>
  <section class="px-3 flex justify-center w-full animate-fade-up" style="animation-delay: 0.1s">
    <div class="glass-card w-full max-w-xl p-4 sm:p-6 transition-all duration-300">

      <!-- Camera / Result viewport: capped at 55 vh so controls stay visible -->
      <div class="relative w-full rounded-xl overflow-hidden bg-black flex items-center justify-center"
           style="max-height: 55vh; min-height: 180px">
        <video
          v-show="cameraActive && !resultImg"
          ref="videoEl"
          autoplay playsinline muted
          class="w-full object-contain rounded-xl"
          style="max-height: 55vh"
        />
        <img v-if="resultImg" :src="resultImg"
             class="w-full object-contain rounded-xl"
             style="max-height: 55vh"
             alt="result" />
        <p v-if="!cameraActive && !resultImg" class="text-white/40 text-sm px-4 text-center">
          Нажмите «Включить камеру»
        </p>

        <!-- Loading overlay -->
        <Transition name="fade">
          <div v-if="loading"
               class="absolute inset-0 flex flex-col items-center justify-center bg-black/70 rounded-xl gap-3">
            <span class="text-white text-sm font-medium">Анализирую… {{ progress }}%</span>
            <div class="w-40 h-1 bg-white/20 rounded-full overflow-hidden">
              <div class="h-full bg-white/80 rounded-full transition-all duration-300 ease-out"
                   :style="{ width: progress + '%' }" />
            </div>
          </div>
        </Transition>
      </div>

      <!-- Controls -->
      <div class="mt-3 space-y-2">
        <BaseButton v-if="!cameraActive" class="w-full" @click="startCamera">
          Включить камеру
        </BaseButton>
        <template v-else>
          <!-- Основная кнопка + закрыть — всегда в одной строке -->
          <div class="flex gap-2">
            <BaseButton
              class="flex-1 min-w-0"
              :disabled="loading || modelLoading"
              :loading="loading || modelLoading"
              @click="captureAndRun"
            >
              <span v-if="modelLoading">Загрузка модели…</span>
              <span v-else-if="loading">{{ progress }}%</span>
              <span v-else>Сегментировать</span>
            </BaseButton>
            <button
              class="shrink-0 w-10 h-10 rounded-xl bg-white/10 text-white/60 hover:text-white hover:bg-white/20 transition-all text-sm flex items-center justify-center"
              @click="stopCamera"
            >✕</button>
          </div>
          <!-- «Ещё раз» — отдельная строка, только когда есть результат -->
          <BaseButton v-if="resultImg" class="w-full" @click="backToCamera">
            Ещё раз
          </BaseButton>
        </template>
      </div>

      <!-- Progress bar (while loading) -->
      <div v-if="loading" class="mt-2 h-0.5 bg-white/10 rounded-full overflow-hidden">
        <div class="h-full bg-white/60 rounded-full transition-all duration-200 ease-out"
             :style="{ width: progress + '%' }" />
      </div>

      <!-- Error -->
      <Transition name="slide-up">
        <p v-if="error" class="mt-3 text-red-300 text-sm text-center whitespace-pre-line">{{ error }}</p>
      </Transition>

      <!-- Detections list -->
      <Transition name="slide-up">
        <div v-if="detections.length" class="mt-3 space-y-1.5">
          <p class="text-white/60 text-[10px] uppercase tracking-[0.15em]">
            Найдено: {{ detections.length }}
          </p>
          <div
            v-for="(det, i) in detections" :key="i"
            class="rounded-lg border border-white/15 bg-black/30 px-3 py-2 flex items-center justify-between"
          >
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    :style="{ background: colorCss(det.classId) }" />
              <span class="text-white text-sm font-semibold">
                {{ CLASS_NAMES[det.classId] ?? `Класс ${det.classId}` }}
              </span>
            </div>
            <span class="text-white/90 text-xs font-mono font-semibold">
              {{ (det.score * 100).toFixed(1) }}%
            </span>
          </div>
        </div>
      </Transition>

      <p v-if="resultImg && !detections.length && !loading"
         class="mt-3 text-white/50 text-xs text-center">
        Объекты не обнаружены. Попробуйте снова.
      </p>

    </div>
  </section>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import BaseButton from '@/components/ui/BaseButton.vue'

// ── Constants ─────────────────────────────────────────────────────────────────
const CLASS_NAMES  = ['Альбатрос', 'Тупик', 'Пингвин']
const CLASS_COLORS = [[249, 115, 22], [59, 130, 246], [34, 197, 94]]
const NC          = 3
const MODEL_SIZE  = 640
const CONF_THRESH = 0.25
const NMS_THRESH  = 0.45
const MODEL_URL  = '/models/best.onnx'
const WASM_PATH  = '/ort/'   // served from public/ort/ (baked into image via Dockerfile)

// ── State ─────────────────────────────────────────────────────────────────────
const videoEl      = ref(null)
const loading      = ref(false)
const modelLoading = ref(false)
const progress     = ref(0)
const error        = ref(null)
const detections   = ref([])
const resultImg    = ref(null)
const cameraActive = ref(false)

let stream        = null
let ortSession    = null
let progressTimer = null

// ── Helpers ───────────────────────────────────────────────────────────────────
function colorCss(id) {
  const [r, g, b] = CLASS_COLORS[id % CLASS_COLORS.length]
  return `rgb(${r},${g},${b})`
}

function startProgress() {
  progress.value = 0
  clearInterval(progressTimer)
  progressTimer = setInterval(() => {
    const p = progress.value
    const step = p < 30 ? 4 : p < 70 ? 1.5 : 0.4
    if (p < 90) progress.value = Math.min(90, p + step)
  }, 250)
}
function stopProgress() {
  clearInterval(progressTimer)
  progress.value = 100
  setTimeout(() => { progress.value = 0 }, 400)
}

// ── Model loading ─────────────────────────────────────────────────────────────
async function ensureModel() {
  if (ortSession) return
  modelLoading.value = true
  error.value = null
  try {
    const ort = await import('onnxruntime-web')
    ort.env.wasm.numThreads = 1          // avoid SharedArrayBuffer requirement
    ort.env.wasm.wasmPaths  = WASM_PATH
    ortSession = await ort.InferenceSession.create(MODEL_URL, {
      executionProviders: ['wasm'],
    })
  } catch (e) {
    error.value = `Не удалось загрузить модель: ${e.message}`
    throw e
  } finally {
    modelLoading.value = false
  }
}

// ── Camera ────────────────────────────────────────────────────────────────────
async function startCamera() {
  error.value = null
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 } },
      audio: false,
    })
    videoEl.value.srcObject = stream
    cameraActive.value = true
    ensureModel()   // preload in background
  } catch (e) {
    error.value = `Нет доступа к камере.\n${e.message}\n\nПроверь: страница открыта по HTTPS?`
  }
}

function stopCamera() {
  stream?.getTracks().forEach(t => t.stop())
  stream = null
  cameraActive.value = false
  resultImg.value  = null
  detections.value = []
}

function backToCamera() {
  resultImg.value  = null
  detections.value = []
  error.value      = null
}

// ── Math utils ────────────────────────────────────────────────────────────────
function sigmoid(x) {
  return 1 / (1 + Math.exp(-Math.max(-88, Math.min(88, x))))
}

function iouBoxes(a, b) {
  const ix1 = Math.max(a[0], b[0]), iy1 = Math.max(a[1], b[1])
  const ix2 = Math.min(a[2], b[2]), iy2 = Math.min(a[3], b[3])
  const inter = Math.max(0, ix2 - ix1) * Math.max(0, iy2 - iy1)
  const area = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - inter
  return inter / (area + 1e-7)
}

function nms(boxes, scores) {
  const order = [...scores.keys()].sort((a, b) => scores[b] - scores[a])
  const keep = []
  const suppressed = new Uint8Array(scores.length)
  for (const i of order) {
    if (suppressed[i]) continue
    keep.push(i)
    for (const j of order) {
      if (j === i || suppressed[j]) continue
      if (iouBoxes(boxes[i], boxes[j]) >= NMS_THRESH) suppressed[j] = 1
    }
  }
  return keep
}

// Resize source (video/canvas) to MODEL_SIZE×MODEL_SIZE with grey letterbox padding
function letterbox(src) {
  const w = src.videoWidth  ?? src.width
  const h = src.videoHeight ?? src.height
  const scale = MODEL_SIZE / Math.max(w, h)
  const nw = Math.round(w * scale)
  const nh = Math.round(h * scale)
  const padW = Math.floor((MODEL_SIZE - nw) / 2)
  const padH = Math.floor((MODEL_SIZE - nh) / 2)

  const cvs = document.createElement('canvas')
  cvs.width = cvs.height = MODEL_SIZE
  const ctx = cvs.getContext('2d')
  ctx.fillStyle = 'rgb(114,114,114)'
  ctx.fillRect(0, 0, MODEL_SIZE, MODEL_SIZE)
  ctx.drawImage(src, padW, padH, nw, nh)
  return { cvs, scale, padW, padH, origW: w, origH: h }
}

// Canvas → Float32 NCHW tensor [1,3,H,W], normalized to [0,1]
function canvasToTensor(ort, cvs) {
  const { data } = cvs.getContext('2d').getImageData(0, 0, MODEL_SIZE, MODEL_SIZE)
  const n  = MODEL_SIZE * MODEL_SIZE
  const f32 = new Float32Array(3 * n)
  for (let i = 0; i < n; i++) {
    f32[i]       = data[i*4]   / 255
    f32[n + i]   = data[i*4+1] / 255
    f32[2*n + i] = data[i*4+2] / 255
  }
  return new ort.Tensor('float32', f32, [1, 3, MODEL_SIZE, MODEL_SIZE])
}

// ── Inference ─────────────────────────────────────────────────────────────────
async function captureAndRun() {
  if (loading.value || modelLoading.value) return
  await ensureModel()
  if (!ortSession) return

  loading.value    = true
  error.value      = null
  detections.value = []
  startProgress()

  try {
    const ort = await import('onnxruntime-web')
    const { cvs: lbCvs, scale, padW, padH, origW, origH } = letterbox(videoEl.value)
    const tensor = canvasToTensor(ort, lbCvs)

    const outputs  = await ortSession.run({ [ortSession.inputNames[0]]: tensor })
    const out0     = outputs[ortSession.outputNames[0]]  // [1, features, 8400]
    const out1     = outputs[ortSession.outputNames[1]]  // [1, 32, 160, 160]
    const anchors  = out0.dims[2]   // 8400
    const out0data = out0.data
    const out1data = out1.data

    // ── Filter by confidence ─────────────────────────────────────────────────
    const boxes = [], scores = [], classIds = [], coefsList = []
    for (let a = 0; a < anchors; a++) {
      let maxScore = 0, classId = 0
      for (let c = 0; c < NC; c++) {
        const s = out0data[(4 + c) * anchors + a]
        if (s > maxScore) { maxScore = s; classId = c }
      }
      if (maxScore < CONF_THRESH) continue

      const cx = out0data[0 * anchors + a]
      const cy = out0data[1 * anchors + a]
      const bw = out0data[2 * anchors + a]
      const bh = out0data[3 * anchors + a]

      boxes.push([
        Math.max(0, cx - bw/2), Math.max(0, cy - bh/2),
        Math.min(MODEL_SIZE, cx + bw/2), Math.min(MODEL_SIZE, cy + bh/2),
      ])
      scores.push(maxScore)
      classIds.push(classId)

      const coefs = new Float32Array(32)
      for (let k = 0; k < 32; k++) coefs[k] = out0data[(4 + NC + k) * anchors + a]
      coefsList.push(coefs)
    }

    if (!boxes.length) { stopProgress(); loading.value = false; return }

    // ── NMS ──────────────────────────────────────────────────────────────────
    const kept = nms(boxes, scores)
    const dets = []

    for (const idx of kept) {
      const [bx1, by1, bx2, by2] = boxes[idx]
      // Map bbox from 640-space back to original image coords
      const ox1 = Math.max(0,     (bx1 - padW) / scale)
      const oy1 = Math.max(0,     (by1 - padH) / scale)
      const ox2 = Math.min(origW, (bx2 - padW) / scale)
      const oy2 = Math.min(origH, (by2 - padH) / scale)

      // ── Reconstruct mask: sigmoid(coefs @ protos) in 160×160 space ────────
      const mask160 = new Float32Array(160 * 160)
      const coefs   = coefsList[idx]
      for (let j = 0; j < 160 * 160; j++) {
        let v = 0
        for (let k = 0; k < 32; k++) v += coefs[k] * out1data[k * 160 * 160 + j]
        mask160[j] = sigmoid(v)
      }

      dets.push({ classId: classIds[idx], score: scores[idx],
                  bbox: [ox1, oy1, ox2, oy2],
                  mask160, padW, padH, scale, origW, origH })
    }

    // ── Render ────────────────────────────────────────────────────────────────
    resultImg.value  = renderResult(videoEl.value, dets, origW, origH)
    detections.value = dets.map(({ classId, score, bbox }) => ({ classId, score, bbox }))

  } catch (e) {
    error.value = `Ошибка инференса: ${e.message}`
    console.error(e)
  } finally {
    stopProgress()
    loading.value = false
  }
}

// ── Render detections onto canvas, return data URL ────────────────────────────
function renderResult(src, dets, origW, origH) {
  const out = document.createElement('canvas')
  out.width = origW; out.height = origH
  const ctx = out.getContext('2d')
  ctx.drawImage(src, 0, 0, origW, origH)

  for (const det of dets) {
    const [r, g, b] = CLASS_COLORS[det.classId % CLASS_COLORS.length]
    const { mask160, padW, padH, scale } = det

    // 1. Draw mask as 160×160 RGBA image
    const small = document.createElement('canvas')
    small.width = small.height = 160
    const sCtx = small.getContext('2d')
    const imgData = sCtx.createImageData(160, 160)
    for (let i = 0; i < 160 * 160; i++) {
      imgData.data[i*4]   = r
      imgData.data[i*4+1] = g
      imgData.data[i*4+2] = b
      imgData.data[i*4+3] = mask160[i] > 0.5 ? 115 : 0  // ~45% alpha
    }
    sCtx.putImageData(imgData, 0, 0)

    // 2. Scale 160→640 (browser bilinear), crop out padding, draw to output
    //    drawImage(src, sx, sy, sw, sh, dx, dy, dw, dh)
    const nw   = Math.round(origW * scale)   // content width in 640 space
    const nh   = Math.round(origH * scale)   // content height in 640 space
    const ratio = 160 / MODEL_SIZE
    ctx.drawImage(
      small,
      padW * ratio, padH * ratio,   // crop start in 160-space
      nw * ratio,   nh * ratio,     // crop size in 160-space
      0, 0, origW, origH,           // destination: full output canvas
    )

    // 3. Bounding box
    const [x1, y1, x2, y2] = det.bbox
    const lw = Math.max(2, Math.round(origW / 200))
    ctx.strokeStyle = `rgb(${r},${g},${b})`
    ctx.lineWidth = lw
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)

    // 4. Label
    const label = `${CLASS_NAMES[det.classId]}  ${(det.score * 100).toFixed(1)}%`
    const fs = Math.max(14, Math.round(origW / 28))
    ctx.font = `bold ${fs}px Arial, sans-serif`
    const tw  = ctx.measureText(label).width
    const pad = 5
    const ly  = y1 - fs - pad * 2 < 0 ? y1 : y1 - fs - pad * 2
    ctx.fillStyle = `rgb(${r},${g},${b})`
    ctx.fillRect(x1, ly, tw + pad * 2, fs + pad * 2)
    ctx.fillStyle = 'white'
    ctx.fillText(label, x1 + pad, ly + fs + pad)
  }

  return out.toDataURL('image/jpeg', 0.92)
}

// ── Cleanup ───────────────────────────────────────────────────────────────────
onUnmounted(() => {
  stream?.getTracks().forEach(t => t.stop())
  clearInterval(progressTimer)
})
</script>
