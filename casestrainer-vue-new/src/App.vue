<template>
  <div id="app">
    <a href="#main-content" class="skip-link" @click="focusMainContent">Skip to main content</a>
    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg navbar-dark navbar-app-shell" aria-label="Primary">
      <div class="container-lg">
        <router-link class="navbar-brand" to="/" aria-label="CaseStrainer home">
          <i class="bi bi-journal-check me-2" aria-hidden="true"></i>
          <span class="d-none d-sm-inline">CaseStrainer</span>
          <span class="d-inline d-sm-none" aria-hidden="true">CS</span>
        </router-link>
        <div class="header-banner mt-1">
          <span class="header-banner-text">
            Free, Open-Source, and No Generative AI - Experimental - Use at Your Own Risk
          </span>
        </div>
        <button 
          class="navbar-toggler" 
          type="button" 
          data-bs-toggle="collapse" 
          data-bs-target="#navbarNav"
          aria-controls="navbarNav" 
          :aria-expanded="navMenuExpanded" 
          aria-label="Toggle navigation menu"
        >
          <span class="navbar-toggler-icon" aria-hidden="true"></span>
        </button>
        <div ref="navCollapse" class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <router-link class="nav-link" to="/" aria-label="Home">
                <i class="bi bi-house-door me-1" aria-hidden="true"></i> 
                <span class="d-none d-md-inline">Home</span>
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/docs" aria-label="Documentation">
                <i class="bi bi-journal-bookmark me-1" aria-hidden="true"></i>
                <span class="d-none d-md-inline">Docs</span>
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/docs/api" aria-label="API documentation">
                <i class="bi bi-code-slash me-1" aria-hidden="true"></i>
                <span class="d-none d-md-inline">API Docs</span>
              </router-link>
            </li>
            <li class="nav-item d-none d-lg-block">
              <router-link class="nav-link" to="/browser-extension">
                <i class="bi bi-puzzle me-1" aria-hidden="true"></i> Browser Extension
              </router-link>
            </li>
            <li class="nav-item d-none d-lg-block">
              <router-link class="nav-link" to="/word-plugin">
                <i class="bi bi-file-earmark-word me-1" aria-hidden="true"></i> Word Plug-in
              </router-link>
            </li>
          </ul>
          <div class="d-flex align-items-center">
            <span class="navbar-text text-light me-2 d-none d-sm-inline">
              v{{ appVersion }}
            </span>
            <a 
              href="https://github.com/jafrank88/casestrainer" 
              target="_blank" 
              rel="noopener noreferrer"
              class="btn btn-outline-light btn-sm"
              aria-label="CaseStrainer on GitHub (opens in new tab)"
            >
              <i class="bi bi-github me-1" aria-hidden="true"></i>
              <span class="d-none d-sm-inline">GitHub</span>
            </a>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main id="main-content" class="container-fluid container-lg py-3 py-md-4" tabindex="-1">
      <ErrorBoundary>
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </ErrorBoundary>
    </main>

    <!-- Footer -->
    <footer class="bg-light py-4 mt-5" role="contentinfo" aria-label="Site footer">
      <div class="container-lg">
        <div class="row g-4">
          <div class="col-12 col-md-6">
            <h5>About CaseStrainer</h5>
            <p class="text-muted">
              A powerful tool for legal professionals to validate, analyze, and manage legal citations.
            </p>
          </div>
          <div class="col-6 col-md-3">
            <h5>Quick Links</h5>
            <ul class="list-unstyled">
              <li><router-link to="/" class="text-decoration-none">Home</router-link></li>
              <li><router-link to="/docs" class="text-decoration-none">Docs</router-link></li>
              <li><router-link to="/docs/api" class="text-decoration-none">API Documentation</router-link></li>
              <li><router-link to="/browser-extension" class="text-decoration-none">Browser Extension</router-link></li>
              <li><router-link to="/word-plugin" class="text-decoration-none">Word Plug-in</router-link></li>
            </ul>
          </div>
          <div class="col-6 col-md-3">
            <h5>Resources</h5>
            <ul class="list-unstyled">
              <li><a href="https://wolf.law.uw.edu/casestrainer/" class="text-decoration-none" target="_blank" rel="noopener noreferrer">CaseStrainer (wolf.law.uw.edu) <span class="visually-hidden">(opens in new tab)</span></a></li>
              <li><a href="https://github.com/jafrank88/casestrainer" class="text-decoration-none" target="_blank" rel="noopener noreferrer">GitHub Repository <span class="visually-hidden">(opens in new tab)</span></a></li>
              <li><a href="mailto:jafrank@uw.edu?subject=CaseStrainer%20feedback" class="footer-link">Report an issue</a></li>
            </ul>
          </div>
        </div>
        <hr>
        <div class="text-center text-muted">
          <p class="mb-0">&copy; {{ currentYear }} CaseStrainer. All rights reserved.</p>
          <small>v{{ appVersion }}</small>
        </div>
      </div>
    </footer>

    <!-- Toast Notifications -->
    <div class="position-fixed bottom-0 end-0 p-3" style="z-index: 11">
      <div class="toast-container">
        <!-- Toasts will be dynamically inserted here -->
      </div>
    </div>
  </div>
