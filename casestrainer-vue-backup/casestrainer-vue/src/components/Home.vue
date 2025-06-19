<template>
  <div class="home">
    <div class="card">
      <div class="card-header">
        <h5 class="mb-0">Citation Analyzer (Legacy)</h5>
      </div>
      <div class="card-body">
        <div class="alert alert-info mb-3">
          <strong>Note:</strong> Please use the main Home page for the new unified input interface.
        </div>
        <MultitoolConfirmed />
        <UnconfirmedCitations />
      </div>
    </div>
  </div>
</template>

<script>
import MultitoolConfirmed from './MultitoolConfirmed.vue';
import UnconfirmedCitations from './UnconfirmedCitations.vue';

export default {
  name: 'Home',
  components: {
    MultitoolConfirmed,
    UnconfirmedCitations
  },
  mounted() {
    // Check if there's a tab to activate from the URL hash
    const hash = window.location.hash.substring(1);
    if (hash) {
      const tabId = `${hash}-tab`;
      const tab = document.getElementById(tabId);
      if (tab) {
        tab.click();
      }
    }
  }
};
</script>

<style scoped>
.home {
  margin-bottom: 2rem;
}
</style>
