<template>
  <div class="app-container">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/">CaseStrainer</router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
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
              <router-link class="nav-link highlight-nav" to="/enhanced-validator">Enhanced Validator</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/about">About</router-link>
            </li>
          </ul>
        </div>
      </div>
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
export default {
  name: 'App'
}
</script>

<style>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
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
}

.highlight-nav:hover, .highlight-nav.router-link-active {
  background-color: #218838;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
