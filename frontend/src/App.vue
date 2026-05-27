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
          <SegmenterCard />
        </template>

      </main>

      <AppFooter />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AppNav         from '@/components/layout/AppNav.vue'
import AppFooter      from '@/components/layout/AppFooter.vue'
import HeroSection    from '@/components/sections/HeroSection.vue'
import SegHeroSection from '@/components/sections/SegHeroSection.vue'
import ClassifierCard from '@/components/sections/ClassifierCard.vue'
import SegmenterCard  from '@/components/sections/SegmenterCard.vue'
import FeaturesRow    from '@/components/sections/FeaturesRow.vue'

const activeTab       = ref('hw1')
const scorePrediction = ref(null)

function onPrediction(result) {
  scorePrediction.value = result
}
</script>
