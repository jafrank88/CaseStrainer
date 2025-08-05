<template>
  <div style="background: orange; color: black; padding: 40px; text-align: center; font-size: 32px; font-weight: bold;">
    🟠 MINIMAL TEST COMPONENT - If you see this, Vue template rendering works! 🟠
  </div>
</template>

<script>
export default {
  name: 'MinimalTest',
  setup() {
    alert('🟠 MinimalTest setup() called!');
  }
}
</script>