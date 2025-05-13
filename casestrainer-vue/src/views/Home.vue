<template>
  <div class="home">
    <div class="jumbotron bg-light p-4 mb-4 rounded">
      <h1 class="display-5">Welcome to CaseStrainer</h1>
      <p class="lead">
        CaseStrainer helps legal professionals verify case citations in legal documents.
        It uses multiple verification sources to identify unconfirmed or hallucinated citations.
      </p>
      <div class="d-grid gap-2 d-md-flex justify-content-md-start mt-3">
        <router-link to="/enhanced-validator" class="btn btn-primary btn-lg px-4 me-md-2">Try Enhanced Validator</router-link>
        <router-link to="/unconfirmed-citations" class="btn btn-outline-secondary btn-lg px-4">View Unconfirmed Citations</router-link>
      </div>
      <hr class="my-4">
    </div>
    
    <!-- Tabbed Interface -->
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
            <EnhancedFileUpload />
          </div>
          <div 
            class="tab-pane fade" 
            id="paste" 
            role="tabpanel" 
            aria-labelledby="paste-tab"
          >
            <EnhancedTextPaste />
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
    
    <div class="row mb-4">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">Recent Updates</h5>
          </div>
          <div class="card-body">
            <ul class="list-group list-group-flush">
              <li class="list-group-item d-flex justify-content-between align-items-center">
                Added Citation Network Visualization
                <span class="badge bg-primary rounded-pill">New</span>
              </li>
              <li class="list-group-item d-flex justify-content-between align-items-center">
                Improved Multi-source Verification
                <span class="badge bg-success rounded-pill">Updated</span>
              </li>
              <li class="list-group-item d-flex justify-content-between align-items-center">
                Machine Learning Citation Classifier
                <span class="badge bg-primary rounded-pill">New</span>
              </li>
              <li class="list-group-item d-flex justify-content-between align-items-center">
                Enhanced Citation Tester
                <span class="badge bg-success rounded-pill">Updated</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <!-- Enhanced Validator Card -->
        <div class="card mb-4">
          <div class="card-header bg-primary text-white">
            <h5 class="mb-0">Enhanced Citation Validator</h5>
          </div>
          <div class="card-body">
            <p class="card-text">Our newest tool provides advanced citation validation with:</p>
            <ul>
              <li>Context-aware validation</li>
              <li>ML-powered classification</li>
              <li>Intelligent correction suggestions</li>
            </ul>
            <div class="d-grid gap-2">
              <router-link to="/enhanced-validator" class="btn btn-primary">Try Enhanced Validator</router-link>
            </div>
          </div>
        </div>
        
        <!-- Quick Stats Card -->
        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">Quick Stats</h5>
          </div>
          <div class="card-body">
            <div class="row text-center">
              <div class="col-6 mb-3">
                <h3>100+</h3>
                <p class="text-muted">Unconfirmed Citations</p>
              </div>
              <div class="col-6 mb-3">
                <h3>50+</h3>
                <p class="text-muted">Confirmed with Multitool</p>
              </div>
              <div class="col-6">
                <h3>95%</h3>
                <p class="text-muted">ML Classifier Accuracy</p>
              </div>
              <div class="col-6">
                <h3>5</h3>
                <p class="text-muted">Verification Sources</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import FileUpload from '@/components/FileUpload.vue';
import TextPaste from '@/components/TextPaste.vue';
import EnhancedFileUpload from '@/components/EnhancedFileUpload.vue';
import EnhancedTextPaste from '@/components/EnhancedTextPaste.vue';
import MultitoolConfirmed from '@/components/MultitoolConfirmed.vue';
import UnconfirmedCitations from '@/components/UnconfirmedCitations.vue';

export default {
  name: 'Home',
  components: {
    FileUpload,
    TextPaste,
    EnhancedFileUpload,
    EnhancedTextPaste,
    MultitoolConfirmed,
    UnconfirmedCitations
  },
  mounted() {
    // Initialize Bootstrap tabs
    // This ensures the tabs work properly
    const triggerTabList = document.querySelectorAll('#citation-tabs button');
    triggerTabList.forEach(triggerEl => {
      triggerEl.addEventListener('click', event => {
        event.preventDefault();
        // Get the tab target
        const tabTarget = document.querySelector(triggerEl.dataset.bsTarget);
        // If we have a tab target, activate it
        if (tabTarget) {
          // Remove active class from all tabs
          triggerTabList.forEach(t => {
            t.classList.remove('active');
            t.setAttribute('aria-selected', 'false');
          });
          // Add active class to clicked tab
          triggerEl.classList.add('active');
          triggerEl.setAttribute('aria-selected', 'true');
          
          // Hide all tab panes
          const tabPanes = document.querySelectorAll('.tab-pane');
          tabPanes.forEach(p => {
            p.classList.remove('show', 'active');
          });
          
          // Show the target tab pane
          tabTarget.classList.add('show', 'active');
        }
      });
    });
    
    // Check if there's a hash in the URL to activate a specific tab
    const hash = window.location.hash.substring(1);
    if (hash) {
      const tab = document.querySelector(`#${hash}-tab`);
      if (tab) {
        tab.click();
      }
    }
  }
}
</script>
