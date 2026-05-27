<template>
  <section class="px-4 flex justify-center w-full animate-fade-up" style="animation-delay: 0.1s">
    <div
      class="glass-card w-full p-6 sm:p-8 transition-all duration-300"
      :class="renderedImg ? 'max-w-5xl' : 'max-w-xl'"
    >

      <!-- ══ ДО РЕЗУЛЬТАТА: обычный вертикальный layout ══════════════════════ -->
      <template v-if="!renderedImg">
        <DropZone
          :preview-url="previewUrl"
          :file-name="fileName"
          :is-dragging="isDragging"
          @file-selected="applyFile"
          @drag-enter="isDragging = true"
          @drag-leave="isDragging = false"
        />

        <FileChip v-if="fileName" :file-name="fileName" class="mt-4" @clear="clearFile" />

        <div v-if="selectedFile" class="flex items-center gap-3 mt-4">
          <span class="text-white/80 text-xs w-28 shrink-0">Порог: {{ confThreshPct }}%</span>
          <input
            v-model.number="confThreshPct"
            type="range" min="5" max="95" step="5"
            class="flex-1 h-1 accent-white cursor-pointer"
          />
        </div>

        <BaseButton :disabled="!selectedFile || loading" :loading="loading" class="w-full mt-5" @click="handleSubmit">
          <span v-if="loading">{{ loadingMsg }}</span>
          <span v-else>Сегментировать</span>
        </BaseButton>

        <Transition name="slide-up">
          <p v-if="error" class="mt-4 text-red-300 text-sm text-center whitespace-pre-line">{{ error }}</p>
        </Transition>
      </template>

      <!-- ══ ПОСЛЕ РЕЗУЛЬТАТА: две колонки ══════════════════════════════════ -->
      <template v-else>

        <!-- Компактная строка управления -->
        <div class="flex flex-wrap items-center gap-3 mb-5">
          <FileChip :file-name="fileName" @clear="clearFile" />
          <div class="flex items-center gap-2 flex-1 min-w-[120px]">
            <span class="text-white/80 text-xs shrink-0">Порог: {{ confThreshPct }}%</span>
            <input
              v-model.number="confThreshPct"
              type="range" min="5" max="95" step="5"
              class="flex-1 h-1 accent-white cursor-pointer"
            />
          </div>
          <BaseButton :disabled="loading" :loading="loading" class="shrink-0" @click="handleSubmit">
            <span v-if="loading">{{ loadingMsg }}</span>
            <span v-else>Повторить</span>
          </BaseButton>
        </div>

        <Transition name="slide-up">
          <p v-if="error" class="mb-4 text-red-300 text-sm text-center whitespace-pre-line">{{ error }}</p>
        </Transition>

        <!-- Двухколоночный layout -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">

          <!-- ── ЛЕВАЯ КОЛОНКА: детекции + карточки ── -->
          <div class="space-y-4">

            <!-- Ничего не найдено -->
            <p v-if="!detections.length && !loading"
               class="text-white text-sm text-center py-4">
              Объекты не обнаружены. Попробуйте снизить порог уверенности.
            </p>

            <!-- Список обнаруженных объектов -->
            <div v-if="detections.length" class="space-y-2">
              <p class="text-white/70 text-[10px] uppercase tracking-[0.15em]">
                Найдено объектов: {{ detections.length }}
              </p>

              <div
                v-for="(det, i) in detections"
                :key="i"
                class="rounded-xl border border-white/20 bg-black/40 px-4 py-3 flex items-center justify-between"
              >
                <div class="flex items-center gap-2.5">
                  <span class="w-3 h-3 rounded-full flex-shrink-0" :style="{ background: colorCss(det.classId) }" />
                  <span class="text-white text-sm font-semibold">{{ CLASS_NAMES[det.classId] ?? `Класс ${det.classId}` }}</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-white/90 text-xs font-mono font-semibold">{{ (det.score * 100).toFixed(1) }}%</span>
                  <button
                    class="text-xs font-semibold px-3 py-1 rounded-full transition-all"
                    :style="{ background: colorCss(det.classId), color: '#fff' }"
                    @click="openCards(det, i)"
                  >
                    Карточки
                  </button>
                </div>
              </div>
            </div>

            <!-- Панель карточек -->
            <Transition name="slide-up">
              <div v-if="activeCards" class="space-y-3">

                <div class="flex items-center justify-between">
                  <p class="text-white font-semibold text-sm">
                    Похожие виды:
                    <span :style="{ color: colorCss(activeCards.classId) }">
                      {{ CLASS_NAMES[activeCards.classId] }}
                    </span>
                  </p>
                  <button class="text-white/70 hover:text-white text-sm transition-colors" @click="activeCards = null">✕</button>
                </div>

                <!-- Инфо о виде -->
                <div v-if="classInfo" class="rounded-xl border border-white/20 bg-black/40 p-4 space-y-2">
                  <p class="font-bold text-white text-sm">
                    {{ classInfo.emoji }} {{ classInfo.name }}
                    <span class="text-white/65 font-normal italic text-xs ml-1.5">{{ classInfo.latin }}</span>
                  </p>
                  <p class="text-white/95 text-sm leading-relaxed">{{ classInfo.about }}</p>
                  <div class="grid grid-cols-1 gap-1 pt-1 text-xs">
                    <p class="text-white/80">📍 {{ classInfo.habitat }}</p>
                    <p class="text-white/80">🍽 {{ classInfo.diet }}</p>
                    <p class="text-white/80">📏 {{ classInfo.size }}</p>
                    <p class="text-emerald-300">🔁 {{ classInfo.similarTo }}</p>
                  </div>
                </div>

                <!-- Сетка похожих карточек -->
                <div v-if="cardsLoading" class="text-white/80 text-sm text-center py-4">Загружаю карточки…</div>
                <div v-else class="grid grid-cols-2 gap-2">
                  <div
                    v-for="card in cardResults"
                    :key="card.id"
                    class="rounded-xl border border-white/20 bg-black/40 p-3 space-y-2"
                  >
                    <!-- Шапка: номер + процент схожести -->
                    <div class="flex items-center justify-between">
                      <span
                        class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0"
                        :style="{ background: colorCss(card.classId) }"
                      >{{ card.id }}</span>

                      <div class="flex flex-col items-end gap-0.5">
                        <span class="text-sm font-mono font-bold text-white">
                          {{ card.similarity != null
                              ? (card.similarity * 100).toFixed(1) + '%'
                              : '~' + card.defaultSimilarity + '%' }}
                        </span>
                        <span class="text-[9px] uppercase tracking-wide"
                              :class="card.similarity != null ? 'text-emerald-300' : 'text-white/55'">
                          {{ card.similarity != null ? 'CLIP' : 'типовой' }}
                        </span>
                      </div>
                    </div>

                    <p class="text-white text-xs font-semibold leading-tight">{{ card.name }}</p>
                  </div>
                </div>

              </div>
            </Transition>

          </div>

          <!-- ── ПРАВАЯ КОЛОНКА: изображение + галерея ── -->
          <div class="space-y-3">
            <p class="text-white/70 text-[10px] uppercase tracking-[0.15em]">Результат сегментации</p>

            <img :src="renderedImg" class="w-full rounded-2xl" alt="segmentation" />

            <div class="flex justify-end">
              <span class="text-white/70 text-[10px] font-mono rounded-full px-2 py-0.5 border border-white/20">
                {{ modelName }}
              </span>
            </div>

            <!-- Галерея -->
            <div v-if="gallery.length" class="pt-1">
              <p class="text-white/70 text-[10px] uppercase tracking-[0.15em] mb-2">История</p>
              <div class="flex gap-2 overflow-x-auto pb-1">
                <button
                  v-for="item in gallery"
                  :key="item.id"
                  class="flex-shrink-0 relative group"
                  @click="restoreFromGallery(item)"
                >
                  <img :src="item.thumb" class="w-16 h-16 object-cover rounded-xl border border-white/10 group-hover:border-white/40 transition-all" />
                  <span class="absolute bottom-1 left-1 text-[9px] text-white bg-black/50 rounded px-1">
                    {{ item.count }}
                  </span>
                </button>
              </div>
            </div>
          </div>

        </div>
      </template>

    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import DropZone   from '@/components/ui/DropZone.vue'
