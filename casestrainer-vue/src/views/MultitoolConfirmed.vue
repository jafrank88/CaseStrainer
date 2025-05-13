<template>
  <div class="multitool-confirmed">
    <h2>Confirmed with Multitool</h2>
    <p class="lead">
      These citations were confirmed using our multi-source verification system but could not be verified through CourtListener.
      This demonstrates the power of our enhanced verification approach.
    </p>
    
    <MultitoolConfirmed />
  </div>
</template>

<script>
import MultitoolConfirmed from '@/components/MultitoolConfirmed.vue';

export default {
  name: 'MultitoolConfirmedView',
  components: {
    MultitoolConfirmed
  }
}
</script>

<style scoped>
.multitool-confirmed {
  margin-bottom: 2rem;
}
</style>
