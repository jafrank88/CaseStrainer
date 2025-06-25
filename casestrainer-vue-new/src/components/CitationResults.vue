<template>
  <div class="citation-results">
    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <h3>Analyzing citations...</h3>
    </div>
    
    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">❌</div>
      <h3>Analysis Error</h3>
      <p>{{ error }}</p>
    </div>
    
    <!-- Results -->
    <div v-else-if="results && results.citations && results.citations.length > 0" class="results-content">
      <!-- Header with Summary -->
      <div class="results-header">
        <div class="header-content">
          <h2>Citation Analysis Results</h2>
          <div class="summary-stats">
            <div class="stat-item">
              <span class="stat-number">{{ results.citations.length }}</span>
              <span class="stat-label">Total</span>
            </div>
            <div class="stat-item verified">
              <span class="stat-number">{{ validCount }}</span>
              <span class="stat-label">Verified</span>
            </div>
            <div class="stat-item invalid">
              <span class="stat-number">{{ invalidCount }}</span>
              <span class="stat-label">Invalid</span>
            </div>
          </div>
        </div>
        
        <!-- Action Buttons -->
        <div class="action-buttons">
          <button @click="copyResults" class="action-btn copy-btn">
            <span class="btn-icon">📋</span>
            Copy Results
          </button>
          <button @click="downloadResults" class="action-btn download-btn">
            <span class="btn-icon">💾</span>
            Download
          </button>
        </div>
      </div>

      <!-- Processing Stats (if available) -->
      <div v-if="results.stats" class="stats-section">
        <h3>Processing Breakdown</h3>
        <div class="stats-grid">
          <div class="stat-card">
            <span class="stat-value">{{ results.stats.total_extracted }}</span>
            <span class="stat-title">Extracted</span>
          </div>
          <div class="stat-card">
            <span class="stat-value">{{ results.stats.deduplicated }}</span>
            <span class="stat-title">Unique</span>
          </div>
          <div class="stat-card verified">
            <span class="stat-value">{{ results.stats.verified_in_cache + results.stats.verified_in_json_array + results.stats.verified_in_text_blob + results.stats.verified_in_single + results.stats.verified_in_langsearch }}</span>
            <span class="stat-title">Verified</span>
          </div>
          <div class="stat-card invalid">
            <span class="stat-value">{{ results.stats.not_verified }}</span>
            <span class="stat-title">Not Verified</span>
          </div>
        </div>
      </div>

      <!-- Filter Controls -->
      <div class="filter-section">
        <div class="filter-controls">
          <button 
            v-for="filter in filters" 
            :key="filter.value"
            :class="['filter-btn', { active: activeFilter === filter.value }]"
            @click="activeFilter = filter.value"
          >
            {{ filter.label }}
            <span class="filter-count">({{ filter.count }})</span>
          </button>
        </div>
        
        <div class="search-box">
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="Search citations..."
            class="search-input"
          />
        </div>
      </div>

      <!-- Citations List -->
      <div v-if="filteredCitations.length > 0" class="citations-list">
        <div
          v-for="citation in paginatedCitations"
          :key="citation.id || citation.citation"
          :class="['citation-item', { verified: citation.verified, invalid: !citation.verified }]"
        >
          <div class="citation-header">
            <div class="citation-text">
              <span class="citation-content">{{ citation.citation }}</span>
              <span :class="['status-badge', citation.verified ? 'verified' : 'invalid']">
                {{ citation.verified ? '✓ Verified' : '✗ Invalid' }}
              </span>
            </div>
            <div class="citation-actions">
              <button
                v-if="getCitationUrl(citation)"
                @click="openCitation(getCitationUrl(citation))"
                class="action-link"
                title="View case details"
              >
                🔗
              </button>
              <button
                @click="copyCitation(citation.citation)"
                class="action-link"
                title="Copy citation"
              >
                📋
              </button>
            </div>
          </div>
          
          <!-- Enhanced Citation Details -->
          <div class="citation-details">
            <!-- Case Name Comparison -->
            <div v-if="getCaseName(citation) || getExtractedCaseName(citation)" class="detail-section">
              <h4 class="section-title">Case Information</h4>
              <div class="detail-row">
                <span class="detail-label">Canonical Case Name:</span>
                <span class="detail-value">{{ getCaseName(citation) || 'N/A' }}</span>
              </div>
              <div v-if="getExtractedCaseName(citation)" class="detail-row">
                <span class="detail-label">Extracted Case Name:</span>
                <span class="detail-value">{{ getExtractedCaseName(citation) }}</span>
              </div>
              <div v-if="getCaseNameSimilarity(citation) !== null" class="detail-row">
                <span class="detail-label">Name Similarity:</span>
                <span :class="['detail-value', getSimilarityClass(getCaseNameSimilarity(citation))]">
                  {{ (getCaseNameSimilarity(citation) * 100).toFixed(1) }}%
                </span>
              </div>
              <div v-if="getCaseNameMismatch(citation)" class="detail-row">
                <span class="detail-label">Name Mismatch:</span>
                <span class="detail-value warning">⚠️ Case names differ significantly</span>
              </div>
            </div>

            <!-- Court and Docket Information -->
            <div v-if="getCourt(citation) || getDocket(citation)" class="detail-section">
              <h4 class="section-title">Court Information</h4>
              <div v-if="getCourt(citation)" class="detail-row">
                <span class="detail-label">Court:</span>
                <span class="detail-value">{{ getCourt(citation) }}</span>
              </div>
              <div v-if="getDocket(citation)" class="detail-row">
                <span class="detail-label">Docket:</span>
                <span class="detail-value">{{ getDocket(citation) }}</span>
              </div>
            </div>

            <!-- Decision Date -->
            <div v-if="getDateFiled(citation) || getExtractedDate(citation)" class="detail-section">
              <h4 class="section-title">Decision Information</h4>
              <div v-if="getExtractedDate(citation)" class="detail-row">
                <span class="detail-label">Extracted Date:</span>
                <span class="detail-value">{{ formatDate(getExtractedDate(citation)) }}</span>
              </div>
              <div v-if="getDateFiled(citation)" class="detail-row">
                <span class="detail-label">Canonical Date:</span>
                <span class="detail-value">{{ formatDate(getDateFiled(citation)) }}</span>
              </div>
              <div v-if="getExtractedDate(citation) && getDateFiled(citation)" class="detail-row">
                <span class="detail-label">Date Match:</span>
                <span :class="['detail-value', getExtractedDate(citation) === getDateFiled(citation) ? 'high-similarity' : 'low-similarity']">
                  {{ getExtractedDate(citation) === getDateFiled(citation) ? '✓ Match' : '✗ Different' }}
                </span>
              </div>
            </div>

            <!-- Parallel Citations -->
            <div v-if="getParallelCitations(citation) && getParallelCitations(citation).length > 0" class="detail-section">
              <h4 class="section-title">Parallel Citations</h4>
              <div class="parallel-citations">
                <span 
                  v-for="(parallel, index) in getParallelCitations(citation)" 
                  :key="index"
                  class="parallel-citation"
                >
                  {{ parallel }}
                </span>
              </div>
            </div>

            <!-- Source Information -->
            <div class="detail-section">
              <h4 class="section-title">Verification Details</h4>
              <div class="detail-row">
                <span class="detail-label">Source:</span>
                <span class="detail-value">{{ getSource(citation) || 'N/A' }}</span>
              </div>
              <div v-if="getNote(citation)" class="detail-row">
                <span class="detail-label">Note:</span>
                <span class="detail-value note">{{ getNote(citation) }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Pagination -->
        <div v-if="totalPages > 1" class="pagination">
          <button 
            @click="currentPage--" 
            :disabled="currentPage <= 1"
            class="pagination-btn"
          >
            ← Previous
          </button>
          <span class="page-info">Page {{ currentPage }} of {{ totalPages }}</span>
          <button 
            @click="currentPage++" 
            :disabled="currentPage >= totalPages"
            class="pagination-btn"
          >
            Next →
          </button>
        </div>
      </div>

      <!-- Empty Filter State -->
      <div v-if="filteredCitations.length === 0 && results.citations.length > 0" class="empty-filter">
        <div class="empty-icon">🔍</div>
        <h3>No citations match your filter</h3>
        <p>Try adjusting your search or filter criteria</p>
      </div>
    </div>

    <!-- No Results State -->
    <div v-else class="no-results">
      <div class="no-results-icon">📄</div>
      <h3>No Citations Found</h3>
      <p>The document didn't contain any recognizable legal citations</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  results: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['apply-correction', 'copy-results', 'download-results', 'toast']);

// Reactive state
const activeFilter = ref('all');
const searchQuery = ref('');
const currentPage = ref(1);
const itemsPerPage = 50;

// Computed properties
const validCount = computed(() => {
  if (!props.results?.citations) return 0;
  return props.results.citations.filter(c => c.verified).length;
});

const invalidCount = computed(() => {
  if (!props.results?.citations) return 0;
  return props.results.citations.filter(c => !c.verified).length;
});

const filteredCitations = computed(() => {
  if (!props.results?.citations) return [];
  
  let filtered = props.results.citations;
  
  // Apply filter
  if (activeFilter.value === 'verified') {
    filtered = filtered.filter(c => c.verified);
  } else if (activeFilter.value === 'invalid') {
    filtered = filtered.filter(c => !c.verified);
  }
  
  // Apply search
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase();
    filtered = filtered.filter(c => 
      c.citation.toLowerCase().includes(query) ||
      (getCaseName(c) && getCaseName(c).toLowerCase().includes(query)) ||
      (getExtractedCaseName(c) && getExtractedCaseName(c).toLowerCase().includes(query)) ||
      (getCourt(c) && getCourt(c).toLowerCase().includes(query)) ||
      (getDocket(c) && getDocket(c).toLowerCase().includes(query)) ||
      (getDateFiled(c) && getDateFiled(c).toLowerCase().includes(query)) ||
      (getExtractedDate(c) && getExtractedDate(c).toLowerCase().includes(query)) ||
      (getParallelCitations(c) && getParallelCitations(c).some(p => p.toLowerCase().includes(query))) ||
      (getSource(c) && getSource(c).toLowerCase().includes(query))
    );
  }
  
  return filtered;
});

