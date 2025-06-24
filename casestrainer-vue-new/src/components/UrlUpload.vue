<template>
  <div class="url-upload">
    <div class="card">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">Analyze Web Content</h5>
      </div>
      <div class="card-body">
        <div v-if="error" class="alert alert-danger">
          <strong>Error:</strong> {{ error }}
        </div>
        
        <div class="mb-3">
          <label for="urlInput" class="form-label">Enter a URL to analyze for citations</label>
          <div class="input-group">
            <span class="input-group-text"><i class="bi bi-link-45deg"></i></span>
            <input
              type="url"
              id="urlInput"
              class="form-control"
              v-model="url"
              placeholder="https://example.com/legal-document"
              :disabled="isAnalyzing"
              @keyup.enter="analyzeUrl"
            >
            <button 
              class="btn btn-primary" 
              @click="analyzeUrl"
              :disabled="!isValidUrl || isAnalyzing"
            >
              <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              {{ isAnalyzing ? 'Analyzing...' : 'Analyze' }}
            </button>
          </div>
          <div class="form-text">Enter a valid URL to a web page containing legal citations</div>
        </div>
        
        <!-- Results/No Results/No Input Message -->
        <div class="mt-4">
          <div v-if="results && results.citations && results.citations.length > 0">
            <h5>Analysis Results</h5>
            <div class="table-responsive">
              <table class="table table-striped table-hover mt-2">
                <thead>
                  <tr>
                    <th>Citation</th>
                    <th>Status</th>
                    <th>Source</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(citation, index) in results.citations" :key="index">
                    <td>
                      <strong>{{ citation.citation }}</strong>
                      <div v-if="citation.correction" class="text-muted small">
                        Suggested: {{ citation.correction }}
                      </div>
                      <div v-if="citation.case_name_mismatch" class="alert alert-warning p-1 mt-1 mb-0">
                        <i class="bi bi-exclamation-triangle me-1"></i>
                        <span>Case name differs. Extracted: <b>{{ citation.extracted_case_name }}</b>, Source: <b>{{ citation.case_name }}</b></span>
                        <div v-if="citation.note" class="small text-muted">{{ citation.note }}</div>
                      </div>
                      <div v-else-if="citation.case_name && citation.extracted_case_name && citation.case_name !== citation.extracted_case_name" class="text-muted small">
                        <span>Extracted: <b>{{ citation.extracted_case_name }}</b>, Source: <b>{{ citation.case_name }}</b></span>
                      </div>
                    </td>
                    <td>
                      <span v-if="citation.verified" class="badge bg-success">Verified</span>
                      <span v-else-if="citation.url" class="badge bg-info text-dark">Citation found, but not verified</span>
                      <span v-else class="badge bg-secondary">Not Verified</span>
                    </td>
                    <td>
                      <a v-if="citation.url" :href="citation.url" target="_blank" class="text-decoration-none">
                        <i class="bi bi-box-arrow-up-right me-1"></i>View Source
                      </a>
                      <span v-else class="text-muted">N/A</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div v-else-if="results && (!results.citations || results.citations.length === 0) && !error" class="alert alert-info">
            Analysis complete. No citations were found in the provided document.
          </div>
          <div v-else-if="!results && !isAnalyzing && !error" class="alert alert-secondary">
            No results to display. Please enter a URL and wait for analysis.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onUnmounted } from 'vue';
import { useAnalysisService } from '@/services/analysisService';

let pollInterval = null;

export default {
  name: 'UrlUpload',
  emits: ['results', 'error', 'loading', 'progress'],
  setup(props, { emit }) {
    const url = ref('');
    const isAnalyzing = ref(false);
    const error = ref(null);
    const results = ref(null);
    
    const {
      analyzeContent,
      cleanup,
      validators
    } = useAnalysisService();
    
    // Validate URL format
    const isValidUrl = computed(() => {
      try {
        validators.validateUrl(url.value);
        return true;
      } catch {
        return false;
      }
    });
    
    const analyzeUrl = async () => {
      if (!url.value) {
        error.value = 'Please enter a URL to analyze';
        return;
      }
      
      try {
        // Validate URL
        validators.validateUrl(url.value);
        
        isAnalyzing.value = true;
        error.value = null;
        results.value = null;
        emit('loading', true);
        
        try {
          const processedResults = await analyzeContent(
            { url: url.value },
            'url',
            {
              follow_redirects: true,
              timeout: 30000, // 30 seconds for URL fetch
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
      url,
      isAnalyzing,
      error,
      results,
      isValidUrl,
      analyzeUrl,
      getAlertClass,
      getStatusBadgeClass,
      getStatusText,
      isValidCitationFormat
    };
  }
};
</script>

<style scoped>
.url-upload {
  width: 100%;
}

.input-group-text {
  background-color: #f8f9fa;
  border-right: none;
}

.input-group .form-control {
  border-left: none;
}

.input-group .form-control:focus {
  border-color: #86b7fe;
  box-shadow: none;
}

.input-group .form-control:focus + .input-group-text {
  border-color: #86b7fe;
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
  
  .input-group {
    flex-direction: column;
  }
  
  .input-group-text {
    border-radius: 0.25rem 0.25rem 0 0 !important;
    border-right: 1px solid #ced4da;
    border-bottom: none;
  }
  
  .input-group .form-control {
    border-radius: 0 0 0.25rem 0.25rem !important;
    border-left: 1px solid #ced4da;
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
