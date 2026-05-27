<template>
  <section class="px-4 flex justify-center w-full animate-fade-up" style="animation-delay: 0.1s">
    <div
      class="glass-card w-full p-6 sm:p-8 transition-all duration-300"
      :class="scorePrediction ? 'max-w-2xl' : 'max-w-md'"
    >

      <!-- Загрузка — только пока нет результата -->
      <template v-if="!scorePrediction">
        <DropZone
          :preview-url="previewUrl"
          :file-name="fileName"
          :is-dragging="isDragging"
          @file-selected="applyFile"
          @drag-enter="isDragging = true"
          @drag-leave="isDragging = false"
        />
        <FileChip
          v-if="fileName"
          :file-name="fileName"
          class="mt-4"
          @clear="clearFile"
        />
      </template>

      <!-- Когда есть результат — компактная строка с файлом -->
      <template v-else>
        <FileChip
          :file-name="fileName"
          class="mb-4"
          @clear="clearFile"
        />
      </template>

      <!-- Кнопка -->
      <BaseButton
        :disabled="!selectedFile || loading"
        :loading="loading"
        class="w-full mt-5"
        @click="handleSubmit"
      >
        {{ loading ? 'Анализирую...' : 'Классифицировать' }}
      </BaseButton>

      <!-- Ошибка -->
      <Transition name="slide-up">
        <p v-if="error" class="mt-4 text-red-300 text-sm text-center">
          {{ error }}
        </p>
      </Transition>

      <!-- Результат: две колонки — слева текст, справа изображение -->
      <Transition name="slide-up">
        <div
          v-if="scorePrediction"
          class="mt-5 grid grid-cols-1 md:grid-cols-2 gap-5 items-start"
        >
          <!-- Левая колонка: результат классификации -->
          <PredictionResult
            :label="scorePrediction"
            :emoji="birdMeta.emoji"
            :latin="birdMeta.latin"
            :weight="birdMeta.weight"
            :description="birdMeta.description"
            :weights-summary="weightsSummary"
          />

          <!-- Правая колонка: загруженное изображение -->
          <img
            v-if="previewUrl"
            :src="previewUrl"
            class="w-full rounded-2xl object-cover"
            alt="Загруженное изображение"
          />
        </div>
      </Transition>

    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import DropZone         from '@/components/ui/DropZone.vue'
import FileChip         from '@/components/ui/FileChip.vue'
import BaseButton       from '@/components/ui/BaseButton.vue'
import PredictionResult from '@/components/ui/PredictionResult.vue'
import { getBirdMeta }  from '@/constants/birdMeta.js'

const props = defineProps({
  scorePrediction: { type: String, default: null },
})
const emit = defineEmits(['prediction'])

const birdMeta       = computed(() => getBirdMeta(props.scorePrediction))
const weightsSummary = ref(null)

const selectedFile = ref(null)
const previewUrl   = ref(null)
const fileName     = ref('')
const isDragging   = ref(false)
const loading      = ref(false)
const error        = ref(null)

function getCsrfToken() {
  const name = 'csrftoken'
  for (const cookie of document.cookie.split(';')) {
    const [key, value] = cookie.trim().split('=')
    if (key === name) return decodeURIComponent(value)
  }
  return null
}

function applyFile(file) {
  if (!file?.type.startsWith('image/')) return
  selectedFile.value   = file
  fileName.value       = file.name
  previewUrl.value     = URL.createObjectURL(file)
  error.value          = null
  weightsSummary.value = null
  emit('prediction', null)
}

function clearFile() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  selectedFile.value   = null
  previewUrl.value     = null
  fileName.value       = ''
  weightsSummary.value = null
  emit('prediction', null)
}

async function handleSubmit() {
  if (!selectedFile.value || loading.value) return
  loading.value = true
  error.value   = null

  try {
    const formData = new FormData()
    formData.append('filePath', selectedFile.value)

    const csrfToken = getCsrfToken()
    if (csrfToken) formData.append('csrfmiddlewaretoken', csrfToken)

    const response = await axios.post('/predictImage', formData, {
      headers: { 'X-CSRFToken': csrfToken ?? '' },
    })

    weightsSummary.value = response.data.weightsSummary ?? null
    emit('prediction', response.data.prediction)
  } catch (e) {
    const serverError = e.response?.data?.error
    error.value = serverError
      ? `Ошибка сервера: ${serverError}`
      : 'Ошибка при классификации. Проверьте соединение.'
  } finally {
    loading.value = false
  }
}
</script>
