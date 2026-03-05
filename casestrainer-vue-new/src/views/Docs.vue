<template>
  <div class="docs-page">
    <h1>CaseStrainer Documentation</h1>
    <p>Comprehensive guides and documentation for using CaseStrainer's citation processing system.</p>

    <div class="docs-section">
      <h2><i class="bi bi-link-45deg me-2"></i>Live Application</h2>
      <ul class="docs-list">
        <li>
          <a href="https://wolf.law.uw.edu/casestrainer/" target="_blank" rel="noopener">
            <i class="bi bi-globe me-2"></i>
            <div>
              <strong>CaseStrainer on the Web</strong>
              <p class="text-muted mb-0">Use CaseStrainer at https://wolf.law.uw.edu/casestrainer/ — upload documents, paste text, or enter URLs to analyze and verify citations.</p>
            </div>
          </a>
        </li>
      </ul>
    </div>
    
    <div class="docs-section">
      <h2><i class="bi bi-book-half me-2"></i>User Guides</h2>
      <ul class="docs-list">
        <li>
          <router-link to="/docs/pipeline">
            <i class="bi bi-diagram-3 me-2"></i>
            <div>
              <strong>Processing Pipeline Guide</strong>
              <p class="text-muted mb-0">Learn how CaseStrainer processes citations through its 6-phase pipeline</p>
            </div>
          </router-link>
        </li>
        <li>
          <a href="https://github.com/jafrank88/casestrainer/blob/main/README.md" target="_blank">
            <i class="bi bi-file-text me-2"></i>
            <div>
              <strong>Getting Started Guide</strong>
              <p class="text-muted mb-0">Installation, setup, and basic usage instructions</p>
            </div>
          </a>
        </li>
      </ul>
    </div>

    <div class="docs-section">
      <h2><i class="bi bi-code-square me-2"></i>Developer Documentation</h2>
      <ul class="docs-list">
        <li>
          <router-link to="/docs/api">
            <i class="bi bi-code-slash me-2"></i>
            <div>
              <strong>API Documentation</strong>
              <p class="text-muted mb-0">REST API endpoints, request/response formats, and integration examples</p>
            </div>
          </router-link>
        </li>
        <li>
          <a href="https://github.com/jafrank88/casestrainer/tree/main/docs" target="_blank">
            <i class="bi bi-github me-2"></i>
            <div>
              <strong>GitHub Documentation</strong>
              <p class="text-muted mb-0">Additional technical documentation and development guides</p>
            </div>
          </a>
        </li>
      </ul>
    </div>

    <div class="docs-section">
      <h2><i class="bi bi-puzzle me-2"></i>Integrations</h2>
      <ul class="docs-list">
        <li>
          <router-link to="/word-plugin">
            <i class="bi bi-file-word me-2"></i>
            <div>
              <strong>Microsoft Word Add-In</strong>
              <p class="text-muted mb-0">Validate citations directly in Word documents</p>
            </div>
          </router-link>
        </li>
        <li>
          <router-link to="/browser-extension">
            <i class="bi bi-browser-chrome me-2"></i>
            <div>
              <strong>Browser Extension</strong>
              <p class="text-muted mb-0">Validate citations on any webpage</p>
            </div>
          </router-link>
        </li>
      </ul>
    </div>

    <div class="text-center mt-4">
      <router-link to="/" class="btn btn-outline-primary">
        <i class="bi bi-house me-2"></i>Back to Home
      </router-link>
    </div>
  </div>
</template>

<script setup>
// No script needed for simple docs hub
</script>

<style scoped>
.docs-page {
  max-width: 800px;
  margin: 2rem auto;
  padding: 2rem;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.docs-page h1 {
  margin-bottom: 0.5rem;
  color: #2c3e50;
  text-align: left;
}

.docs-page > p {
  color: #6c757d;
  margin-bottom: 2rem;
  text-align: left;
}

.docs-section {
  margin-bottom: 2.5rem;
}

.docs-section h2 {
  font-size: 1.5rem;
  color: #495057;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e9ecef;
  text-align: left;
}

.docs-list {
  list-style: none;
  padding: 0;
}

.docs-list li {
  margin: 1rem 0;
}

.docs-list a {
  display: flex;
  align-items: flex-start;
  padding: 1rem;
  border-radius: 8px;
  background: #f8f9fa;
  text-decoration: none;
  color: #212529;
  transition: all 0.2s;
  border: 1px solid #e9ecef;
}

.docs-list a:hover {
  background: #e9ecef;
  border-color: #007bff;
  transform: translateX(4px);
  text-decoration: none;
}

.docs-list a i {
  font-size: 1.5rem;
  color: #007bff;
  flex-shrink: 0;
}

.docs-list a strong {
  display: block;
  color: #212529;
  margin-bottom: 0.25rem;
}

.docs-list a .text-muted {
  font-size: 0.9rem;
  color: #6c757d !important;
}

/* Mobile Responsive Design */
@media (max-width: 768px) {
  .docs-page {
    margin: 1rem auto;
    padding: 1.5rem;
    max-width: 100%;
  }
  
  .docs-page h1 {
    font-size: 1.75rem;
  }
  
  .docs-page p {
    font-size: 1rem;
  }
  
  .docs-list li {
    margin: 0.75rem 0;
    font-size: 1rem;
  }
  
  .docs-list a {
    display: block;
    padding: 0.75rem;
    border-radius: 6px;
    background: #f8f9fa;
    transition: background-color 0.2s;
    min-height: 44px;
    display: flex;
    align-items: center;
  }
  
  .docs-list a:hover {
    background: #e9ecef;
    text-decoration: none;
  }
}

@media (max-width: 480px) {
  .docs-page {
    margin: 0.5rem auto;
    padding: 1rem;
  }
  
  .docs-page h1 {
    font-size: 1.5rem;
  }
  
  .docs-page p {
    font-size: 0.95rem;
  }
  
  .docs-list li {
    margin: 0.5rem 0;
    font-size: 0.95rem;
  }
  
  .docs-list a {
    padding: 0.5rem;
    font-size: 0.9rem;
  }
}

/* Touch-friendly improvements */
@media (hover: none) and (pointer: coarse) {
  .docs-list a {
    min-height: 44px;
  }
  
  /* Remove hover effects on touch devices */
  .docs-list a:hover {
    background: #f8f9fa;
  }
}
</style> 