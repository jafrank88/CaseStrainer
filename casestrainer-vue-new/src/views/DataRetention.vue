<template>
  <div class="retention-docs">
    <div class="container py-4">
      <h1 class="mb-3">Data retention</h1>
      <p class="lead text-muted">
        What CaseStrainer keeps in Redis, on disk, and how operators can limit retention (defaults favor a short window).
      </p>

      <div class="section-card mb-4">
        <h2 class="h4">Defaults</h2>
        <ul>
          <li>
            <strong>Async results and progress</strong> expire from Redis after about
            <strong>one hour</strong> (<code>DATA_RETENTION_ASYNC_SECONDS</code>, default <code>3600</code>),
            unless your deployment sets another value (clamped between 1 minute and 7 days).
          </li>
          <li>
            <strong>Uploaded files</strong> for async jobs are removed on the worker after processing when
            <code>UPLOAD_DELETE_AFTER_PROCESSING</code> is <code>true</code> (default).
          </li>
          <li>
            <strong>Full API response logging</strong> to <code>/app/logs/frontend_api_results.log</code> is
            <strong>disabled</strong> unless <code>CASESTRAINER_LOG_FULL_API_RESPONSES=true</code>.
          </li>
        </ul>
      </div>

      <div class="section-card mb-4">
        <h2 class="h4">Environment variables</h2>
        <p>See the repository <code>.env.example</code> and <code>docs/DATA_RETENTION.md</code> for the full table and operational notes.</p>
        <ul>
          <li><code>DATA_RETENTION_ASYNC_SECONDS</code> — Redis TTL for task results, progress, and verification keys.</li>
          <li><code>UPLOAD_DELETE_AFTER_PROCESSING</code> — Remove upload path after async file jobs.</li>
          <li><code>CASESTRAINER_LOG_FULL_API_RESPONSES</code> — Optional full JSON response audit log.</li>
        </ul>
      </div>

      <div class="section-card mb-4">
        <h2 class="h4">Third parties</h2>
        <p class="mb-0">
          Verification may call external APIs (for example CourtListener). Those services have their own data policies;
          CaseStrainer sends only what is required for citation verification.
        </p>
      </div>

      <p class="small text-muted mb-4">
        Canonical technical write-up:
        <a
          href="https://github.com/jafrank88/casestrainer/blob/main/docs/DATA_RETENTION.md"
          target="_blank"
          rel="noopener noreferrer"
        >docs/DATA_RETENTION.md<span class="visually-hidden"> (opens in new tab)</span></a>
      </p>

      <router-link to="/docs" class="btn btn-outline-primary">Back to documentation</router-link>
    </div>
  </div>
</template>

<script setup>
// Static policy summary; full detail in repo docs/DATA_RETENTION.md
</script>

<style scoped>
.retention-docs {
  max-width: 900px;
  margin: 0 auto;
}
.section-card {
  background: #fff;
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
</style>
