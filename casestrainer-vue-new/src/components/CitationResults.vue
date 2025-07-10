<script setup>
import { ref, computed, watch } from 'vue'
import ProcessingProgress from './ProcessingProgress.vue'

const props = defineProps({
  results: { type: Object, default: null },
  showLoading: { type: Boolean, default: false },
  error: { type: String, default: '' }
})

const emit = defineEmits(['copy-results', 'download-results', 'toast'])

const activeFilter = ref('all')
const searchQuery = ref('')
const currentPage = ref(1)
const itemsPerPage = 50
const expandedCitations = ref(new Set())
const progress = ref(0)
const etaSeconds = ref(null)

watch(() => props.results, (newVal) => {
  if (newVal && typeof newVal.progress === 'number') {
    progress.value = newVal.progress
    etaSeconds.value = newVal.eta_seconds
  }
})

const shouldShowProgressBar = computed(() => {
  return props.showLoading && progress.value > 0 && progress.value < 100
})

const validCount = computed(() => {
  if (!props.results?.citations) return 0
  return props.results.citations.filter(c => c.verified === 'true' || c.verified === true).length
})

const invalidCount = computed(() => {
  if (!props.results?.citations) return 0
  return props.results.citations.filter(c => c.verified === 'false' || c.verified === false).length
})

const filteredCitations = computed(() => {
  if (!props.results?.citations) return []
  let filtered = props.results.citations
  
  // Filter out statutes and regulations
  filtered = filtered.filter(c => !isStatuteOrRegulation(c))
  
  if (activeFilter.value === 'verified') {
    filtered = filtered.filter(c => c.verified === 'true' || c.verified === true)
  } else if (activeFilter.value === 'invalid') {
    filtered = filtered.filter(c => c.verified === 'false' || c.verified === false)
  }
  
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(c => 
      (c.citation && c.citation.toLowerCase().includes(query)) ||
      (c.canonical_citation && c.canonical_citation.toLowerCase().includes(query)) ||
      (c.primary_citation && c.primary_citation.toLowerCase().includes(query)) ||
      (getCaseName(c) && getCaseName(c).toLowerCase().includes(query))
    )
  }
  
  return filtered
})

// Utility function to identify statutes/regulations
const isStatuteOrRegulation = (citation) => {
  const citationText = citation.citation || citation.canonical_citation || citation.primary_citation || ''
  const text = citationText.toUpperCase()
  
  // Check for common statute/regulation patterns
  if (text.includes('U.S.C.') || text.includes('USC') || text.includes('C.F.R.') || text.includes('CFR') ||
      text.includes('UNITED STATES CODE') || text.includes('CODE OF FEDERAL REGULATIONS')) {
    return true
  }
  
  // Regex patterns for statutes and regulations
  return /\d+\s+U\.?\s*S\.?\s*C\.?\s*[§]?\s*\d+/i.test(text) || 
         /\d+\s+C\.?\s*F\.?\s*R\.?\s*[§]?\s*\d+/i.test(text)
}

const totalPages = computed(() => Math.ceil(filteredCitations.value.length / itemsPerPage))

const paginatedCitations = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return filteredCitations.value.slice(start, end)
})

const filters = computed(() => [
  { value: 'all', label: 'All', count: filteredCitations.value.length },
  { value: 'verified', label: 'Verified', count: validCount.value },
  { value: 'invalid', label: 'Invalid', count: invalidCount.value }
])

// Helper functions to handle the actual data structure
const getCanonicalCaseName = (citation) => {
  return citation.case_name || citation.canonical_name || null
}

const getExtractedCaseName = (citation) => {
  const value = citation.extracted_case_name;
  return (value && value !== 'N/A') ? value : null;
}

const getCanonicalDate = (citation) => {
  return citation.canonical_date || null
}

const getExtractedDate = (citation) => {
  const value = citation.extracted_date;
  return (value && value !== 'N/A') ? value : null;
}

const getCitation = (citation) => {
  return citation.citation || 
         citation.canonical_citation || 
         citation.primary_citation || 
         'N/A'
}

