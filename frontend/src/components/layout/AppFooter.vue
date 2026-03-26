<template>
  <footer class="glass-dark py-4 px-4 mt-auto">
    <p class="text-center text-white/30 text-xs">
      CNN Classifier &copy; {{ year }} &middot; Powered by PyTorch &amp; Vue&nbsp;3
    </p>
  </footer>
</template>

<script setup>
const year = new Date().getFullYear()
</script>
