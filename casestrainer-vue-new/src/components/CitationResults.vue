<script setup>
console.log('🚀 Citation Results Component Loaded!')

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
const useHorizontalLayout = ref(false) // Toggle for alternative layout
const displayMode = ref('full') // 'full', 'horizontal', 'canonical-only'

const attentionFilter = ref('all')
const showAll = ref(false)

// Helper functions for filtering
function isUnverified(cluster) {
  return cluster.citations.every(c => getVerificationStatus(c) === 'unverified')
}
function isNameMismatch(cluster) {
  return cluster.citations.some(c => !areCaseNamesSimilar(getCanonicalCaseName(c), getExtractedCaseName(c)))
}
function isDateMismatch(cluster) {
  return cluster.citations.some(c => !areDatesSimilar(getCanonicalDate(c), getExtractedDate(c)))
}

const filteredCitationsNeedingAttention = computed(() => {
  if (showAll.value) {
    // Show all clusters/citations
    if (props.results?.clusters && props.results.clusters.length > 0) {
      return props.results.clusters
    }
    if (props.results?.citations) {
      return [{ citations: props.results.citations }]
    }
    return []
  }
  // Default: show only those needing attention
  if (attentionFilter.value === 'unverified') {
    return citationsNeedingAttention.value.filter(isUnverified)
  } else if (attentionFilter.value === 'name') {
    return citationsNeedingAttention.value.filter(isNameMismatch)
  } else if (attentionFilter.value === 'date') {
    return citationsNeedingAttention.value.filter(isDateMismatch)
  }
  return citationsNeedingAttention.value
})

watch(() => props.results, (newVal, oldVal) => {
  // Update progress values
  if (newVal && typeof newVal.progress === 'number') {
    progress.value = newVal.progress
    etaSeconds.value = newVal.eta_seconds
  }
  
  // Debug logging
  console.log('🔍 Results prop changed:', {
    newVal,
    oldVal,
    hasClusters: !!(newVal && newVal.clusters),
    clustersLength: newVal && newVal.clusters ? newVal.clusters.length : 'N/A',
    hasCitations: !!(newVal && newVal.citations),
    citationsLength: newVal && newVal.citations ? newVal.citations.length : 'N/A'
  })
}, { immediate: true, deep: true })

const shouldShowProgressBar = computed(() => {
  return props.showLoading && progress.value > 0 && progress.value < 100
})

const validCount = computed(() => {
  if (props.results?.clusters && props.results.clusters.length > 0) {
    // Count verified citations from clusters
    return props.results.clusters.reduce((total, cluster) => {
      return total + cluster.citations.filter(c => c.verified === 'true' || c.verified === true).length
    }, 0)
  }
  if (!props.results?.citations) return 0
  return props.results.citations.filter(c => c.verified === 'true' || c.verified === true).length
})

const invalidCount = computed(() => {
  if (props.results?.clusters && props.results.clusters.length > 0) {
    // Count invalid citations from clusters
    return props.results.clusters.reduce((total, cluster) => {
      return total + cluster.citations.filter(c => c.verified === 'false' || c.verified === false).length
    }, 0)
  }
  if (!props.results?.citations) return 0
  return props.results.citations.filter(c => c.verified === 'false' || c.verified === false).length
})

const filteredClusters = computed(() => {
  if (!props.results?.clusters || props.results.clusters.length === 0) {
    return []
  }
  
  return props.results.clusters.map(cluster => {
    // Filter citations within each cluster
    let filteredCitations = cluster.citations.filter(c => !isStatuteOrRegulation(c))
    
    if (activeFilter.value === 'verified') {
      filteredCitations = filteredCitations.filter(c => c.verified === 'true' || c.verified === true)
    } else if (activeFilter.value === 'invalid') {
      filteredCitations = filteredCitations.filter(c => c.verified === 'false' || c.verified === false)
    }
    
    if (searchQuery.value.trim()) {
      const query = searchQuery.value.toLowerCase()
      filteredCitations = filteredCitations.filter(c => 
        (c.citation && c.citation.toLowerCase().includes(query)) ||
        (c.canonical_citation && c.canonical_citation.toLowerCase().includes(query)) ||
        (c.primary_citation && c.primary_citation.toLowerCase().includes(query)) ||
        (getCaseName(c) && getCaseName(c).toLowerCase().includes(query))
      )
    }
    
    // Return cluster with filtered citations, but only if it has any citations left
    if (filteredCitations.length > 0) {
      return {
        ...cluster,
        citations: filteredCitations,
        size: filteredCitations.length
      }
    }
    return null
  }).filter(cluster => cluster !== null)
})

const allCitations = computed(() => {
  if (props.results?.clusters && props.results.clusters.length > 0) {
    // Get all citations from all clusters
    return props.results.clusters.flatMap(cluster => cluster.citations)
  }
  
  if (!props.results?.citations) return []
  return props.results.citations.filter(c => !isStatuteOrRegulation(c))
})

