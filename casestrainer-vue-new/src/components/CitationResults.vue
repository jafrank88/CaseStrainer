<template>
  <div class="citation-results">
    <div v-if="loading" class="text-center my-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Analyzing citations...</p>
    </div>
    
    <div v-else-if="error" class="alert alert-danger">
      <h5 class="alert-heading">Error</h5>
      <p class="mb-0">{{ error }}</p>
    </div>
    
    <div v-else-if="results && results.citations && results.citations.length > 0" class="results-container">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="mb-0">Citation Analysis Results</h4>
        <div>
          <span class="badge bg-primary me-2">
            Total: {{ results.citations.length }}
          </span>
          <span class="badge bg-success me-2">
            Valid: {{ validCount }}
          </span>
          <span class="badge bg-warning text-dark me-2" v-if="results.citations.some(c => c.confidence < 0.7)">
            Low Confidence: {{ results.citations.filter(c => c.confidence < 0.7).length }}
          </span>
          <span class="badge bg-danger">
            Invalid: {{ invalidCount }}
          </span>
        </div>
      </div>
      
      <div class="table-responsive">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>Citation</th>
              <th>Status</th>
              <th>Type</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(citation, index) in sortedCitations" :key="index" class="align-middle">
              <td>
                <div class="d-flex align-items-center">
                  <span class="citation-text">{{ citation.text }}</span>
                  <button 
                    v-if="citation.correction"
                    class="btn btn-sm btn-outline-secondary ms-2"
                    @click="applyCorrection(citation)"
                    title="Apply correction"
                  >
                    <i class="bi bi-arrow-clockwise"></i>
                  </button>
                </div>
                <div v-if="citation.correction" class="text-muted small mt-1">
                  <i class="bi bi-lightbulb"></i> Suggested: {{ citation.correction }}
                </div>
              </td>
              <td>
                <span :class="['badge', getStatusBadgeClass(citation)]">
                  {{ getStatusText(citation) }}
                </span>
              </td>
              <td>
                <span class="badge bg-info">
                  {{ citation.type || 'Unknown' }}
                </span>
              </td>
              <td>
                <button 
                  class="btn btn-sm btn-outline-primary"
                  @click="toggleDetails(index)"
                >
                  {{ expandedDetails === index ? 'Hide' : 'View' }} Details
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Expanded Details Panels -->
      <div 
        v-for="(citation, index) in sortedCitations" 
        :key="'detail-' + index"
        v-show="expandedCitation === index"
        class="card mb-3"
      >
        <div class="card-header">
          <h5 class="mb-0">Citation Details: {{ citation.text }}</h5>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <h6>Basic Information</h6>
              <dl class="row">
                <dt class="col-sm-4">Status</dt>
                <dd class="col-sm-8">
                  <span :class="['badge', getStatusBadgeClass(citation)]">
                    {{ getStatusText(citation) }}
                  </span>
                  <span v-if="citation.confidence < 0.7" class="ms-2 badge bg-warning text-dark">
                    Low Confidence ({{ Math.round(citation.confidence * 100) }}%)
                  </span>
                </dd>
                
                <dt class="col-sm-4">Source</dt>
                <dd class="col-sm-8">
                  <span class="text-capitalize">{{ citation.source || 'N/A' }}</span>
                  <a v-if="citation.url" :href="citation.url" target="_blank" class="ms-2">
                    <i class="bi bi-box-arrow-up-right"></i>
                  </a>
                </dd>
                
                <dt class="col-sm-4">Case Name</dt>
                <dd class="col-sm-8">{{ citation.case_name || 'N/A' }}</dd>
                
                <dt class="col-sm-4">Confidence</dt>
                <dd class="col-sm-8">
                  <div class="progress" style="height: 20px;">
                    <div 
                      class="progress-bar" 
                      :class="{
                        'bg-success': citation.confidence >= 0.7,
                        'bg-warning': citation.confidence >= 0.4 && citation.confidence < 0.7,
                        'bg-danger': citation.confidence < 0.4
                      }"
                      role="progressbar" 
                      :style="{ width: (citation.confidence * 100) + '%' }"
                      :aria-valuenow="citation.confidence * 100"
                      aria-valuemin="0"
                      aria-valuemax="100"
                    >
                      {{ Math.round(citation.confidence * 100) }}%
                    </div>
                  </div>
                </dd>
              </dl>
            </div>
            
            <div class="col-md-6">
              <h6>Verification</h6>
              <dl class="row">
                <dt class="col-sm-4">Verified</dt>
                <dd class="col-sm-8">
                  <i 
                    class="bi" 
                    :class="(citation.valid || citation.verified) ? 'bi-check-circle-fill text-success' : 'bi-x-circle-fill text-danger'"
                  ></i>
                  {{ (citation.valid || citation.verified) ? 'Yes' : 'No' }}
                </dd>
                
                <dt class="col-sm-4">Confidence</dt>
                <dd class="col-sm-8">
                  <div class="progress" style="height: 20px;">
                    <div 
                      class="progress-bar" 
                      role="progressbar" 
                      :style="{ width: (citation.confidence * 100) + '%' }"
                      :aria-valuenow="citation.confidence * 100"
                      aria-valuemin="0"
                      aria-valuemax="100"
                    >
                      {{ Math.round(citation.confidence * 100) }}%
                    </div>
                  </div>
                </dd>
                
                <dt class="col-sm-4">Source</dt>
                <dd class="col-sm-8">
                  <template v-if="citation.source">
                    <a v-if="citation.sourceUrl" :href="citation.sourceUrl" target="_blank">
                      {{ citation.source }}
                    </a>
                    <span v-else>{{ citation.source }}</span>
                  </template>
                  <span v-else>N/A</span>
                </dd>
              </dl>
            </div>
          </div>
          
          <div v-if="citation.context" class="mt-3">
            <h6>Context</h6>
            <div class="context-box">
              {{ citation.context }}
            </div>
          </div>
          
          <div v-if="citation.metadata" class="mt-3">
            <h6>Additional Metadata</h6>
            <pre class="bg-light p-2 rounded">{{ JSON.stringify(citation.metadata, null, 2) }}</pre>
          </div>
        </div>
      </div>
      
      <div class="d-flex justify-content-between align-items-center mt-4">
        <div>
          <button class="btn btn-outline-secondary me-2" @click="downloadResults('json')">
            <i class="bi bi-download me-1"></i> Download JSON
          </button>
          <button class="btn btn-outline-secondary me-2" @click="downloadResults('csv')">
            <i class="bi bi-file-earmark-spreadsheet me-1"></i> Download CSV
          </button>
          <button class="btn btn-outline-secondary" @click="copyToClipboard">
            <i class="bi bi-clipboard me-1"></i> Copy to Clipboard
          </button>
        </div>
        <div>
          <button class="btn btn-primary" @click="startNewAnalysis">
            <i class="bi bi-arrow-repeat me-1"></i> New Analysis
          </button>
        </div>
      </div>
    </div>
    
    <div v-else class="text-center py-5">
      <div class="text-muted">
        <i class="bi bi-search" style="font-size: 3rem;"></i>
        <h4 class="mt-3">No citations found</h4>
        <p class="mb-0">Try analyzing some legal text to see citation results here.</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';

