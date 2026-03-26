<template>
  <button
    type="button"
    class="btn-primary"
    :disabled="disabled"
    v-bind="$attrs"
  >
    <IconSpinner v-if="loading" class="w-5 h-5 animate-spin-slow" />
    <IconSparkles v-else class="w-5 h-5" />
    <slot />
  </button>
</template>

<script setup>
import IconSpinner  from '@/components/icons/IconSpinner.vue'
import IconSparkles from '@/components/icons/IconSparkles.vue'

defineProps({
  loading:  { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})
</script>
