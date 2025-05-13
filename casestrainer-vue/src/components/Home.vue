<template>
  <div class="home">
    <div class="card">
      <div class="card-header">
        <ul class="nav nav-tabs card-header-tabs" id="citation-tabs" role="tablist">
          <li class="nav-item" role="presentation">
            <button 
              class="nav-link active" 
              id="upload-tab" 
              data-bs-toggle="tab" 
              data-bs-target="#upload" 
              type="button" 
              role="tab" 
              aria-controls="upload" 
              aria-selected="true"
            >
              Upload File
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button 
              class="nav-link" 
              id="paste-tab" 
              data-bs-toggle="tab" 
              data-bs-target="#paste" 
              type="button" 
              role="tab" 
              aria-controls="paste" 
              aria-selected="false"
            >
              Paste Text
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button 
              class="nav-link" 
              id="multitool-tab" 
              data-bs-toggle="tab" 
              data-bs-target="#multitool" 
              type="button" 
              role="tab" 
              aria-controls="multitool" 
              aria-selected="false"
            >
              Verified with Multi-tool
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button 
              class="nav-link" 
              id="unconfirmed-tab" 
              data-bs-toggle="tab" 
              data-bs-target="#unconfirmed" 
              type="button" 
              role="tab" 
              aria-controls="unconfirmed" 
              aria-selected="false"
            >
              Unconfirmed Citations
            </button>
          </li>
        </ul>
      </div>
      <div class="card-body">
        <div class="tab-content" id="citation-tabs-content">
          <div 
            class="tab-pane fade show active" 
            id="upload" 
            role="tabpanel" 
            aria-labelledby="upload-tab"
          >
            <FileUpload />
          </div>
          <div 
            class="tab-pane fade" 
            id="paste" 
            role="tabpanel" 
            aria-labelledby="paste-tab"
          >
            <TextPaste />
          </div>
          <div 
            class="tab-pane fade" 
            id="multitool" 
            role="tabpanel" 
            aria-labelledby="multitool-tab"
          >
            <MultitoolConfirmed />
          </div>
          <div 
            class="tab-pane fade" 
            id="unconfirmed" 
            role="tabpanel" 
            aria-labelledby="unconfirmed-tab"
          >
            <UnconfirmedCitations />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import FileUpload from './FileUpload.vue';
import TextPaste from './TextPaste.vue';
import MultitoolConfirmed from './MultitoolConfirmed.vue';
import UnconfirmedCitations from './UnconfirmedCitations.vue';

export default {
  name: 'Home',
  components: {
    FileUpload,
    TextPaste,
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