import FileChip   from '@/components/ui/FileChip.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import { CLASS_NAMES, CLASS_COLORS, CLASS_INFO } from '@/constants/segmentMeta.js'
import { BIRD_CARDS, getCardsByClass }            from '@/constants/birdCards.js'

/** Добавляет defaultSimilarity из локального справочника к карточкам с API */
function enrichCards(cards) {
  return cards.map(card => ({
    ...card,
    defaultSimilarity: BIRD_CARDS.find(c => c.id === card.id)?.defaultSimilarity ?? 80,
  }))
}

// ── State ──────────────────────────────────────────────────────────────────────
const confThreshPct = ref(25)
const confThresh    = computed(() => confThreshPct.value / 100)

const selectedFile = ref(null)
const previewUrl   = ref(null)
const fileName     = ref('')
const isDragging   = ref(false)
const loading      = ref(false)
const loadingMsg   = ref('Сегментирую...')
const error        = ref(null)
const detections   = ref([])
const renderedImg  = ref(null)
const modelName    = ref('')

const gallery      = ref([])
let   galleryId    = 0

const activeCards  = ref(null)
const cardResults  = ref([])
const cardsLoading = ref(false)
const classInfo    = computed(() =>
  activeCards.value != null ? CLASS_INFO[activeCards.value.classId] : null
)

