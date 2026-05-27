<template>
  <div class="glass rounded-2xl p-5 space-y-4">

    <!-- ── Заголовок: эмодзи + название + латинское имя ── -->
    <p class="text-white/40 text-[10px] uppercase tracking-[0.15em]">Результат классификации</p>

    <div class="flex items-center gap-3">
      <span class="text-3xl leading-none select-none">{{ emoji }}</span>
      <div>
        <p class="text-white font-bold text-2xl leading-tight">{{ label }}</p>
        <p v-if="latin" class="text-white/40 text-xs italic mt-0.5">{{ latin }}</p>
      </div>
    </div>

    <!-- ── Метаданные птицы ── -->
    <div class="border-t border-white/10 pt-4 space-y-2">
      <div class="flex items-baseline gap-2">
        <span class="text-white/40 text-[10px] uppercase tracking-[0.15em] shrink-0">Масса</span>
        <span class="text-white/90 text-sm font-medium">{{ weight }}</span>
      </div>
      <p class="text-white/65 text-sm leading-relaxed">{{ description }}</p>
    </div>

    <!-- ── Весовые коэффициенты (сворачиваемые) ── -->
    <div v-if="weightsSummary && weightsSummary.length" class="border-t border-white/10 pt-4">

      <button
        class="flex items-center justify-between w-full group"
        @click="showWeights = !showWeights"
      >
        <span class="text-white/40 text-[10px] uppercase tracking-[0.15em] group-hover:text-white/60 transition-colors">
          Весовые коэффициенты
        </span>
        <span class="text-white/30 text-xs group-hover:text-white/50 transition-colors">
          {{ showWeights ? '▲ скрыть' : '▼ показать' }}
        </span>
      </button>

      <Transition name="slide-up">
        <div v-if="showWeights" class="mt-3 space-y-3">
          <p class="text-white/55 text-xs leading-relaxed">{{ weightsDescription }}</p>

          <div
            v-for="layer in weightsSummary"
            :key="layer.name"
            class="rounded-xl bg-white p-3 shadow-sm space-y-2"
          >
            <!-- Layer header -->
            <div class="flex items-start justify-between gap-3">
              <span class="text-slate-800 text-xs font-semibold leading-snug">{{ layer.role }}</span>
              <span class="text-slate-400 text-[11px] font-mono shrink-0 mt-px bg-slate-100 px-1.5 py-0.5 rounded">
                {{ formatShape(layer.shape) }}
              </span>
            </div>

            <!-- Small tensor -->
            <div v-if="layer.values" class="flex flex-wrap gap-1">
              <span
                v-for="(v, i) in layer.values"
                :key="i"
                class="text-slate-700 text-xs font-mono bg-slate-100 px-2 py-0.5 rounded"
              >{{ fmt(v) }}</span>
            </div>

            <!-- Large tensor: stats -->
            <div v-else class="space-y-1.5">
              <div class="grid grid-cols-4 gap-1.5">
                <div v-for="stat in ['min','max','mean','std']" :key="stat"
                     class="bg-slate-50 rounded px-2 py-1 text-center">
                  <p class="text-slate-400 text-[10px] uppercase leading-none mb-0.5">{{ stat }}</p>
                  <p class="text-slate-800 text-xs font-mono font-medium">{{ fmt(layer[stat]) }}</p>
                </div>
              </div>
              <div class="flex flex-wrap items-center gap-1 pt-0.5">
                <span class="text-slate-400 text-[10px] uppercase mr-0.5">выборка</span>
                <span
                  v-for="(v, i) in layer.sample"
                  :key="i"
                  class="text-slate-600 text-xs font-mono bg-slate-100 px-1.5 py-0.5 rounded"
                >{{ fmt(v) }}</span>
                <span class="text-slate-300 text-xs">…</span>
              </div>
            </div>

          </div>
        </div>
      </Transition>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { WEIGHTS_DESCRIPTION } from '@/constants/weightsInfo.js'

defineProps({
  label:          { type: String, required: true },
  emoji:          { type: String, default: '🐦' },
  latin:          { type: String, default: '' },
  weight:         { type: String, required: true },
  description:    { type: String, required: true },
  weightsSummary: { type: Array,  default: null },
})

const showWeights      = ref(false)
const weightsDescription = WEIGHTS_DESCRIPTION

function formatShape(shape) {
  return shape.length === 0 ? 'scalar' : shape.join(' × ')
}

function fmt(v) {
  return Number(v).toFixed(4)
}
</script>
