<template>
  <div class="glass rounded-2xl p-4 flex flex-col items-center text-center">
    <span class="text-2xl mb-2" role="img" :aria-label="label">{{ icon }}</span>
    <p class="text-white/80 text-xs font-semibold">{{ label }}</p>
    <p class="text-white/35 text-xs mt-0.5">{{ description }}</p>
  </div>
</template>

<script setup>
defineProps({
  icon:        { type: String, required: true },
  label:       { type: String, required: true },
  description: { type: String, required: true },
})
</script>
