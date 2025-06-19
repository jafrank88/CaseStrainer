<template>
  <div class="text-paste">
    <div class="card">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">Paste Text</h5>
      </div>
      <div class="card-body">
        <div v-if="error" class="alert alert-danger">
          <strong>Error:</strong> {{ error }}
        </div>
        
        <div class="mb-3">
          <label for="textInput" class="form-label">Paste your legal text to analyze for citations</label>
          <textarea
            id="textInput"
            class="form-control"
            v-model="text"
            rows="10"
            placeholder="Paste your legal document text here..."
            :disabled="isAnalyzing"
          ></textarea>
        </div>
        
        <div class="form-check form-switch mb-3">
          <input 
            class="form-check-input" 
            type="checkbox" 
            id="includeContext" 
            v-model="includeContext"
          >
          <label class="form-check-label" for="includeContext">Include context around citations</label>
        </div>
        
        <button 
          class="btn btn-primary" 
          @click="analyzeText"
          :disabled="!text || isAnalyzing"
        >
          <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
          {{ isAnalyzing ? 'Analyzing...' : 'Analyze Text' }}
        </button>
        
        <div v-if="false" class="mt-4">
          <pre>{{ results }}</pre>
          <h5>Analysis Results</h5>
          <div :class="['alert', getAlertClass(results.valid)]">
            <p><strong>Status:</strong> {{ results.valid ? 'Valid' : 'Invalid' }}</p>
            <p v-if="results.message">{{ results.message }}</p>
            
            <div v-if="results.citations && results.citations.length > 0">
              <h6>Found {{ results.citations.length }} citations:</h6>
              <!-- Retry All Button -->
              <button v-if="retryCitations.length > 0" class="btn btn-warning mb-2" @click="retryAllCitations" :disabled="isAnalyzing">
                Retry All Failed
              </button>
              <div class="table-responsive">
                <table class="table table-striped table-hover mt-2">
                  <thead>
                    <tr>
                      <th>Citation</th>
                      <th>Status</th>
                      <th v-if="includeContext">Context</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(citation, index) in results.citations" :key="index">
                      <td>
                        <strong>{{ citation.citation }}</strong>
                        <div v-if="citation.correction" class="text-muted small">
                          Suggested: {{ citation.correction }}
                        </div>
                      </td>
                      <td>
                        <span :class="['badge', getStatusBadgeClass(citation)]">
                          {{ getStatusText(citation) }}
                        </span>
                      </td>
                      <td v-if="includeContext">
                        <div v-if="citation.context" class="context-preview">
                          {{ citation.context }}
                        </div>
                        <div v-else class="text-muted small">No context available</div>
                      </td>
                      <td>
                        <button v-if="citation.status === 'retry'" class="btn btn-sm btn-warning" @click="retrySingleCitation(citation)">
                          Retry
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            
            <div v-else class="alert alert-info">
              No citations found in the provided text.
            </div>
            
            <div v-if="results.summary" class="mt-3">
              <h6>Summary:</h6>
              <!--
              <ul class="list-group">
                <li class="list-group-item d-flex justify-content-between align-items-center">
                  Total Citations
                  <span class="badge bg-primary rounded-pill">{{ results.summary.total || 0 }}</span>
                </li>
                <li class="list-group-item d-flex justify-content-between align-items-center">
                  Valid Citations
                  <span class="badge bg-success rounded-pill">{{ results.summary.valid || 0 }}</span>
                </li>
                <li class="list-group-item d-flex justify-content-between align-items-center">
                  Invalid Citations
                  <span class="badge bg-danger rounded-pill">{{ results.summary.invalid || 0 }}</span>
                </li>
              </ul>
              -->
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onUnmounted } from 'vue';
import { useAnalysisService } from '@/services/analysisService';

