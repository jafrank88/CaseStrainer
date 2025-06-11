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
        
        <div v-if="results" class="mt-4">
          <h5>Analysis Results</h5>
          <div :class="['alert', getAlertClass(results.valid)]">
            <p><strong>Status:</strong> {{ results.valid ? 'Valid' : 'Invalid' }}</p>
            <p v-if="results.message">{{ results.message }}</p>
            
            <div v-if="results.citations && results.citations.length > 0">
              <h6>Found {{ results.citations.length }} citations:</h6>
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
                        <strong>{{ citation.text }}</strong>
                        <div v-if="citation.correction" class="text-muted small">
                          Suggested: {{ citation.correction }}
                        </div>
                      </td>
                      <td>
                        <span :class="['badge', citation.valid ? 'bg-success' : 'bg-danger']">
                          {{ citation.valid ? 'Valid' : 'Invalid' }}
                        </span>
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
            
            <div v-else class="alert alert-info">
              No citations found in the provided URL content.
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';

export default {
  name: 'UrlUpload',
  emits: ['results', 'error'],
  setup(props, { emit }) {
    const url = ref('');
    const isAnalyzing = ref(false);
    const error = ref(null);
    const results = ref(null);
    
    // Base path for API requests
    const basePath = import.meta.env.VITE_API_BASE_URL || '';
    
    // Validate URL format
    const isValidUrl = computed(() => {
      try {
        new URL(url.value);
        return true;
      } catch {
        return false;
      }
    });
    
    const analyzeUrl = async () => {
      if (!isValidUrl.value) {
        error.value = 'Please enter a valid URL';
        return;
      }
      
      isAnalyzing.value = true;
      error.value = null;
      results.value = null;
      
      try {
        // Import and use the API utility
        const api = (await import('@/utils/api')).default;
        const response = await api.post('/casestrainer/api/analyze', {
          url: url.value
        });
        
        // Transform the backend response to match frontend expectations
        const responseData = response.data;
        const transformedResults = {
          valid: responseData.validation_results?.some(r => r.verified) || false,
          message: `Found ${responseData.citations_count || 0} citations`,
          citations: (responseData.validation_results || []).map(item => ({
            text: item.citation || '',
            valid: item.verified || false,
            source: item.validation_method || 'unknown',
            correction: item.explanation || '',
            url: item.url || '',
            case_name: item.case_name || '',
            confidence: item.confidence || 0,
            name_match: item.name_match || false
          })),
          metadata: {
            analysis_id: responseData.analysis_id,
            source_url: url.value
          }
        };
        
        results.value = transformedResults;
        emit('results', transformedResults);
      } catch (err) {
        console.error('URL analysis error:', err);
        error.value = err.response?.data?.message || 'Failed to analyze URL content';
        emit('error', error.value);
      } finally {
        isAnalyzing.value = false;
      }
    };
    
    const getAlertClass = (isValid) => {
      return {
        'alert-success': isValid === true,
        'alert-danger': isValid === false,
        'alert-info': isValid === null || isValid === undefined
      };
    };
    
    return {
      url,
      isAnalyzing,
      error,
      results,
      isValidUrl,
      analyzeUrl,
      getAlertClass
    };
  }
};
</script>

<style scoped>
.url-upload {
  width: 100%;
}

.form-control:disabled {
  background-color: #e9ecef;
  opacity: 1;
}

.table th, .table td {
  vertical-align: middle;
}

.badge {
  font-size: 0.8em;
  padding: 0.35em 0.65em;
}
</style>
