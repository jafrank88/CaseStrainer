<template>
  <div class="container py-4">
    <h1 class="mb-3">API Documentation</h1>
    <p class="lead">Welcome to the CaseStrainer API documentation page.</p>
    <p class="text-muted small mb-3">
      <strong>Release 2.1.0:</strong> Web UI version comes from the frontend <code>package.json</code>.
      The API <code>version</code> field on <code>GET /casestrainer/api/health</code> is read from the <code>VERSION</code> file in the backend container (repo root <code>VERSION</code> in source).
      Completed analysis tasks include <code>metadata.clustering_version</code> (citation clustering build id).
    </p>
    <p>
      Here you will find information about available API endpoints, request/response formats, and usage examples.
    </p>
    <p class="text-muted small">
      Async task results and progress in Redis use a configurable TTL (default one hour). See
      <router-link to="/docs/data-retention">data retention</router-link>.
    </p>
    <div class="alert alert-info" role="region" aria-label="Production API base URL">
      <p class="mb-0">
        <strong>Production API base:</strong> <code>https://wolf.law.uw.edu/casestrainer/api</code> — use this base URL for all endpoints when integrating with the live application.
      </p>
    </div>
    <hr />
    
    <div class="mb-5">
      <h2>Available Endpoints</h2>
      <ul>
        <li><code>POST /casestrainer/api/analyze</code> &mdash; Analyze and validate citations (file, URL, or text; async returns task_id)</li>
        <li><code>GET /casestrainer/api/task_status/{task_id}</code> &mdash; Check async processing status and get results</li>
        <li><code>GET /casestrainer/api/health</code> &mdash; Health check endpoint</li>
        <li><code>GET /casestrainer/api/db_stats</code> &mdash; Database statistics</li>
        <li><code>GET /casestrainer/api/metrics/summary</code> &mdash; Metrics summary</li>
        <li><code>GET /casestrainer/api/metrics</code> &mdash; Metrics dashboard</li>
        <li><code>GET /casestrainer/api/analyze/progress/{request_id}</code> &mdash; JSON progress snapshot for a request</li>
        <li><code>GET /casestrainer/api/analyze/progress-stream/{request_id}</code> &mdash; Server-Sent Events stream for live progress</li>
      </ul>
    </div>

    <div class="mb-5">
      <h2>Analyze Endpoint</h2>
      <p class="text-muted">POST <code>/casestrainer/api/analyze</code></p>
      
      <h3>Overview</h3>
      <p>
        The analyze endpoint processes legal documents and extracts/verifies citations. It supports file uploads,
        pasted text, and URL extraction. Production is <strong>async-first</strong>: the response usually includes a
        <code>task_id</code> to poll via <code>GET /task_status/{task_id}</code>. For small inputs, the same endpoint may
        return a <strong>synchronous</strong> JSON body with <code>citations</code> and <code>clusters</code> immediately
        (see server routing and optional <code>force_mode</code> in form/JSON). Optional form field
        <code>force_mode</code>: <code>async</code>, <code>sync</code>, or <code>auto</code> where supported.
      </p>

      <h3>Input Types</h3>
      
      <div class="card mb-3">
        <div class="card-header">
          <h4 class="mb-0">1. File Upload</h4>
        </div>
        <div class="card-body">
          <p><strong>Content-Type:</strong> <code>multipart/form-data</code></p>
          <p><strong>Supported formats:</strong> PDF, DOCX, TXT, RTF, MD, HTML, XML</p>
          <p><strong>Field name:</strong> <code>file</code></p>
          
          <h5>Example Request:</h5>
          <pre><code>curl -X POST /casestrainer/api/analyze \
  -F "file=@document.pdf"</code></pre>
        </div>
      </div>

      <div class="card mb-3">
        <div class="card-header">
          <h4 class="mb-0">2. Text Input</h4>
        </div>
        <div class="card-body">
          <p><strong>Content-Type:</strong> <code>application/json</code> or <code>application/x-www-form-urlencoded</code></p>
          
          <h5>JSON Format:</h5>
          <pre><code>{
  "type": "text",
  "text": "The court held in Smith v. Jones, 123 F.3d 456 (9th Cir. 2020) that..."
}</code></pre>
          
          <h5>Form Data Format:</h5>
          <pre><code>type=text&text=The court held in Smith v. Jones, 123 F.3d 456 (9th Cir. 2020) that...</code></pre>
        </div>
      </div>

      <div class="card mb-3">
        <div class="card-header">
          <h4 class="mb-0">3. URL Input</h4>
        </div>
        <div class="card-body">
          <p><strong>Content-Type:</strong> <code>application/json</code> or <code>application/x-www-form-urlencoded</code></p>
          
          <h5>JSON Format:</h5>
          <pre><code>{
  "type": "url",
  "url": "https://example.com/legal-document"
}</code></pre>
          
          <h5>Form Data Format:</h5>
          <pre><code>type=url&url=https://example.com/legal-document</code></pre>
        </div>
      </div>

      <h3>Response Format</h3>
      <p>The analyze endpoint returns an immediate response with a task ID for tracking:</p>
      
      <div class="card mb-3">
        <div class="card-header">
          <h4 class="mb-0">Initial Response</h4>
        </div>
        <div class="card-body">
          <pre><code>{
  "status": "processing",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "File upload received, processing started",
  "metadata": {
    "source_type": "file",
    "source_name": "document.pdf",
    "file_type": ".pdf",
    "timestamp": "2026-04-02T10:30:00Z",
    "user_agent": "curl/7.68.0"
  }
}</code></pre>
        </div>
      </div>

      <h3>Checking Results</h3>
      <p>Use the task ID to poll for results using the task status endpoint:</p>
      
      <div class="card mb-3">
        <div class="card-header">
          <h4 class="mb-0">Task Status Endpoint</h4>
        </div>
        <div class="card-body">
          <p><strong>GET</strong> <code>/casestrainer/api/task_status/{task_id}</code></p>
          
          <h5>Processing Response:</h5>
          <pre><code>{
  "status": "processing",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Task is processing",
  "progress": 45,
  "status_message": "Extracting citations from content...",
  "current_step": "Citation extraction",
  "estimated_time_remaining": 30
}</code></pre>
          
          <h5>Completed Response:</h5>
          <pre><code>{
  "status": "completed",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "citations": [
    {
      "citation": "123 F.3d 456",
      "found": true,
      "source": "CourtListener",
      "canonical_name": "Smith v. Jones",
      "extracted_case_name": "Smith v. Jones",
      "url": "https://www.courtlistener.com/opinion/12345/",
      "explanation": "Citation found and verified",
      "is_westlaw": false,
      "sources_checked": ["CourtListener", "Google Scholar", "Justia"],
      "details": {
        "court": "9th Cir.",
        "year": "2020",
        "reporter": "F.3d",
        "volume": "123",
        "page": "456"
      }
    }
  ],
  "metadata": {
    "source_type": "file",
    "source_name": "document.pdf",
    "file_type": ".pdf",
    "timestamp": "2026-04-02T10:30:00Z",
    "clustering_version": "2026-04-v8"
  },
  "progress": 100,
  "total_citations": 1,
  "verified_citations": 1
}</code></pre>
        </div>
      </div>

      <h3>Citation Result Fields</h3>
      <div class="table-responsive">
        <table class="table table-striped">
          <thead>
            <tr>
              <th>Field</th>
              <th>Type</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>citation</code></td>
              <td>string</td>
              <td>The original citation text</td>
            </tr>
            <tr>
              <td><code>found</code></td>
              <td>boolean</td>
              <td>UI-oriented flag (mapped from verification); prefer <code>verified</code> for API logic</td>
            </tr>
            <tr>
              <td><code>verified</code></td>
              <td>boolean</td>
              <td>Whether the citation matched a canonical case (e.g. CourtListener) with required fields</td>
            </tr>
            <tr>
              <td><code>source</code></td>
              <td>string</td>
              <td>Primary source where citation was found (CourtListener, Google Scholar, Justia, etc.)</td>
            </tr>
            <tr>
              <td><code>canonical_name</code></td>
              <td>string</td>
              <td>Official case name from the legal database</td>
            </tr>
            <tr>
              <td><code>extracted_case_name</code></td>
              <td>string</td>
              <td>Case name extracted from the document text</td>
            </tr>
            <tr>
              <td><code>url</code> / <code>canonical_url</code></td>
              <td>string</td>
              <td>Opinion URL when resolved (often CourtListener)</td>
            </tr>
            <tr>
              <td><code>explanation</code></td>
              <td>string</td>
              <td>Human-readable explanation of the verification result</td>
            </tr>
            <tr>
              <td><code>is_westlaw</code></td>
              <td>boolean</td>
              <td>Whether this is a Westlaw citation</td>
            </tr>
            <tr>
              <td><code>sources_checked</code></td>
              <td>array</td>
              <td>List of legal databases that were checked</td>
            </tr>
            <tr>
              <td><code>details</code></td>
              <td>object</td>
              <td>Additional citation details (court, year, reporter, etc.)</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h3>Error Responses</h3>
      <div class="card mb-3">
        <div class="card-header">
          <h4 class="mb-0">Error Format</h4>
        </div>
        <div class="card-body">
          <pre><code>{
  "status": "error",
  "error_type": "input_validation",
  "message": "No valid input provided",
  "status_code": 400,
  "metadata": {
    "source_type": "text",
    "source_name": "pasted_text"
  }
}</code></pre>
        </div>
      </div>

      <h3>Processing Times</h3>
      <p>Typical processing times vary by input type:</p>
      <ul>
        <li><strong>Text input:</strong> 10-30 seconds</li>
        <li><strong>File upload:</strong> 30-120 seconds (depends on file size and complexity)</li>
        <li><strong>URL content:</strong> 60-300 seconds (includes download time)</li>
      </ul>

      <h3>Rate Limits</h3>
      <p>To ensure fair usage, the API implements rate limiting:</p>
      <ul>
        <li>Maximum 10 requests per minute per IP address</li>
        <li>Maximum file size: 50MB</li>
        <li>Maximum text length: 100,000 characters</li>
      </ul>

      <h3>Complete Example</h3>
      <div class="card">
        <div class="card-header">
          <h4 class="mb-0">Full Workflow Example</h4>
        </div>
        <div class="card-body">
          <h5>1. Submit Analysis Request:</h5>
          <pre><code>curl -X POST /casestrainer/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "type": "text",
    "text": "The court held in Smith v. Jones, 123 F.3d 456 (9th Cir. 2020) that..."
  }'</code></pre>
          
          <h5>2. Get Task ID Response:</h5>
          <pre><code>{
  "status": "processing",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Text received, processing started"
}</code></pre>
          
          <h5>3. Poll for Results:</h5>
          <pre><code>curl /casestrainer/api/task_status/550e8400-e29b-41d4-a716-446655440000</code></pre>
          
                <h5>4. Get Final Results:</h5>
      <pre><code>{
  "status": "completed",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "results": [...],
  "citations": [
    {
      "citation": "123 F.3d 456",
      "found": true,
      "source": "CourtListener",
      "canonical_name": "Smith v. Jones",
      "extracted_case_name": "Smith v. Jones",
      "url": "https://www.courtlistener.com/opinion/12345/",
      "explanation": "Citation found and verified"
    }
  ],
  "clusters": [...],
  "case_names": [...],
  "metadata": {...},
  "statistics": {...},
  "summary": {...}
}</code></pre>
        </div>
      </div>
    </div>

    <div class="mb-5">
      <h2>Synchronous vs asynchronous <code>/analyze</code></h2>
      <p>
        There is <strong>no</strong> separate <code>/analyze_enhanced</code> endpoint. The same
        <code>POST /casestrainer/api/analyze</code> route either enqueues work and returns a <code>task_id</code>
        (then poll <code>/task_status/{task_id}</code>) or, for small inputs, returns <code>citations</code> and
        <code>clusters</code> immediately with <code>success: true</code>. Routing depends on document size,
        estimated citation count, optional <code>force_mode</code>, and server configuration.
      </p>
    </div>

    <div class="mb-5">
      <h2>Health Check Endpoint</h2>
      <p class="text-muted">GET <code>/casestrainer/api/health</code> (alias: same handler on the API blueprint)</p>
      <p>Returns service status, <code>version</code> from the container <code>VERSION</code> file (e.g. <strong>2.1.0</strong>), database and Redis component checks, and environment metadata.</p>
      
      <h5>Example response (abridged):</h5>
      <pre><code>{
  "status": "healthy",
  "timestamp": "2026-04-02T12:00:00.000000",
  "version": "2.1.0",
  "components": {
    "database": "healthy",
    "upload_directory": "healthy",
    "citation_processor": "healthy",
    "redis": "healthy"
  },
  "database_stats": {
    "tables": 0,
    "size_mb": 0.0,
    "path": "/path/to/data.db"
  },
  "environment": {
    "python_version": "3.11.0",
    "platform": "linux"
  },
  "endpoints": {
    "current": "/casestrainer/api/health",
    "alias": "/health",
    "base_url": "https://example.com/casestrainer/api/health"
  }
}</code></pre>
    </div>

    <div class="mb-5">
      <h2>Metrics &amp; Statistics</h2>
      <p class="text-muted">GET <code>/casestrainer/api/metrics/summary</code>, <code>/casestrainer/api/metrics</code>, <code>/casestrainer/api/db_stats</code></p>
      <p>Returns metrics summaries, dashboard data, and database statistics. See the Available Endpoints list above for full URLs.</p>
    </div>

    <div class="mb-5">
      <h2>Database Statistics Endpoint</h2>
      <p class="text-muted">GET <code>/casestrainer/api/db_stats</code></p>
      <p>Returns database and service statistics.</p>
      
      <h5>Response:</h5>
      <pre><code>{
  "timestamp": 1642248600,
  "current_time": "2026-04-02 10:30:00",
  "uptime": {
    "seconds": 3600,
    "formatted": "1 hour"
  },
  "rq_available": true,
  "queue_length": 5,
  "worker_health": "running"
}</code></pre>
    </div>

    <div class="mb-5">
      <h2>Integrations (same API)</h2>
      <p>
        <router-link to="/browser-extension">Browser extension</router-link> (Chromium, load unpacked from <code>browser-extension/</code>)
        and <router-link to="/word-plugin">Word add-in</router-link> (task pane hosted at <code>/casestrainer/word-addin/</code> after deploy)
        call this API. Use JSON <code>{ "type": "text", "text": "...", "force_mode": "sync" }</code> when you need an immediate
        <code>citations</code> array; otherwise poll <code>task_status</code> when you receive a <code>task_id</code>.
      </p>
    </div>

    <div class="mb-5">
      <h2>Additional Resources</h2>
      <p>For more detailed information, see the <a href="https://wolf.law.uw.edu/casestrainer/" target="_blank" rel="noopener noreferrer">live application<span class="visually-hidden"> (opens in new tab)</span></a> and the <a href="https://github.com/jafrank88/casestrainer" target="_blank" rel="noopener noreferrer">GitHub repository<span class="visually-hidden"> (opens in new tab)</span></a>.</p>
    </div>
  </div>
