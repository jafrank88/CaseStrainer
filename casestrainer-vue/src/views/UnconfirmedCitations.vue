<template>
  <div class="unconfirmed-citations">
    <h2>Unconfirmed Citations</h2>
    <p class="lead">These citations could not be verified through standard legal databases or AI verification.</p>
    
    <UnconfirmedCitations />
              <select 
  </div>
</template>

<script>
import UnconfirmedCitations from '@/components/UnconfirmedCitations.vue';

export default {
  name: 'UnconfirmedCitationsView',
  components: {
    UnconfirmedCitations
  }
}
</script>

<style scoped>
.unconfirmed-citations {
  margin-bottom: 2rem;
}
</style>
