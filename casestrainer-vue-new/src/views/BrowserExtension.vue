<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-lg-10">
        <h1 class="display-4 mb-3 text-center">
          <i class="bi bi-puzzle me-2" aria-hidden="true"></i> CaseStrainer Browser Extension
        </h1>
        <p class="lead mb-4 text-center">
          A Manifest V3 extension in the repo calls the same <router-link to="/docs/api">CaseStrainer API</router-link> as the web app
          to detect citation-like strings on supported pages and show verified vs unverified styling.
        </p>

        <div class="alert alert-info mb-4" role="status">
          <h4 class="mb-2"><i class="bi bi-download me-2" aria-hidden="true"></i> Install (Chrome / Edge, developer mode)</h4>
          <ol class="mb-0 ps-3">
            <li class="mb-2">Clone or download the <a href="https://github.com/jafrank88/casestrainer" target="_blank" rel="noopener noreferrer">repository<span class="visually-hidden"> (opens in new tab)</span></a>.</li>
            <li class="mb-2">Open <code>chrome://extensions</code> (or Edge <code>edge://extensions</code>), enable <strong>Developer mode</strong>, then <strong>Load unpacked</strong>.</li>
            <li class="mb-2">Select the <code>browser-extension</code> folder at the repo root (contains <code>manifest.json</code>).</li>
            <li class="mb-0">Optional: open the extension <strong>Options</strong> page and set the API base (default <code>https://wolf.law.uw.edu/casestrainer/api</code>). Use <code>http://127.0.0.1:5001/casestrainer/api</code> when running the backend locally.</li>
          </ol>
        </div>

        <div class="card mb-4">
          <div class="card-header bg-primary text-white">
            <h3 class="mb-0"><i class="bi bi-gear me-2" aria-hidden="true"></i> How it works</h3>
          </div>
          <div class="card-body">
            <ul class="mb-0">
              <li><strong>Content script</strong> scans the page for common reporter patterns, then asks the service worker to <code>POST /analyze</code> with JSON <code>{ "type": "text", "text": "...", "force_mode": "sync" }</code> (with polling if the server returns a <code>task_id</code>).</li>
              <li><strong>Popup</strong> lists detected strings and verification hints from the API <code>citations</code> list.</li>
              <li><strong>Host permissions</strong> allow HTTPS and local dev hosts so you can point Options at your own API base.</li>
            </ul>
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header bg-secondary text-white">
            <h3 class="mb-0"><i class="bi bi-browser-chrome me-2" aria-hidden="true"></i> Browser notes</h3>
          </div>
          <div class="card-body">
            <p class="mb-2">Packaged for <strong>Chromium</strong> today (Chrome / Edge). Firefox and Safari builds are not shipped in-repo yet.</p>
            <p class="mb-0 text-muted small">Icons are simple generated PNGs under <code>browser-extension/icons/</code>. Replace them before publishing to a store.</p>
          </div>
        </div>

        <!-- Documentation & Contributing -->
        <div class="card mb-4">
          <div class="card-header bg-secondary text-white">
            <h3 class="mb-0"><i class="bi bi-book me-2" aria-hidden="true"></i> Documentation & Contributing</h3>
          </div>
          <div class="card-body">
            <p>
              Use CaseStrainer on the web for citation analysis today, or check out our documentation and contributing guidelines:
            </p>
            <div class="list-group">
              <a href="https://wolf.law.uw.edu/casestrainer/" 
                 target="_blank" 
                 rel="noopener noreferrer"
                 class="list-group-item list-group-item-action">
                <i class="bi bi-globe me-2" aria-hidden="true"></i> CaseStrainer on the Web (wolf.law.uw.edu)<span class="visually-hidden"> (opens in new tab)</span>
              </a>
              <a href="https://github.com/jafrank88/casestrainer/tree/main/docs/BROWSER_EXTENSION.md" 
                 target="_blank" 
                 rel="noopener noreferrer"
                 class="list-group-item list-group-item-action">
                <i class="bi bi-file-text me-2" aria-hidden="true"></i> Complete Browser Extension Documentation<span class="visually-hidden"> (opens in new tab)</span>
              </a>
              <a href="https://github.com/jafrank88/casestrainer" 
                 target="_blank" 
                 rel="noopener noreferrer"
                 class="list-group-item list-group-item-action">
                <i class="bi bi-github me-2" aria-hidden="true"></i> GitHub Repository<span class="visually-hidden"> (opens in new tab)</span>
              </a>
              <a href="https://github.com/jafrank88/casestrainer/issues" 
                 target="_blank" 
                 rel="noopener noreferrer"
                 class="list-group-item list-group-item-action">
                <i class="bi bi-bug me-2" aria-hidden="true"></i> Report Issues or Request Features<span class="visually-hidden"> (opens in new tab)</span>
              </a>
              <a href="https://github.com/jafrank88/casestrainer/discussions" 
                 target="_blank" 
                 rel="noopener noreferrer"
                 class="list-group-item list-group-item-action">
                <i class="bi bi-chat-dots me-2" aria-hidden="true"></i> Join the Discussion<span class="visually-hidden"> (opens in new tab)</span>
              </a>
            </div>
          </div>
        </div>

        <!-- Call to Action -->
        <div class="text-center">
          <router-link to="/" class="btn btn-primary btn-lg me-2">
            <i class="bi bi-house-door me-1" aria-hidden="true"></i> Back to Home
          </router-link>
          <a href="https://github.com/jafrank88/casestrainer" 
             target="_blank" 
             rel="noopener noreferrer"
             class="btn btn-outline-secondary btn-lg"
             aria-label="View CaseStrainer on GitHub (opens in new tab)">
            <i class="bi bi-github me-1" aria-hidden="true"></i> View on GitHub
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