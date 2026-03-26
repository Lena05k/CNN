<template>
  <div class="app-wrapper">
    <AppNav />
    <main class="main-content">
      <HeroSection />
      <ClassifierCard
        :score-prediction="scorePrediction"
        @prediction="onPrediction"
      />
      <FeaturesRow />
    </main>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AppNav        from '@/components/layout/AppNav.vue'
import AppFooter     from '@/components/layout/AppFooter.vue'
import HeroSection   from '@/components/sections/HeroSection.vue'
import ClassifierCard from '@/components/sections/ClassifierCard.vue'
import FeaturesRow   from '@/components/sections/FeaturesRow.vue'

const scorePrediction = ref(null)

function onPrediction(result) {
  scorePrediction.value = result
}
</script>
