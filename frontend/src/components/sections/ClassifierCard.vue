<template>
  <section class="px-4 flex justify-center animate-fade-up" style="animation-delay: 0.1s">
    <div class="glass-card w-full max-w-md p-6 sm:p-8">

      <!-- Drop Zone -->
      <DropZone
        :preview-url="previewUrl"
        :file-name="fileName"
        :is-dragging="isDragging"
        @file-selected="applyFile"
        @drag-enter="isDragging = true"
        @drag-leave="isDragging = false"
      />

      <!-- File chip -->
      <FileChip
        v-if="fileName"
        :file-name="fileName"
        class="mt-4"
        @clear="clearFile"
      />

      <!-- Submit -->
      <BaseButton
        :disabled="!selectedFile || loading"
        :loading="loading"
        class="w-full mt-6"
        @click="handleSubmit"
      >
        {{ loading ? 'Анализирую...' : 'Классифицировать' }}
      </BaseButton>

      <!-- Result -->
      <Transition name="slide-up">
        <PredictionResult
          v-if="scorePrediction"
          :label="scorePrediction"
          class="mt-5"
        />
      </Transition>

      <!-- Error -->
      <Transition name="slide-up">
        <p v-if="error" class="mt-4 text-red-300 text-sm text-center">
          {{ error }}
        </p>
      </Transition>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import DropZone         from '@/components/ui/DropZone.vue'
import FileChip         from '@/components/ui/FileChip.vue'
import BaseButton       from '@/components/ui/BaseButton.vue'
import PredictionResult from '@/components/ui/PredictionResult.vue'

const props = defineProps({
  scorePrediction: { type: String, default: null },
})
const emit = defineEmits(['prediction'])

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
  selectedFile.value = file
  fileName.value     = file.name
  previewUrl.value   = URL.createObjectURL(file)
  error.value        = null
  emit('prediction', null)
}

function clearFile() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  selectedFile.value = null
  previewUrl.value   = null
  fileName.value     = ''
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