const getCitationUrl = (citation) => {
  return citation.url || null
}

const getSource = (citation) => {
  return citation.source || 'Unknown'
}

const getVerificationMethod = (citation) => {
  return citation.verification_method || 'N/A'
}

const getConfidence = (citation) => {
  return citation.confidence || citation.likelihood_score || 'N/A'
}

const getError = (citation) => {
  return citation.error || citation.explanation || null
}

const getVerificationStatus = (citation) => {
  if (citation.verified === 'true' || citation.verified === true) return 'verified'
  if (citation.verified === 'true_by_parallel') return 'true_by_parallel'
  return 'unverified'
}

const isVerified = (citation) => {
  const status = getVerificationStatus(citation)
  return status === 'verified' || status === 'true_by_parallel'
}

// Helper function to check if case names are substantially similar
const areCaseNamesSimilar = (canonical, extracted) => {
  if (!canonical || !extracted) return false
  if (canonical === 'N/A' || extracted === 'N/A') return false
  
  const normalize = (name) => {
    return name.toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
  }
  
  const norm1 = normalize(canonical)
  const norm2 = normalize(extracted)
  
  if (norm1 === norm2) return true
  
  // Check if one contains the other or they have significant overlap
  const words1 = norm1.split(' ')
  const words2 = norm2.split(' ')
  const commonWords = words1.filter(word => words2.includes(word) && word.length > 2)
  
  return commonWords.length >= Math.min(words1.length, words2.length) * 0.6
}

// Helper function to check if dates are substantially similar
const areDatesSimilar = (canonical, extracted) => {
  if (!canonical || !extracted) return false
  
  // Extract year from both dates
  const getYear = (dateStr) => {
    const match = dateStr.match(/\d{4}/)
    return match ? match[0] : null
  }
  
  const year1 = getYear(canonical)
  const year2 = getYear(extracted)
  
  return year1 && year2 && year1 === year2
}

const getCitationStatusClass = (citation) => {
  const status = getVerificationStatus(citation)
  if (status === 'verified') return 'citation-verified'
  if (status === 'true_by_parallel') return 'citation-parallel'
  return 'citation-unverified'
}

const getCaseNameClass = (citation) => {
  const canonical = getCanonicalCaseName(citation)
  const extracted = getExtractedCaseName(citation)
  
  if (areCaseNamesSimilar(canonical, extracted)) return 'name-similar'
  return 'name-different'
}

const getDateClass = (citation) => {
  const canonical = getCanonicalDate(citation)
  const extracted = getExtractedDate(citation)
  
  if (areDatesSimilar(canonical, extracted)) return 'date-similar'
  return 'date-different'
}

const getScoreClass = (citation) => {
  const confidence = getConfidence(citation)
  if (typeof confidence === 'number') {
    if (confidence >= 0.8) return 'green'
    if (confidence >= 0.6) return 'yellow'
    if (confidence >= 0.4) return 'orange'
    return 'red'
  }
  return isVerified(citation) ? 'green' : 'red'
}

const getScoreDisplay = (citation) => {
  const confidence = getConfidence(citation)
  if (typeof confidence === 'number') {
    return Math.round(confidence * 100) + '%'
  }
  return isVerified(citation) ? '✓' : '✗'
}

const formatYear = (dateStr) => {
  if (!dateStr) return null
  const match = dateStr.match(/\d{4}/)
  return match ? match[0] : dateStr
}

const toggleExpanded = (citationKey) => {
  if (expandedCitations.value.has(citationKey)) {
    expandedCitations.value.delete(citationKey)
  } else {
    expandedCitations.value.add(citationKey)
  }
}

const resetPagination = () => { currentPage.value = 1 }
watch(activeFilter, resetPagination)
watch(searchQuery, resetPagination)
</script>

