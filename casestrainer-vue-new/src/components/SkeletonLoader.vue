<template>
  <div class="skeleton-loader" :style="{ height: height, width: width }">
    <div v-for="n in lines" :key="n" class="skeleton-line"></div>
  </div>
</template>

<script setup>
const props = defineProps({
  lines: { type: Number, default: 3 },
  height: { type: String, default: 'auto' },
  width: { type: String, default: '100%' }
});
</script>

<style scoped>
.skeleton-loader {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
}
.skeleton-line {
  height: 1.2em;
  width: 100%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  border-radius: 6px;
  animation: skeleton-pulse 1.2s infinite ease-in-out;
}
@keyframes skeleton-pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}
</style> 