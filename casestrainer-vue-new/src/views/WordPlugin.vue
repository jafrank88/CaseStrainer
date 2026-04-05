<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-lg-10">
        <h1 class="display-4 mb-3 text-center">
          <i class="bi bi-file-earmark-word me-2" aria-hidden="true"></i> CaseStrainer Word add-in
        </h1>
        <p class="lead mb-4 text-center">
          Analyze and verify legal citations directly within Microsoft Word documents. Detect hallucinated or incorrect citations in briefs, memos, and legal documents.
        </p>

        <!-- Status Alert -->
        <div class="alert alert-success mb-4" role="status">
          <h4 class="mb-2"><i class="bi bi-check-circle me-2" aria-hidden="true"></i> Hosted with the web app</h4>
          <p class="mb-0">
            The task pane is served as static files from the Vue app at
            <a href="https://wolf.law.uw.edu/casestrainer/word-addin/index.html" target="_blank" rel="noopener noreferrer"><code>/casestrainer/word-addin/</code><span class="visually-hidden"> (opens in new tab)</span></a>.
            Sideload <a href="https://wolf.law.uw.edu/casestrainer/word-addin/manifest.xml" target="_blank" rel="noopener noreferrer">the production <code>manifest.xml</code><span class="visually-hidden"> (opens in new tab)</span></a>
            or use the copy under <code>casestrainer-vue-new/public/word-addin/</code> in the repo (including <code>manifest.local.xml</code> for Vite on port 5173).
          </p>
        </div>

        <!-- Quick Start -->
        <div class="card mb-4">
          <div class="card-header bg-primary text-white">
            <h3 class="mb-0"><i class="bi bi-rocket me-2" aria-hidden="true"></i> Quick Start</h3>
          </div>
          <div class="card-body">
            <ol class="mb-0">
              <li class="mb-2">
                <strong>Download</strong>
                <a href="https://wolf.law.uw.edu/casestrainer/word-addin/manifest.xml" target="_blank" rel="noopener noreferrer">production <code>manifest.xml</code><span class="visually-hidden"> (opens in new tab)</span></a>
                (or from
                <a href="https://github.com/jafrank88/casestrainer/tree/main/casestrainer-vue-new/public/word-addin" target="_blank" rel="noopener noreferrer">GitHub: <code>public/word-addin</code><span class="visually-hidden"> (opens in new tab)</span></a>)
              </li>
              <li class="mb-2">
                <strong>Copy</strong> to your Office Web Extensions folder:
                <ul class="mt-2">
                  <li>Windows: <code>%USERPROFILE%\AppData\Local\Microsoft\Office\16.0\Wef\</code></li>
                  <li>Mac: <code>~/Library/Containers/com.microsoft.Word/Data/Documents/wef/</code></li>
                </ul>
              </li>
              <li class="mb-2">
                <strong>Restart</strong> Microsoft Word
              </li>
              <li class="mb-0">
                <strong>Enable</strong> the add-in from <strong>Insert → Add-ins → My Add-ins</strong> (display name <strong>CaseStrainer</strong>)
              </li>
            </ol>
          </div>
        </div>

        <!-- Features Section -->
        <div class="card mb-4">
          <div class="card-header bg-info text-white">
            <h3 class="mb-0"><i class="bi bi-star me-2" aria-hidden="true"></i> Features</h3>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-md-6 mb-3">
                <h5><i class="bi bi-file-text text-primary me-2" aria-hidden="true"></i> Citation Analysis</h5>
                <ul>
                  <li>Document-wide citation analysis</li>
                  <li>Selection-based analysis</li>
                  <li>Real-time processing</li>
                  <li>Confidence scoring</li>
                </ul>
              </div>
              <div class="col-md-6 mb-3">
                <h5><i class="bi bi-search text-success me-2" aria-hidden="true"></i> Verification Methods</h5>
                <ul>
                  <li>CourtListener API lookup</li>
                  <li>Summary comparison analysis</li>
                  <li>Multi-iteration verification</li>
                  <li>Adjustable similarity threshold</li>
                </ul>
              </div>
              <div class="col-md-6 mb-3">
                <h5><i class="bi bi-eye text-info me-2" aria-hidden="true"></i> Visual Feedback</h5>
                <ul>
                  <li>Color-coded results (green/red)</li>
                  <li>Detailed accordion view</li>
                  <li>Confidence bars</li>
                  <li>Toggle-able case summaries</li>
                </ul>
              </div>
              <div class="col-md-6 mb-3">
                <h5><i class="bi bi-gear text-warning me-2" aria-hidden="true"></i> Advanced Features</h5>
                <ul>
                  <li>Local PDF search option</li>
                  <li>Batch processing</li>
                  <li>Customizable settings</li>
                  <li>Export options</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- How It Works -->
        <div class="card mb-4">
          <div class="card-header bg-success text-white">
            <h3 class="mb-0"><i class="bi bi-info-circle me-2" aria-hidden="true"></i> How It Works</h3>
          </div>
          <div class="card-body">
            <h5 class="mb-3">How validation works:</h5>
            <ol>
              <li class="mb-2">
                <strong>Citation Extraction:</strong> Extracts case citations from your document using specialized legal citation parsers
              </li>
              <li class="mb-2">
                <strong>API Verification:</strong> Each citation is checked against legal databases like CourtListener
              </li>
              <li class="mb-2">
                <strong>Summary Generation:</strong> Generates multiple summaries using AI for additional verification
              </li>
              <li class="mb-2">
                <strong>Similarity Calculation:</strong> Calculates similarity between summaries to detect hallucinations
              </li>
              <li class="mb-0">
                <strong>Results Display:</strong> Citations with low similarity scores are flagged as potentially hallucinated
              </li>
            </ol>
          </div>
        </div>

        <!-- Usage Instructions -->
        <div class="card mb-4">
          <div class="card-header bg-warning text-dark">
            <h3 class="mb-0"><i class="bi bi-play-circle me-2" aria-hidden="true"></i> Using the add-in</h3>
          </div>
          <div class="card-body">
            <h5 class="mb-3">Basic Usage:</h5>
            <ol>
              <li>Open your legal brief in Microsoft Word</li>
              <li>Click <strong>Citations</strong> (CaseStrainer group) on the Home tab</li>
              <li>Configure settings (iterations: 2-5, threshold: 0.5-0.9)</li>
              <li>Click <strong>Analyze Document</strong></li>
              <li>Review results with confidence scores and case summaries</li>
            </ol>

            <h5 class="mt-4 mb-3">Settings:</h5>
            <ul>
              <li><strong>Iterations (2-5):</strong> More iterations = higher accuracy but slower</li>
              <li><strong>Similarity Threshold (0.5-0.9):</strong> Higher = stricter verification</li>
              <li><strong>Local PDF Search:</strong> Search local PDF repositories (slower but comprehensive)</li>
            </ul>
          </div>
        </div>

        <!-- System Requirements -->
        <div class="card mb-4">
          <div class="card-header bg-secondary text-white">
            <h3 class="mb-0"><i class="bi bi-laptop me-2" aria-hidden="true"></i> System Requirements</h3>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-md-6">
                <h5>Software:</h5>
                <ul>
                  <li>Microsoft Word 2016 or later</li>
                  <li>Office 365 or standalone Office</li>
                  <li>Windows or macOS</li>
                </ul>
              </div>
              <div class="col-md-6">
                <h5>Other:</h5>
                <ul>
                  <li>Internet connection required</li>
                  <li>Connects to: <a href="https://wolf.law.uw.edu/casestrainer/" target="_blank" rel="noopener noreferrer">wolf.law.uw.edu/casestrainer<span class="visually-hidden"> (opens in new tab)</span></a></li>
                  <li>No API key needed</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- Documentation & Support -->
        <div class="card mb-4">
          <div class="card-header bg-dark text-white">
            <h3 class="mb-0"><i class="bi bi-book me-2" aria-hidden="true"></i> Documentation & Support</h3>
          </div>
          <div class="card-body">
            <p>
              For detailed installation instructions, troubleshooting, and development information:
            </p>
            <div class="list-group">
              <a href="https://wolf.law.uw.edu/casestrainer/" 
                 target="_blank" 
                 rel="noopener noreferrer"
                 class="list-group-item list-group-item-action">
                <i class="bi bi-globe me-2" aria-hidden="true"></i> Use CaseStrainer on the Web (wolf.law.uw.edu)<span class="visually-hidden"> (opens in new tab)</span>
              </a>
              <a href="https://github.com/jafrank88/casestrainer/tree/main/docs/WORD_ADDIN.md" 
                 target="_blank" 
                 rel="noopener noreferrer"
                 class="list-group-item list-group-item-action">
                <i class="bi bi-file-text me-2" aria-hidden="true"></i> Complete Word Add-In Documentation<span class="visually-hidden"> (opens in new tab)</span>
              </a>
              <a href="https://github.com/jafrank88/casestrainer/tree/main/casestrainer-vue-new/public/word-addin" 
                 target="_blank" 
                 rel="noopener noreferrer"
                 class="list-group-item list-group-item-action">
                <i class="bi bi-download me-2" aria-hidden="true"></i> Word add-in source (<code>public/word-addin</code>)<span class="visually-hidden"> (opens in new tab)</span>
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
                <i class="bi bi-bug me-2" aria-hidden="true"></i> Report Issues<span class="visually-hidden"> (opens in new tab)</span>
              </a>
            </div>
          </div>
        </div>

        <!-- Roadmap -->
        <div class="card mb-4">
          <div class="card-header bg-info text-white">
            <h3 class="mb-0"><i class="bi bi-calendar-check me-2" aria-hidden="true"></i> Roadmap</h3>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-md-4">
                <h5>Current (v1.0)</h5>
                <ul>
                  <li>✅ Basic citation detection</li>
                  <li>✅ API integration</li>
                  <li>✅ Confidence scoring</li>
                  <li>✅ Summary comparison</li>
                </ul>
              </div>
              <div class="col-md-4">
                <h5>Planned (v1.1)</h5>
                <ul>
                  <li>Batch document processing</li>
                  <li>BibTeX/EndNote export</li>
                  <li>Custom verification rules</li>
                  <li>Team collaboration</li>
                </ul>
              </div>
              <div class="col-md-4">
                <h5>Future roadmap</h5>
                <ul>
                  <li>ML citation classifier</li>
                  <li>Real-time verification</li>
                  <li>Citation management tools</li>
                  <li>Advanced analytics</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- Call to Action -->
        <div class="text-center">
          <router-link to="/" class="btn btn-primary btn-lg me-2">
            <i class="bi bi-house-door me-1" aria-hidden="true"></i> Back to Home
          </router-link>
          <a href="https://wolf.law.uw.edu/casestrainer/word-addin/manifest.xml" 
             target="_blank" 
             rel="noopener noreferrer"
             class="btn btn-success btn-lg me-2"
             aria-label="Open production Word manifest (opens in new tab)">
            <i class="bi bi-download me-1" aria-hidden="true"></i> Production manifest
          </a>
          <a href="https://github.com/jafrank88/casestrainer/tree/main/docs/WORD_ADDIN.md" 
             target="_blank" 
             rel="noopener noreferrer"
             class="btn btn-outline-secondary btn-lg"
             aria-label="View Word add-in documentation (opens in new tab)">
            <i class="bi bi-book me-1" aria-hidden="true"></i> View Documentation
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'WordPlugin'
}
</script>

<style scoped>
.display-4 {
  font-weight: 700;
}
</style> 