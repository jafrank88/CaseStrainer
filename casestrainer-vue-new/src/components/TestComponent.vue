<template>
  <div class="test-component">
    <h3>Test Component Loaded Successfully</h3>
    <p>This is a test component to verify component loading.</p>
    <div class="test-content">
      <p>If you can see this, components are loading correctly.</p>
      <p>Current time: {{ currentTime }}</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';

export default {
  name: 'TestComponent',
  setup() {
    const currentTime = ref(new Date().toLocaleTimeString());
    
    onMounted(() => {
      console.log('TestComponent mounted at:', currentTime.value);
    });
    
    return {
      currentTime
    };
  }
};
</script>

<style scoped>
.test-component {
  padding: 20px;
  border: 2px solid #4CAF50;
  border-radius: 8px;
  background-color: #f8fff8;
  margin: 20px 0;
}

.test-content {
  margin-top: 15px;
  padding: 10px;
  background-color: #f0f8ff;
  border-radius: 4px;
}
</style>