// ── Helpers ────────────────────────────────────────────────────────────────────
function colorCss(classId) {
  const [r, g, b] = CLASS_COLORS[classId % CLASS_COLORS.length]
  return `rgb(${r},${g},${b})`
}

// ── File handling ──────────────────────────────────────────────────────────────
function applyFile(file) {
  if (!file?.type.startsWith('image/')) return
  selectedFile.value = file
  fileName.value     = file.name
  previewUrl.value   = URL.createObjectURL(file)
  error.value        = null
  detections.value   = []
  renderedImg.value  = null
  activeCards.value  = null
}

function clearFile() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  selectedFile.value = null
  previewUrl.value   = null
  fileName.value     = ''
  detections.value   = []
  renderedImg.value  = null
  activeCards.value  = null
}

// ── Segmentation ───────────────────────────────────────────────────────────────
async function handleSubmit() {
  if (!selectedFile.value || loading.value) return
  loading.value    = true
  loadingMsg.value = 'Сегментирую...'
  error.value      = null
  detections.value = []
  activeCards.value = null

  try {
    const form = new FormData()
    form.append('filePath',   selectedFile.value)
    form.append('confThresh', String(confThresh.value))

    const res = await fetch('/api/segment', { method: 'POST', body: form })
    if (!res.ok) {
      const b = await res.json().catch(() => ({}))
      throw new Error(b.error ?? `HTTP ${res.status}`)
    }

    const data        = await res.json()
    renderedImg.value = data.rendered
    detections.value  = data.detections ?? []
    modelName.value   = data.model ?? ''

    if (data.rendered) {
      gallery.value.unshift({ id: ++galleryId, thumb: data.rendered, count: detections.value.length })
      if (gallery.value.length > 10) gallery.value.pop()
    }
  } catch (e) {
    error.value = `Ошибка: ${e.message}`
  } finally {
    loading.value = false
  }
}

// ── Найти карточки ─────────────────────────────────────────────────────────────
async function openCards(det, detIndex) {
  activeCards.value  = { classId: det.classId, detIndex }
  cardsLoading.value = true
  cardResults.value  = []

  try {
    const form = new FormData()
    form.append('classId', String(det.classId))

    if (selectedFile.value && det.bbox) {
      const [x1, y1, x2, y2] = det.bbox
      const cvs = document.createElement('canvas')
      cvs.width  = Math.round(x2 - x1)
      cvs.height = Math.round(y2 - y1)
      if (cvs.width > 0 && cvs.height > 0) {
        const img = new Image()
        img.src = previewUrl.value
        await new Promise(r => { img.onload = r })
        cvs.getContext('2d').drawImage(img, x1, y1, cvs.width, cvs.height, 0, 0, cvs.width, cvs.height)
        await new Promise(resolve => cvs.toBlob(blob => {
          if (blob) form.append('cropImage', blob, 'crop.png')
          resolve()
        }, 'image/png'))
      }
    }

    const res = await fetch('/api/clip-search', { method: 'POST', body: form })
    const raw = res.ok
      ? (await res.json()).results ?? getCardsByClass(det.classId)
      : getCardsByClass(det.classId)
    cardResults.value = enrichCards(raw)
  } catch {
    cardResults.value = enrichCards(getCardsByClass(det.classId))
  } finally {
    cardsLoading.value = false
  }
}

// ── Галерея ───────────────────────────────────────────────────────────────────
function restoreFromGallery(item) {
  renderedImg.value = item.thumb
  activeCards.value = null
}
</script>
