<template>
  <div class="enhanced-text-paste">
    <div class="card">
      <div class="bg-primary text-white p-3 rounded-top">
  <h5 class="mb-0">Paste Text</h5>
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
      <ReusableResults :results="textAnalysisResult" />
    </div>
  </div>
</template>

<script>
import axios from 'axios';

import ProgressBar from './ProgressBar.vue';
import ReusableResults from './ReusableResults.vue';

export default {
  name: 'EnhancedTextPaste',
  components: {
    ProgressBar,
    ReusableResults
  },
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
      this.debugInfo += `Request to ${this.basePath}/api/analyze: [Text data]\n`;

      axios.post(`${this.basePath}/api/analyze`, { text: this.pastedText })
      .then(response => {
        // Add to debug info
        this.debugInfo += `Response received: Processing data...\n`;
        const jsonString = JSON.stringify(response.data, null, 2);
        this.debugInfo += `Success: ${jsonString.substring(0, 500)}${jsonString.length > 500 ? '... [truncated]' : ''}\n`;

        this.textAnalysisResult = response.data;
      })
      .catch(error => {
        alert(`Error analyzing text: ${error.response?.data?.message || error.message || 'Unknown error'}`);
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
