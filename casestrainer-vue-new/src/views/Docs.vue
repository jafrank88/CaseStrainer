<template>
  <div class="docs-page">
    <h1>CaseStrainer Documentation</h1>
    <p>Welcome to the CaseStrainer documentation hub. Find guides, API docs, and more below.</p>
    <ul class="docs-list">
      <li><router-link to="/docs/api">API Documentation</router-link></li>
      <li><a href="https://github.com/your-org/CaseStrainer/blob/main/README.md" target="_blank">User Guide (README)</a></li>
      <li><a href="https://github.com/your-org/CaseStrainer/tree/main/docs" target="_blank">More Documentation</a></li>
      <li><router-link to="/">Back to Home</router-link></li>
    </ul>
  </div>
</template>

<script setup>
// No script needed for simple docs hub
</script>

<style scoped>
.docs-page {
  max-width: 600px;
  margin: 2rem auto;
  padding: 2rem;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.docs-page h1 {
  margin-bottom: 1rem;
}
.docs-list {
  list-style: none;
  padding: 0;
}
.docs-list li {
  margin: 1rem 0;
  font-size: 1.1em;
}
.docs-list a {
  color: #007bff;
  text-decoration: none;
}
.docs-list a:hover {
  text-decoration: underline;
}
</style> 