</template>

<script>
import ErrorBoundary from '@/components/ErrorBoundary.vue';

export default {
  name: 'App',
  components: {
    ErrorBoundary
  },
  data() {
    return {
      appVersion: typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '0.0.0',
      currentYear: new Date().getFullYear(),
      navMenuExpanded: false
    }
  },

  mounted() {
    this.$nextTick(() => this.attachNavbarCollapseListeners())
  },

  beforeUnmount() {
    const el = this.$refs.navCollapse
    if (el && this._navShownHandler) {
      el.removeEventListener('shown.bs.collapse', this._navShownHandler)
      el.removeEventListener('hidden.bs.collapse', this._navHiddenHandler)
    }
  },

  methods: {
    focusMainContent() {
      this.$nextTick(() => {
        const main = document.getElementById('main-content')
        if (main) {
          main.focus({ preventScroll: false })
        }
      })
    },
    attachNavbarCollapseListeners() {
      const el = this.$refs.navCollapse
      if (!el) return
      this.navMenuExpanded = el.classList.contains('show')
      this._navShownHandler = () => { this.navMenuExpanded = true }
      this._navHiddenHandler = () => { this.navMenuExpanded = false }
      el.addEventListener('shown.bs.collapse', this._navShownHandler)
      el.addEventListener('hidden.bs.collapse', this._navHiddenHandler)
    }
  }

}
</script>

<style>
/* Skip link (2.4.1 Bypass Blocks) */
.skip-link {
  position: absolute;
  left: -9999px;
  top: 0;
  z-index: 10000;
  padding: 0.5rem 1rem;
  background: #fff;
  color: #212529;
  font-weight: 600;
  border-radius: 0 0 0.25rem 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  text-decoration: none;
}
.skip-link:focus {
  left: 0;
  outline: 3px solid #b45309;
  outline-offset: 2px;
}

