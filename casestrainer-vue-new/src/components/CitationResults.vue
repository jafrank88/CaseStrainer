<script setup>
console.log('🚀 Citation Results Component Loaded!')

import { ref, computed, watch } from 'vue'
import ProcessingProgress from './ProcessingProgress.vue'

const props = defineProps({
  results: { type: Object, default: null },
  showLoading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  elapsedTime: { type: Number, default: 0 },
  remainingTime: { type: Number, default: 0 },
  totalProgress: { type: Number, default: 0 },
  currentStep: { type: String, default: '' },
  currentStepProgress: { type: Number, default: 0 },
  processingSteps: { type: Array, default: () => [] },
  citationInfo: { type: Object, default: null },
  rateLimitInfo: { type: Object, default: null },
  processingError: { type: String, default: '' },
  canRetry: { type: Boolean, default: false },
  timeout: { type: Number, default: null }
})

const emit = defineEmits(['copy-results', 'download-results', 'toast'])

const activeFilter = ref('all')
const searchQuery = ref('')
const currentPage = ref(1)
const itemsPerPage = 50
const expandedCitations = ref(new Set())
const expandedClusters = ref(new Set())
const progress = ref(0)
const etaSeconds = ref(null)
const useHorizontalLayout = ref(false) // Toggle for alternative layout
const displayMode = ref('canonical-only') // Default to canonical-only display

const attentionFilter = ref('all')
const showAll = ref(false)

// DEBUG: Watch for changes in results prop
watch(() => props.results, (newResults) => {
  console.log('🔍 CITATION RESULTS COMPONENT DEBUG:', {
    hasResults: !!newResults,
    resultsKeys: newResults ? Object.keys(newResults) : [],
    hasCitations: !!(newResults?.citations),
    hasClusters: !!(newResults?.clusters),
    citationsLength: newResults?.citations?.length || 0,
    clustersLength: newResults?.clusters?.length || 0,
    clustersData: newResults?.clusters,
    displayCondition: !!(newResults && newResults.clusters && newResults.clusters.length > 0),
    sampleCluster: newResults?.clusters?.[0]
  });
}, { immediate: true, deep: true })

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
    citationsLength: newVal && newVal.citations ? newVal.citations.length : 'N/A',
    totalCitations: newVal && newVal.total_citations ? newVal.total_citations : 'N/A',
    noCitationsFound: noCitationsFound.value
  })
}, { immediate: true, deep: true })

