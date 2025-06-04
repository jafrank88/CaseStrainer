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
            v-model="pastedText"
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
          :disabled="!pastedText || isAnalyzing"
        >
          <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
          {{ isAnalyzing ? 'Analyzing...' : 'Analyze Text' }}
        </button>
        
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
                      <th v-if="includeContext">Context</th>
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
                      <td v-if="includeContext">
                        <div v-if="citation.context" class="context-preview">
                          {{ citation.context }}
                        </div>
                        <div v-else class="text-muted small">No context available</div>
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
  name: 'TextPaste',
  emits: ['results', 'error'],
  setup(props, { emit }) {
    const pastedText = ref('');
    const isAnalyzing = ref(false);
    const error = ref(null);
    const results = ref(null);
    const includeContext = ref(true);
    
    // Base path for API requests
    const basePath = import.meta.env.VITE_API_BASE_URL || '';
    
    const analyzeText = async () => {
      if (!pastedText.value.trim()) {
        error.value = 'Please enter some text to analyze';
        return;
      }
      
      isAnalyzing.value = true;
      error.value = null;
      results.value = null;
      
      try {
        // Import and use the API utility
        const api = (await import('@/utils/api')).default;
        const response = await api.post('/analyze-text', {
          text: pastedText.value,
          includeContext: includeContext.value
        });
        
        results.value = response;
        emit('results', results.value);
      } catch (err) {
        console.error('Text analysis error:', err);
        error.value = err.response?.data?.message || 'Failed to analyze text';
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
      pastedText,
      isAnalyzing,
      error,
      results,
      includeContext,
      analyzeText,
      getAlertClass
    };
  }
};
</script>

<style scoped>
.text-paste {
  width: 100%;
}

.form-control {
  min-height: 150px;
}

.context-preview {
  max-height: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  font-size: 0.9em;
  color: #495057;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
  padding: 0.5rem;
  margin-top: 0.5rem;
}

.table {
  width: 100%;
  margin-bottom: 1rem;
  color: #212529;
  vertical-align: top;
  border-color: #dee2e6;
}

.table th,
.table td {
  padding: 0.75rem;
  vertical-align: top;
  border-top: 1px solid #dee2e6;
}

.table thead th {
  vertical-align: bottom;
  border-bottom: 2px solid #dee2e6;
  background-color: #f8f9fa;
}

.table-striped > tbody > tr:nth-of-type(odd) > * {
  --bs-table-accent-bg: rgba(0, 0, 0, 0.02);
  color: var(--bs-table-striped-color);
}

.table-hover > tbody > tr:hover > * {
  --bs-table-accent-bg: rgba(0, 0, 0, 0.075);
  color: var(--bs-table-hover-color);
}

.table-responsive {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .table {
    display: block;
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  
  .table > :not(caption) > * > * {
    padding: 0.5rem;
  }
  
  .form-control {
    font-size: 16px; /* Prevent zoom on mobile */
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .table {
    color: #dee2e6;
    border-color: #495057;
  }
  
  .table thead th {
    background-color: #343a40;
    border-bottom-color: #6c757d;
  }
  
  .table-striped > tbody > tr:nth-of-type(odd) > * {
    --bs-table-accent-bg: rgba(255, 255, 255, 0.05);
  }
  
  .table-hover > tbody > tr:hover > * {
    --bs-table-accent-bg: rgba(255, 255, 255, 0.075);
  }
  
  .context-preview {
    background-color: #2c3034;
    color: #e9ecef;
  }
}
</style>
