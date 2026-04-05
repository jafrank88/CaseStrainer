<template>
  <div class="pipeline-docs">
    <div class="container">
      <h1 class="mb-4">Citation Processing Pipeline</h1>
      
      <div class="alert alert-info" role="region" aria-label="Pipeline overview">
        <p class="mb-0">
          <strong>Overview:</strong> CaseStrainer uses a single unified pipeline (5 stages) for all inputs. Requests are async-first in production and return a task ID for progress polling. Clustering build id <code>2026-04-v8</code> is recorded as <code>metadata.clustering_version</code> on completed tasks. See <a href="https://github.com/jafrank88/casestrainer/blob/main/docs/PIPELINE_ENTRY_POINTS.md" target="_blank" rel="noopener noreferrer">PIPELINE_ENTRY_POINTS.md<span class="visually-hidden"> (opens in new tab)</span></a> for flowcharts and entry points.
        </p>
      </div>

      <!-- Flowchart: how documents are processed -->
      <div class="section-card mb-4">
        <h2>How documents are processed</h2>
        <p class="text-muted">Request → input handling → queue async task → unified pipeline in worker → task_status polling.</p>
        <div class="flowchart-code">
          <pre class="mermaid mb-0">
flowchart TB
  A[POST /analyze: file, URL, or text] --> B[Extract text]
  B --> C[Enqueue RQ → return task_id]
  C --> F[Worker: run_citation_task]
  F --> D
  D --> G[1. Extraction]
  G --> H[2. Law-review filter]
  H --> I[3. Verification]
  I --> J[4. Parallel verification]
  J --> K[5. Formatting & clustering]
  K --> L[citations + clusters]
  L --> N[Store in Redis → client polls task_status]
          </pre>
        </div>
        <p class="small text-muted mt-2">All document inputs use the same unified pipeline through async task processing in production.</p>
      </div>

      <!-- Stage 1 -->
      <div class="phase-card">
        <div class="phase-header phase-1">
          <h2><span class="phase-number">1</span> Extraction</h2>
        </div>
        <div class="phase-body">
          <p>Extract citations, case names, and dates from plain text using the unified processor (eyecite + context-aware extraction).</p>
          <ul>
            <li>Detects standard formats (e.g., "467 U.S. 526", "171 Wn.2d 486")</li>
            <li>Case names from surrounding context; dates from parentheticals</li>
            <li>Filters statutes, regulations, cross-references</li>
          </ul>
        </div>
      </div>

      <!-- Stage 2 -->
      <div class="phase-card">
        <div class="phase-header phase-2">
          <h2><span class="phase-number">2</span> Law-review filter</h2>
        </div>
        <div class="phase-body">
          <p>Removes law review and other secondary-source citations so only case citations are verified and clustered.</p>
        </div>
      </div>

      <!-- Stage 3 -->
      <div class="phase-card">
        <div class="phase-header phase-3">
          <h2><span class="phase-number">3</span> Verification</h2>
        </div>
        <div class="phase-body">
          <p>Verifies citations against CourtListener (and fallbacks when configured). Sets canonical name, date, URL, and verified flag.</p>
          <p><strong>Results:</strong> Verified, Verified by Parallel, or Unverified</p>
        </div>
      </div>

      <!-- Stage 4 -->
      <div class="phase-card">
        <div class="phase-header phase-4">
          <h2><span class="phase-number">4</span> Parallel verification</h2>
        </div>
        <div class="phase-body">
          <p>Propagates canonical data from one citation to parallel citations (same case, different reporter). Ensures clusters show one canonical identity.</p>
        </div>
      </div>

      <!-- Stage 5 -->
      <div class="phase-card">
        <div class="phase-header phase-5">
          <h2><span class="phase-number">5</span> Formatting & clustering</h2>
        </div>
        <div class="phase-body">
          <p>Builds clusters (minimal clustering: same-case / parallel detection, year and reporter conflicts, Westlaw pins vs reporter cites). Annotates mismatch flags, applies date overrides, and formats the response for the UI.</p>
        </div>
      </div>

      <!-- Processing Modes -->
      <div class="section-card mt-5">
        <h2>Processing Behavior</h2>
        <div class="mode-card">
          <h3>Async-first</h3>
          <p>Requests return <code>task_id</code> and progress/status are read via <code>/task_status/&lt;task_id&gt;</code>.</p>
          <p>The worker executes the same unified extraction, verification, and clustering stages used across all input types.</p>
        </div>
      </div>

      <!-- Doc reference -->
      <div class="section-card mt-4">
        <h2>Reference</h2>
        <p>Canonical entry points and flowcharts: <a href="https://github.com/jafrank88/casestrainer/blob/main/docs/PIPELINE_ENTRY_POINTS.md" target="_blank" rel="noopener">docs/PIPELINE_ENTRY_POINTS.md</a></p>
      </div>

    </div>
  </div>
</template>

<script setup>
// Processing pipeline documentation
</script>

<style scoped>
.pipeline-docs {
  padding: 2rem 0;
  background: #f8f9fa;
  min-height: 100vh;
}

.container {
  max-width: 900px;
}

h1 {
  color: #2c3e50;
  font-weight: 600;
}

.phase-card {
  background: white;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow: hidden;
}

.phase-header {
  padding: 1rem 1.5rem;
  color: white;
  font-weight: 600;
}

.phase-1 { background: #007bff; }
.phase-2 { background: #28a745; }
.phase-3 { background: #17a2b8; }
.phase-4 { background: #ffc107; color: #333; }
.phase-5 { background: #fd7e14; }
.phase-6 { background: #6f42c1; }

.phase-number {
  display: inline-block;
  width: 32px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  background: rgba(255,255,255,0.2);
  border-radius: 50%;
  margin-right: 0.5rem;
}

.phase-body {
  padding: 1.5rem;
}

.phase-body h4 {
  margin-top: 1rem;
  color: #495057;
  font-size: 1.1rem;
}

.section-card {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.mode-card {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 1.5rem;
  height: 100%;
  border-left: 4px solid #007bff;
}

@media (max-width: 768px) {
  .pipeline-docs {
    padding: 1rem 0;
  }
  
  .phase-body {
    padding: 1rem;
  }
  
  .section-card {
    padding: 1.5rem;
  }
}
</style>
