<template>
  <div class="app-container">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container-fluid position-relative">
        <router-link class="navbar-brand" to="/">CaseStrainer</router-link>
        <router-link class="nav-link highlight-nav ms-2 d-inline-block" style="min-width:170px;" to="/enhanced-validator">Enhanced Validator</router-link>
        <button class="navbar-toggler" type="button" aria-label="Toggle navigation" @click="toggleNavbar" ref="navbarToggler">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav" ref="navbarCollapse">
          <ul class="navbar-nav">
            <li class="nav-item">
              <router-link class="nav-link" to="/">Home</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/unconfirmed-citations">Unconfirmed Citations</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/multitool-confirmed">Confirmed with Multitool</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/citation-network">Citation Network</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/ml-classifier">ML Classifier</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/citation-tester">Citation Tester</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/about">About</router-link>
            </li>
          </ul>
        </div>
      </div>
      <span class="version-badge position-absolute top-0 end-0 mt-2 me-3 bg-light text-primary px-2 py-1 rounded" style="font-size:0.95rem;font-weight:bold;">
  v{{ version || '?' }}
</span>
    </nav>

    <main class="container mt-4">
      <router-view />
    </main>

    <footer class="footer mt-5 py-3 bg-light">
      <div class="container text-center">
        <span class="text-muted">CaseStrainer &copy; 2025 - University of Washington</span>
      </div>
    </footer>
  </div>
</template>

<script>
import { fetchVersion } from './version.js';

export default {
  name: 'App',
  data() {
    return {
      version: null
    }
  },
  mounted() {
    fetchVersion().then(v => { this.version = v; });
  },
  methods: {
    toggleNavbar() {
      // Bootstrap 5 collapse
      const collapse = this.$refs.navbarCollapse;
      if (!collapse) return;
      if (collapse.classList.contains('show')) {
        // Close menu
        collapse.classList.remove('show');
      } else {
        // Open menu
        collapse.classList.add('show');
      }
    }
  }
}
</script>

<style>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Responsive navbar tweaks */
@media (max-width: 991.98px) {
  .navbar-nav {
    flex-direction: column;
    width: 100%;
  }
  .navbar-nav .nav-item {
    margin-bottom: 0.5rem;
  }
  .highlight-nav {
    width: 100%;
    text-align: center;
  }
}

@media (max-width: 575.98px) {
  .navbar-brand {
    font-size: 1.1rem;
  }
  .version-badge {
    font-size: 0.85rem !important;
    padding: 0.25rem 0.5rem !important;
    margin-right: 0.5rem !important;
  }
}


main {
  flex: 1;
}

.footer {
  margin-top: auto;
}

.highlight-nav {
  font-weight: bold;
  color: #fff !important;
  background-color: #28a745;
  border-radius: 0.25rem;
  padding: 0.5rem 1rem !important;
  margin: 0 0.25rem;
  transition: all 0.3s ease;
  vertical-align: middle;
}

@media (max-width: 991.98px) {
  .navbar-brand, .highlight-nav {
    display: block;
    margin-bottom: 0.5rem;
    min-width: 0;
  }
  .highlight-nav {
    width: 100%;
    text-align: center;
    margin: 0.25rem 0;
  }
}

@media (max-width: 575.98px) {
  .navbar-brand {
    font-size: 1.1rem;
  }
  .highlight-nav {
    font-size: 0.95rem;
    padding: 0.35rem 0.5rem !important;
  }
  .version-badge {
    font-size: 0.85rem !important;
    padding: 0.25rem 0.5rem !important;
    margin-right: 0.5rem !important;
  }
}

.highlight-nav:hover, .highlight-nav.router-link-active {
  background-color: #218838;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
