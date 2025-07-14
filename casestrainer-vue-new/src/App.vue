<template>
  <div id="app">
    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg navbar-dark" style="background: linear-gradient(90deg, #4b2e83 60%, #6a4c93 100%);">
      <div class="container">
        <router-link class="navbar-brand" to="/">
          <i class="bi bi-journal-check me-2"></i>
          <span class="d-none d-sm-inline">CaseStrainer</span>
          <span class="d-inline d-sm-none">CS</span>
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
          aria-expanded="false" 
          aria-label="Toggle navigation"
        >
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <router-link class="nav-link" to="/">
                <i class="bi bi-house-door me-1"></i> 
                <span class="d-none d-md-inline">Home</span>
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/docs">
                <i class="bi bi-journal-bookmark me-1"></i>
                <span class="d-none d-md-inline">Docs</span>
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/docs/api">
                <i class="bi bi-code-slash me-1"></i>
                <span class="d-none d-md-inline">API Docs</span>
              </router-link>
            </li>
            <li class="nav-item d-none d-lg-block">
              <router-link class="nav-link" to="/browser-extension">
                <i class="bi bi-puzzle me-1"></i> Browser Extension
              </router-link>
            </li>
            <li class="nav-item d-none d-lg-block">
              <router-link class="nav-link" to="/word-plugin">
                <i class="bi bi-file-earmark-word me-1"></i> Word Plug-in
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
              class="btn btn-outline-light btn-sm"
            >
              <i class="bi bi-github me-1"></i>
              <span class="d-none d-sm-inline">GitHub</span>
            </a>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="container-fluid container-lg py-3 py-md-4">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Footer -->
    <footer class="bg-light py-4 mt-5">
      <div class="container">
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
            </ul>
          </div>
          <div class="col-6 col-md-3">
            <h5>Resources</h5>
            <ul class="list-unstyled">
              <li><a href="https://github.com/jafrank88/casestrainer" class="text-decoration-none" target="_blank">GitHub Repository</a></li>
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
export default {
  name: 'App',
  data() {
    return {
      appVersion: typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '0.0.0',
      currentYear: new Date().getFullYear()
    }
  }
}
</script>

<style>
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
    --light-color: #2c3034;
    --dark-color: #e9ecef;
  }
  
  .bg-light {
    background-color: var(--light-color) !important;
    color: var(--dark-color);
  }
  
  .text-muted {
    color: #adb5bd !important;
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
  color: #fff;
  background: rgba(75, 46, 131, 0.85);
  border-radius: 0.5rem;
  padding: 0.15rem 0.75rem;
  font-size: 0.95rem;
  font-weight: 500;
  letter-spacing: 0.01em;
  box-shadow: 0 2px 8px rgba(75, 46, 131, 0.08);
  display: inline-block;
}
.navbar, .navbar * {
  color: #fff !important;
  text-shadow: 0 1px 2px rgba(0,0,0,0.08);
}
.navbar .navbar-brand, .navbar .navbar-brand * {
  color: #fff !important;
}
.navbar .nav-link {
  color: #fff !important;
  opacity: 0.95;
}
.navbar .nav-link.router-link-exact-active {
  font-weight: 700;
  color: #fff !important;
  background: rgba(255,255,255,0.12);
}
</style>