<template>
  <div class="citation-results">
    <div v-if="showLoading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Processing citations...</p>
      <ProcessingProgress 
        v-if="shouldShowProgressBar"
        :elapsed-time="0"
        :remaining-time="etaSeconds || 0"
        :total-progress="progress"
        :current-step="'Processing Citations'"
        :current-step-progress="progress"
        :processing-steps="[]"
        :citation-info="null"
        :rate-limit-info="null"
        :error="''"
        :can-retry="false"
        :timeout="null"
      />
    </div>

    <div v-else-if="error" class="error-state">
      <div class="error-icon">⚠️</div>
      <h3>Error Processing Citations</h3>
      <p>{{ error }}</p>
    </div>

    <div v-else-if="results && results.citations" class="results-content">
      <div class="results-header">
        <div class="header-content">
          <h2>Citation Verification Results</h2>
          <div class="summary-stats">
            <div class="stat-item verified">
              <span class="stat-number">{{ validCount }}</span>
              <span class="stat-label">Verified</span>
            </div>
            <div class="stat-item invalid">
              <span class="stat-number">{{ invalidCount }}</span>
              <span class="stat-label">Invalid</span>
            </div>
            <div class="stat-item total">
              <span class="stat-number">{{ filteredCitations.length }}</span>
              <span class="stat-label">Total (excluding statutes)</span>
            </div>
          </div>
        </div>
        <div class="action-buttons">
          <button class="action-btn copy-btn" @click="$emit('copy-results')">
            Copy Results
          </button>
          <button class="action-btn download-btn" @click="$emit('download-results')">
            Download
          </button>
        </div>
      </div>

      <div class="filter-section">
        <div class="filter-controls">
          <button 
            v-for="filter in filters" 
            :key="filter.value"
            :class="['filter-btn', { active: activeFilter === filter.value }]"
            @click="activeFilter = filter.value"
          >
            {{ filter.label }} ({{ filter.count }})
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

      <div v-if="filteredCitations.length > 0" class="citations-list">
        <div 
          v-for="citation in paginatedCitations" 
          :key="getCitation(citation)"
          :class="['citation-item', { verified: isVerified(citation), invalid: !isVerified(citation) }]"
        >
          <div class="citation-header">
            <div class="citation-main">
              <div class="citation-score">
                <span 
                  :class="['score-badge', getScoreClass(citation)]"
                  :title="'Confidence: ' + getConfidence(citation)"
                >
                  {{ getScoreDisplay(citation) }}
                </span>
              </div>
              <div class="citation-content">
                <div class="citation-link">
                  <a 
                    v-if="getCitationUrl(citation)"
                    :href="getCitationUrl(citation)" 
                    target="_blank"
                    :class="['citation-hyperlink', getCitationStatusClass(citation)]"
                  >
                    {{ getCitation(citation) }}
                  </a>
                  <span 
                    v-else 
                    :class="['citation-text', getCitationStatusClass(citation)]"
                  >
                    {{ getCitation(citation) }}
                  </span>
                </div>
                
                <!-- Canonical Case Name and Date -->
                <div v-if="getCanonicalCaseName(citation)" class="canonical-info">
                  <div class="canonical-label">Canonical:</div>
                  <div class="canonical-details">
                    <a 
                      v-if="getCitationUrl(citation)"
                      :href="getCitationUrl(citation)"
                      target="_blank"
                      :class="['canonical-name', getCaseNameClass(citation)]"
                    >
                      {{ getCanonicalCaseName(citation) }}
                    </a>
                    <span 
                      v-else
                      :class="['canonical-name', getCaseNameClass(citation)]"
                    >
                      {{ getCanonicalCaseName(citation) }}
                    </span>
                    <span v-if="getCanonicalDate(citation)" :class="['canonical-date', getDateClass(citation)]">
                      ({{ formatYear(getCanonicalDate(citation)) }})
                    </span>
                  </div>
                </div>
                
                <!-- Extracted Case Name and Date -->
                <div v-if="getExtractedCaseName(citation) || getExtractedDate(citation)" class="extracted-info">
                  <div class="extracted-label">Extracted from document:</div>
                  <div class="extracted-details">
                    <span v-if="getExtractedCaseName(citation)" :class="['extracted-name', getCaseNameClass(citation)]">
                      {{ getExtractedCaseName(citation) }}
                    </span>
                    <span v-if="getExtractedDate(citation)" :class="['extracted-date', getDateClass(citation)]">
                      ({{ formatYear(getExtractedDate(citation)) }})
                    </span>
                    <span v-if="!getExtractedCaseName(citation) && !getExtractedDate(citation)" class="no-extraction">
                      No case name or date extracted
                    </span>
                  </div>
                </div>
                
                <div class="citation-meta">
                  <span class="source">{{ getSource(citation) }}</span>
                  <span v-if="getVerificationMethod(citation) !== 'N/A'" class="method">
                    via {{ getVerificationMethod(citation) }}
                  </span>
                  <span class="verification-status" :class="getVerificationStatus(citation)">
                    {{ getVerificationStatus(citation).replace('_', ' ') }}
                  </span>
                </div>
              </div>
            </div>
            <div class="citation-actions">
              <button 
                :class="['expand-btn', { expanded: expandedCitations.has(getCitation(citation)) }]"
                @click="toggleExpanded(getCitation(citation))"
              >
                {{ expandedCitations.has(getCitation(citation)) ? '−' : '+' }}
              </button>
            </div>
          </div>

          <div v-if="expandedCitations.has(getCitation(citation))" class="citation-details">
            <div class="detail-section">
              <h4 class="section-title">Citation Information</h4>
              <div class="detail-row">
                <span class="detail-label">Status:</span>
                <span :class="{ 'text-success': isVerified(citation), 'text-danger': !isVerified(citation) }">
                  {{ isVerified(citation) ? 'Verified' : 'Invalid' }}
                </span>
              </div>
              <div v-if="citation.canonical_date" class="detail-row">
                <span class="detail-label">Date:</span>
                <span>{{ citation.canonical_date }}</span>
              </div>
              <div v-if="citation.court" class="detail-row">
                <span class="detail-label">Court:</span>
                <span>{{ citation.court }}</span>
              </div>
              <div v-if="citation.docket_number" class="detail-row">
                <span class="detail-label">Docket:</span>
                <span>{{ citation.docket_number }}</span>
              </div>
              <div v-if="getError(citation)" class="detail-row">
                <span class="detail-label">Error:</span>
                <span class="text-danger">{{ getError(citation) }}</span>
              </div>
              <div v-if="citation.parallel_citations && citation.parallel_citations.length > 0" class="detail-row">
                <span class="detail-label">Parallel Citations:</span>
                <div class="parallel-citations">
                  <span 
                    v-for="parallel in citation.parallel_citations"
                    :key="parallel.citation"
                    class="parallel-citation"
                  >
                    {{ parallel.citation }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="no-results">
        <p>No citations found matching your criteria.</p>
      </div>

      <div v-if="totalPages > 1" class="pagination">
        <button 
          :disabled="currentPage === 1"
          @click="currentPage = currentPage - 1"
          class="pagination-btn"
        >
          Previous
        </button>
        <span class="pagination-info">
          Page {{ currentPage }} of {{ totalPages }}
        </span>
        <button 
          :disabled="currentPage === totalPages"
          @click="currentPage = currentPage + 1"
          class="pagination-btn"
        >
          Next
        </button>
      </div>
    </div>

    <div v-else class="no-results-state">
      <p>No citation results to display.</p>
    </div>
  </div>
</template>

<style scoped>
.citation-results {
  max-width: 1200px;
  margin: 0 auto;
}

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
}