// Helper function to calculate citation score (4/4 system)
const calculateCitationScore = (citation) => {
  let score = 0
  
  // Check if we have canonical name (2 points)
  if (citation.canonical_name && citation.canonical_name !== 'N/A') {
    score += 2
  }
  
  // Check if extracted and canonical names are similar (1 point)
  const canonical = citation.canonical_name
  const extracted = citation.extracted_case_name
  if (canonical && canonical !== 'N/A' && extracted && extracted !== 'N/A') {
    if (areCaseNamesSimilar(canonical, extracted)) {
      score += 1
    }
  }
  
  // Check if we have canonical date (1 point)
  if (citation.canonical_date && citation.canonical_date !== 'N/A') {
    score += 1
  }
  
  // Check if we have URL (1 point)
  if (citation.url && citation.url !== '') {
    score += 1
  }
  
  return score
}

// Filter clusters to only show those that don't have perfect 4/4 scores
const citationsNeedingAttention = computed(() => {
  if (props.results?.clusters && props.results.clusters.length > 0) {
    return props.results.clusters.filter(cluster => {
      // Check if any citation in the cluster doesn't have a perfect score
      return cluster.citations.some(citation => {
        const score = calculateCitationScore(citation)
        return score < 4
      })
    })
  }
  
  // For individual citations (no clusters)
  if (props.results?.citations) {
    const imperfectCitations = props.results.citations.filter(citation => {
      const score = calculateCitationScore(citation)
      return score < 4
    })
    
    // Return as a single cluster for display consistency
    return imperfectCitations.length > 0 ? [{ citations: imperfectCitations }] : []
  }
  
  return []
})

