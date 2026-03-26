<template>
  <nav class="glass-dark fixed top-0 left-0 right-0 z-50">
    <div class="max-w-5xl mx-auto px-4 sm:px-8 h-14 flex items-center justify-between">
      <!-- Logo -->
      <div class="flex items-center gap-2.5">
        <div class="w-7 h-7 rounded-lg bg-white/15 border border-white/20 flex items-center justify-center">
          <IconBrain class="w-4 h-4 text-white" />
        </div>
        <span class="text-white font-semibold text-sm tracking-wide">CNN Classifier</span>
      </div>

      <!-- Badge -->
      <span class="hidden sm:inline-flex items-center gap-1.5 text-xs text-white/60 glass rounded-full px-3 py-1">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        CIFAR-100
      </span>
    </div>
  </nav>
</template>

<script setup>
import IconBrain from '@/components/icons/IconBrain.vue'
</script>
