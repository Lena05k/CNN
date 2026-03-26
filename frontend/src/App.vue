<template>
  <div class="bg-hero min-h-screen flex flex-col">
    <!-- dark overlay for readability -->
    <div class="min-h-screen flex flex-col bg-black/10">
      <AppNav />
      <main class="flex-1 flex flex-col items-center justify-center pt-20 pb-8">
        <HeroSection />
        <ClassifierCard
          :score-prediction="scorePrediction"
          @prediction="onPrediction"
        />
        <FeaturesRow />
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
import ClassifierCard from '@/components/sections/ClassifierCard.vue'
import FeaturesRow    from '@/components/sections/FeaturesRow.vue'

const scorePrediction = ref(null)

function onPrediction(result) {
  scorePrediction.value = result
}
</script>