const shouldShowProgressBar = computed(() => {
  return props.showLoading
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
    // Group by extracted_case_name + extracted_date
    const grouped = {};
    imperfectCitations.forEach(c => {
      const key = `${c.extracted_case_name || 'N/A'}||${c.extracted_date || 'N/A'}`;
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push(c);
    });
    return Object.values(grouped).map(citations => ({ citations }));
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

// Utility: Acceptable web content sites for legal citations
const ACCEPTABLE_WEB_SITES = [
  'courtlistener.com',
  'justia.com',
  'leagle.com',
  'caselaw.findlaw.com',
  'scholar.google.com',
  'cetient.com',
  'casetext.com',
  'openjurist.org',
  'vlex.com',
  'supremecourt.gov',
  'uscourts.gov',
  'law.cornell.edu',
  'law.duke.edu',
  'westlaw.com',
  'lexis.com',
  'anylaw.com' // explicitly included as requested
];

function isAcceptableWebSource(domain) {
  if (!domain) return false;
  return ACCEPTABLE_WEB_SITES.some(site => domain.endsWith(site));
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
  return citation.canonical_name || citation.extracted_case_name || null
}

const getCanonicalCaseName = (citation) => {
  return citation.canonical_name || null
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
  
  // Enhanced normalization for legal abbreviations
  const normalizeWithAbbreviations = (name) => {
    return name.toLowerCase()
      // Handle common legal abbreviations
      .replace(/\bcnty\.?\b/g, 'county')
      .replace(/\bco\.?\b/g, 'company')
      .replace(/\bcorp\.?\b/g, 'corporation')
      .replace(/\binc\.?\b/g, 'incorporated')
      .replace(/\bllc\.?\b/g, 'limited liability company')
      .replace(/\bltd\.?\b/g, 'limited')
      .replace(/\bdept?\.?\b/g, 'department')
      .replace(/\bex\s+rel\.?\b/g, 'ex rel')
      .replace(/\bv\.?\s+/g, 'v ')
      .replace(/\bvs\.?\s+/g, 'v ')
      // Remove punctuation and normalize spaces
      .replace(/[^\w\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
  }
  
  const norm1 = normalize(canonical)
  const norm2 = normalize(extracted)
  
  // First try exact match after basic normalization
  if (norm1 === norm2) return true
  
  // Try enhanced normalization with abbreviation handling
  const enhanced1 = normalizeWithAbbreviations(canonical)
  const enhanced2 = normalizeWithAbbreviations(extracted)
  
  if (enhanced1 === enhanced2) return true
  
  // Check word overlap with more lenient threshold for legal names
  const words1 = enhanced1.split(' ').filter(w => w.length > 1)
  const words2 = enhanced2.split(' ').filter(w => w.length > 1)
  const commonWords = words1.filter(word => words2.includes(word) && word.length > 1)
  
  // More lenient threshold: 50% for legal names (was 60%)
  const threshold = 0.5
  const matchRatio = commonWords.length / Math.min(words1.length, words2.length)
  
  // DEBUG: Log similarity analysis for troubleshooting
  if (import.meta.env.DEV) {
    console.log('🔍 CASE NAME SIMILARITY DEBUG:', {
      canonical,
      extracted,
      enhanced1,
      enhanced2,
      words1,
      words2,
      commonWords,
      matchRatio,
      threshold,
      result: matchRatio >= threshold
    });
  }
  
  return matchRatio >= threshold
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

// Add missing computed properties
const noCitationsFound = computed(() => {
  if (!props.results) return true
  
  // Check if we have any citations in clusters
  if (props.results.clusters && props.results.clusters.length > 0) {
    const totalCitations = props.results.clusters.reduce((total, cluster) => {
      return total + (cluster.citations ? cluster.citations.length : 0)
    }, 0)
    if (totalCitations > 0) return false
  }
  
  // Check if we have any citations in the flat citations array
  if (props.results.citations && props.results.citations.length > 0) {
    return false
  }
  
  // Check if we have any citations in other possible fields
  if (props.results.total_citations && props.results.total_citations > 0) {
    return false
  }
  
  return true
})

const inputType = computed(() => {
  // This would need to be passed as a prop or determined from context
  return 'text'
})

const inputValue = computed(() => {
  // This would need to be passed as a prop or determined from context
  return ''
})

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

const toggleClusterDetails = (clusterId) => {
  if (expandedClusters.value.has(clusterId)) {
    expandedClusters.value.delete(clusterId)
  } else {
    expandedClusters.value.add(clusterId)
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
  <div v-if="showLoading" class="loading-state">
    <div class="loading-spinner"></div>
    <p>Processing citations...</p>
    <ProcessingProgress 
      v-if="shouldShowProgressBar"
      :elapsed-time="props.elapsedTime"
      :remaining-time="props.remainingTime"
      :total-progress="props.totalProgress"
      :current-step="props.currentStep"
      :current-step-progress="props.currentStepProgress"
      :processing-steps="props.processingSteps"
      :citation-info="props.citationInfo"
      :rate-limit-info="props.rateLimitInfo"
      :error="props.processingError"
      :can-retry="props.canRetry"
      :timeout="props.timeout"
    />
  </div>

  <div v-else-if="error" class="error-state">
    <div class="error-icon">⚠️</div>
    <h3>Error Processing Citations</h3>
    <p>{{ error }}</p>
  </div>

  <div v-else-if="noCitationsFound" class="no-citations-found text-center my-5">
    <img src="/no-results.svg" alt="No citations found" style="width:120px; margin:20px 0;">
    <p class="lead">No case citations found in your {{ inputType }}.</p>
    <a :href="`mailto:jafrank@uw.edu?subject=CaseStrainer%20feedback&body=I%20submitted%20the%20following%20${inputType}:%0A${encodeURIComponent(inputValue)}%0Aand%20no%20citations%20were%20found.`" class="btn btn-outline-primary mt-2">
      Report a possible extraction error
    </a>
  </div>
  <div v-else class="citation-results">

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
                  <span class="row-label">Canonical:</span>
                  <span style="color: #dc3545; font-weight: bold;">N/A (N/A)</span>
                </div>
                <!-- Third line: N/A, N/A for extracted in red -->
                <div class="citation-row flex-names-row">
                  <span class="row-label">Extracted:</span>
                  <span style="color: #dc3545; font-weight: bold;">N/A (N/A)</span>
                </div>
              </template>
              <template v-else>
                <!-- Line 1: Verified Name & Date -->
                <div class="citation-row flex-names-row">
                  <span class="row-label">Verifying Source:</span>
                  <span>
                    <template v-if="getCanonicalCaseName(cluster.citations[0]) && getCanonicalCaseName(cluster.citations[0]) !== 'N/A'">
                      {{ getCanonicalCaseName(cluster.citations[0]) }}
                      <span v-if="getCanonicalDate(cluster.citations[0])"> ({{ formatYear(getCanonicalDate(cluster.citations[0])) }})</span>
                      <span v-else> (N/A)</span>
                    </template>
                    <template v-else>
                      N/A (N/A)
                    </template>
                  </span>
                </div>
                <!-- Line 2: From Document Name & Date -->
                <div class="citation-row flex-names-row">
                  <span class="row-label">From Document:</span>
                  <span>
                    <template v-if="getExtractedCaseName(cluster.citations[0]) && getExtractedCaseName(cluster.citations[0]) !== 'N/A'">
                      {{ getExtractedCaseName(cluster.citations[0]) }}
                      <span v-if="getExtractedDate(cluster.citations[0])"> ({{ formatYear(getExtractedDate(cluster.citations[0])) }})</span>
                      <span v-else> (N/A)</span>
                    </template>
                    <template v-else>
                      N/A (N/A)
                    </template>
                  </span>
                </div>
                <!-- Line 3+: Each citation in the cluster, one per line, with status -->
                <div class="citations-list-vertical">
                  <div v-for="(citation, idx) in cluster.citations" :key="idx" class="citation-row-item">
                    <span class="citation-text">{{ getCitation(citation) }}</span>
                    <span class="verification-badge" :class="getVerificationStatus(citation)">
                      <template v-if="getVerificationStatus(citation) === 'verified'">VERIFIED</template>
                      <template v-else-if="getVerificationStatus(citation) === 'true_by_parallel'">verified by parallel citation</template>
                      <template v-else>UNVERIFIED</template>
                    </span>
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

    <!-- CLUSTERED DISPLAY: Always show results when clusters exist (even for perfect scores) -->
    <div v-if="results && results.clusters && results.clusters.length > 0" class="results-content">
      
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
          <button class="action-btn copy-btn" @click="copyAllCitations">
            Copy Results
          </button>
          <button class="action-btn download-btn" @click="downloadAllCitations">
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

      <!-- CLUSTER DISPLAY -->
      <div class="citations-list">
        <!-- SIMPLIFIED DISPLAY: Canonical name/date, Extracted name/date, Citations -->
        <div class="canonical-only-clusters">
          <div v-for="cluster in filteredClusters" :key="cluster.cluster_id" class="canonical-only-card">
            <!-- Main content with expandable details -->
            <div class="cluster-main-content">
              <!-- First line: Verified name and date -->
              <div class="canonical-line">
                <span class="canonical-label">Verifying Source:</span>
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
              
              <!-- Second line: From Document name and date -->
              <div class="extracted-line">
                <span class="extracted-label">From Document:</span>
                <span v-if="getExtractedCaseName(cluster.citations[0]) && getExtractedCaseName(cluster.citations[0]) !== 'N/A'" 
                      :class="['extracted-name', getCaseNameClass(cluster.citations[0])]">
                  {{ getExtractedCaseName(cluster.citations[0]) }}
                  <span v-if="getExtractedDate(cluster.citations[0])" :class="['extracted-date', getDateClass(cluster.citations[0])]">
                    ({{ formatYear(getExtractedDate(cluster.citations[0])) }})
                  </span>
                  <span v-else class="extracted-date missing">(no date)</span>
                </span>
                <span v-else class="extracted-name missing">No extracted name or year</span>
              </div>
              
              <!-- Third line and beyond: Each citation on its own row -->
              <div class="citations-section">
                <span class="citations-label"></span>
                <div class="citations-list-vertical">
                  <div v-for="(citation, idx) in cluster.citations" :key="idx" class="citation-row-item">
                    <a v-if="getVerificationStatus(citation) === 'verified' && getCitationUrl(citation)" 
                       :href="getCitationUrl(citation)" 
                       target="_blank" 
                       class="citation-link-verified">
                      {{ getCitation(citation) }}
                    </a>
                    <span v-else class="citation-text">{{ getCitation(citation) }}</span>
                    <span class="verification-badge" :class="getVerificationStatus(citation)">
                      {{ getVerificationStatus(citation).replace('_', ' ') }}
                    </span>
                  </div>
                </div>
              </div>
              
              <!-- Expand/Collapse button -->
              <div class="expand-section">
                <button 
                  @click="toggleClusterDetails(cluster.cluster_id)" 
                  class="expand-btn"
                  :class="{ expanded: expandedClusters.has(cluster.cluster_id) }"
                >
                  <span class="expand-text">{{ expandedClusters.has(cluster.cluster_id) ? 'Hide Details' : 'Show Details' }}</span>
                  <span class="expand-icon">▼</span>
                </button>
              </div>
            </div>
            
            <!-- Collapsible Details Section -->
            <div v-if="expandedClusters.has(cluster.cluster_id)" class="cluster-details">
              <div class="details-content">
                <!-- Cluster metadata -->
                <div class="detail-section">
                  <h4 class="detail-section-title">Cluster Information</h4>
                  <div class="detail-grid">
                    <div class="detail-item">
                      <span class="detail-label">Cluster ID:</span>
                      <span class="detail-value">{{ cluster.cluster_id }}</span>
                    </div>
                    <div class="detail-item">
                      <span class="detail-label">Size:</span>
                      <span class="detail-value">{{ cluster.size }} citation{{ cluster.size > 1 ? 's' : '' }}</span>
                    </div>
                    <div v-if="cluster.url" class="detail-item">
                      <span class="detail-label">CourtListener URL:</span>
                      <a :href="cluster.url" target="_blank" class="detail-link">View on CourtListener</a>
                    </div>
                  </div>
                </div>
                
                <!-- Individual citation details -->
                <div class="detail-section">
                  <h4 class="detail-section-title">Citation Details</h4>
                  <div v-for="(citation, idx) in cluster.citations" :key="idx" class="citation-detail-item">
                    <div class="citation-detail-header">
                      <h5 class="citation-detail-title">{{ getCitation(citation) }}</h5>
                      <span class="verification-badge" :class="getVerificationStatus(citation)">
                        {{ getVerificationStatus(citation).replace('_', ' ') }}
                      </span>
                    </div>
                    
                    <div class="citation-detail-content">
                      <div class="detail-grid">
                        <div class="detail-item">
                          <span class="detail-label">Source:</span>
                          <span class="detail-value">{{ getSource(citation) }}</span>
                        </div>
                        <div class="detail-item">
                          <span class="detail-label">Confidence:</span>
                          <span class="detail-value">{{ getConfidence(citation) }}</span>
                        </div>
                        <div class="detail-item">
                          <span class="detail-label">Mismatch Reason:</span>
                          <span class="detail-value">{{ getMismatchReason(citation) || 'None' }}</span>
                        </div>
                        <div v-if="getError(citation)" class="detail-item">
                          <span class="detail-label">Error:</span>
                          <span class="detail-value error-text">{{ getError(citation) }}</span>
                        </div>
                        <div v-if="getCitationUrl(citation)" class="detail-item">
                          <span class="detail-label">URL:</span>
                          <a :href="getCitationUrl(citation)" target="_blank" class="detail-link">View Citation</a>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
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
          <button class="action-btn copy-btn" @click="copyAllCitations">
            Copy Results
          </button>
          <button class="action-btn download-btn" @click="downloadAllCitations">
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
          <!-- New format: Verified first, then From Document, then citations -->
          <div class="citation-row citation-row-canonical flex-names-row">
            <span class="row-label">Verifying Source:</span>
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
              <span v-else class="extracted-name missing">No extracted name or year</span>
            </span>
          </div>
          <div class="citation-row citation-row-citations">
            <span class="citation-text">{{ getCitation(citation) }}</span>
            <span class="verification-badge" :class="getVerificationStatus(citation)">
              {{ getVerificationStatus(citation) }}
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

/* Verifying source display styles */
.source-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.source-name {
  font-weight: 600;
  color: #007bff;
}

.canonical-info {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #495057;
}

.canonical-info .canonical-name {
  font-weight: 500;
  font-size: 0.9rem;
}

.canonical-info .canonical-date {
  font-weight: 400;
  font-size: 0.9rem;
  color: #6c757d;
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

.citations-section {
  margin-top: 0.5rem;
}

.citations-list-vertical {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.citation-row-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #007bff;
}

.citation-row-item:hover {
  background: #e9ecef;
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

/* Expandable Details Styles */
.cluster-main-content {
  position: relative;
}

.expand-section {
  margin-top: 1rem;
  text-align: center;
}

.expand-btn {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #6c757d;
}

.expand-btn:hover {
  background: #e9ecef;
  border-color: #adb5bd;
}

.expand-btn.expanded {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.expand-btn.expanded:hover {
  background: #0056b3;
}

.expand-icon {
  font-size: 0.8rem;
  transition: transform 0.2s;
}

.expand-btn.expanded .expand-icon {
  transform: rotate(180deg);
}

.cluster-details {
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.details-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.detail-section {
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 1rem;
}

.detail-section:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.detail-section-title {
  font-size: 1rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 0.75rem 0;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  font-size: 0.9rem;
  color: #2c3e50;
  word-break: break-word;
}

.detail-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
}

.detail-link:hover {
  color: #0056b3;
  text-decoration: underline;
}

.error-text {
  color: #dc3545;
  font-style: italic;
}

.citation-detail-item {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.citation-detail-item:last-child {
  margin-bottom: 0;
}

.citation-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
  gap: 1rem;
}

.citation-detail-title {
  font-size: 1rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
  font-family: 'Courier New', monospace;
  flex: 1;
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
  
  /* Expandable details mobile styles */
  .expand-btn {
    width: 100%;
    justify-content: center;
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
  
  .citation-detail-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .citation-detail-title {
    font-size: 0.9rem;
    word-break: break-word;
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
  
  /* Expandable details small mobile styles */
  .expand-btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.85rem;
  }
  
  .cluster-details {
    padding: 0.75rem;
  }
  
  .detail-section {
    padding-bottom: 0.75rem;
  }
  
  .details-content {
    gap: 1rem;
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