const totalPages = computed(() => {
  return Math.ceil(filteredCitations.value.length / itemsPerPage);
});

const paginatedCitations = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  return filteredCitations.value.slice(start, end);
});

const filters = computed(() => [
  { value: 'all', label: 'All', count: props.results?.citations?.length || 0 },
  { value: 'verified', label: 'Verified', count: validCount.value },
  { value: 'invalid', label: 'Invalid', count: invalidCount.value }
]);

// Methods
const copyCitation = async (citation) => {
  try {
    await navigator.clipboard.writeText(citation);
    emit('toast', 'Citation copied to clipboard!', 'success');
  } catch (err) {
    emit('toast', 'Failed to copy citation', 'error');
  }
};

const openCitation = (url) => {
  window.open(url, '_blank');
};

// Helper functions for enhanced data structure compatibility
const getCaseName = (citation) => {
  return citation.case_name || citation.metadata?.case_name || null;
};

const getExtractedCaseName = (citation) => {
  return citation.extracted_case_name || null;
};

const getCaseNameSimilarity = (citation) => {
  return citation.case_name_similarity || null;
};

const getCaseNameMismatch = (citation) => {
  return citation.case_name_mismatch || false;
};

const getCourt = (citation) => {
  return citation.court || citation.metadata?.court || null;
};