.stat-item.verified .stat-number {
  color: #28a745;
}

.stat-item.invalid .stat-number {
  color: #dc3545;
}

.stat-item.total .stat-number {
  color: #007bff;
}

.stat-label {
  font-size: 0.8rem;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.action-buttons {
  display: flex;
  gap: 1rem;
}

.action-btn {
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

.citations-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.citation-item {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.citation-item:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  transform: translateY(-1px);
}

.citation-item.verified {
  border-left: 4px solid #28a745;
}

.citation-item.invalid {
  border-left: 4px solid #dc3545;
}

.citation-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1rem;
}

.citation-main {
  flex: 1;
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.citation-score {
  flex-shrink: 0;
}

.score-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: bold;
  color: white;
  min-width: 35px;
  text-align: center;
}

.score-badge.green {
  background: #28a745;
}

.score-badge.yellow {
  background: #ffc107;
  color: #212529;
}

.score-badge.orange {
  background: #fd7e14;
}

.score-badge.red {
  background: #dc3545;
}

.citation-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.citation-link {
  font-weight: 600;
}

.citation-hyperlink {
  color: #007bff;
  text-decoration: none;
  font-family: 'Courier New', monospace;
  font-weight: 600;
}

.citation-hyperlink:hover {
  text-decoration: underline;
}

.citation-text {
  font-weight: 600;
  color: #2c3e50;
  font-family: 'Courier New', monospace;
}

/* Citation status colors */
.citation-verified {
  color: #28a745 !important;
}

.citation-parallel {
  color: #ffc107 !important;
}

.citation-unverified {
  color: #dc3545 !important;
}

/* Canonical and Extracted Info Sections */
.canonical-info,
.extracted-info {
  margin: 0.5rem 0;
  padding: 0.5rem;
  border-radius: 4px;
  background: #f8f9fa;
}

.canonical-info {
  border-left: 3px solid #007bff;
}

.extracted-info {
  border-left: 3px solid #6c757d;
}

.canonical-label,
.extracted-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.25rem;
}

