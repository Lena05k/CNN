<template>
  <nav class="glass-dark fixed top-0 left-0 right-0 z-50">
    <div class="max-w-5xl mx-auto px-4 sm:px-8 h-14 flex items-center justify-between">

      <!-- Логотип -->
      <div class="flex items-center gap-2.5">
        <div class="w-7 h-7 rounded-lg bg-white/15 border border-white/20 flex items-center justify-center">
          <IconBrain class="w-4 h-4 text-white" />
        </div>
        <span class="text-white font-semibold text-sm tracking-wide">Deep Learning</span>
      </div>

      <!-- Вкладки ДЗ1 / ДЗ2 -->
      <div class="flex gap-1 glass rounded-full p-1">
        <button
          class="px-3 sm:px-4 py-1.5 text-xs font-medium rounded-full transition-all duration-200"
          :class="activeTab === 'hw1'
            ? 'bg-white text-slate-900 shadow-sm'
            : 'text-white/60 hover:text-white'"
          @click="$emit('tab-change', 'hw1')"
        >
          ДЗ 1 · Классификация
        </button>
        <button
          class="px-3 sm:px-4 py-1.5 text-xs font-medium rounded-full transition-all duration-200"
          :class="activeTab === 'hw2'
            ? 'bg-white text-slate-900 shadow-sm'
            : 'text-white/60 hover:text-white'"
          @click="$emit('tab-change', 'hw2')"
        >
          ДЗ 2 · Сегментация
        </button>
      </div>

      <!-- Бейдж -->
      <span class="hidden sm:inline-flex items-center gap-1.5 text-xs text-white/60 glass rounded-full px-3 py-1">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        {{ activeTab === 'hw1' ? 'CIFAR-100' : 'YOLOv8-seg' }}
      </span>

    </div>
  </nav>
</template>

<script setup>
import IconBrain from '@/components/icons/IconBrain.vue'

defineProps({
  activeTab: { type: String, default: 'hw1' },
})
defineEmits(['tab-change'])
</script>