</template>

<script setup>
// No script needed for static docs
</script>

<style scoped>
h1 {
  color: #2563eb;
}

.card {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
}

.card-header {
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

pre {
  background-color: #f1f5f9;
  color: #0f172a;
  border: 1px solid #cbd5e1;
  border-radius: 0.375rem;
  padding: 1rem;
  font-size: 0.875rem;
  overflow-x: auto;
}

code {
  background-color: #e2e8f0;
  color: #0f172a;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
}

.table th {
  background-color: #f8f9fa;
  font-weight: 600;
}

/* Mobile Responsive Design */
@media (max-width: 768px) {
  .container {
    padding: 0 1rem;
  }
  
  h1 {
    font-size: 1.75rem;
  }
  
  h2 {
    font-size: 1.5rem;
  }
  
  h3 {
    font-size: 1.25rem;
  }
  
  h4 {
    font-size: 1.125rem;
  }
  
  .lead {
    font-size: 1rem;
  }
  
  .card {
    margin-bottom: 1rem;
  }
  
  .card-body {
    padding: 1rem;
  }
  
  .card-header {
    padding: 0.75rem 1rem;
  }
  
  pre {
    font-size: 0.8rem;
    padding: 0.75rem;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-word;
  }
  
  code {
    font-size: 0.8em;
    padding: 0.1rem 0.2rem;
  }
  
  .table-responsive {
    font-size: 0.9rem;
  }
  
  .table th,
  .table td {
    padding: 0.5rem 0.25rem;
    font-size: 0.85rem;
  }
  
  .table th {
    font-size: 0.8rem;
  }
  
  ul {
    padding-left: 1.25rem;
  }
  
  li {
    margin-bottom: 0.5rem;
  }
}

@media (max-width: 480px) {
  .container {
    padding: 0 0.5rem;
  }
  
  h1 {
    font-size: 1.5rem;
  }
  
  h2 {
    font-size: 1.25rem;
  }
  
  h3 {
    font-size: 1.125rem;
  }
  
  h4 {
    font-size: 1rem;
  }
  
  .lead {
    font-size: 0.95rem;
  }
  
  .card-body {
    padding: 0.75rem;
  }
  
  .card-header {
    padding: 0.5rem 0.75rem;
  }
  
  pre {
    font-size: 0.75rem;
    padding: 0.5rem;
  }
  
  code {
    font-size: 0.75em;
  }
  
  .table th,
  .table td {
    padding: 0.375rem 0.125rem;
    font-size: 0.8rem;
  }
  
  .table th {
    font-size: 0.75rem;
  }
  
  ul {
    padding-left: 1rem;
  }
  
  li {
    margin-bottom: 0.375rem;
    font-size: 0.9rem;
  }
}

/* Touch-friendly improvements */
@media (hover: none) and (pointer: coarse) {
  .card {
    min-height: 44px;
  }
  
  .btn {
    min-height: 44px;
    padding: 0.75rem 1rem;
  }
  
  /* Remove hover effects on touch devices */
  .card:hover {
    transform: none;
  }
}
</style> 