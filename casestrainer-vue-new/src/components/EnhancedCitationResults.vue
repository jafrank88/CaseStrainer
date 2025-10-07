<template>
  <div class="enhanced-citation-results">
    <!-- Verification Progress Section -->
    <div v-if="verificationStatus.isVerifying || verificationStatus.status !== 'idle'" 
         class="verification-progress-section">
      <div class="verification-header">
        <h3>
          <i class="bi bi-shield-check me-2"></i>
          Citation Verification Progress
        </h3>
        <div class="verification-status-badge" :class="verificationStatus.status">
          {{ getStatusDisplayText(verificationStatus.status) }}
        </div>
      </div>
      
      <!-- Progress Bar -->
      <div v-if="verificationStatus.status === 'running'" class="verification-progress">
        <div class="progress-container">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: verificationStatus.progress + '%' }"></div>
          </div>
          <div class="progress-text">
            {{ verificationStatus.progress.toFixed(1) }}% Complete
          </div>
        </div>
        
        <!-- Current Method -->
        <div v-if="verificationStatus.currentMethod" class="current-method">
          <i class="bi bi-gear me-2"></i>
          {{ verificationStatus.currentMethod }}
        </div>
        
        <!-- Citations Progress -->
        <div class="citations-progress">
          <span class="citations-count">
            {{ verificationStatus.citationsProcessed }} of {{ verificationStatus.citationsCount }} citations processed
          </span>
        </div>
      </div>
      
      <!-- Status Messages -->
      <div class="verification-messages">
        <div v-if="verificationStatus.status === 'queued'" class="message queued">
          <i class="bi bi-clock me-2"></i>
          Verification queued and starting...
        </div>
        
        <div v-if="verificationStatus.status === 'completed'" class="message completed">
          <i class="bi bi-check-circle me-2"></i>
          Verification completed successfully!
        </div>
        
        <div v-if="verificationStatus.status === 'failed'" class="message failed">
          <i class="bi bi-exclamation-triangle me-2"></i>
          Verification failed. Please try again.
        </div>
      </div>
    </div>

    <!-- Results Section -->
    <div v-if="results && (results.citations || results.clusters)" class="results-section">
      <div class="results-header">
        <h2>
          <i class="bi bi-clipboard-check me-2"></i>
          Citation Analysis Results
        </h2>
        
        <!-- Verification Summary -->
        <div v-if="verificationResults" class="verification-summary">
          <div class="summary-stats">
            <div class="stat-item">
              <span class="stat-label">Total Citations:</span>
              <span class="stat-value">{{ verificationResults.verification_summary?.total_citations || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Verified:</span>
              <span class="stat-value verified">{{ verificationResults.verification_summary?.verified_citations || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Coverage:</span>
              <span class="stat-value">{{ (verificationResults.verification_summary?.verification_coverage || 0) * 100 }}%</span>
            </div>
          </div>
          
          <div v-if="verificationResults.verification_summary?.methods_used" class="methods-used">
            <span class="methods-label">Verification Methods:</span>
            <span class="methods-list">{{ verificationResults.verification_summary.methods_used.join(', ') }}</span>
          </div>
        </div>
      </div>

      <!-- Clusters Display -->
      <div v-if="results.clusters && results.clusters.length > 0" class="clusters-section">
        <h3>Citation Clusters</h3>
        
        <div class="clusters-grid">
          <div v-for="cluster in results.clusters" :key="cluster.cluster_id" 
               class="cluster-card" :class="{ verified: cluster.verified }">
            
            <!-- Cluster Header -->
            <div class="cluster-header">
              <div class="cluster-title">
                <h4>{{ cluster.canonical_name || cluster.extracted_case_name }}</h4>
                <span class="cluster-year">{{ cluster.canonical_date || cluster.extracted_date }}</span>
              </div>
              
              <div class="cluster-status">
                <span v-if="cluster.verified" class="status-badge verified">
                  <i class="bi bi-check-circle me-1"></i>
                  Verified via {{ cluster.source }}
                </span>
                <span v-else class="status-badge unverified">
                  <i class="bi bi-clock me-1"></i>
                  Not verified
                </span>
              </div>
            </div>
            
            <!-- Cluster Citations -->
            <div class="cluster-citations">
              <div class="citations-count">
                {{ cluster.size || cluster.citations?.length || 0 }} citations
              </div>
              
              <div class="citations-list">
                <div v-for="citation in Array.isArray(cluster.citations) && cluster.citations[0] && typeof cluster.citations[0] === 'object' ? cluster.citations : cluster.citations.map(c => ({ text: c, verified: false }))" 
                     :key="citation.text" 
                     class="citation-item" 
                     :class="{ 'verified-citation': citation.verified }">
                  <span class="citation-text">{{ citation.text }}</span>
                  <span v-if="citation.verified" class="citation-status verified">
                    <i class="bi bi-check-circle-fill"></i>
                    <span class="citation-source" v-if="citation.verification_source">
                      ({{ citation.verification_source }})
                    </span>
                  </span>
                  <span v-else class="citation-status unverified">
                    <i class="bi bi-question-circle-fill"></i>
                    Not verified
                  </span>
                  <a v-if="citation.verification_url" 
                     :href="citation.verification_url" 
                     target="_blank" 
                     class="verification-link"
                     title="View source">
                    <i class="bi bi-box-arrow-up-right"></i>
                  </a>
                </div>
              </div>
            </div>
            
            <!-- Verification Details -->
            <div v-if="cluster.verified" class="verification-details">
              <div class="detail-row">
                <span class="detail-label">Source:</span>
                <span class="detail-value">{{ cluster.source }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Method:</span>
                <span class="detail-value">{{ cluster.validation_method }}</span>
              </div>
              <div v-if="cluster.canonical_url" class="detail-row">
                <span class="detail-label">URL:</span>
                <a :href="cluster.canonical_url" target="_blank" class="detail-value link">
                  View Source
                </a>
              </div>
            </div>
            
            <!-- Extracted vs Canonical Comparison -->
            <div class="comparison-section">
              <div class="comparison-header">
                <h5>Extracted vs Verified Data</h5>
              </div>
              
              <div class="comparison-grid">
                <div class="comparison-item">
                  <span class="comparison-label">Case Name:</span>
                  <div class="comparison-values">
                    <span class="extracted-value">{{ cluster.extracted_case_name }}</span>
                    <i class="bi bi-arrow-right"></i>
                    <span class="canonical-value" :class="{ 
                      'same': cluster.extracted_case_name === cluster.canonical_name,
                      'different': cluster.extracted_case_name !== cluster.canonical_name 
                    }">
                      {{ cluster.canonical_name || 'Not verified' }}
                    </span>
                  </div>
                </div>
                
                <div class="comparison-item">
                  <span class="comparison-label">Year:</span>
                  <div class="comparison-values">
                    <span class="extracted-value">{{ cluster.extracted_date }}</span>
                    <i class="bi bi-arrow-right"></i>
                    <span class="canonical-value" :class="{ 
                      'same': cluster.extracted_date === cluster.canonical_date,
                      'different': cluster.extracted_date !== cluster.canonical_date 
                    }">
                      {{ cluster.canonical_date || 'Not verified' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Individual Citations Display -->
      <div v-if="results.citations && results.citations.length > 0" class="citations-section">
        <h3>Individual Citations</h3>
        
        <div class="citations-table">
          <div class="table-header">
            <div class="header-cell">Citation</div>
            <div class="header-cell">Case Name</div>
            <div class="header-cell">Year</div>
            <div class="header-cell">Status</div>
            <div class="header-cell">Source</div>
          </div>
          
          <div v-for="citation in results.citations" :key="citation.citation" 
               class="table-row" :class="{ verified: citation.verified }">
            
            <div class="cell citation-cell">
              <code>{{ citation.citation }}</code>
            </div>
            
            <div class="cell name-cell">
              <div class="extracted-name">{{ citation.extracted_case_name }}</div>
              <div v-if="citation.canonical_name && citation.canonical_name !== citation.extracted_case_name" 
                   class="canonical-name">
                <i class="bi bi-arrow-up"></i>
                {{ citation.canonical_name }}
              </div>
            </div>
            
            <div class="cell year-cell">
              <div class="extracted-year">{{ citation.extracted_date }}</div>
              <div v-if="citation.canonical_date && citation.canonical_date !== citation.extracted_date" 
                   class="canonical-year">
                <i class="bi bi-arrow-up"></i>
                {{ citation.canonical_date }}
              </div>
            </div>
            
            <div class="cell status-cell">
              <span v-if="citation.verified" class="status-badge verified">
                <i class="bi bi-check-circle me-1"></i>
                Verified
              </span>
              <span v-else class="status-badge unverified">
                <i class="bi bi-clock me-1"></i>
                Not verified
              </span>
            </div>
            
            <div class="cell source-cell">
              <span v-if="citation.verified" class="source-name">
                {{ citation.source }}
              </span>
              <span v-else class="source-name local">
                Local extraction
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- No Results Message -->
    <div v-else-if="!verificationStatus.isVerifying" class="no-results">
      <div class="no-results-content">
        <i class="bi bi-inbox me-3"></i>
        <h3>No citation results to display</h3>
        <p>Please analyze a document to see citation results.</p>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="action-buttons">
      <button @click="startNewAnalysis" class="btn btn-primary">
        <i class="bi bi-arrow-clockwise me-2"></i>
        New Analysis
      </button>
      
      <button @click="copyResults" class="btn btn-outline-secondary" 
              :disabled="!results || (!results.citations && !results.clusters)">
        <i class="bi bi-clipboard me-2"></i>
        Copy Results
      </button>
      
      <button @click="downloadResults" class="btn btn-outline-secondary"
              :disabled="!results || (!results.citations && !results.clusters)">
        <i class="bi bi-download me-2"></i>
        Download
      </button>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, onUnmounted } from 'vue'
import { useUnifiedProgress } from '@/stores/progressStore'

export default {
  name: 'EnhancedCitationResults',
  
  props: {
    results: {
      type: Object,
      default: null
    },
    error: {
      type: String,
      default: null
    },
    componentId: {
      type: String,
      default: 'unknown'
    }
  },
  
  emits: ['new-analysis', 'copy-results', 'download-results'],
  
  setup(props, { emit }) {
    const { 
      progressState, 
      startVerificationStream, 
      stopVerificationStream,
      verificationStatus,
      verificationResults
    } = useUnifiedProgress()
    
    // Computed properties
    const hasVerificationData = computed(() => {
      return verificationResults && verificationResults.verification_summary
    })
    
    // Methods
    const getStatusDisplayText = (status) => {
      const statusMap = {
        'idle': 'Idle',
        'queued': 'Queued',
        'running': 'Running',
        'completed': 'Completed',
        'failed': 'Failed'
      }
      return statusMap[status] || status
    }
    
    const startNewAnalysis = () => {
      emit('new-analysis')
    }
    
    const copyResults = () => {
      emit('copy-results')
    }
    
    const downloadResults = () => {
      emit('download-results')
    }
    
    // Lifecycle
    onMounted(() => {
      // Start verification stream if we have results with request_id
      if (props.results?.request_id) {
        startVerificationStream(props.results.request_id)
      }
    })
    
    onUnmounted(() => {
      // Clean up verification stream
      stopVerificationStream()
    })
    
    return {
      verificationStatus,
      verificationResults,
      hasVerificationData,
      getStatusDisplayText,
      startNewAnalysis,
      copyResults,
      downloadResults
    }
  }
}
</script>

<style scoped>
.enhanced-citation-results {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

/* Verification Progress Section */
.verification-progress-section {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 32px;
  border: 1px solid #dee2e6;
}

.verification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.verification-header h3 {
  margin: 0;
  color: #495057;
  font-size: 1.25rem;
}

.verification-status-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 500;
  text-transform: capitalize;
}

.verification-status-badge.queued {
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.verification-status-badge.running {
  background-color: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.verification-status-badge.completed {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.verification-status-badge.failed {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

/* Progress Bar */
.verification-progress {
  margin-bottom: 20px;
}
.progress-container {
  margin-bottom: 16px;
}

.citation-item {
  margin: 4px 0;
  padding: 8px 12px;
  transition: width 0.3s ease;
}

.progress-text {
  text-align: center;
  font-size: 0.875rem;
  color: #6c757d;
  font-weight: 500;
}

.current-method {
  background-color: #fff;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  border: 1px solid #dee2e6;
  color: #495057;
  font-size: 0.875rem;
}

.citations-progress {
  text-align: center;
  color: #6c757d;
  font-size: 0.875rem;
}

/* Verification Messages */
.verification-messages {
  margin-top: 16px;
}

.message {
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  font-size: 0.875rem;
}

.message.queued {
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.message.completed {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message.failed {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

/* Results Section */
.results-section {
  margin-bottom: 32px;
}

.results-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e9ecef;
}

.results-header h2 {
  margin: 0 0 16px 0;
  color: #212529;
  font-size: 1.5rem;
}

.verification-summary {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #dee2e6;
}

.summary-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  font-size: 0.75rem;
  color: #6c757d;
  text-transform: uppercase;
  font-weight: 500;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #212529;
}

.stat-value.verified {
  color: #28a745;
}

.methods-used {
  font-size: 0.875rem;
  color: #6c757d;
}

.methods-label {
  font-weight: 500;
  margin-right: 8px;
}

/* Clusters Section */
.clusters-section {
  margin-bottom: 32px;
}

.clusters-section h3 {
  margin: 0 0 20px 0;
  color: #212529;
  font-size: 1.25rem;
}

.clusters-grid {
  display: grid;
  gap: 20px;
}

.cluster-card {
  background-color: #fff;
  border: 1px solid #dee2e6;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.2s ease;
}

.cluster-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.cluster-card.verified {
  border-color: #28a745;
  background-color: #f8fff9;
}

.cluster-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.cluster-title h4 {
  margin: 0 0 4px 0;
  color: #212529;
  font-size: 1.125rem;
}

.cluster-year {
  color: #6c757d;
  font-size: 0.875rem;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-badge.verified {
  background-color: #d4edda;
  color: #155724;
}

.status-badge.unverified {
  background-color: #f8f9fa;
  color: #6c757d;
  border: 1px solid #dee2e6;
}

.cluster-citations {
  margin-bottom: 16px;
}

.citations-count {
.citations-list {
  display: flex;
  border-radius: 4px;
  font-size: 0.75rem;
  font-family: 'Courier New', monospace;
  color: #495057;
}

.verification-details {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-weight: 500;
  color: #6c757d;
  font-size: 0.875rem;
}

.detail-value {
  color: #212529;
  font-size: 0.875rem;
}

.detail-value.link {
  color: #007bff;
  text-decoration: none;
}

.detail-value.link:hover {
  text-decoration: underline;
}

/* Comparison Section */
.comparison-section {
  border-top: 1px solid #dee2e6;
  padding-top: 16px;
}

.comparison-header h5 {
  margin: 0 0 12px 0;
  color: #495057;
  font-size: 1rem;
}

.comparison-grid {
  display: grid;
  gap: 12px;
}

.comparison-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.comparison-label {
  font-weight: 500;
  color: #6c757d;
  font-size: 0.875rem;
}

.comparison-values {
  display: flex;
  align-items: center;
  gap: 12px;
}

.extracted-value {
  background-color: #e9ecef;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.875rem;
  color: #495057;
}

.canonical-value {
  background-color: #f8f9fa;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.875rem;
  border: 1px solid #dee2e6;
}

.canonical-value.same {
  background-color: #d4edda;
  color: #155724;
  border-color: #c3e6cb;
}

.canonical-value.different {
  background-color: #fff3cd;
  color: #856404;
  border-color: #ffeaa7;
}

/* Citations Table */
.citations-section {
  margin-bottom: 32px;
}

.citations-section h3 {
  margin: 0 0 20px 0;
  color: #212529;
  font-size: 1.25rem;
}

.citations-table {
  background-color: #fff;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 2fr 1fr 1fr 1fr;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.header-cell {
  padding: 12px;
  font-weight: 600;
  color: #495057;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.table-row {
  display: grid;
  grid-template-columns: 2fr 2fr 1fr 1fr 1fr;
  border-bottom: 1px solid #f1f3f4;
  transition: background-color 0.2s ease;
}

.table-row:hover {
  background-color: #f8f9fa;
}

.table-row.verified {
  background-color: #f8fff9;
}

.cell {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.citation-cell code {
  background-color: #f8f9fa;
  padding: 4px 6px;
  border-radius: 4px;
  font-size: 0.875rem;
  color: #495057;
}

.extracted-name, .extracted-year {
  font-size: 0.875rem;
  color: #212529;
}

.canonical-name, .canonical-year {
  font-size: 0.75rem;
  color: #6c757d;
  font-style: italic;
}

.source-name {
  font-size: 0.875rem;
  color: #6c757d;
}

.source-name.local {
  color: #6c757d;
  font-style: italic;
}

/* No Results */
.no-results {
  text-align: center;
  padding: 60px 20px;
  color: #6c757d;
}

.no-results-content i {
  font-size: 3rem;
  color: #dee2e6;
}

.no-results-content h3 {
  margin: 16px 0 8px 0;
  color: #495057;
}

.no-results-content p {
  margin: 0;
  font-size: 1rem;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding-top: 24px;
  border-top: 1px solid #e9ecef;
}

.btn {
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 500;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #007bff;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-outline-secondary {
  background-color: transparent;
  color: #6c757d;
  border: 1px solid #6c757d;
}

.btn-outline-secondary:hover:not(:disabled) {
  background-color: #6c757d;
  color: #fff;
}

/* Responsive Design */
@media (max-width: 768px) {
  .enhanced-citation-results {
    padding: 16px;
  }
  
  .verification-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .summary-stats {
    flex-direction: column;
    gap: 16px;
  }
  
  .table-header,
  .table-row {
    grid-template-columns: 1fr;
  }
  
  .header-cell {
    display: none;
  }
  
  .cell {
    padding: 8px 12px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
}
</style>
