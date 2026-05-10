<template>
  <div class="glass rounded-2xl p-6 space-y-5">

    <!-- ── Classification result ── -->
    <p class="text-white/40 text-[10px] uppercase tracking-[0.15em]">Результат классификации</p>

    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-white/15 flex items-center justify-center flex-shrink-0 shadow-inner">
        <IconCheck class="w-5 h-5 text-white" />
      </div>
      <p class="text-white font-bold text-2xl">{{ label }}</p>
    </div>

    <!-- ── Bird metadata ── -->
    <div class="border-t border-white/10 pt-5 space-y-3">
      <div class="flex items-baseline gap-2">
        <span class="text-white/40 text-[10px] uppercase tracking-[0.15em] shrink-0">Масса</span>
        <span class="text-white/90 text-sm font-medium">{{ weight }}</span>
      </div>
      <p class="text-white/65 text-sm leading-relaxed">{{ description }}</p>
    </div>

    <!-- ── Neural-network weights summary ── -->
    <div v-if="weightsSummary && weightsSummary.length" class="border-t border-white/10 pt-5 space-y-4">

      <p class="text-white/40 text-[10px] uppercase tracking-[0.15em]">Весовые коэффициенты</p>
      <p class="text-white/55 text-xs leading-relaxed">{{ weightsDescription }}</p>

      <div class="space-y-2.5">
        <div
          v-for="layer in weightsSummary"
          :key="layer.name"
          class="rounded-xl bg-white p-3.5 shadow-sm space-y-2.5"
        >
          <!-- Layer header -->
          <div class="flex items-start justify-between gap-3">
            <span class="text-slate-800 text-xs font-semibold leading-snug">{{ layer.role }}</span>
            <span class="text-slate-400 text-[11px] font-mono shrink-0 mt-px bg-slate-100 px-1.5 py-0.5 rounded">
              {{ formatShape(layer.shape) }}
            </span>
          </div>

          <!-- Small tensor: all values as chips -->
          <div v-if="layer.values" class="flex flex-wrap gap-1.5">
            <span
              v-for="(v, i) in layer.values"
              :key="i"
              class="text-slate-700 text-xs font-mono bg-slate-100 px-2 py-1 rounded-lg"
            >{{ fmt(v) }}</span>
          </div>

          <!-- Large tensor: stats grid + sample row -->
          <div v-else class="space-y-2">
            <div class="grid grid-cols-4 gap-2">
              <div v-for="stat in ['min','max','mean','std']" :key="stat"
                   class="bg-slate-50 rounded-lg px-2 py-1.5 text-center">
                <p class="text-slate-400 text-[10px] uppercase tracking-wide leading-none mb-0.5">{{ stat }}</p>
                <p class="text-slate-800 text-xs font-mono font-medium">{{ fmt(layer[stat]) }}</p>
              </div>
            </div>
            <div class="flex flex-wrap items-center gap-1.5 pt-0.5">
              <span class="text-slate-400 text-[10px] uppercase tracking-wide mr-0.5">выборка</span>
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
    </div>

  </div>
</template>

<script setup>
import IconCheck from '@/components/icons/IconCheck.vue'
import { WEIGHTS_DESCRIPTION } from '@/constants/weightsInfo.js'

defineProps({
  label:          { type: String, required: true },
  weight:         { type: String, required: true },
  description:    { type: String, required: true },
  weightsSummary: { type: Array,  default: null },
})

const weightsDescription = WEIGHTS_DESCRIPTION

function formatShape(shape) {
  return shape.length === 0 ? 'scalar' : shape.join(' × ')
}

function fmt(v) {
  return Number(v).toFixed(4)
}
</script>
