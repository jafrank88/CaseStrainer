// CourtListener Gaps Component
class CourtListenerGaps {
  constructor() {
    this.citations = [];
    this.loading = true;
    this.error = null;
    this.searchQuery = '';
  }

  // Initialize the component
  init() {
    this.fetchCitations();
    this.setupEventListeners();
  }

  // Set up event listeners
  setupEventListeners() {
    // Search input
    const searchInput = document.getElementById('cl-gaps-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value;
        this.renderCitations();
      });
    }
  }

  // Fetch citations from the API
  async fetchCitations() {
    this.loading = true;
    
    // Check if citations are still being processed
    if (window.citationProcessing && window.citationProcessing.isProcessing) {
      this.renderProcessing();
      return;
    }
    
    // Check if we have an analysis ID from the current session
    const currentAnalysisId = window.analysisResults ? window.analysisResults.analysis_id : null;
    if (!currentAnalysisId) {
      this.renderNoAnalysis();
      return;
    }
    
    this.citations = [];
    this.renderLoading();
    
    try {
      // Check if we have analysis results in the window object
      if (window.analysisResults && window.analysisResults.citations) {
        console.log('Using analysis results from window object');
        
        // Include all citations as potential gaps in CourtListener
        // This ensures we show all citations that weren't explicitly validated by CourtListener
        const gapCitations = window.analysisResults.citations.map(c => ({
          citation_text: c.citation,
          case_name: c.found_case_name || 'Unknown',
          found: c.found || false,
          source: c.source || 'Not found',
          confidence: c.confidence || 0.0,
          explanation: c.explanation || 'Not in CourtListener database',
          document: ''
        }));
        
        console.log('Filtered gap citations:', gapCitations);
        
        if (gapCitations.length > 0) {
          this.citations = gapCitations;
          this.loading = false;
          this.renderCitations();
          return;
        }
      }
      
      // If no window.analysisResults or no citations in it, fetch from API
      const basePath = window.location.pathname.includes('/casestrainer/') ? '/casestrainer' : '';
      const apiUrl = `${basePath}/api/courtlistener_gaps`;
      
      console.log('Fetching from API:', apiUrl);
      const response = await fetch(`${basePath}/api/courtlistener_gaps`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('CourtListener gaps data from API:', data);
      
      if (data && data.citations) {
        this.citations = data.citations;
        this.loading = false;
        this.renderCitations();
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('Error fetching CourtListener gaps:', error);
      this.error = error.message || 'An error occurred while fetching citations';
      this.loading = false;
      this.renderError();
    }
  }

  // Filter citations based on search query
  getFilteredCitations() {
    if (!this.searchQuery) {
      return this.citations;
    }
    
    const query = this.searchQuery.toLowerCase();
    return this.citations.filter(citation => 
      (citation.citation_text && citation.citation_text.toLowerCase().includes(query)) ||
      (citation.case_name && citation.case_name.toLowerCase().includes(query)) ||
      (citation.source && citation.source.toLowerCase().includes(query))
    );
  }

  // Get CSS class for confidence level
  getConfidenceClass(confidence) {
    if (confidence >= 0.8) {
      return 'bg-success';
    } else if (confidence >= 0.5) {
      return 'bg-warning';
    } else {
      return 'bg-danger';
    }
  }

  // Render loading state
  renderLoading() {
    const container = document.getElementById('cl-gaps-container');
    if (container) {
      container.innerHTML = `
        <div class="text-center py-4">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2">Loading citations...</p>
        </div>
      `;
    }
  }
  
  // Render processing state
  renderProcessing() {
    const container = document.getElementById('cl-gaps-container');
    if (container) {
      // Calculate elapsed time if available
      let elapsedText = '';
      if (window.citationProcessing && window.citationProcessing.startTime) {
        const elapsed = Math.floor((new Date() - window.citationProcessing.startTime) / 1000);
        elapsedText = `<div class="mt-2">Elapsed time: ${elapsed} seconds</div>`;
      }
      
      container.innerHTML = `
        <div class="alert alert-info">
          <div class="d-flex align-items-center">
            <div class="spinner-border spinner-border-sm me-2" role="status">
              <span class="visually-hidden">Processing...</span>
            </div>
            <div>
              <strong>Citations are still being processed...</strong>
              <p class="mb-0">Please wait for the analysis to complete before viewing the CourtListener Gaps.</p>
              ${elapsedText}
            </div>
          </div>
        </div>
      `;
    }
  }

  // Render error state
  renderError() {
    const container = document.getElementById('cl-gaps-container');
    if (container) {
      container.innerHTML = `
        <div class="alert alert-danger">
          <h5>Error</h5>
          <p>${this.error}</p>
        </div>
      `;
    }
  }
  
  // Render no analysis state
  renderNoAnalysis() {
    const container = document.getElementById('cl-gaps-container');
    if (container) {
      container.innerHTML = `
        <div class="alert alert-warning">
          <div class="d-flex align-items-center">
            <i class="bi bi-exclamation-triangle-fill me-2"></i>
            <div>
              <strong>No citation analysis available</strong>
              <p class="mb-0">Please upload a document or paste text in the appropriate tab to analyze citations.</p>
            </div>
          </div>
          <div class="mt-3">
            <button class="btn btn-sm btn-primary" id="goto-upload-btn">
              <i class="bi bi-upload"></i> Go to Upload Tab
            </button>
          </div>
        </div>
      `;
      
      // Add event listener to the button
      const gotoUploadBtn = container.querySelector('#goto-upload-btn');
      if (gotoUploadBtn) {
        gotoUploadBtn.addEventListener('click', () => {
          const uploadTab = document.getElementById('upload-tab');
          if (uploadTab) {
            uploadTab.click();
          }
        });
      }
    }
  }

  // Render citations
  renderCitations() {
    const container = document.getElementById('cl-gaps-container');
    if (!container) return;
    
    const filteredCitations = this.getFilteredCitations();
    
    if (this.loading) {
      this.renderLoading();
      return;
    }
    
    if (this.error) {
      this.renderError();
      return;
    }
    
    if (filteredCitations.length === 0) {
      container.innerHTML = `
        <div class="alert alert-info">
          <p>No citations found that represent gaps in the CourtListener database.</p>
        </div>
      `;
      return;
    }
    
    // Render search box
    let html = `
      <div class="mb-3">
        <input 
          type="text" 
          class="form-control" 
          id="cl-gaps-search"
          placeholder="Search citations..." 
          value="${this.searchQuery}"
        >
      </div>
    `;
    
    // Render table
    html += `
      <div class="table-responsive">
        <table class="table table-striped table-hover">
          <thead>
            <tr>
              <th>Citation</th>
              <th>Case Name</th>
              <th>Status</th>
              <th>Source</th>
              <th>Confidence</th>
              <th>Explanation</th>
            </tr>
          </thead>
          <tbody>
    `;
    
    // Add rows for each citation
    filteredCitations.forEach(citation => {
      const statusBadge = citation.found 
        ? '<span class="badge bg-success">Found Elsewhere</span>' 
        : '<span class="badge bg-danger">Not Found</span>';
      
      const confidenceBadge = citation.found
        ? `<div class="progress">
            <div class="progress-bar ${this.getConfidenceClass(citation.confidence)}" 
                 role="progressbar" 
                 style="width: ${citation.confidence * 100}%" 
                 aria-valuenow="${citation.confidence * 100}" 
                 aria-valuemin="0" 
                 aria-valuemax="100">
              ${Math.round(citation.confidence * 100)}%
            </div>
          </div>`
        : '<span class="badge bg-secondary">N/A</span>';
      
      html += `
        <tr>
          <td>${citation.citation_text}</td>
          <td>${citation.case_name || 'Unknown'}</td>
          <td>${statusBadge}</td>
          <td>${citation.source || 'None'}</td>
          <td>${confidenceBadge}</td>
          <td>${citation.explanation || 'No explanation available'}</td>
        </tr>
      `;
    });
    
    html += `
          </tbody>
        </table>
      </div>
    `;
    
    container.innerHTML = html;
    this.setupEventListeners();
  }
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Check if we're on the right page
  const container = document.getElementById('cl-gaps-container');
  if (container) {
    const clGaps = new CourtListenerGaps();
    clGaps.init();
  }
});
