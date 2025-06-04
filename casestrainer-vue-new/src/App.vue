<template>
  <div id="app">
    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container">
        <router-link class="navbar-brand" to="/">
          <i class="bi bi-journal-check me-2"></i>
          CaseStrainer
        </router-link>
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
                <i class="bi bi-house-door me-1"></i> Home
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/enhanced-validator">
                <i class="bi bi-shield-check me-1"></i> Enhanced Validator
              </router-link>
            </li>
            <li class="nav-item">
              <a class="nav-link" href="/api/" target="_blank">
                <i class="bi bi-code-slash me-1"></i> API Docs
              </a>
            </li>
          </ul>
          <div class="d-flex">
            <span class="navbar-text text-light me-3">
              v{{ appVersion }}
            </span>
            <a 
              href="https://github.com/yourusername/casestrainer" 
              target="_blank" 
              class="btn btn-outline-light btn-sm"
            >
              <i class="bi bi-github me-1"></i> GitHub
            </a>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="container py-4">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Footer -->
    <footer class="bg-light py-4 mt-5">
      <div class="container">
        <div class="row">
          <div class="col-md-6">
            <h5>About CaseStrainer</h5>
            <p class="text-muted">
              A powerful tool for legal professionals to validate, analyze, and manage legal citations.
            </p>
          </div>
          <div class="col-md-3">
            <h5>Quick Links</h5>
            <ul class="list-unstyled">
              <li><router-link to="/" class="text-decoration-none">Home</router-link></li>
              <li><router-link to="/enhanced-validator" class="text-decoration-none">Enhanced Validator</router-link></li>
              <li><a href="/api/" target="_blank" class="text-decoration-none">API Documentation</a></li>
            </ul>
          </div>
          <div class="col-md-3">
            <h5>Resources</h5>
            <ul class="list-unstyled">
              <li><a href="#" class="text-decoration-none">Documentation</a></li>
              <li><a href="#" class="text-decoration-none">GitHub Repository</a></li>
              <li><a href="#" class="text-decoration-none">Report an Issue</a></li>
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
      appVersion: import.meta.env.VITE_APP_VERSION || '0.4.8',
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
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

/* Cards */
.card {
  border: none;
  border-radius: 0.5rem;
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
  margin-bottom: 1.5rem;
  overflow: hidden;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.1);
}

.card-header {
  font-weight: 600;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

/* Forms */
.form-control, .form-select {
  padding: 0.5rem 0.75rem;
  border-radius: 0.25rem;
  border: 1px solid #dee2e6;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-control:focus, .form-select:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

/* Animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .navbar-brand {
    font-size: 1.25rem;
  }
  
  .btn {
    width: 100%;
    margin-bottom: 0.5rem;
  }
  
  .container {
    padding-left: 1rem;
    padding-right: 1rem;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  :root {
    --bs-body-bg: #1a1a1a;
    --bs-body-color: #f8f9fa;
    --bs-border-color: #495057;
  }
  
  body {
    background-color: var(--bs-body-bg);
    color: var(--bs-body-color);
  }
  
  .card {
    background-color: #2d2d2d;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.3);
  }
  
  .card-header {
    background-color: #252525;
    border-bottom-color: #3a3a3a;
  }
  
  .form-control, .form-select {
    background-color: #2d2d2d;
    border-color: #3a3a3a;
    color: #f8f9fa;
  }
  
  .form-control:focus, .form-select:focus {
    background-color: #2d2d2d;
    color: #f8f9fa;
  }
  
  .bg-light {
    background-color: #252525 !important;
  }
  
  .text-muted {
    color: #adb5bd !important;
  }
  
  .navbar-dark .navbar-nav .nav-link {
    color: rgba(255, 255, 255, 0.85);
  }
  
  .navbar-dark .navbar-nav .nav-link:hover, 
  .navbar-dark .navbar-nav .nav-link:focus {
    color: white;
  }
}
</style>
