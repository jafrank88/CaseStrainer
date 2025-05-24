<template>
  <div class="text-paste">
    <div class="card">
      <div class="card-header">
        <h5>Paste Text</h5>
      </div>
      <div class="card-body">
        <div class="mb-3">
          <label for="textInput" class="form-label">Paste text containing legal citations</label>
          <textarea 
            class="form-control" 
            id="textInput" 
            rows="10" 
            v-model="text"
            placeholder="Paste text from a legal document containing citations..."
          ></textarea>
        </div>
        
        <button class="btn btn-primary" @click="analyzeText" :disabled="!text || isAnalyzing">
          <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
          {{ isAnalyzing ? 'Analyzing...' : 'Analyze Citations' }}
        </button>
      </div>
    </div>
    
    <div v-if="results" class="mt-4">
      
      <div class="card">
        <div class="card-header">
          <ul class="nav nav-tabs card-header-tabs" id="result-tabs">
            <li class="nav-item">
              <a class="nav-link active" id="results-tab" data-bs-toggle="tab" href="#results-content" role="tab">
                Analysis Results
              </a>
            </li>

          </ul>
        </div>
        <div class="card-body">
          <div class="tab-content">
            <!-- Results Tab -->
            <div class="tab-pane fade show active" id="results-content" role="tabpanel">
              <div class="alert alert-success">
                <h5>Analysis complete!</h5>
                <p>Found {{ results.totalCitations }} citations in your text.</p>
              </div>
              
              <div class="mt-3">
                <h6>Citation Summary:</h6>
                <ul class="list-group">
                  <li class="list-group-item d-flex justify-content-between align-items-center">
                    Confirmed Citations
                    <span class="badge bg-success rounded-pill">{{ results.confirmedCount }}</span>
                  </li>
                  <li class="list-group-item d-flex justify-content-between align-items-center">
                    Unconfirmed Citations
                    <span class="badge bg-danger rounded-pill">{{ results.unconfirmedCount }}</span>
                  </li>
                  <li class="list-group-item d-flex justify-content-between align-items-center">
                    Verified with Multi-tool
                    <span class="badge bg-info rounded-pill">{{ results.multitoolCount }}</span>
                  </li>
                </ul>
              </div>
              
              <div class="mt-3">
                <button class="btn btn-outline-primary me-2" @click="viewConfirmedCitations">
                  View Confirmed Citations
                </button>
                <button class="btn btn-outline-danger me-2" @click="viewUnconfirmedCitations">
                  View Unconfirmed Citations
                </button>
                <button class="btn btn-outline-info" @click="viewMultitoolCitations">
                  View Multi-tool Verified
                </button>
              </div>
            </div>
            

          </div>
        </div>
      </div>
    </div>
    
    <div v-if="error" class="mt-4 alert alert-danger">
      <h5>Error</h5>
      <p>{{ error }}</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

import ProgressBar from './ProgressBar.vue';
import ReusableResults from './ReusableResults.vue';

export default {
  name: 'TextPaste',
  components: {
    ProgressBar,
    ReusableResults
  },
  data() {
    return {
      text: '',
      isAnalyzing: false,
      results: null,
      error: null,
      debugInfo: ''
    };
  },
  methods: {
    async analyzeText() {
      if (!this.text) {
        this.error = 'Please enter some text to analyze';
        return;
      }
      
      this.isAnalyzing = true;
      this.error = null;
      
      // Clear previous debug info
      this.debugInfo = 'Debug: Starting text analysis...\n';
      
      try {
        // Add to debug info
        this.debugInfo += `Request to /api/analyze: [Text data]\n`; // Only for backend logging
        
        const response = await axios.post('/api/analyze', { text: this.text, debugInfo: this.debugInfo });
        
        // Add to debug info
        this.debugInfo += `Response received: Processing data...\n`;
        this.debugInfo += `Success: ${JSON.stringify(response.data, null, 2)}\n`;
        
        this.results = {
          totalCitations: response.data.citations.length,
          confirmedCount: response.data.citations.filter(c => c.valid).length,
          unconfirmedCount: response.data.citations.filter(c => !c.valid).length,
          multitoolCount: response.data.citations.filter(c => c.valid && c.source !== 'courtlistener_api').length,
          analysisId: response.data.analysis_id,
          citations: response.data.citations
        };
        
        // Store the results in localStorage for other components to access
        localStorage.setItem('lastAnalysisResults', JSON.stringify(this.results));
        
      } catch (error) {
        console.error('Error analyzing text:', error);
        this.error = error.response?.data?.error || 'An error occurred while analyzing the text';
        
        // Add error to debug info
        this.debugInfo += `Error: ${error.message}\n`;
        if (error.response) {
          this.debugInfo += `Response status: ${error.response.status}\n`;
          this.debugInfo += `Response data: ${JSON.stringify(error.response.data, null, 2)}\n`;
        }
      } finally {
        this.isAnalyzing = false;
      }
    },
    viewConfirmedCitations() {
      // Navigate to confirmed citations view
      this.$router.push('/confirmed-citations');
    },
    viewUnconfirmedCitations() {
      // Navigate to unconfirmed citations view
      this.$router.push('/unconfirmed-citations');
    },
    viewMultitoolCitations() {
      // Navigate to multi-tool verified citations view
      this.$router.push('/multitool-confirmed');
    }
  }
};
</script>

<style scoped>
.text-paste {
  margin-bottom: 2rem;
}
</style>
