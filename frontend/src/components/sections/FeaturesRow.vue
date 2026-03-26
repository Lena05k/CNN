<template>
  <section class="px-4 pb-16 mt-8 animate-fade-up" style="animation-delay: 0.2s">
    <div class="max-w-md mx-auto grid grid-cols-3 gap-3">
      <FeatureCard
        v-for="feature in features"
        :key="feature.label"
        v-bind="feature"
      />
    </div>
  </section>
</template>

<script setup>
import FeatureCard from '@/components/ui/FeatureCard.vue'

const features = [
  { icon: '🧠', label: 'ResNet CNN',   description: 'Глубокая сеть' },
  { icon: '🎯', label: '100 классов',  description: 'Датасет CIFAR-100' },
  { icon: '⚡', label: 'PyTorch',      description: 'Быстрый inference' },
]
</script>