const filteredCitations = computed(() => {
  if (props.results?.clusters && props.results.clusters.length > 0) {
    // Use filtered clusters and flatten for backward compatibility
    return filteredClusters.value.flatMap(cluster => cluster.citations)
  }
  
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

// Remove clustersPerPage, totalClusterPages, paginatedClusters
// Only use filteredClusters for rendering

const filters = computed(() => [
  { value: 'all', label: 'All', count: filteredCitations.value.length },
  { value: 'verified', label: 'Verified', count: validCount.value },
  { value: 'invalid', label: 'Invalid', count: invalidCount.value }
])

// Helper functions to handle the actual data structure
const getCaseName = (citation) => {
  return citation.case_name || citation.canonical_name || citation.extracted_case_name || null
}

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

const toggleCitationDetails = (citationKey) => {
  toggleExpanded(citationKey)
}

const resetPagination = () => { currentPage.value = 1 }
watch(activeFilter, resetPagination)
watch(searchQuery, resetPagination)

// Helper: Deduplicate (name, year) pairs for canonical and extracted
function uniqueNameYearPairs(citations, getName, getYear) {
  const seen = new Set();
  const result = [];
  for (const c of citations) {
    const name = getName(c);
    const year = getYear(c);
    if (!name && !year) continue;
    const key = `${name || ''}||${year || ''}`;
    if (!seen.has(key)) {
      seen.add(key);
      result.push({ name, year, citation: c });
    }
  }
  return result;
}

// Helper: Get mismatch reason for a citation
function getMismatchReason(citation) {
  const canonical = getCanonicalCaseName(citation)
  const extracted = getExtractedCaseName(citation)
  const canonicalDate = getCanonicalDate(citation)
  const extractedDate = getExtractedDate(citation)
  if (!isVerified(citation)) return 'Unverified';
  if (canonical && extracted && !areCaseNamesSimilar(canonical, extracted)) return 'Name mismatch';
  if (canonicalDate && extractedDate && !areDatesSimilar(canonicalDate, extractedDate)) return 'Date mismatch';
  return '';
}

// Add copy/download all logic
function getAllCitationData() {
  // Flatten all clusters/citations for export
  let allCitations = []
  if (props.results?.clusters && props.results.clusters.length > 0) {
    props.results.clusters.forEach(cluster => {
      allCitations.push(...cluster.citations)
    })
  } else if (props.results?.citations) {
    allCitations = props.results.citations
  }
  return allCitations
}

function copyAllCitations() {
  const allCitations = getAllCitationData()
  const text = allCitations.map(c =>
    `${getCitation(c)}\nExtracted Name: ${getExtractedCaseName(c) || 'N/A'}\nCanonical Name: ${getCanonicalCaseName(c) || 'N/A'}\nExtracted Date: ${getExtractedDate(c) || 'N/A'}\nCanonical Date: ${getCanonicalDate(c) || 'N/A'}\nStatus: ${getVerificationStatus(c)}\nMismatch Reason: ${getMismatchReason(c)}\nSource: ${getSource(c)}\nConfidence: ${getConfidence(c)}\nError: ${getError(c) || ''}\n---`
  ).join('\n')
  navigator.clipboard.writeText(text)
  emit('toast', { type: 'success', message: 'All citation data copied!' })
}

function downloadAllCitations() {
  const allCitations = getAllCitationData()
  const data = allCitations.map(c => ({
    citation: getCitation(c),
    extracted_name: getExtractedCaseName(c),
    canonical_name: getCanonicalCaseName(c),
    extracted_date: getExtractedDate(c),
    canonical_date: getCanonicalDate(c),
    status: getVerificationStatus(c),
    mismatch_reason: getMismatchReason(c),
    source: getSource(c),
    confidence: getConfidence(c),
    error: getError(c)
  }))
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'all_citations.json'
  a.click()
  URL.revokeObjectURL(url)
  emit('toast', { type: 'success', message: 'All citation data downloaded!' })
}
</script>

<template>
  <div class="citation-results">

    <!-- CITATIONS THAT NEED ATTENTION SECTION AT TOP -->
    <div v-if="results && (results.clusters || results.citations)" class="prominent-citations-section">
      <div class="citations-summary">
        <div v-if="citationsNeedingAttention.length > 0">
          <h3>Citations That Need Attention</h3>
          <div class="attention-filter-btns">
            <button :class="['attention-filter-btn', { active: attentionFilter === 'all' }]" @click="attentionFilter = 'all'">All</button>
            <button :class="['attention-filter-btn', { active: attentionFilter === 'unverified' }]" @click="attentionFilter = 'unverified'">Unverified</button>
            <button :class="['attention-filter-btn', { active: attentionFilter === 'name' }]" @click="attentionFilter = 'name'">Name Mismatch</button>
            <button :class="['attention-filter-btn', { active: attentionFilter === 'date' }]" @click="attentionFilter = 'date'">Date Mismatch</button>
          </div>
          <div class="citations-grid">
            <div v-for="cluster in filteredCitationsNeedingAttention" :key="cluster.cluster_id || getCitation(cluster.citations[0])" class="citation-comparison-card">
              <!-- Custom forced display for all-unverified, no canonical/extracted -->
              <template v-if="cluster.citations.every(c => getVerificationStatus(c) === 'unverified') &&
                uniqueNameYearPairs(cluster.citations, getCanonicalCaseName, c => formatYear(getCanonicalDate(c))).length === 0 &&
                uniqueNameYearPairs(cluster.citations, getExtractedCaseName, c => formatYear(getExtractedDate(c))).length === 0">
                <!-- First line: Citation in red, no link -->
                <div class="citation-row" style="color: #dc3545; font-weight: bold; font-size: 1.15rem;">
                  {{ getCitation(cluster.citations[0]) }}
                </div>
                <!-- Second line: N/A, N/A for canonical in red -->
                <div class="citation-row flex-names-row">
                  <span class="row-label">Verified:</span>
                  <span style="color: #dc3545; font-weight: bold;">N/A, N/A</span>
                </div>
                <!-- Third line: N/A, N/A for extracted in red -->
                <div class="citation-row flex-names-row">
                  <span class="row-label">From Document:</span>
                  <span style="color: #dc3545; font-weight: bold;">N/A, N/A</span>
                </div>
              </template>
              <template v-else>
                <!-- First row: all parallel citations with their verification badges -->
                <div class="citation-row citation-row-citations" @click="toggleCitationDetails(getCitation(cluster.citations[0]))">
                  <template v-for="(citation, idx) in cluster.citations">
                    <span class="citation-parallel-item">
                      <a v-if="getVerificationStatus(citation) === 'verified' && getCitationUrl(citation)" :href="getCitationUrl(citation)" target="_blank" class="citation-link-verified" @click.stop>{{ getCitation(citation) }}</a>
                      <span v-else class="citation-text">{{ getCitation(citation) }}</span>
                      <span class="verification-badge" :class="getVerificationStatus(citation)">
                        <template v-if="getVerificationStatus(citation) === 'true_by_parallel'">PARALLEL CITATION VERIFIED</template>
                        <template v-else>{{ getVerificationStatus(citation).replace('_', ' ') }}</template>
                      </span>
                    </span>
                    <span v-if="idx < cluster.citations.length - 1">, </span>
                  </template>
                  <div class="expand-icon" :class="{ expanded: expandedCitations.has(getCitation(cluster.citations[0])) }">▼</div>
                </div>
                <!-- Second row: unique canonical names/dates -->
                <div class="citation-row citation-row-canonical flex-names-row">
                  <span class="row-label">Verified:</span>
                  <div class="names-flex-wrap">
                    <template v-for="(pair, idx) in uniqueNameYearPairs(cluster.citations, getCanonicalCaseName, c => formatYear(getCanonicalDate(c)))">
                      <span class="canonical-name-block">
                        <span v-if="pair.name && pair.name !== 'N/A'" :class="['canonical-name', getCaseNameClass(pair.citation)]">
                          {{ pair.name }}
                          <span v-if="pair.year" :class="['canonical-date', getDateClass(pair.citation)]"> ({{ pair.year }})</span>
                          <span v-else class="canonical-date missing">(no date)</span>
                        </span>
                        <span v-else class="canonical-name missing">No canonical name</span>
                      </span>
                      <span v-if="idx < uniqueNameYearPairs(cluster.citations, getCanonicalCaseName, c => formatYear(getCanonicalDate(c))).length - 1">, </span>
                    </template>
                  </div>
                </div>
                <!-- Force a line break between canonical and extracted rows -->
                <div style="height: 0.5em;"></div>
                <!-- Third row: unique extracted names/dates -->
                <div class="citation-row citation-row-extracted flex-names-row">
                  <span class="row-label">From Document:</span>
                  <div class="names-flex-wrap">
                    <template v-for="(pair, idx) in uniqueNameYearPairs(cluster.citations, getExtractedCaseName, c => formatYear(getExtractedDate(c)))">
                      <span class="extracted-name-block">
                        <span v-if="pair.name && pair.name !== 'N/A'" :class="['extracted-name', getCaseNameClass(pair.citation)]">
                          {{ pair.name }}
                          <span v-if="pair.year" :class="['extracted-date', getDateClass(pair.citation)]"> ({{ pair.year }})</span>
                          <span v-else class="extracted-date missing">(no date)</span>
                        </span>
                        <span v-else class="extracted-name missing">No extracted name</span>
                      </span>
                      <span v-if="idx < uniqueNameYearPairs(cluster.citations, getExtractedCaseName, c => formatYear(getExtractedDate(c))).length - 1">, </span>
                    </template>
                  </div>
                </div>
                <!-- Collapsible details section -->
                <div v-show="expandedCitations.has(getCitation(cluster.citations[0]))" class="citation-details">
                  <div v-for="(citation, idx) in cluster.citations" :key="getCitation(citation) + '-details'">
                    <div class="detail-row"><span class="detail-label">Source:</span> <span>{{ getSource(citation) }}</span></div>
                    <div class="detail-row"><span class="detail-label">Verification:</span> <span>{{ getVerificationStatus(citation) }}</span></div>
                    <div class="detail-row" v-if="getError(citation)"><span class="detail-label">Error:</span> <span>{{ getError(citation) }}</span></div>
                    <div class="detail-row"><span class="detail-label">Mismatch Reason:</span> <span>{{ getMismatchReason(citation) }}</span></div>
                    <!-- Add more details/context as needed -->
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
        <div v-else class="perfect-score-celebration">
          <div class="celebration-content">
            <div class="celebration-icon">🎉</div>
            <h3 class="celebration-title">Perfect Score! 🏆</h3>
            <p class="celebration-message">All citations are verified and complete! Great job on your legal research.</p>
            <div class="celebration-stats">
              <span class="stat-badge">✅ All Verified</span>
              <span class="stat-badge">📋 Complete Data</span>
              <span class="stat-badge">🔗 Links Available</span>
            </div>
          </div>
        </div>
      </div>
    </div>

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

    <!-- CLUSTERED DISPLAY: Check for clusters first and prioritize this display -->
    <div v-else-if="results && results.clusters && results.clusters.length > 0" class="results-content">
      
      <div class="results-header">
        <div class="header-content">
          <h2>Citation Verification Results (Clustered)</h2>
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
              <span class="stat-number">{{ filteredClusters.length }}</span>
              <span class="stat-label">Clusters</span>
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
        <div class="layout-controls">
          <button 
            :class="['layout-btn', { active: displayMode === 'full' }]"
            @click="displayMode = 'full'"
            title="Full Display with All Details"
          >
            <span>📋</span> Citation on Top
          </button>
          <button 
            :class="['layout-btn', { active: displayMode === 'horizontal' }]"
            @click="displayMode = 'horizontal'"
            title="Horizontal Layout"
          >
            <span>��</span> Horizontal
          </button>
          <button 
            :class="['layout-btn', { active: displayMode === 'canonical-only' }]"
            @click="displayMode = 'canonical-only'"
            title="Name/Date on Top"
          >
            <span>📝</span> Name/Date on Top
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

      <!-- CLUSTER DISPLAY -->
      <div class="citations-list">
        <!-- FULL DISPLAY (Original) -->
        <div v-if="displayMode === 'full'">
          <div v-for="cluster in filteredClusters" :key="cluster.cluster_id" class="cluster-item">
            <!-- Cluster-level info -->
            <div class="cluster-header">
              <h3>
                <span v-if="cluster.canonical_name && cluster.canonical_name !== 'N/A'">
                  {{ cluster.canonical_name }}
                </span>
                <span v-else>Unverified Cluster</span>
                <span v-if="cluster.canonical_date" class="canonical-date">
                  ({{ formatYear(cluster.canonical_date) }})
                </span>
              </h3>
              <div v-if="cluster.extracted_case_name && cluster.extracted_case_name !== 'N/A'" class="extracted-info">
                <span class="extracted-label">Extracted from document:</span>
                <span class="extracted-name">{{ cluster.extracted_case_name }}</span>
                <span v-if="cluster.extracted_date" class="extracted-date">
                  ({{ formatYear(cluster.extracted_date) }})
                </span>
              </div>
              <div class="cluster-meta">
                <span class="cluster-size">{{ cluster.size }} citation<span v-if="cluster.size > 1">s</span></span>
                <span v-if="cluster.url">
                  <a :href="cluster.url" target="_blank">View on CourtListener</a>
                </span>
              </div>
            </div>
            
            <!-- List all citations in this cluster as rows -->
            <div class="cluster-citations">
              <div v-for="(citation, index) in cluster.citations" :key="`${cluster.cluster_id}-${index}`" class="citation-row">
                <div class="citation-row-content">
                  <div class="citation-score">
                    <span 
                      :class="['score-badge', getScoreClass(citation)]"
                      :title="'Confidence: ' + getConfidence(citation)"
                    >
                      {{ getScoreDisplay(citation) }}
                    </span>
                  </div>
                  <div class="citation-details">
                    <div class="citation-text-line">
                      <a 
                        v-if="getCitationUrl(citation)"
                        :href="getCitationUrl(citation)" 
                        target="_blank"
                        class="citation-link"
                      >
                        {{ getCitation(citation) }}
                      </a>
                      <span v-else class="citation-text">
                        {{ getCitation(citation) }}
                      </span>
                    </div>
                    <div class="citation-meta-line">
                      <span class="source">{{ getSource(citation) }}</span>
                      <span class="verification-status" :class="getVerificationStatus(citation)">
                        {{ getVerificationStatus(citation).replace('_', ' ') }}
                      </span>
                    </div>
                    <div class="detail-row"><span class="detail-label">Mismatch Reason:</span> <span>{{ getMismatchReason(citation) }}</span></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- HORIZONTAL LAYOUT (Alternative) -->
        <div v-else-if="displayMode === 'horizontal'" class="horizontal-clusters">
          <div v-for="cluster in filteredClusters" :key="cluster.cluster_id" class="horizontal-cluster-card">
            <div class="horizontal-cluster-header">
              <div class="cluster-title-section">
                <h3 class="cluster-title">
                  <span v-if="cluster.canonical_name && cluster.canonical_name !== 'N/A'">
                    {{ cluster.canonical_name }}
                  </span>
                  <span v-else>Unverified Cluster</span>
                  <span v-if="cluster.canonical_date" class="canonical-date">
                    ({{ formatYear(cluster.canonical_date) }})
                  </span>
                </h3>
                <div v-if="cluster.extracted_case_name && cluster.extracted_case_name !== 'N/A'" class="extracted-info">
                  <span class="extracted-label">Extracted:</span>
                  <span class="extracted-name">{{ cluster.extracted_case_name }}</span>
                  <span v-if="cluster.extracted_date" class="extracted-date">
                    ({{ formatYear(cluster.extracted_date) }})
                  </span>
                </div>
              </div>
              <div class="cluster-actions">
                <span class="cluster-size-badge">{{ cluster.size }} citation<span v-if="cluster.size > 1">s</span></span>
                <a v-if="cluster.url" :href="cluster.url" target="_blank" class="courtlistener-link">
                  <span>🔗</span> CourtListener
                </a>
              </div>
            </div>
            
            <div class="horizontal-citations-grid">
              <div v-for="(citation, index) in cluster.citations" :key="`${cluster.cluster_id}-${index}`" class="horizontal-citation-card">
                <div class="citation-card-header">
                  <span 
                    :class="['score-badge', getScoreClass(citation)]"
                    :title="'Confidence: ' + getConfidence(citation)"
                  >
                    {{ getScoreDisplay(citation) }}
                  </span>
                  <span class="verification-status" :class="getVerificationStatus(citation)">
                    {{ getVerificationStatus(citation).replace('_', ' ') }}
                  </span>
                </div>
                <div class="citation-card-body">
                  <div class="citation-text">
                    <a 
                      v-if="getCitationUrl(citation)"
                      :href="getCitationUrl(citation)" 
                      target="_blank"
                      class="citation-link"
                    >
                      {{ getCitation(citation) }}
                    </a>
                    <span v-else>
                      {{ getCitation(citation) }}
                    </span>
                  </div>
                  <div class="citation-source">
                    <span class="source-label">Source:</span>
                    <span class="source-value">{{ getSource(citation) }}</span>
                  </div>
                  <div class="detail-row"><span class="detail-label">Mismatch Reason:</span> <span>{{ getMismatchReason(citation) }}</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- CANONICAL-ONLY DISPLAY -->
        <div v-else-if="displayMode === 'canonical-only'" class="canonical-only-clusters">
          <div v-for="cluster in filteredClusters" :key="cluster.cluster_id" class="canonical-only-card">
            <!-- First line: Canonical name and date -->
            <div class="canonical-line">
              <span class="canonical-label">Canonical:</span>
              <span v-if="getCanonicalCaseName(cluster.citations[0]) && getCanonicalCaseName(cluster.citations[0]) !== 'N/A'" 
                    :class="['canonical-name', getCaseNameClass(cluster.citations[0])]">
                {{ getCanonicalCaseName(cluster.citations[0]) }}
                <span v-if="getCanonicalDate(cluster.citations[0])" :class="['canonical-date', getDateClass(cluster.citations[0])]">
                  ({{ formatYear(getCanonicalDate(cluster.citations[0])) }})
                </span>
                <span v-else class="canonical-date missing">(no date)</span>
              </span>
              <span v-else class="canonical-name missing">No canonical name</span>
            </div>
            
            <!-- Second line: Extracted name and date -->
            <div class="extracted-line">
              <span class="extracted-label">Extracted:</span>
              <span v-if="getExtractedCaseName(cluster.citations[0]) && getExtractedCaseName(cluster.citations[0]) !== 'N/A'" 
                    :class="['extracted-name', getCaseNameClass(cluster.citations[0])]">
                {{ getExtractedCaseName(cluster.citations[0]) }}
                <span v-if="getExtractedDate(cluster.citations[0])" :class="['extracted-date', getDateClass(cluster.citations[0])]">
                  ({{ formatYear(getExtractedDate(cluster.citations[0])) }})
                </span>
                <span v-else class="extracted-date missing">(no date)</span>
              </span>
              <span v-else class="extracted-name missing">No extracted name</span>
            </div>
            
            <!-- Third line: All citations in the cluster -->
            <div class="citations-line">
              <span class="citations-label">Citations:</span>
              <div class="citations-list-inline">
                <template v-for="(citation, idx) in cluster.citations">
                  <a v-if="getVerificationStatus(citation) === 'verified' && getCitationUrl(citation)" 
                     :href="getCitationUrl(citation)" 
                     target="_blank" 
                     class="citation-link-verified">
                    {{ getCitation(citation) }}
                  </a>
                  <span v-else class="citation-text">{{ getCitation(citation) }}</span>
                  <span v-if="idx < cluster.citations.length - 1">, </span>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- FALLBACK: Single-citation display if no clusters -->
    <div v-else-if="results && results.citations && results.citations.length > 0" class="results-content">
      <div class="results-header">
        <div class="header-content">
          <h2>Citation Verification Results (Individual)</h2>
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
              <span class="stat-label">Total</span>
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

      <!-- Individual citations display -->
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
        <div class="layout-controls">
          <button 
            :class="['layout-btn', { active: displayMode === 'full' }]"
            @click="displayMode = 'full'"
            title="Full Display with All Details"
          >
            <span>📋</span> Citation on Top
          </button>
          <button 
            :class="['layout-btn', { active: displayMode === 'horizontal' }]"
            @click="displayMode = 'horizontal'"
            title="Horizontal Layout"
          >
            <span>📄</span> Horizontal
          </button>
          <button 
            :class="['layout-btn', { active: displayMode === 'canonical-only' }]"
            @click="displayMode = 'canonical-only'"
            title="Name/Date on Top"
          >
            <span>📝</span> Name/Date on Top
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

      <div class="citations-list">
        <div v-for="citation in filteredCitations" :key="getCitation(citation)" class="citation-item individual">
          <!-- Three-line display for single citation, matching cluster card -->
          <div class="citation-row citation-row-citations">
            <span class="citation-text">{{ getCitation(citation) }}</span>
            <span class="verification-badge" :class="getVerificationStatus(citation)">
              {{ getVerificationStatus(citation) }}
            </span>
          </div>
          <div class="citation-row citation-row-canonical flex-names-row">
            <span class="row-label">Verified:</span>
            <span>
              <span v-if="getCanonicalCaseName(citation) && getCanonicalCaseName(citation) !== 'N/A'">
                {{ getCanonicalCaseName(citation) }}
                <span v-if="getCanonicalDate(citation)" :class="['canonical-date', getDateClass(citation)]">
                  ({{ formatYear(getCanonicalDate(citation)) }})
                </span>
                <span v-else class="canonical-date missing">(no date)</span>
              </span>
              <span v-else class="canonical-name missing">No canonical name</span>
            </span>
          </div>
          <div class="citation-row citation-row-extracted flex-names-row">
            <span class="row-label">From Document:</span>
            <span>
              <span v-if="getExtractedCaseName(citation) && getExtractedCaseName(citation) !== 'N/A'">
                {{ getExtractedCaseName(citation) }}
                <span v-if="getExtractedDate(citation)" :class="['extracted-date', getDateClass(citation)]">
                  ({{ formatYear(getExtractedDate(citation)) }})
                </span>
                <span v-else class="extracted-date missing">(no date)</span>
              </span>
              <span v-else class="extracted-name missing">No extracted name</span>
            </span>
          </div>
          <div class="detail-row"><span class="detail-label">Mismatch Reason:</span> <span>{{ getMismatchReason(citation) }}</span></div>
        </div>
      </div>
    </div>

    <div v-else class="no-results-state">
      <p>No citation results to display.</p>
    </div>
  </div>
</template>

<style scoped>
/* Your existing styles here - keeping them the same */
.citation-results {
  max-width: 1200px;
  margin: 0 auto;
}

/* Prominent Citations Section at Top */
.prominent-citations-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

/* Perfect Score Celebration */
.perfect-score-celebration {
  text-align: center;
  padding: 2rem;
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  border-radius: 12px;
  border: 2px solid #28a745;
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.15);
}

.celebration-content {
  max-width: 600px;
  margin: 0 auto;
}

.celebration-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  animation: bounce 2s infinite;
}

