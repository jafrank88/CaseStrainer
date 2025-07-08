<template>
  <div class="citation-progress-tracker">
    <!-- Progress Container -->
    <div 
      v-if="showProgress" 
      :class="['progress-container', progressStatus]"
      :data-status="progressData.status"
    >
      <div class="progress-header">
        <h4 class="progress-title">Citation Analysis</h4>
        <span class="progress-percentage">{{ Math.round(progressData.progress) }}%</span>
      </div>
      
      <div class="progress-bar-container" role="progressbar" :aria-valuenow="progressData.progress">
        <div 
          class="progress-bar" 
          :style="{ width: progressData.progress + '%' }"
        ></div>
      </div>
      
      <div class="progress-status">{{ progressData.message }}</div>
      
      <div class="progress-details">
        <div class="progress-steps">
          <span>Step {{ progressData.currentStep }} of {{ progressData.totalSteps }}</span>
          <span>•</span>
          <span>{{ progressData.resultsCount }} citations found</span>
        </div>
        <div v-if="progressData.estimatedCompletion" class="progress-estimate">
          ~{{ formatTime(progressData.estimatedCompletion) }} remaining
        </div>
      </div>
      
      <!-- Partial Results -->
      <div v-if="partialResults.length > 0" class="partial-results">
        <h5>Citations Found:</h5>
        <div 
          v-for="citation in partialResults" 
          :key="citation.id || citation.raw_text"
          class="citation-preview"
        >
          <div class="citation-case-name">{{ citation.case_name || 'Unknown Case' }}</div>
          <div class="citation-details">
            <span class="year">{{ citation.year || 'No year' }}</span>
            <span class="confidence">
              Confidence: {{ Math.round((citation.confidence_score || 0) * 100) }}%
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Error Container -->
    <div v-if="error" class="error-container">
      <div class="alert alert-danger">
        <strong>Error:</strong> {{ error }}
      </div>
    </div>
    
    <!-- Final Results -->
    <div v-if="finalResults && !showProgress" class="final-results">
      <h3>Citation Analysis Complete</h3>
      <p>Found {{ finalResults.results ? finalResults.results.length : 0 }} citations</p>
      
      <div v-if="finalResults.results && finalResults.results.length > 0" class="citations-list">
        <div 
          v-for="citation in finalResults.results" 
          :key="citation.id || citation.raw_text"
          class="citation-item"
        >
          <div class="citation-text">{{ citation.raw_text || citation.text || 'Unknown' }}</div>
          <div class="citation-details">
            <span class="case-name">{{ citation.case_name || 'Unknown Case' }}</span>
            <span class="year">{{ citation.year || 'No year' }}</span>
            <span class="confidence">
              Confidence: {{ Math.round((citation.confidence_score || 0) * 100) }}%
            </span>
          </div>
        </div>
      </div>
      
      <div v-if="finalResults.analysis" class="analysis-summary">
        <h4>Analysis Summary</h4>
        <div class="analysis-details">
          <p><strong>Total Citations:</strong> {{ finalResults.analysis.total_citations || 0 }}</p>
          <p><strong>High Confidence:</strong> {{ finalResults.analysis.high_confidence || 0 }}</p>
          <p><strong>Needs Review:</strong> {{ finalResults.analysis.needs_review || 0 }}</p>
        </div>
      </div>
      
      <div v-if="finalResults.recommendations && finalResults.recommendations.length > 0" class="recommendations">
        <h4>Recommendations</h4>
        <ul>
          <li v-for="rec in finalResults.recommendations" :key="rec.priority + rec.message">
            <strong>{{ rec.priority }}:</strong> {{ rec.message }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CitationProgressTracker',
  props: {
    documentText: {
      type: String,
      required: true
    },
    documentType: {
      type: String,
      default: 'legal_brief'
    },
    autoStart: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      tracker: null,
      showProgress: false,
      progressData: {
        progress: 0,
        message: 'Initializing...',
        currentStep: 0,
        totalSteps: 0,
        resultsCount: 0,
        estimatedCompletion: null,
        status: 'starting'
      },
      partialResults: [],
      finalResults: null,
      error: null,
      isProcessing: false
    }
  },
  mounted() {
    this.initializeTracker();
    if (this.autoStart) {
      this.startAnalysis();
    }
  },
  beforeUnmount() {
    if (this.tracker) {
      this.tracker.stop();
    }
  },
  methods: {
    initializeTracker() {
      // Import the tracker dynamically
      import('/casestrainer/static/js/citation-progress.js').then(() => {
        this.tracker = new window.CitationProgressTracker();
      }).catch(error => {
        console.error('Failed to load citation progress tracker:', error);
        this.error = 'Failed to initialize progress tracker';
      });
    },
    
    async startAnalysis() {
      if (!this.tracker || this.isProcessing) return;
      
      this.isProcessing = true;
      this.showProgress = true;
      this.error = null;
      this.finalResults = null;
      this.partialResults = [];
      
      // Reset progress data
      this.progressData = {
        progress: 0,
        message: 'Starting analysis...',
        currentStep: 0,
        totalSteps: 0,
        resultsCount: 0,
        estimatedCompletion: null,
        status: 'starting'
      };
      
      try {
        const results = await this.tracker.startAnalysisWithSSE(
          this.documentText,
          this.documentType,
          this.handleProgress,
          this.handleComplete,
          this.handleError
        );
        
        this.$emit('analysis-complete', results);
        
      } catch (error) {
        this.handleError(error);
      } finally {
        this.isProcessing = false;
      }
    },
    
    handleProgress(progressData) {
      this.progressData = { ...progressData };
      this.progressStatus = progressData.status;
      
      // Update partial results if available
      if (progressData.partialResults) {
        this.partialResults = [...this.partialResults, ...progressData.partialResults];
      }
      
      this.$emit('progress-update', progressData);
    },
    
    handleComplete(results) {
      this.finalResults = results;
      this.showProgress = false;
      this.progressStatus = 'completed';
      
      this.$emit('analysis-complete', results);
    },
    
    handleError(error) {
      this.error = error.error || error.message || 'Unknown error occurred';
      this.showProgress = false;
      this.progressStatus = 'failed';
      
      this.$emit('analysis-error', error);
    },
    
    formatTime(seconds) {
      if (!seconds || seconds < 0) return 'Unknown';
      
      if (seconds < 60) {
        return `${Math.round(seconds)}s`;
      } else if (seconds < 3600) {
        const minutes = Math.round(seconds / 60);
        return `${minutes}m`;
      } else {
        const hours = Math.round(seconds / 3600);
        return `${hours}h`;
      }
    },
    
    stopAnalysis() {
      if (this.tracker) {
        this.tracker.stop();
      }
      this.isProcessing = false;
      this.showProgress = false;
    },
    
    reset() {
      this.stopAnalysis();
      this.showProgress = false;
      this.progressData = {
        progress: 0,
        message: 'Initializing...',
        currentStep: 0,
        totalSteps: 0,
        resultsCount: 0,
        estimatedCompletion: null,
        status: 'starting'
      };
      this.partialResults = [];
      this.finalResults = null;
      this.error = null;
      this.isProcessing = false;
    }
  }
}
</script>

<style scoped>
/* Import the progress styles */
@import '/casestrainer/static/css/citation-progress.css';

.citation-progress-tracker {
  width: 100%;
}

.analysis-summary {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.analysis-summary h4 {
  margin-bottom: 10px;
  color: #333;
}

.analysis-details p {
  margin: 5px 0;
  color: #6c757d;
}

.recommendations {
  margin-top: 20px;
  padding: 15px;
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 6px;
}

.recommendations h4 {
  margin-bottom: 10px;
  color: #856404;
}

.recommendations ul {
  margin: 0;
  padding-left: 20px;
}

.recommendations li {
  margin: 5px 0;
  color: #856404;
}
</style> 