export default {
  name: 'CitationResults',
  props: {
    results: {
      type: Object,
      default: () => ({
        citations: [],
        metadata: {}
      })
    },
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: ''
    }
  },
  emits: ['new-analysis', 'apply-correction'],
  setup(props, { emit }) {
    const expandedCitation = ref(null);
    
    const validCount = computed(() => {
      return props.results.citations.filter(c => c.valid || c.verified).length;
    });
    
    const invalidCount = computed(() => {
      return props.results.citations.filter(c => !(c.valid || c.verified)).length;
    });
    
    const lowConfidenceCount = computed(() => {
      return props.results?.citations?.filter(c => c.confidence >= 0.4 && c.confidence < 0.7).length || 0;
    });
    
    const showResults = computed(() => {
      return props.results && props.results.citations && props.results.citations.length > 0;
    });
    
    const sortedCitations = computed(() => {
      if (!props.results?.citations) return [];
      // Sort by confidence (highest first) and then by validation status
      return [...props.results.citations].sort((a, b) => {
        // First sort by confidence (descending)
        if (b.confidence !== a.confidence) {
          return b.confidence - a.confidence;
        }
        // Then by validation status (valid first)
        if ((a.valid || a.verified) !== (b.valid || b.verified)) {
          return (a.valid || a.verified) ? -1 : 1;
        }
        return 0;
      });
    });
    
    function getStatusText(citation) {
      if (citation.valid === true || citation.verified === true) return 'Valid';
      if (citation.valid === false || citation.verified === false) return 'Unverified';
      return 'Unknown';
    }
    
    function getStatusBadgeClass(citation) {
      if (citation.valid === true || citation.verified === true) {
        return citation.confidence < 0.7 ? 'bg-warning text-dark' : 'bg-success';
      } else if (citation.valid === false || citation.verified === false) {
        return 'bg-warning text-dark';
      }
      return 'bg-secondary';
    };
    
    const toggleDetails = (index) => {
      expandedDetails.value = expandedDetails.value === index ? null : index;
    };
    
    const startNewAnalysis = () => {
      emit('new-analysis');
    };
    
    const applyCorrection = (citation) => {
      emit('apply-correction', citation);
    };
    
    const downloadResults = (format) => {
      // This would be implemented to handle the download
      console.log(`Downloading results as ${format}`);
      // In a real implementation, this would trigger a file download
    };
    
    const copyToClipboard = () => {
      // This would copy the results to clipboard
      console.log('Copying results to clipboard');
      // In a real implementation, this would use the Clipboard API
    };
    
    return {
      expandedCitation,
      validCount,
      invalidCount,
      lowConfidenceCount,
      showResults,
      sortedCitations,
      getStatusText,
      getStatusBadgeClass,
      toggleDetails: (index) => {
        expandedCitation.value = expandedCitation.value === index ? null : index;
      },
      startNewAnalysis,
      applyCorrection,
      downloadResults,
      copyToClipboard
    };
  }
};
</script>

