<template>
  <div
    class="drop-zone p-6"
    :class="{ 'is-dragging': isDragging }"
    @dragover.prevent="$emit('drag-enter')"
    @dragleave.prevent="$emit('drag-leave')"
    @drop.prevent="onDrop"
    @click="fileInput.click()"
  >
    <!-- Preview -->
    <template v-if="previewUrl">
      <img
        :src="previewUrl"
        :alt="fileName"
        class="max-h-44 rounded-xl object-contain shadow-lg"
      />
      <p class="mt-2 text-white/50 text-xs truncate max-w-full px-2">
        {{ fileName }}
      </p>
    </template>

    <!-- Placeholder -->
    <template v-else>
      <div class="w-12 h-12 rounded-2xl glass flex items-center justify-center mb-3 animate-pulse-ring">
        <IconUpload class="w-6 h-6 text-white/70" />
      </div>
      <p class="text-white/70 font-medium text-sm">Перетащите изображение сюда</p>
      <p class="text-white/35 text-xs mt-1">или нажмите для выбора файла</p>
      <p class="text-white/25 text-xs mt-2">PNG, JPG, WEBP — до 10 МБ</p>
    </template>

    <input
      ref="fileInput"
      type="file"
      name="filePath"
      accept="image/*"
      class="hidden"
      @change="onFileChange"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import IconUpload from '@/components/icons/IconUpload.vue'

defineProps({
  previewUrl:  { type: String,  default: null },
  fileName:    { type: String,  default: '' },
  isDragging:  { type: Boolean, default: false },
})

const emit = defineEmits(['file-selected', 'drag-enter', 'drag-leave'])
const fileInput = ref(null)

function onFileChange(e) {
  emit('file-selected', e.target.files[0])
  e.target.value = ''
}

function onDrop(e) {
  emit('drag-leave')
  emit('file-selected', e.dataTransfer.files[0])
}
</script>
