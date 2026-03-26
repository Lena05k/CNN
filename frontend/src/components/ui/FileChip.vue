<template>
  <div class="flex items-center gap-2 glass rounded-xl px-4 py-2">
    <IconImage class="w-4 h-4 text-white/50 flex-shrink-0" />
    <span class="text-white/70 text-xs truncate flex-1">{{ fileName }}</span>
    <button
      type="button"
      class="text-white/35 hover:text-white/80 transition-colors flex-shrink-0 ml-auto"
      aria-label="Удалить файл"
      @click.stop="$emit('clear')"
    >
      <IconClose class="w-4 h-4" />
    </button>
  </div>
</template>

<script setup>
import IconImage from '@/components/icons/IconImage.vue'
import IconClose from '@/components/icons/IconClose.vue'

defineProps({
  fileName: { type: String, required: true },
})
defineEmits(['clear'])
</script>