export default {
  name: 'TextPaste',
  emits: ['results', 'error', 'loading', 'progress'],
  setup(props, { emit }) {
    const text = ref('');
    const isAnalyzing = ref(false);
    const error = ref(null);
    const results = ref(null);
    const includeContext = ref(false);
    
    const {
      analyzeContent,
      cleanup,
      validators,
      textUtils
    } = useAnalysisService();
    
    const analyzeText = async () => {
      if (!text.value) {
        error.value = 'Please enter text to analyze';
        return;
      }
      
      try {
        // Validate text
        validators.validateText(text.value);
        
        // Clean text
        const cleanedText = textUtils.cleanText(text.value);
        
        isAnalyzing.value = true;
        error.value = null;
        results.value = null;
        emit('loading', true);
        
        try {
          const processedResults = await analyzeContent(
            { text: cleanedText },
            'text',
            { 
              preserve_formatting: true,
              onProgress: (progress) => {
                // Emit progress updates to parent component
                emit('progress', progress);
              }
            }
          );
          
          results.value = processedResults;
          emit('results', processedResults);
          
        } catch (err) {
          error.value = err.message;
          emit('error', err);
        }
        
      } catch (err) {
        error.value = err.message;
        emit('error', { message: err.message, status: 400 });
      } finally {
        isAnalyzing.value = false;
        emit('loading', false);
      }
    };
    
    onUnmounted(() => {
      cleanup();
    });
    
    const getAlertClass = (isValid) => {
      return {
        'alert-success': isValid === true,
        'alert-danger': isValid === false,
        'alert-info': isValid === null || isValid === undefined
      };
    };
    
    // Computed: retry citations
    const retryCitations = computed(() => {
      if (!results.value || !results.value.citations) return [];
      return results.value.citations.filter(c => c.status === 'retry');
    });

    // Retry all failed citations
    const retryAllCitations = () => {
      if (retryCitations.value.length === 0) return;
      text.value = retryCitations.value.map(c => c.citation).join('\n');
      analyzeText();
    };

    // Retry a single citation
    const retrySingleCitation = (citation) => {
      text.value = citation.citation;
      analyzeText();
    };
    
    const getStatusBadgeClass = (citation) => {
      if (citation.valid || citation.verified || citation.data?.valid || citation.data?.found || citation.exists) {
        return 'bg-success';
      } else if (isValidCitationFormat(citation)) {
        return 'bg-warning text-dark';
      }
      return 'bg-danger';
    };

    const getStatusText = (citation) => {
      if (citation.valid || citation.verified || citation.data?.valid || citation.data?.found || citation.exists) {
        return 'Verified';
      } else if (isValidCitationFormat(citation)) {
        return 'Valid but Not Verified';
      }
      return 'Invalid';
    };
    
    const isValidCitationFormat = (citation) => {
      const citationText = citation.citation || citation.text || citation.citation_text || 'Unknown Citation';
      
      // Check if it's clearly invalid (like "Filed", "Page", etc.)
      const invalidPatterns = [
        /^filed\s+\d+$/i,
        /^page\s+\d+$/i,
        /^docket\s+\d+$/i,
        /^\d+\s+filed\s+\d+$/i,
        /^\d+\s+page\s+\d+$/i,
        /^\d+\s+docket\s+\d+$/i
      ];
      
      for (const pattern of invalidPatterns) {
        if (pattern.test(citationText)) {
          return false;
        }
      }
      
      // Check if it looks like a valid legal citation format
      const validPatterns = [
        /\d+\s+[A-Z]\.\s*\d+/i,  // e.g., "534 F.3d 1290"
        /\d+\s+[A-Z]{2,}\.\s*\d+/i,  // e.g., "123 Wash. 456"
        /\d+\s+WL\s+\d+/i,  // Westlaw citations
        /\d+\s+U\.S\.\s+\d+/i,  // Supreme Court
        /\d+\s+S\.\s*Ct\.\s+\d+/i,  // Supreme Court
        /\d+\s+[A-Z]\.\s*App\.\s*\d+/i,  // Appellate courts
      ];
      
      for (const pattern of validPatterns) {
        if (pattern.test(citationText)) {
          return true;
        }
      }
      
      return false;
    };
    
    return {
      text,
      isAnalyzing,
      error,
      results,
      includeContext,
      analyzeText,
      getAlertClass,
      retryCitations,
      retryAllCitations,
      retrySingleCitation,
      getStatusBadgeClass,
      getStatusText,
      isValidCitationFormat
    };
  }
};
</script>

<style scoped>
.text-paste {
  width: 100%;
}

.form-check-input:checked {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.form-check-input:focus {
  border-color: #86b7fe;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.form-control {
  min-height: 150px;
  font-family: monospace;
  resize: vertical;
}

.form-control:disabled {
  background-color: #e9ecef;
  cursor: not-allowed;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .card {
    margin-bottom: 1rem;
  }
  
  .btn {
    width: 100%;
    margin-top: 0.5rem;
  }
  
  .form-control {
    font-size: 16px; /* Prevent zoom on mobile */
  }
}
</style>
