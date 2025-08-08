<template>
  <div class="container py-4">
    <h1 class="mb-3">API Documentation</h1>
    <p class="lead">Welcome to the CaseStrainer API documentation page.</p>
    <p>
      Here you will find information about available API endpoints, request/response formats, and usage examples.
    </p>
    <hr />
    
    <div class="mb-5">
      <h2>Available Endpoints</h2>
      <ul>
        <li><code>/casestrainer/api/analyze</code> &mdash; Analyze and validate citations (async)</li>
        <li><code>/casestrainer/api/analyze_enhanced</code> &mdash; Enhanced citation analysis (sync)</li>
        <li><code>/casestrainer/api/task_status/{task_id}</code> &mdash; Check processing status</li>
        <li><code>/casestrainer/api/health</code> &mdash; Health check endpoint</li>
        <li><code>/casestrainer/api/version</code> &mdash; Application version info</li>
        <li><code>/casestrainer/api/server_stats</code> &mdash; Server statistics</li>
        <li><code>/casestrainer/api/db_stats</code> &mdash; Database statistics</li>
      </ul>
    </div>

    <div class="mb-5">
      <h2>Endpoint Comparison</h2>
      <p>Choose the right endpoint based on your needs:</p>
      
      <div class="table-responsive">
        <table class="table table-striped">
          <thead>
            <tr>
              <th>Feature</th>
              <th><code>/analyze</code></th>
              <th><code>/analyze_enhanced</code></th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Processing Type</strong></td>
              <td><span class="badge bg-success">Async</span> (RQ/Redis)</td>
              <td><span class="badge bg-warning">Sync</span> (Direct)</td>
            </tr>
            <tr>
              <td><strong>File Uploads</strong></td>
              <td><span class="badge bg-success">✅ Yes</span></td>
              <td><span class="badge bg-danger">❌ No</span> (501 error)</td>
            </tr>
            <tr>
              <td><strong>URL Processing</strong></td>
              <td><span class="badge bg-success">✅ Yes</span></td>
              <td><span class="badge bg-danger">❌ No</span></td>
            </tr>
            <tr>
              <td><strong>Task ID Response</strong></td>
              <td><span class="badge bg-success">✅ Yes</span></td>
              <td><span class="badge bg-danger">❌ No</span> (immediate results)</td>
            </tr>
            <tr>
              <td><strong>Progress Tracking</strong></td>
              <td><span class="badge bg-success">✅ Yes</span></td>
              <td><span class="badge bg-danger">❌ No</span></td>
            </tr>
            <tr>
              <td><strong>Citation Clustering</strong></td>
              <td><span class="badge bg-success">✅ Yes</span></td>
              <td><span class="badge bg-success">✅ Yes</span></td>
            </tr>
            <tr>
              <td><strong>Enhanced Extraction</strong></td>
              <td><span class="badge bg-success">✅ Yes</span></td>
              <td><span class="badge bg-success">✅ Yes</span></td>
            </tr>
            <tr>
              <td><strong>Best For</strong></td>
              <td>Production use, large files, progress tracking</td>
              <td>Quick testing, simple text analysis</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="mb-5">
      <h2>Analyze Endpoint</h2>
      <p class="text-muted">POST <code>/casestrainer/api/analyze</code></p>
      
      <h3>Overview</h3>
      <p>
        The analyze endpoint processes legal documents and extracts/verifies citations. It supports three input types:
        file uploads, direct text input, and URL content extraction. Processing is asynchronous and returns a task ID
        that can be used to poll for results.
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
    "timestamp": "2024-01-15T10:30:00Z",
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
    "timestamp": "2024-01-15T10:30:00Z"
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
              <td>Whether the citation was found in legal databases</td>
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
              <td><code>url</code></td>
              <td>string</td>
              <td>Direct link to the case (if available)</td>
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
      <h2>Enhanced Analyze Endpoint</h2>
      <p class="text-muted">POST <code>/casestrainer/api/analyze_enhanced</code></p>
      
      <h3>Overview</h3>
      <p>
        The enhanced analyze endpoint provides synchronous citation analysis with immediate results.
        It's optimized for quick text processing and testing, but doesn't support file uploads or URL processing.
      </p>

      <h3>Input Format</h3>
      <div class="card mb-3">
        <div class="card-header">
          <h4 class="mb-0">Text Input Only</h4>
        </div>
        <div class="card-body">
          <p><strong>Content-Type:</strong> <code>application/json</code></p>
          
          <h5>Request Format:</h5>
          <pre><code>{
  "type": "text",
  "text": "The court held in Smith v. Jones, 123 F.3d 456 (9th Cir. 2020) that..."
}</code></pre>
        </div>
      </div>

      <h3>Response Format</h3>
      <p>The enhanced endpoint returns immediate results without task IDs:</p>
      
      <div class="card mb-3">
        <div class="card-header">
          <h4 class="mb-0">Success Response</h4>
        </div>
        <div class="card-body">
          <pre><code>{
  "citations": [
    {
      "citation": "123 F.3d 456",
      "case_name": "Smith v. Jones",
      "extracted_case_name": "Smith v. Jones",
      "canonical_name": "Smith v. Jones",
      "extracted_date": "2020",
      "canonical_date": "2020",
      "verified": true,
      "court": "9th Cir.",
      "confidence": 0.95,
      "method": "CourtListener",
      "url": "https://www.courtlistener.com/opinion/12345/",
      "source": "CourtListener",
      "metadata": {...}
    }
  ],
  "clusters": [
    {
      "cluster_id": "cluster_1",
      "canonical_name": "Smith v. Jones",
      "canonical_date": "2020",
      "extracted_case_name": "Smith v. Jones",
      "extracted_date": "2020",
      "citations": [...],
      "size": 2
    }
  ],
  "success": true
}</code></pre>
        </div>
      </div>

      <h3>Error Response</h3>
      <div class="card mb-3">
        <div class="card-header">
          <h4 class="mb-0">Error Format</h4>
        </div>
        <div class="card-body">
          <pre><code>{
  "error": "Analysis failed",
  "details": "Error message details"
}</code></pre>
        </div>
      </div>

      <h3>Example Usage</h3>
      <div class="card">
        <div class="card-header">
          <h4 class="mb-0">Complete Example</h4>
        </div>
        <div class="card-body">
          <h5>Request:</h5>
          <pre><code>curl -X POST /casestrainer/api/analyze_enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "type": "text",
    "text": "The court held in Smith v. Jones, 123 F.3d 456 (9th Cir. 2020) that..."
  }'</code></pre>
          
          <h5>Response:</h5>
          <pre><code>{
  "citations": [
    {
      "citation": "123 F.3d 456",
      "case_name": "Smith v. Jones",
      "extracted_case_name": "Smith v. Jones",
      "canonical_name": "Smith v. Jones",
      "verified": true,
      "confidence": 0.95
    }
  ],
  "clusters": [...],
  "success": true
}</code></pre>
        </div>
      </div>
    </div>

    <div class="mb-5">
      <h2>Health Check Endpoint</h2>
      <p class="text-muted">GET <code>/casestrainer/api/health</code></p>
      <p>Returns the current status of the API service.</p>
      
      <h5>Response:</h5>
      <pre><code>{
  "status": "healthy",
  "service": "CaseStrainer Vue API",
  "timestamp": "2024-01-15T10:30:00Z",
  "uptime": {
    "seconds": 3600,
    "formatted": "1 hour"
  },
  "redis": "connected",
  "database": "healthy",
  "rq_worker": "running",
  "environment": "production",
  "version": "2.0.0"
}</code></pre>
    </div>

    <div class="mb-5">
      <h2>Version Endpoint</h2>
      <p class="text-muted">GET <code>/casestrainer/api/version</code></p>
      <p>Returns application version information and uptime statistics.</p>
      
      <h5>Response:</h5>
      <pre><code>{
  "version": "2.0.0",
  "name": "CaseStrainer",
  "description": "Legal Citation Analysis Tool",
  "uptime": {
    "seconds": 3600,
    "formatted": "1 hour"
  },
  "environment": "production",
  "timestamp": "2024-01-15T10:30:00Z"
}</code></pre>
    </div>

    <div class="mb-5">
      <h2>Server Statistics Endpoint</h2>
      <p class="text-muted">GET <code>/casestrainer/api/server_stats</code></p>
      <p>Returns detailed server statistics including queue length and worker health.</p>
      
      <h5>Response:</h5>
      <pre><code>{
  "timestamp": 1642248600,
  "current_time": "2024-01-15 10:30:00",
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
      <h2>Database Statistics Endpoint</h2>
      <p class="text-muted">GET <code>/casestrainer/api/db_stats</code></p>
      <p>Returns database statistics including citation counts and cache information.</p>
      
      <h5>Response:</h5>
      <pre><code>{
  "database": {
    "path": "/path/to/citations.db",
    "exists": true,
    "size": 1048576
  },
  "citations": {
    "total": 1500,
    "verified": 1200,
    "unverified": 300
  },
  "cache": {
    "redis_available": true,
    "active_requests": 3
  },
  "timestamp": "2024-01-15T10:30:00Z"
}</code></pre>
    </div>

    <div class="mb-5">
      <h2>Additional Resources</h2>
      <p>For more detailed information, see the <a href="https://github.com/jafrank88/casestrainer" target="_blank">GitHub repository</a>.</p>
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
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 0.375rem;
  padding: 1rem;
  font-size: 0.875rem;
  overflow-x: auto;
}

code {
  background-color: #f1f3f4;
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