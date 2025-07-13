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