const getDocket = (citation) => {
  return citation.docket_number || citation.metadata?.docket || null;
};

const getDateFiled = (citation) => {
  return citation.date_filed || null;
};

const getExtractedDate = (citation) => {
  return citation.extracted_date || null;
};

const getParallelCitations = (citation) => {
  return citation.parallel_citations || [];
};

const getCitationUrl = (citation) => {
  return citation.url || citation.metadata?.url || null;
};

const getSource = (citation) => {
  return citation.source || citation.metadata?.source || null;
};

const getNote = (citation) => {
  return citation.note || null;
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  } catch (err) {
    return dateString; // Return as-is if parsing fails
  }
};

const getSimilarityClass = (similarity) => {
  if (similarity === null) return '';
  if (similarity >= 0.9) return 'high-similarity';
  if (similarity >= 0.7) return 'medium-similarity';
  return 'low-similarity';
};

const copyResults = async () => {
  try {
    const resultsText = filteredCitations.value
      .map(c => `${c.citation} - ${c.verified ? 'Verified' : 'Invalid'}`)
      .join('\n');
    
    await navigator.clipboard.writeText(resultsText);
    emit('copy-results');
    emit('toast', 'Results copied to clipboard!', 'success');
  } catch (err) {
    emit('toast', 'Failed to copy results', 'error');
  }
};