<style scoped>
.citation-results {
  width: 100%;
}

.results-container {
  animation: fadeIn 0.3s ease-in-out;
}

.citation-text {
  font-family: 'Courier New', monospace;
  font-weight: bold;
}

.context-box {
  background-color: #f8f9fa;
  border-left: 3px solid #0d6efd;
  padding: 1rem;
  border-radius: 0.25rem;
  font-style: italic;
  max-height: 200px;
  overflow-y: auto;
}

.table th {
  background-color: #f8f9fa;
  position: sticky;
  top: 0;
  z-index: 10;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .table-responsive {
    border: 0;
  }
  
  .table thead {
    display: none;
  }
  
  .table, .table tbody, .table tr, .table td {
    display: block;
    width: 100%;
  }
  
  .table tr {
    margin-bottom: 1rem;
    border: 1px solid #dee2e6;
    border-radius: 0.25rem;
  }
  
  .table td {
    text-align: right;
    padding-left: 50%;
    position: relative;
    min-height: 2.5rem;
  }
  
  .table td::before {
    content: attr(data-label);
    position: absolute;
    left: 1rem;
    width: 45%;
    padding-right: 1rem;
    text-align: left;
    font-weight: bold;
  }
  
  .btn {
    width: 100%;
    margin-bottom: 0.5rem;
  }
  
  .d-flex {
    flex-direction: column;
  }
  
  .me-2 {
    margin-right: 0 !important;
    margin-bottom: 0.5rem;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .context-box {
    background-color: #2c3034;
    border-left-color: #0d6efd;
  }
  
  .table th {
    background-color: #2c3034;
  }
  
  .table-striped > tbody > tr:nth-of-type(odd) > * {
    --bs-table-accent-bg: rgba(255, 255, 255, 0.05);
  }
  
  .bg-light {
    background-color: #2c3034 !important;
    color: #e9ecef;
  }
}
</style>
