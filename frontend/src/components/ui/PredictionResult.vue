<template>
  <div class="glass rounded-2xl p-5">
    <p class="text-white/40 text-xs uppercase tracking-widest mb-2">Результат классификации</p>
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 rounded-xl bg-white/15 flex items-center justify-center flex-shrink-0">
        <IconCheck class="w-5 h-5 text-white" />
      </div>
      <p class="text-white font-bold text-xl truncate">{{ label }}</p>
    </div>
  </div>
</template>

<script setup>
import IconCheck from '@/components/icons/IconCheck.vue'

defineProps({
  label: { type: String, required: true },
})
</script>