const downloadResults = () => {
  try {
    const data = {
      timestamp: new Date().toISOString(),
      total: filteredCitations.value.length,
      verified: validCount.value,
      invalid: invalidCount.value,
      citations: filteredCitations.value.map(c => ({
        citation: c.citation,
        verified: c.verified,
        case_name: getCaseName(c),
        extracted_case_name: getExtractedCaseName(c),
        case_name_similarity: getCaseNameSimilarity(c),
        case_name_mismatch: getCaseNameMismatch(c),
        court: getCourt(c),
        docket_number: getDocket(c),
        date_filed: getDateFiled(c),
        extracted_date: getExtractedDate(c),
        parallel_citations: getParallelCitations(c),
        url: getCitationUrl(c),
        source: getSource(c),
        note: getNote(c),
        metadata: c.metadata // Keep original metadata for backward compatibility
      }))
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `citation-results-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    emit('download-results');
    emit('toast', 'Results downloaded successfully!', 'success');
  } catch (err) {
    emit('toast', 'Failed to download results', 'error');
  }
};

// Reset pagination when filter changes
const resetPagination = () => {
  currentPage.value = 1;
};

// Watch for filter changes
watch(activeFilter, resetPagination);
watch(searchQuery, resetPagination);
</script>

<style scoped>
.citation-results {
  max-width: 1200px;
  margin: 0 auto;
}

/* Loading State */
.loading-state {
  text-align: center;
  padding: 3rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Error State */
.error-state {
  text-align: center;
  padding: 3rem;
  background: #fff5f5;
  border-radius: 12px;
  border: 1px solid #fed7d7;
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

/* Results Header */
.results-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid #f8f9fa;
}

.header-content h2 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.summary-stats {
  display: flex;
  gap: 2rem;
}

.stat-item {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 1.5rem;
  font-weight: bold;
  color: #007bff;
}

.stat-item.verified .stat-number {
  color: #28a745;
}

.stat-item.invalid .stat-number {
  color: #dc3545;
}

.stat-label {
  font-size: 0.9rem;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 1rem;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn {
  background: #007bff;
  color: white;
}

.copy-btn:hover {
  background: #0056b3;
}

.download-btn {
  background: #28a745;
  color: white;
}

.download-btn:hover {
  background: #1e7e34;
}

/* Stats Section */
.stats-section {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.stats-section h3 {
  margin: 0 0 1rem 0;
  color: #495057;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-card.verified {
  border-left: 4px solid #28a745;
}

.stat-card.invalid {
  border-left: 4px solid #dc3545;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: bold;
  color: #2c3e50;
}

.stat-title {
  font-size: 0.8rem;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Filter Section */
.filter-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  gap: 1rem;
}

.filter-controls {
  display: flex;
  gap: 0.5rem;
}

.filter-btn {
  padding: 0.5rem 1rem;
  border: 2px solid #e9ecef;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.filter-btn:hover {
  border-color: #007bff;
}

.filter-btn.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.filter-count {
  font-size: 0.8rem;
  opacity: 0.8;
}

.search-box {
  flex: 1;
  max-width: 300px;
}

.search-input {
  width: 100%;
  padding: 0.5rem 1rem;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 0.9rem;
}

.search-input:focus {
  outline: none;
  border-color: #007bff;
}

/* Citations List */
.citations-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.citation-item {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #6c757d;
  transition: all 0.2s;
}

.citation-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.citation-item.verified {
  border-left-color: #28a745;
}

.citation-item.invalid {
  border-left-color: #dc3545;
}

.citation-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.citation-text {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.citation-content {
  font-weight: 600;
  color: #2c3e50;
  font-family: 'Courier New', monospace;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-badge.verified {
  background: #d4edda;
  color: #155724;
}

.status-badge.invalid {
  background: #f8d7da;
  color: #721c24;
}

.citation-actions {
  display: flex;
  gap: 0.5rem;
}

.action-link {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.action-link:hover {
  background: #f8f9fa;
}

/* Citation Details */
.citation-details {
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #007bff;
}

.detail-section {
  margin-bottom: 1.5rem;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.section-title {
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: #495057;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 0.25rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
  padding: 0.25rem 0;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-weight: 600;
  color: #495057;
  min-width: 140px;
  flex-shrink: 0;
}

.detail-value {
  color: #2c3e50;
  text-align: right;
  flex: 1;
  word-break: break-word;
}

.detail-value.warning {
  color: #dc3545;
  font-weight: 600;
}

.detail-value.note {
  color: #6c757d;
  font-style: italic;
}

.detail-value.high-similarity {
  color: #28a745;
  font-weight: 600;
}

.detail-value.medium-similarity {
  color: #ffc107;
  font-weight: 600;
}

.detail-value.low-similarity {
  color: #dc3545;
  font-weight: 600;
}

/* Parallel Citations */
.parallel-citations {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.parallel-citation {
  background: #e9ecef;
  color: #495057;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
  font-family: 'Courier New', monospace;
}

/* Empty States */
.empty-filter,
.no-results {
  text-align: center;
  padding: 3rem;
  color: #6c757d;
}

.empty-icon,
.no-results-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .results-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .summary-stats {
    gap: 1rem;
  }
  
  .filter-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-box {
    max-width: none;
  }
  
  .citation-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .citation-text {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .citation-details {
    grid-template-columns: 1fr;
  }
}
</style>
