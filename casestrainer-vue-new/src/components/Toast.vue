<template>
  <transition name="toast-fade">
    <div v-if="visible" :class="['toast', type]">
      <span class="toast-icon">{{ icon }}</span>
      <span class="toast-message">{{ message }}</span>
      <button class="toast-close" @click="close">×</button>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
const props = defineProps({
  message: String,
  type: { type: String, default: 'info' }, // 'success', 'error', 'info'
  duration: { type: Number, default: 3500 }
});
const emit = defineEmits(['close']);
const visible = ref(true);

const icon = computed(() => {
  if (props.type === 'success') return '✅';
  if (props.type === 'error') return '❌';
  return 'ℹ️';
});

function close() {
  visible.value = false;
  emit('close');
}

watch(() => props.message, (msg) => {
  if (msg) {
    visible.value = true;
    setTimeout(close, props.duration);
  }
});
</script>

<style scoped>
.toast {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #fff;
  color: #333;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.15);
  padding: 1rem 1.5rem;
  min-width: 220px;
  max-width: 400px;
  font-size: 1rem;
  position: fixed;
  top: 2rem;
  right: 2rem;
  z-index: 9999;
  border-left: 6px solid #007bff;
  animation: toast-in 0.3s;
}
.toast.success { border-left-color: #28a745; }
.toast.error { border-left-color: #dc3545; }
.toast.info { border-left-color: #007bff; }
.toast-icon { font-size: 1.5rem; }
.toast-message { flex: 1; }
.toast-close {
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #888;
  cursor: pointer;
  margin-left: 0.5rem;
}
@keyframes toast-in {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}
.toast-fade-enter-active, .toast-fade-leave-active {
  transition: opacity 0.3s;
}
.toast-fade-enter-from, .toast-fade-leave-to {
  opacity: 0;
}
</style> 