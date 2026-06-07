<template>
  <div class="bg-hero min-h-screen flex flex-col">
    <div class="min-h-screen flex flex-col bg-black/10">

      <AppNav :active-tab="activeTab" @tab-change="activeTab = $event" />

      <main class="flex-1 flex flex-col items-center justify-center pt-20 pb-8">

        <!-- ДЗ 1 — Классификация -->
        <template v-if="activeTab === 'hw1'">
          <HeroSection />
          <ClassifierCard
            :score-prediction="scorePrediction"
            @prediction="onPrediction"
          />
          <FeaturesRow />
        </template>

        <!-- ДЗ 2 — Сегментация -->
        <template v-else>
          <SegHeroSection />
          <!-- Переключатель: файл / камера -->
          <div class="flex gap-2 justify-center mt-2 mb-1">
            <button
              v-for="m in segModes" :key="m.key"
              class="px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200"
              :class="segMode === m.key
                ? 'bg-white text-black shadow'
                : 'text-white/60 hover:text-white border border-white/20'"
              @click="segMode = m.key"
            >{{ m.label }}</button>
          </div>
          <SegmenterCard       v-if="segMode === 'file'" />
          <CameraSegmenterCard v-else />
        </template>

      </main>

      <AppFooter />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AppNav              from '@/components/layout/AppNav.vue'
import AppFooter           from '@/components/layout/AppFooter.vue'
import HeroSection         from '@/components/sections/HeroSection.vue'
import SegHeroSection      from '@/components/sections/SegHeroSection.vue'
import ClassifierCard      from '@/components/sections/ClassifierCard.vue'
import SegmenterCard       from '@/components/sections/SegmenterCard.vue'
import CameraSegmenterCard from '@/components/sections/CameraSegmenterCard.vue'
import FeaturesRow         from '@/components/sections/FeaturesRow.vue'

const activeTab       = ref('hw1')
const scorePrediction = ref(null)
const segMode         = ref('file')
const segModes        = [
  { key: 'file',   label: 'Файл' },
  { key: 'camera', label: '📱 Камера' },
]

function onPrediction(result) {
  scorePrediction.value = result
}
</script>