.celebration-title {
  color: #155724;
  font-size: 1.8rem;
  font-weight: bold;
  margin-bottom: 1rem;
  text-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.celebration-message {
  color: #155724;
  font-size: 1.1rem;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.celebration-stats {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.stat-badge {
  background: #28a745;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}

.citations-summary h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.2rem;
}

.citations-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.citation-comparison-card {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  overflow: hidden;
}

.citation-comparison-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  transform: translateY(-1px);
}

.citation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.citation-header:hover {
  background-color: #f8f9fa;
}

.citation-main {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.expand-icon {
  font-size: 0.8rem;
  color: #6c757d;
  transition: transform 0.2s;
  margin-left: 0.5rem;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.citation-details {
  padding: 1rem;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.canonical-section,
.extracted-section {
  margin-bottom: 0.75rem;
}

.section-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.25rem;
}

.canonical-content,
.extracted-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.canonical-name,
.extracted-name {
  font-weight: 600;
  font-size: 0.9rem;
  display: inline;
}

.canonical-date,
.extracted-date {
  font-weight: 500;
  font-size: 0.85rem;
  display: inline;
  margin-left: 0.25rem;
}

/* Color coding for names - green if similar, dark yellow if different */
.canonical-name.name-similar,
.extracted-name.name-similar {
  color: #28a745;
}

.canonical-name.name-different,
.extracted-name.name-different {
  color: #ff9800;
}

.canonical-name.missing,
.extracted-name.missing {
  color: #6c757d;
  font-style: italic;
}

/* Color coding for dates - green if same year, yellow if different */
.canonical-date.date-similar,
.extracted-date.date-similar {
  color: #28a745;
}

.canonical-date.date-different,
.extracted-date.date-different {
  color: #ff9800;
}

.canonical-date.missing,
.extracted-date.missing {
  color: #6c757d;
  font-style: italic;
}



.citation-link-verified {
  color: #007bff;
  text-decoration: none;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.citation-link-verified:hover {
  color: #0056b3;
  text-decoration: underline;
}

.citation-text {
  font-weight: 600;
  font-family: 'Courier New', monospace;
  color: #2c3e50;
}

.verification-badge {
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.verification-badge.verified {
  background: #d4edda;
  color: #155724;
}

.verification-badge.true_by_parallel {
  background: #ff9800;
  color: #fff;
}

.verification-badge.unverified {
  background: #f8d7da;
  color: #721c24;
}

.cluster-citations {
  padding: 0;
}

.citation-row {
  border-bottom: 1px solid #e9ecef;
  transition: background-color 0.2s;
}

.citation-row:last-child {
  border-bottom: none;
}

.citation-row:hover {
  background-color: #f8f9fa;
}

.citation-row-content {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  gap: 1rem;
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

.score-badge.red {
  background: #dc3545;
}

.citation-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.citation-text-line {
  font-weight: 600;
}

.citation-link {
  color: #007bff;
  text-decoration: none;
  font-family: 'Courier New', monospace;
}

.citation-link:hover {
  text-decoration: underline;
}

.citation-text {
  font-family: 'Courier New', monospace;
  color: #2c3e50;
}

.citation-meta-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
  color: #6c757d;
}

.source {
  font-weight: 500;
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

.verification-status.unverified {
  background: #f8d7da;
  color: #721c24;
}

/* Rest of your existing styles... */
.loading-state {
  text-align: center;
  padding: 3rem;
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

.download-btn {
  background: #28a745;
  color: white;
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

.layout-controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.layout-btn {
  padding: 0.5rem 1rem; /* Match .filter-btn */
  border: 2px solid #e9ecef;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem; /* Match .filter-btn */
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
  height: 2.2rem; /* Match filter button height */
}

.layout-btn span {
  font-size: 1rem; /* Slightly smaller icon */
}

.layout-btn:hover {
  border-color: #007bff;
}

.layout-btn.active {
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

.citations-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.cluster-item {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.cluster-header {
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.cluster-header h3 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.extracted-info {
  margin: 0.5rem 0;
  font-size: 0.9rem;
}

.cluster-meta {
  font-size: 0.85rem;
  color: #6c757d;
  margin-top: 0.5rem;
}

.citation-item.individual {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1rem;
}

.citation-item.individual .citation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.no-results-state {
  text-align: center;
  padding: 3rem;
  color: #6c757d;
}

.name-date-row {
  display: flex;
  gap: 2rem;
  margin: 0.5rem 0 0.5rem 0;
  align-items: center;
  font-size: 1rem;
}
.canonical-name-block, .extracted-name-block {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.citation-parallels {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
  font-size: 1.05rem;
}
.citation-parallel-item {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #f8f9fa;
  border-radius: 6px;
  padding: 0.25rem 0.5rem;
  margin-bottom: 0.25rem;
}
.citation-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 0.25rem;
}
.citation-row-citations {
  font-size: 1.15rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}
.citation-row-canonical {
  font-size: 1rem;
  color: #28a745;
  margin-bottom: 0.25rem;
}
.citation-row-extracted {
  font-size: 1rem;
  color: #007bff;
  margin-bottom: 0.5rem;
}
.canonical-name-block, .extracted-name-block {
  margin-right: 1.5rem;
  white-space: nowrap;
}
.canonical-name.missing, .extracted-name.missing {
  color: #6c757d;
  font-style: italic;
}

.citation-row-canonical,
.citation-row-extracted {
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1.6;
  margin-bottom: 0.25rem;
}

.canonical-name, .extracted-name {
  font-size: 1.25rem;
  font-weight: 600;
}

.canonical-date, .extracted-date {
  font-size: 1.1rem;
  font-weight: 500;
}

/* Dark orange for parallel/different */
.citation-parallel,
.name-different {
  color: #ff9800 !important;
  background: rgba(255, 152, 0, 0.12) !important;
  border-color: #ff9800 !important;
}

.verification-badge.citation-parallel {
  background: #ff9800 !important;
  color: #fff !important;
  border-radius: 6px;
  padding: 0.15em 0.7em;
  font-weight: 700;
  font-size: 1rem;
  margin-left: 0.5em;
}

/* Add style for row-label */
.row-label {
  font-weight: bold;
  margin-right: 0.5em;
  color: #888;
}

/* Add flex styles for name rows */
.flex-names-row {
  display: flex;
  align-items: flex-start;
}
.names-flex-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5em 1em;
  align-items: flex-start;
}
.canonical-name-block, .extracted-name-block {
  margin-bottom: 0.2em;
  white-space: normal;
}

/* Canonical-Only Display Styles */
.canonical-only-clusters {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.canonical-only-card {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.canonical-only-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  transform: translateY(-1px);
}

.canonical-line, .extracted-line, .citations-line {
  display: flex;
  align-items: flex-start;
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.canonical-line {
  color: #28a745;
  font-weight: 600;
}

.extracted-line {
  color: #007bff;
  font-weight: 600;
}

.citations-line {
  color: #2c3e50;
  font-weight: 500;
}

.canonical-label, .extracted-label, .citations-label {
  font-weight: bold;
  margin-right: 0.5rem;
  color: #6c757d;
  min-width: 80px;
  flex-shrink: 0;
}

.citations-list-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  align-items: center;
}

.citation-link-verified {
  color: #007bff;
  text-decoration: none;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.citation-link-verified:hover {
  color: #0056b3;
  text-decoration: underline;
}

.citation-text {
  font-weight: 600;
  font-family: 'Courier New', monospace;
  color: #2c3e50;
}

/* Mobile Responsive Design */
@media (max-width: 768px) {
  .citation-results {
    padding: 0 1rem;
  }
  
  /* Filter section - stack vertically on mobile */
  .filter-section {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }
  
  .filter-controls {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .filter-btn {
    flex: 1;
    min-width: 80px;
    padding: 0.75rem 0.5rem;
    font-size: 0.85rem;
  }
  
  /* Layout controls - stack vertically */
  .layout-controls {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .layout-btn {
    width: 100%;
    justify-content: center;
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
  }
  
  /* Search box - full width */
  .search-box {
    max-width: none;
  }
  
  .search-input {
    font-size: 16px; /* Prevent zoom on mobile */
    padding: 0.75rem 1rem;
  }
  
  /* Citation comparison cards */
  .citations-grid {
    gap: 0.75rem;
  }
  
  .citation-comparison-card {
    margin: 0 -0.5rem;
  }
  
  .citation-header {
    padding: 0.75rem;
  }
  
  .citation-main {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .citation-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .citation-row-citations {
    font-size: 1rem;
    line-height: 1.4;
    word-break: break-word;
  }
  
  .citation-parallels {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .citation-parallel-item {
    width: 100%;
    justify-content: space-between;
    padding: 0.5rem;
  }
  
  /* Name/date rows */
  .name-date-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .canonical-name-block, .extracted-name-block {
    margin-right: 0;
    white-space: normal;
    width: 100%;
  }
  
  .canonical-name, .extracted-name {
    font-size: 1rem;
    word-break: break-word;
  }
  
  .canonical-date, .extracted-date {
    font-size: 0.9rem;
  }
  
  /* Canonical-only display */
  .canonical-line, .extracted-line, .citations-line {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
  
  .canonical-label, .extracted-label, .citations-label {
    min-width: auto;
    margin-right: 0;
    margin-bottom: 0.25rem;
  }
  
  .citations-list-inline {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  /* Horizontal layout adjustments */
  .horizontal-cluster-card {
    margin: 0 -0.5rem;
  }
  
  .horizontal-cluster-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .cluster-title-section {
    width: 100%;
  }
  
  .cluster-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  /* Verification badges */
  .verification-badge {
    font-size: 0.8rem;
    padding: 0.25rem 0.5rem;
    margin-left: 0.25rem;
  }
  
  /* Expand icon */
  .expand-icon {
    align-self: flex-end;
    margin-left: 0;
  }
}

@media (max-width: 480px) {
  .citation-results {
    padding: 0 0.5rem;
  }
  
  .prominent-citations-section {
    padding: 1rem;
    margin-bottom: 1.5rem;
  }
  
  .citations-summary h3 {
    font-size: 1.1rem;
  }
  
  .filter-btn {
    padding: 0.5rem 0.25rem;
    font-size: 0.8rem;
    min-width: 70px;
  }
  
  .layout-btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.85rem;
  }
  
  .search-input {
    padding: 0.5rem 0.75rem;
    font-size: 16px;
  }
  
  .citation-header {
    padding: 0.5rem;
  }
  
  .citation-details {
    padding: 0.75rem;
  }
  
  .canonical-only-card {
    padding: 0.75rem;
  }
  
  .citation-parallel-item {
    padding: 0.375rem;
    font-size: 0.9rem;
  }
  
  .verification-badge {
    font-size: 0.75rem;
    padding: 0.2rem 0.4rem;
  }
}

/* Touch-friendly improvements */
@media (hover: none) and (pointer: coarse) {
  .filter-btn,
  .layout-btn,
  .citation-header {
    min-height: 44px;
  }
  
  .citation-parallel-item {
    min-height: 44px;
  }
  
  /* Remove hover effects on touch devices */
  .citation-comparison-card:hover,
  .canonical-only-card:hover {
    transform: none;
  }
}
.attention-filter-btns {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.attention-filter-btn {
  padding: 0.4rem 1rem;
  border: 2px solid #e9ecef;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}
.attention-filter-btn.active {
  background: #198754;
  color: white;
  border-color: #198754;
}
</style>