.canonical-details,
.extracted-details {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

/* Case name similarity colors */
.canonical-name,
.extracted-name {
  font-weight: 600;
  font-size: 0.9rem;
  text-decoration: none;
}

.canonical-name:hover {
  text-decoration: underline;
}

.name-similar {
  color: #28a745;
}

.name-different {
  color: #ffc107;
}

/* Maintain color on hover for canonical name links */
.canonical-name.name-similar:hover {
  color: #1e7e34;
}

.canonical-name.name-different:hover {
  color: #e0a800;
}

/* Date similarity colors */
.canonical-date,
.extracted-date {
  font-weight: 500;
  font-size: 0.85rem;
}

.date-similar {
  color: #28a745;
}

.date-different {
  color: #ffc107;
}

.no-extraction {
  color: #6c757d;
  font-style: italic;
  font-size: 0.85rem;
}

.citation-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: #6c757d;
  flex-wrap: wrap;
  margin-top: 0.5rem;
}

.source {
  font-weight: 500;
}

.method {
  font-style: italic;
}

.verification-status {
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.verification-status.verified {
  background: #d4edda;
  color: #155724;
}

.verification-status.true_by_parallel {
  background: #fff3cd;
  color: #856404;
}

.verification-status.unverified {
  background: #f8d7da;
  color: #721c24;
}

.citation-actions {
  display: flex;
  gap: 0.5rem;
}

.expand-btn {
  background: none;
  border: none;
  padding: 0.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  color: #6c757d;
  transition: all 0.2s;
}

.expand-btn:hover {
  background: #f8f9fa;
  color: #495057;
}

.expand-btn.expanded {
  background: #e9ecef;
  color: #495057;
}

.citation-details {
  padding: 1rem;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
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

.text-success {
  color: #28a745;
  font-weight: 600;
}

.text-danger {
  color: #dc3545;
  font-weight: 600;
}

.parallel-citations {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.parallel-citation {
  background: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
  font-family: 'Courier New', monospace;
}

.no-results,
.no-results-state {
  text-align: center;
  padding: 3rem;
  color: #6c757d;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
  padding: 1rem;
}

.pagination-btn {
  padding: 0.5rem 1rem;
  border: 2px solid #e9ecef;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.pagination-btn:hover:not(:disabled) {
  border-color: #007bff;
  background: #f8f9fa;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-info {
  font-weight: 600;
  color: #495057;
}

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
  
  .citation-main {
    align-items: flex-start;
  }
}
</style>