<template>
  <div class="enhanced-text-paste">
    <div class="card">
      <div class="card-header">
        <h5>Paste Text</h5>
      </div>
      <div class="card-body">
        <div class="mb-3">
          <label for="textInput" class="form-label">Paste legal text to analyze for citations</label>
          <textarea
            class="form-control"
            id="textInput"
            v-model="pastedText"
            rows="10"
            placeholder="Paste your legal document text here..."
          ></textarea>
        </div>
        
        <button 
          class="btn btn-primary" 
          @click="analyzeText"
          :disabled="isAnalyzing || !pastedText"
        >
          <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
          {{ isAnalyzing ? 'Analyzing...' : 'Analyze Citations' }}
        </button>
      </div>
    </div>
    
    <!-- Analysis Results -->
    <div v-if="textAnalysisResult" class="mt-4">
      <div class="card">
        <div class="card-header">
          <ul class="nav nav-tabs card-header-tabs" role="tablist">
            <li class="nav-item" role="presentation">
              <button class="nav-link active" id="results-tab" data-bs-toggle="tab" data-bs-target="#results-content" 
                type="button" role="tab" aria-controls="results-content" aria-selected="true">
                Analysis Results
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button class="nav-link" id="debug-tab" data-bs-toggle="tab" data-bs-target="#debug-content" 
                type="button" role="tab" aria-controls="debug-content" aria-selected="false">
                Debug Information
              </button>
            </li>
          </ul>
        </div>
        <div class="card-body">
          <div class="tab-content">
            <!-- Results Tab -->
            <div class="tab-pane fade show active" id="results-content" role="tabpanel" aria-labelledby="results-tab">
              <div class="alert alert-success">
                <h5>Analysis complete!</h5>
                <p>Found {{ textAnalysisResult.citations_count }} citations in your text.</p>
              </div>
              
              <div class="mt-3">
                <h6>Citation Summary:</h6>
                <ul class="list-group">
                  <li class="list-group-item d-flex justify-content-between align-items-center">
                    Confirmed Citations
                    <span class="badge bg-success rounded-pill">{{ confirmedCount }}</span>
                  </li>
                  <li class="list-group-item d-flex justify-content-between align-items-center">
                    Unconfirmed Citations
                    <span class="badge bg-danger rounded-pill">{{ unconfirmedCount }}</span>
                  </li>
                </ul>
              </div>
            </div>
            
            <!-- Debug Tab -->
            <div class="tab-pane fade" id="debug-content" role="tabpanel" aria-labelledby="debug-tab">
              <div class="card bg-light">
                <div class="card-header bg-secondary text-white">
                  <h6 class="mb-0">Debug Information</h6>
                </div>
                <div class="card-body">
                  <pre class="bg-dark text-light p-3 rounded" style="max-height: 400px; overflow-y: auto;">{{ debugInfo }}</pre>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Citations Table -->
          <div class="mt-4">
            <h6>Citations Found:</h6>
            <div class="table-responsive">
              <table class="table table-striped table-hover">
                <thead>
                  <tr>
                    <th>Citation</th>
                    <th>Status</th>
                    <th>Validation Method</th>
                    <th>Case Name</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(result, index) in textAnalysisResult.validation_results" :key="index">
                    <td>{{ result.citation }}</td>
                    <td>
                      <span class="badge" :class="result.verified ? 'bg-success' : 'bg-danger'">
                        {{ result.verified ? 'Verified' : 'Not Verified' }}
                      </span>
                    </td>
                    <td>
                      <span v-if="result.validation_method" class="badge" :class="getBadgeClass(result.validation_method)">
                        {{ result.validation_method }}
                      </span>
                      <span v-else>-</span>
                    </td>
                    <td>{{ result.case_name || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          
          <div class="mt-3">
            <button class="btn btn-outline-primary me-2" @click="viewConfirmedCitations">View All Confirmed</button>
            <button class="btn btn-outline-danger" @click="viewUnconfirmedCitations">View All Unconfirmed</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'EnhancedTextPaste',
  data() {
    return {
      pastedText: '',
      isAnalyzing: false,
      textAnalysisResult: null,
      error: null,
      debugInfo: ''
    };
  },
  computed: {
    confirmedCount() {
      if (!this.textAnalysisResult || !this.textAnalysisResult.validation_results) {
        return 0;
      }
      return this.textAnalysisResult.validation_results.filter(r => r.verified).length;
    },
    unconfirmedCount() {
      if (!this.textAnalysisResult || !this.textAnalysisResult.validation_results) {
        return 0;
      }
      return this.textAnalysisResult.validation_results.filter(r => !r.verified).length;
    },
    basePath() {
      // Determine the base path for API requests
      const path = window.location.pathname;
      if (path.includes('/casestrainer/')) {
        return '/casestrainer';
      } else {
        return '';
      }
    }
  },
  methods: {
    analyzeText() {
      if (!this.pastedText) {
        alert('Please paste some text to analyze');
        return;
      }
      
      this.isAnalyzing = true;
      this.textAnalysisResult = null;
      
      // Clear previous debug info
      this.debugInfo = 'Debug: Starting text analysis...\n';
      this.debugInfo += `Text length: ${this.pastedText.length} characters\n`;
      
      // Create form data
      const formData = new FormData();
      formData.append('brief_text', this.pastedText);
      
      // Add to debug info
      this.debugInfo += `Request to ${this.basePath}/api/analyze: [Text data]\n`;
      
      // Send request to main API endpoint
      axios.post(`${this.basePath}/api/analyze`, formData)
      .then(response => {
        // Add to debug info
        this.debugInfo += `Response received: Processing data...\n`;
        this.debugInfo += `Success: ${JSON.stringify(response.data, null, 2)}\n`;
        
        this.textAnalysisResult = response.data;
        console.log('Text analysis result:', this.textAnalysisResult);
      })
      .catch(error => {
        console.error('Error analyzing text:', error);
        alert(`Error analyzing text: ${error.response?.data?.message || error.message || 'Unknown error'}`);
        
        // Add error to debug info
        this.debugInfo += `Error: ${error.message}\n`;
        if (error.response) {
          this.debugInfo += `Response status: ${error.response.status}\n`;
          this.debugInfo += `Response data: ${JSON.stringify(error.response.data, null, 2)}\n`;
        }
      })
      .finally(() => {
        this.isAnalyzing = false;
      });
    },
    getBadgeClass(validationMethod) {
      // Return appropriate Bootstrap badge classes based on validation method
      switch(validationMethod) {
        case 'Landmark':
          return 'bg-primary';
        case 'CourtListener':
          return 'bg-success';
        case 'Multitool':
          return 'bg-info';
        case 'Other':
          return 'bg-secondary';
        default:
          return 'bg-dark';
      }
    },
    viewConfirmedCitations() {
      this.$router.push('/unconfirmed-citations?filter=confirmed');
    },
    viewUnconfirmedCitations() {
      this.$router.push('/unconfirmed-citations?filter=unconfirmed');
    }
  }
};
</script>

<style scoped>
.enhanced-text-paste {
  margin-bottom: 2rem;
}
</style>