/* Darker header gradient + link colors: WCAG AA contrast vs white text (~4.5:1) */
.navbar-app-shell {
  background: linear-gradient(90deg, #2a1a48 0%, #3a2460 55%, #322056 100%);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

/* Focus visibility + scroll padding (2.4.11 Focus Not Obscured–friendly) */
html {
  scroll-padding-top: 1.25rem;
}

:focus-visible {
  outline: 3px solid #0d6efd;
  outline-offset: 3px;
}

.navbar-app-shell :focus-visible {
  outline-color: #ffc107;
  outline-offset: 3px;
}

.navbar-app-shell .btn-outline-light:focus-visible {
  outline-color: #fff;
  box-shadow: 0 0 0 3px #ffc107;
}

#main-content:focus-visible {
  outline: 2px solid rgba(107, 70, 193, 0.55);
  outline-offset: 0;
  box-shadow:
    0 0 0 5px rgba(107, 70, 193, 0.10),
    0 0 18px 2px rgba(107, 70, 193, 0.08);
  border-radius: 2px;
  transition: outline 0.15s ease, box-shadow 0.15s ease;
}

/* Base styles */
:root {
  --primary-color: #0d6efd;
  --secondary-color: #6c757d;
  --success-color: #198754;
  --danger-color: #dc3545;
  --warning-color: #ffc107;
  --light-color: #f8f9fa;
  --dark-color: #212529;
}

/* Smooth scrolling */
html {
  scroll-behavior: smooth;
}

/* Layout */
#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}

main {
  flex: 1 0 auto;
  scroll-margin-top: 1.25rem;
}

/* Navigation */
.navbar {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.navbar-brand {
  font-weight: 700;
  font-size: 1.5rem;
}

.nav-link {
  font-weight: 500;
  padding: 0.5rem 1rem !important;
  border-radius: 0.25rem;
  transition: all 0.2s ease-in-out;
  min-height: 44px; /* Touch target minimum */
  display: flex;
  align-items: center;
}

.nav-link:hover, .nav-link:focus {
  background-color: rgba(255, 255, 255, 0.1);
}

.nav-link.router-link-exact-active {
  font-weight: 600;
  color: white !important;
  background-color: rgba(255, 255, 255, 0.15);
}

/* Buttons */
.btn {
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  transition: all 0.2s ease-in-out;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-height: 44px; /* Touch target minimum */
  min-width: 44px; /* Touch target minimum */
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
  min-height: 36px; /* Smaller touch target for small buttons */
  min-width: 36px;
}

/* Mobile-specific improvements */
@media (max-width: 768px) {
  /* Typography */
  h1 { font-size: 1.75rem; }
  h2 { font-size: 1.5rem; }
  h3 { font-size: 1.25rem; }
  h4 { font-size: 1.125rem; }
  h5 { font-size: 1rem; }
  
  /* Spacing */
  .container {
    padding-left: 1rem;
    padding-right: 1rem;
  }
  
  /* Navigation */
  .navbar-nav {
    margin-top: 1rem;
  }
  
  .nav-link {
    padding: 0.75rem 1rem !important;
    border-radius: 0.375rem;
    margin-bottom: 0.25rem;
  }
  
  /* Buttons */
  .btn {
    padding: 0.75rem 1rem;
    font-size: 1rem;
    width: 100%;
    margin-bottom: 0.5rem;
  }
  
  .btn-sm {
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
  }
  
  /* Cards */
  .card {
    margin-bottom: 1rem;
  }
  
  .card-body {
    padding: 1rem;
  }
  
  /* Tables */
  .table-responsive {
    border: 0;
    margin: 0 -1rem;
  }
  
  /* Footer */
  footer {
    text-align: center;
  }
  
  footer .col-6 {
    margin-bottom: 1rem;
  }
}

/* Tablet improvements */
@media (min-width: 769px) and (max-width: 1024px) {
  .container {
    max-width: 100%;
    padding-left: 2rem;
    padding-right: 2rem;
  }
  
  .btn {
    min-height: 40px;
  }
}

/* Large screen improvements */
@media (min-width: 1025px) {
  .container {
    max-width: 1200px;
  }
}

/* Touch improvements */
@media (hover: none) and (pointer: coarse) {
  /* Larger touch targets for touch devices */
  .btn {
    min-height: 48px;
    min-width: 48px;
  }
  
  .nav-link {
    min-height: 48px;
  }
  
  /* Remove hover effects on touch devices */
  .btn:hover, .nav-link:hover {
    transform: none;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  :root {
    --light-color: #1e2228;
    --dark-color: #e9ecef;
  }

  body {
    background: var(--background, #18181b);
    color: var(--foreground, #f3f4f6);
  }

  #app {
    background: var(--background, #18181b);
    color: var(--foreground, #f3f4f6);
  }

  main {
    background: transparent;
    color: var(--foreground, #f3f4f6);
  }

  .bg-light {
    background-color: var(--light-color) !important;
    color: var(--dark-color);
  }

  .text-muted {
    color: #94a3b8 !important;
  }

  footer.bg-light h5 {
    color: #f1f5f9 !important;
  }

  footer.bg-light .text-muted {
    color: #94a3b8 !important;
  }

  footer.bg-light a {
    color: var(--primary, #60a5fa);
  }

  .results-section-header {
    background: linear-gradient(135deg, #252830 0%, #1e2228 100%);
    border-left-color: #c4a8fc;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
  }

  .results-title {
    color: #f1f5f9;
  }

  .results-subtitle {
    color: #94a3b8;
  }

  .results-section-header .bi {
    color: #c4a8fc;
  }

  .route-mismatch {
    background: #252830;
    border-color: #3d4451;
  }

  .route-mismatch-message {
    color: #94a3b8;
  }
}

/* Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* Utility classes */
.hover-shadow {
  transition: box-shadow 0.2s ease-in-out;
}

.hover-shadow:hover {
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
}

.transition-all {
  transition: all 0.2s ease-in-out;
}

/* Accessibility improvements */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  
  html {
    scroll-behavior: auto;
  }
}

.header-banner {
  margin-top: 0.25rem;
}
.header-banner-text {
  color: #ffffff;
  background: rgba(15, 8, 28, 0.72);
  border-radius: 0.5rem;
  padding: 0.2rem 0.85rem;
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
  display: inline-block;
  border: 1px solid rgba(255, 255, 255, 0.2);
}
.navbar-app-shell .navbar-brand,
.navbar-app-shell .navbar-brand :not(.visually-hidden) {
  color: #ffffff !important;
}
.navbar-app-shell .navbar-text {
  color: #f5f3ff !important;
}
.navbar-app-shell .nav-link {
  color: #ffffff !important;
  opacity: 1;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.35);
}
.navbar-app-shell .nav-link:hover,
.navbar-app-shell .nav-link:focus-visible {
  color: #ffffff !important;
  background-color: rgba(255, 255, 255, 0.12) !important;
}
.navbar-app-shell .nav-link.router-link-exact-active {
  font-weight: 700;
  color: #ffffff !important;
  background: rgba(255, 255, 255, 0.18) !important;
}
.navbar-app-shell .btn-outline-light {
  color: #ffffff !important;
  border-color: rgba(255, 255, 255, 0.85) !important;
}
.navbar-app-shell .btn-outline-light:hover,
.navbar-app-shell .btn-outline-light:focus-visible {
  color: #1e1b2e !important;
  background-color: #ffffff !important;
  border-color: #ffffff !important;
}

/* Results Section Headers */
.results-section-header {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 0.75rem;
  border-left: 4px solid #4b2e83;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.results-title {
  color: #4b2e83;
  font-size: 1.75rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
}

.results-subtitle {
  color: #6c757d;
  font-size: 1rem;
  margin-bottom: 0;
  font-style: italic;
}

.results-section-header .bi {
  color: #6a4c93;
}

/* Route mismatch message */
.route-mismatch {
  padding: 2rem;
  text-align: center;
  background: #f8f9fa;
  border-radius: 0.75rem;
  border: 2px dashed #dee2e6;
}

.route-mismatch-message {
  color: #6c757d;
  font-size: 1.1rem;
  font-weight: 500;
}

.route-mismatch .bi {
  color: #ffc107;
}
</style>