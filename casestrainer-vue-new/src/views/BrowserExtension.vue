<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-lg-10">
        <h1 class="display-4 mb-3 text-center">
          <i class="bi bi-puzzle me-2"></i> CaseStrainer Browser Extension
        </h1>
        <p class="lead mb-4 text-center">
          Verify legal citations in real-time while browsing legal websites, court opinions, and legal documents.
        </p>

        <!-- Status Alert -->
        <div class="alert alert-warning mb-4">
          <h4 class="mb-2"><i class="bi bi-info-circle me-2"></i> Planned Feature</h4>
          <p class="mb-0">
            The CaseStrainer Browser Extension is currently in the planning phase. We're working on bringing 
            real-time citation verification to Chrome, Firefox, and Safari. Follow our development progress on 
            <a href="https://github.com/jafrank88/casestrainer" target="_blank" class="alert-link">GitHub</a>.
          </p>
        </div>

        <!-- Features Section -->
        <div class="card mb-4">
          <div class="card-header bg-primary text-white">
            <h3 class="mb-0"><i class="bi bi-star me-2"></i> Planned Features</h3>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-md-6 mb-3">
                <h5><i class="bi bi-check-circle text-success me-2"></i> Real-Time Verification</h5>
                <ul>
                  <li>Automatic citation detection on web pages</li>
                  <li>Visual indicators for verified/unverified citations</li>
                  <li>Hover information without leaving the page</li>
                  <li>Quick access to case details</li>
                </ul>
              </div>
              <div class="col-md-6 mb-3">
                <h5><i class="bi bi-globe me-2"></i> Supported Websites</h5>
                <ul>
                  <li>CourtListener and Google Scholar</li>
                  <li>Justia and FindLaw</li>
                  <li>Law school websites</li>
                  <li>Any page with legal citations</li>
                </ul>
              </div>
              <div class="col-md-6 mb-3">
                <h5><i class="bi bi-cloud-arrow-down me-2"></i> Export Options</h5>
                <ul>
                  <li>Save verified citations to your account</li>
                  <li>Export to BibTeX and EndNote</li>
                  <li>Generate citation reports</li>
                  <li>Batch verification support</li>
                </ul>
              </div>
              <div class="col-md-6 mb-3">
                <h5><i class="bi bi-shield-check me-2"></i> Privacy & Security</h5>
                <ul>
                  <li>No browsing history tracking</li>
                  <li>Local citation detection</li>
                  <li>Secure HTTPS API calls</li>
                  <li>No external data storage</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- Browser Support -->
        <div class="card mb-4">
          <div class="card-header bg-info text-white">
            <h3 class="mb-0"><i class="bi bi-browser-chrome me-2"></i> Planned Browser Support</h3>
          </div>
          <div class="card-body">
            <div class="row text-center">
              <div class="col-md-4">
                <i class="bi bi-browser-chrome" style="font-size: 3rem; color: #4285F4;"></i>
                <h5 class="mt-2">Chrome & Edge</h5>
                <p class="text-muted">Chromium-based browsers</p>
              </div>
              <div class="col-md-4">
                <i class="bi bi-browser-firefox" style="font-size: 3rem; color: #FF7139;"></i>
                <h5 class="mt-2">Firefox</h5>
                <p class="text-muted">Mozilla Firefox browser</p>
              </div>
              <div class="col-md-4">
                <i class="bi bi-browser-safari" style="font-size: 3rem; color: #006CFF;"></i>
                <h5 class="mt-2">Safari</h5>
                <p class="text-muted">Apple Safari browser</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Development Roadmap -->
        <div class="card mb-4">
          <div class="card-header bg-success text-white">
            <h3 class="mb-0"><i class="bi bi-calendar-check me-2"></i> Development Roadmap</h3>
          </div>
          <div class="card-body">
            <div class="timeline">
              <div class="mb-3">
                <h5>Phase 1: Core Features (Q1-Q2 2026)</h5>
                <ul>
                  <li>Basic citation detection</li>
                  <li>CourtListener API integration</li>
                  <li>Visual highlighting</li>
                  <li>Chrome/Edge support</li>
                </ul>
              </div>
              <div class="mb-3">
                <h5>Phase 2: Enhanced Features (Q3 2026)</h5>
                <ul>
                  <li>Firefox support</li>
                  <li>Advanced filtering options</li>
                  <li>Citation export functionality</li>
                  <li>Custom verification rules</li>
                </ul>
              </div>
              <div class="mb-3">
                <h5>Phase 3: Advanced Features (Q4 2026)</h5>
                <ul>
                  <li>Safari support</li>
                  <li>Batch verification</li>
                  <li>Citation reports</li>
                  <li>Team collaboration features</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- Documentation & Contributing -->
        <div class="card mb-4">
          <div class="card-header bg-secondary text-white">
            <h3 class="mb-0"><i class="bi bi-book me-2"></i> Documentation & Contributing</h3>
          </div>
          <div class="card-body">
            <p>
              Interested in the browser extension development? Check out our comprehensive documentation 
              and contributing guidelines:
            </p>
            <div class="list-group">
              <a href="https://github.com/jafrank88/casestrainer/tree/main/docs/BROWSER_EXTENSION.md" 
                 target="_blank" 
                 class="list-group-item list-group-item-action">
                <i class="bi bi-file-text me-2"></i> Complete Browser Extension Documentation
              </a>
              <a href="https://github.com/jafrank88/casestrainer" 
                 target="_blank" 
                 class="list-group-item list-group-item-action">
                <i class="bi bi-github me-2"></i> GitHub Repository
              </a>
              <a href="https://github.com/jafrank88/casestrainer/issues" 
                 target="_blank" 
                 class="list-group-item list-group-item-action">
                <i class="bi bi-bug me-2"></i> Report Issues or Request Features
              </a>
              <a href="https://github.com/jafrank88/casestrainer/discussions" 
                 target="_blank" 
                 class="list-group-item list-group-item-action">
                <i class="bi bi-chat-dots me-2"></i> Join the Discussion
              </a>
            </div>
          </div>
        </div>

        <!-- Call to Action -->
        <div class="text-center">
          <router-link to="/" class="btn btn-primary btn-lg me-2">
            <i class="bi bi-house-door me-1"></i> Back to Home
          </router-link>
          <a href="https://github.com/jafrank88/casestrainer" 
             target="_blank" 
             class="btn btn-outline-secondary btn-lg">
            <i class="bi bi-github me-1"></i> View on GitHub
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BrowserExtension'
}
</script>

<style scoped>
.display-4 {
  font-weight: 700;
}
</style> 