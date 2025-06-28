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
        <!-- Grouped and sorted citations -->
        <template v-for="(group, groupIndex) in groupedCitations" :key="group.status">
          <div class="group-header" :class="group.status">
            <span v-if="group.status === 'verified'" class="group-icon">✔️</span>
            <span v-else-if="group.status === 'unverified'" class="group-icon">❌</span>
            <span class="group-title">
              {{ group.status === 'verified' ? 'Verified Citations' : 'Unverified Citations' }}
              ({{ group.citations.length }})
            </span>
          </div>
          
          <!-- Citation Clusters -->
          <div v-for="cluster in citationClusters.filter(c => {
            const isVerified = c.primary?.verified || c.parallels.some(p => p.verified);
            return group.status === 'verified' ? isVerified : !isVerified;
          })" :key="cluster.primary?.citation || 'cluster'" class="citation-cluster">
            
            <!-- Primary Citation -->
            <div v-if="cluster.primary" :class="['citation-item', { verified: cluster.primary.verified, invalid: !cluster.primary.verified }]">
              <div class="citation-header">
                <div class="citation-main">
                  <!-- Primary Citation Badge -->
                  <div class="primary-badge" title="Primary citation in this cluster">
                    🎯 Primary
                  </div>
                  
                  <!-- Score Flag -->
                  <div :class="['score-flag', `score-${cluster.primary.scoreColor}`]"
                       :title="getScoreDescription(cluster.primary.score)"
                       @mouseenter="showScoreTooltip(cluster.primary)"
                       @mouseleave="hideScoreTooltip"
                       @click="toggleScoreTooltip(cluster.primary)"
                       style="cursor: pointer; position: relative;">
                    {{ cluster.primary.score }}/4
                    <div v-if="scoreTooltipGroup === cluster.primary" class="score-tooltip">
                      <div><strong>Score Breakdown:</strong></div>
                      <div>Case name match: <span :class="{ 'text-success': cluster.primary.case_name && cluster.primary.case_name !== 'N/A' }">{{ cluster.primary.case_name && cluster.primary.case_name !== 'N/A' ? '+2' : '0' }}</span></div>
                      <div>Hinted name similarity: <span :class="{ 'text-success': getCaseNameSimilarity(cluster.primary) >= 0.5 }">{{ getCaseNameSimilarity(cluster.primary) >= 0.5 ? '+1' : '0' }}</span></div>
                      <div>Year match: <span :class="{ 'text-success': getExtractedDate(cluster.primary) && getCanonicalDate(cluster.primary) && getExtractedDate(cluster.primary).substring(0,4) === getCanonicalDate(cluster.primary).substring(0,4) }">{{ getExtractedDate(cluster.primary) && getCanonicalDate(cluster.primary) && getExtractedDate(cluster.primary).substring(0,4) === getCanonicalDate(cluster.primary).substring(0,4) ? '+1' : '0' }}</span></div>
                    </div>
                  </div>
                  
                  <!-- Case Name with Hyperlink -->
                  <div class="case-name">
                    <a 
                      v-if="cluster.primary.verified && getCitationUrl(cluster.primary)"
                      :href="getCitationUrl(cluster.primary)"
                      target="_blank"
                      class="case-name-link"
                      title="View case details"
                    >
                      {{ getCaseName(cluster.primary) || 'Unknown Case' }}
                    </a>
                    <span v-else>
                      {{ getCaseName(cluster.primary) || 'Unknown Case' }}
                    </span>
                  </div>
                  
                  <!-- Citation with Hyperlink -->
                  <div class="citation-link">
                    <a 
                      v-if="cluster.primary.verified && getCitationUrl(cluster.primary)"
                      :href="getCitationUrl(cluster.primary)"
                      target="_blank"
                      class="citation-hyperlink"
                      title="View case details"
                    >
                      {{ getMainCitationText(cluster.primary) }}
                    </a>
                    <span v-else class="citation-text">
                      {{ getMainCitationText(cluster.primary) }}
                    </span>
                    <!-- Complex Citation Indicator -->
                    <span v-if="cluster.isComplex" class="complex-indicator" title="Complex citation with multiple components">
                      🔗
                    </span>
                  </div>
                </div>
                
                <!-- Expand/Collapse Button -->
                <div class="citation-actions">
                  <button
                    @click="toggleCitationDetails(cluster.primary)"
                    class="expand-btn"
                    :class="{ expanded: expandedCitations.has(cluster.primary.citation) }"
                    :title="expandedCitations.has(cluster.primary.citation) ? 'Hide details' : 'Show details'"
                  >
                    {{ expandedCitations.has(cluster.primary.citation) ? '▼' : '▶' }}
                  </button>
                </div>
              </div>
              
              <!-- Expandable Details Section for Primary -->
              <div v-if="expandedCitations.has(cluster.primary.citation)" class="citation-details">
                <!-- Include all the existing detail sections here -->
                <!-- Basic Citation Info -->
                <div class="detail-section">
                  <h4 class="section-title">Citation Information</h4>
                  <div class="detail-row"><span class="detail-label">Citation Text:</span> <span class="detail-value">{{ getMainCitationText(cluster.primary) }}</span></div>
                  <div class="detail-row" v-if="cluster.primary.id"><span class="detail-label">Database ID:</span> <span class="detail-value">{{ cluster.primary.id }}</span></div>
                  <div class="detail-row"><span class="detail-label">Status:</span> <span :class="['detail-value', cluster.primary.verified ? 'verified' : 'invalid']">{{ cluster.primary.verified ? 'Verified' : 'Not Verified' }}</span></div>
                </div>

                <!-- Case Name Comparison -->
                <div class="detail-section">
                  <h4 class="section-title">Case Information</h4>
                  <div class="detail-row"><span class="detail-label">Canonical Case Name:</span> <span class="detail-value">{{ getCaseName(cluster.primary) || 'N/A' }}</span></div>
                  <div class="detail-row"><span class="detail-label">Extracted Case Name:</span> <span class="detail-value">{{ getExtractedCaseName(cluster.primary) || 'N/A' }}</span></div>
                  <div class="detail-row"><span class="detail-label">Hinted Case Name:</span> <span class="detail-value">{{ cluster.primary.hinted_case_name || 'N/A' }}</span></div>
                  <div v-if="getCaseNameSimilarity(cluster.primary) !== null" class="detail-row"><span class="detail-label">Name Similarity:</span> <span :class="['detail-value', getSimilarityClass(getCaseNameSimilarity(cluster.primary))]">{{ (getCaseNameSimilarity(cluster.primary) * 100).toFixed(1) }}%</span></div>
                  <div v-if="getCaseNameMismatch(cluster.primary)" class="detail-row"><span class="detail-label">Name Mismatch:</span> <span class="detail-value warning">⚠️ Case names differ significantly</span></div>
                </div>

                <!-- Citation Components -->
                <div class="detail-section">
                  <h4 class="section-title">Citation Components</h4>
                  <div class="detail-row" v-if="cluster.primary.volume"><span class="detail-label">Volume:</span> <span class="detail-value">{{ cluster.primary.volume }}</span></div>
                  <div class="detail-row" v-if="cluster.primary.reporter"><span class="detail-label">Reporter:</span> <span class="detail-value">{{ cluster.primary.reporter }}</span></div>
                  <div class="detail-row" v-if="cluster.primary.page"><span class="detail-label">Page:</span> <span class="detail-value">{{ cluster.primary.page }}</span></div>
                  <div class="detail-row" v-if="cluster.primary.year"><span class="detail-label">Year:</span> <span class="detail-value">{{ cluster.primary.year }}</span></div>
                  <div class="detail-row" v-if="cluster.primary.court"><span class="detail-label">Court:</span> <span class="detail-value">{{ cluster.primary.court }}</span></div>
                </div>

                <!-- Decision Date -->
                <div v-if="getDateFiled(cluster.primary) || getExtractedDate(cluster.primary) || getCanonicalDate(cluster.primary)" class="detail-section">
                  <h4 class="section-title">Decision Information</h4>
                  <div class="detail-row"><span class="detail-label">Extracted Date:</span> <span class="detail-value">{{ formatDate(getExtractedDate(cluster.primary)) || 'N/A' }}</span></div>
                  <div v-if="getCanonicalDate(cluster.primary)" class="detail-row"><span class="detail-label">Canonical Date (Case Name):</span> <span class="detail-value">{{ formatDate(getCanonicalDate(cluster.primary)) }}</span></div>
                  <div v-if="getDateFiled(cluster.primary)" class="detail-row"><span class="detail-label">Canonical Date (Verified):</span> <span class="detail-value">{{ formatDate(getDateFiled(cluster.primary)) }}</span></div>
                  <div v-if="getExtractedDate(cluster.primary) && getDateFiled(cluster.primary)" class="detail-row"><span class="detail-label">Date Match:</span> <span :class="['detail-value', getExtractedDate(cluster.primary) === getDateFiled(cluster.primary) ? 'high-similarity' : 'low-similarity']">{{ getExtractedDate(cluster.primary) === getDateFiled(cluster.primary) ? '✓ Match' : '✗ Different' }}</span></div>
                </div>

                <!-- Context -->
                <div v-if="cluster.primary.context" class="detail-section">
                  <h4 class="section-title">Context</h4>
                  <div class="context-box">{{ cluster.primary.context }}</div>
                </div>

                <!-- Parallel Citations -->
                <div v-if="cluster.parallels.length > 0" class="detail-section">
                  <h4 class="section-title">Parallel Citations in This Cluster</h4>
                  <div class="parallel-citations">
                    <div v-for="(parallel, index) in cluster.parallels" :key="index" class="parallel-citation-item">
                      <span class="parallel-badge" title="Parallel citation">🔗 Parallel</span>
                      <span class="parallel-citation-text">{{ parallel.citation }}</span>
                      <span v-if="parallel.verified === 'true_by_parallel'" class="inherited-badge" title="Verified by association with primary">✓ Inherited</span>
                    </div>
                  </div>
                </div>

                <!-- Source Information -->
                <div class="detail-section">
                  <h4 class="section-title">Verification Details</h4>
                  <div class="detail-row"><span class="detail-label">Source:</span> <span class="detail-value">{{ getSource(cluster.primary) || 'N/A' }}</span></div>
                  <div class="detail-row" v-if="cluster.primary.confidence !== undefined"><span class="detail-label">Confidence:</span> <span class="detail-value">{{ (cluster.primary.confidence * 100).toFixed(1) }}%</span></div>
                  <div v-if="getNote(cluster.primary)" class="detail-row"><span class="detail-label">Note:</span> <span class="detail-value note">{{ getNote(cluster.primary) }}</span></div>
                </div>

                <!-- Complex Citation Information -->
                <div v-if="cluster.isComplex && cluster.primary.complex_metadata" class="detail-section">
                  <h4 class="section-title">Complex Citation Details</h4>
                  <div class="complex-citation-info">
                    <div class="detail-row" v-if="cluster.primary.complex_metadata.primary_citation">
                      <span class="detail-label">Primary Citation:</span> 
                      <span class="detail-value">{{ cluster.primary.complex_metadata.primary_citation }}</span>
                    </div>
                    <div class="detail-row" v-if="cluster.primary.complex_metadata.parallel_citations && cluster.primary.complex_metadata.parallel_citations.length > 0">
                      <span class="detail-label">Parallel Citations:</span> 
                      <div class="detail-value">
                        <span v-for="(parallel, index) in cluster.primary.complex_metadata.parallel_citations" :key="index" class="parallel-citation-tag">
                          {{ parallel }}
                        </span>
                      </div>
                    </div>
                    <div class="detail-row" v-if="cluster.primary.complex_metadata.pinpoint_pages && cluster.primary.complex_metadata.pinpoint_pages.length > 0">
                      <span class="detail-label">Pinpoint Pages:</span> 
                      <span class="detail-value">{{ cluster.primary.complex_metadata.pinpoint_pages.join(', ') }}</span>
                    </div>
                    <div class="detail-row" v-if="cluster.primary.complex_metadata.docket_numbers && cluster.primary.complex_metadata.docket_numbers.length > 0">
                      <span class="detail-label">Docket Numbers:</span> 
                      <span class="detail-value">{{ cluster.primary.complex_metadata.docket_numbers.join(', ') }}</span>
                    </div>
                    <div class="detail-row" v-if="cluster.primary.complex_metadata.case_history && cluster.primary.complex_metadata.case_history.length > 0">
                      <span class="detail-label">Case History:</span> 
                      <span class="detail-value">{{ cluster.primary.complex_metadata.case_history.join(', ') }}</span>
                    </div>
                    <div class="detail-row" v-if="cluster.primary.complex_metadata.publication_status">
                      <span class="detail-label">Publication Status:</span> 
                      <span class="detail-value">{{ cluster.primary.complex_metadata.publication_status }}</span>
                    </div>
                    <div class="detail-row" v-if="cluster.primary.complex_metadata.year">
                      <span class="detail-label">Year:</span> 
                      <span class="detail-value">{{ cluster.primary.complex_metadata.year }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Parallel Citations (if any) -->
            <div v-if="cluster.parallels.length > 0" class="parallel-citations-section">
              <div v-for="parallel in cluster.parallels" :key="parallel.citation" :class="['citation-item', 'parallel-item', { verified: parallel.verified, invalid: !parallel.verified }]">
                <div class="citation-header">
                  <div class="citation-main">
                    <!-- Parallel Citation Badge -->
                    <div class="parallel-badge" title="Parallel citation">
                      🔗 Parallel
                    </div>
                    
                    <!-- Inherited Status Badge -->
                    <div v-if="parallel.verified === 'true_by_parallel'" class="inherited-badge" title="Verified by association with primary">
                      ✓ Inherited
                    </div>
                    
                    <!-- Case Name (inherited from primary) -->
                    <div class="case-name">
                      <span>{{ getCaseName(parallel) || 'Unknown Case' }}</span>
                    </div>
                    
                    <!-- Citation Text -->
                    <div class="citation-link">
                      <span class="citation-text">{{ getMainCitationText(parallel) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
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

    <!-- Citation Details Modal -->
    <div v-if="selectedCitation" class="modal-overlay" @click="closeCitationDetails">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Citation Details</h3>
          <button @click="closeCitationDetails" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <!-- Basic Citation Info -->
          <div class="detail-section">
            <h4>Citation Information</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">Citation Text:</span>
                <span class="detail-value">{{ getMainCitationText(selectedCitation) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Database ID:</span>
                <span class="detail-value">{{ selectedCitation.id || 'N/A' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Status:</span>
                <span :class="['detail-value', selectedCitation.verified ? 'verified' : 'invalid']">
                  {{ selectedCitation.verified ? 'Verified' : 'Not Verified' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Citation Components -->
          <div class="detail-section">
            <h4>Citation Components</h4>
            <div class="detail-grid">
              <div class="detail-item" v-if="selectedCitation.volume">
                <span class="detail-label">Volume:</span>
                <span class="detail-value">{{ selectedCitation.volume }}</span>
              </div>
              <div class="detail-item" v-if="selectedCitation.reporter">
                <span class="detail-label">Reporter:</span>
                <span class="detail-value">{{ selectedCitation.reporter }}</span>
              </div>
              <div class="detail-item" v-if="selectedCitation.page">
                <span class="detail-label">Page:</span>
                <span class="detail-value">{{ selectedCitation.page }}</span>
              </div>
              <div class="detail-item" v-if="selectedCitation.year">
                <span class="detail-label">Year:</span>
                <span class="detail-value">{{ selectedCitation.year }}</span>
              </div>
              <div class="detail-item" v-if="selectedCitation.court">
                <span class="detail-label">Court:</span>
                <span class="detail-value">{{ selectedCitation.court }}</span>
              </div>
            </div>
          </div>

          <!-- Verification Details -->
          <div class="detail-section">
            <h4>Verification Details</h4>
            <div class="detail-grid">
              <div class="detail-item" v-if="selectedCitation.verification_source">
                <span class="detail-label">Verification Source:</span>
                <span class="detail-value">{{ selectedCitation.verification_source }}</span>
              </div>
              <div class="detail-item" v-if="selectedCitation.verification_confidence !== undefined">
                <span class="detail-label">Verification Confidence:</span>
                <span class="detail-value">{{ (selectedCitation.verification_confidence * 100).toFixed(1) }}%</span>
              </div>
              <div class="detail-item" v-if="selectedCitation.verification_count !== undefined">
                <span class="detail-label">Times Verified:</span>
                <span class="detail-value">{{ selectedCitation.verification_count }}</span>
              </div>
              <div class="detail-item" v-if="selectedCitation.error_count !== undefined">
                <span class="detail-label">Verification Errors:</span>
                <span class="detail-value">{{ selectedCitation.error_count }}</span>
              </div>
            </div>
          </div>

          <!-- Timestamps -->
          <div class="detail-section">
            <h4>Database Timestamps</h4>
            <div class="detail-grid">
              <div class="detail-item" v-if="selectedCitation.created_at">
                <span class="detail-label">First Added:</span>
                <span class="detail-value">{{ formatTimestamp(selectedCitation.created_at) }}</span>
              </div>
              <div class="detail-item" v-if="selectedCitation.updated_at">
                <span class="detail-label">Last Updated:</span>
                <span class="detail-value">{{ formatTimestamp(selectedCitation.updated_at) }}</span>
              </div>
              <div class="detail-item" v-if="selectedCitation.last_verified_at">
                <span class="detail-label">Last Verified:</span>
                <span class="detail-value">{{ formatTimestamp(selectedCitation.last_verified_at) }}</span>
              </div>
            </div>
          </div>

          <!-- Raw Verification Result -->
          <div class="detail-section" v-if="selectedCitation.verification_result">
            <h4>Raw Verification Data</h4>
            <div class="raw-data">
              <pre>{{ formatJson(selectedCitation.verification_result) }}</pre>
            </div>
          </div>

          <!-- Parallel Citations -->
          <div class="detail-section" v-if="getOtherParallelCitations(selectedCitation) && getOtherParallelCitations(selectedCitation).length > 0">
            <h4>Additional Parallel Citations</h4>
            <div class="parallel-citations">
              <span 
                v-for="(parallel, index) in getOtherParallelCitations(selectedCitation)" 
                :key="index"
                class="parallel-citation"
              >
                {{ formatParallelCitation(parallel) }}
              </span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeCitationDetails" class="btn btn-secondary">Close</button>
        </div>
      </div>
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
const selectedCitation = ref(null);
const expandedCitations = ref(new Set());
const scoreTooltipGroup = ref(null);

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
  
  // Sort by score from worst to best (ascending order)
  filtered.sort((a, b) => {
    const scoreA = a.score || 0;
    const scoreB = b.score || 0;
    return scoreA - scoreB;
  });
  
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

const groupedCitations = computed(() => {
  // Group and sort citations by status
  const verified = paginatedCitations.value.filter(c => c.verified);
  const unverified = paginatedCitations.value.filter(c => !c.verified);
  return [
    { status: 'verified', citations: verified },
    { status: 'unverified', citations: unverified }
  ].filter(group => group.citations.length > 0);
});

// New computed property for citation clusters
const citationClusters = computed(() => {
  if (!props.results?.citations) return [];
  
  // Group citations by primary citation
  const clusters = new Map();
  
  paginatedCitations.value.forEach(citation => {
    const primaryCitation = citation.primary_citation || citation.citation;
    
    if (!clusters.has(primaryCitation)) {
      clusters.set(primaryCitation, {
        primary: null,
        parallels: [],
        isComplex: false
      });
    }
    
    const cluster = clusters.get(primaryCitation);
    
    // Determine if this is the primary or a parallel
    if (citation.citation === primaryCitation || !citation.is_parallel_citation) {
      cluster.primary = citation;
    } else {
      cluster.parallels.push(citation);
    }
    
    // Mark as complex if any citation in the cluster is complex
    if (citation.is_complex_citation) {
      cluster.isComplex = true;
    }
  });
  
  // Convert to array and sort by verification status
  return Array.from(clusters.values())
    .sort((a, b) => {
      // Sort verified clusters first
      const aVerified = a.primary?.verified || a.parallels.some(p => p.verified);
      const bVerified = b.primary?.verified || b.parallels.some(p => p.verified);
      if (aVerified !== bVerified) return bVerified ? 1 : -1;
      
      // Then sort by primary citation text
      const aText = a.primary?.citation || '';
      const bText = b.primary?.citation || '';
      return aText.localeCompare(bText);
    });
});

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
  const caseName = citation.case_name || citation.metadata?.case_name || citation.group_metadata?.case_name || null;
  console.log('getCaseName called for citation:', citation.citation, 'returning:', caseName);
  return caseName;
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
  return citation.court || citation.metadata?.court || citation.group_metadata?.court || null;
};

const getDocket = (citation) => {
  return citation.docket_number || citation.metadata?.docket || citation.group_metadata?.docket || null;
};

const getDateFiled = (citation) => {
  return citation.date_filed || citation.group_metadata?.date_filed || null;
};

const getExtractedDate = (citation) => {
  return citation.extracted_date || null;
};

const getCanonicalDate = (citation) => {
  return citation.canonical_date || citation.group_metadata?.canonical_date || null;
};

const getParallelCitations = (citation) => {
  return citation.parallel_citations && citation.parallel_citations.length > 0 ? citation.parallel_citations : (citation.all_citations || []);
};

const getCitationUrl = (citation) => {
  return citation.url || citation.metadata?.url || citation.group_metadata?.url || null;
};

const getSource = (citation) => {
  // Prefer the domain of the 'url' field if present (for web_search and others)
  const urlField = citation.url || '';
  if (urlField) {
    try {
      const domain = (new URL(urlField)).hostname.replace(/^www\./, '');
      return domain;
    } catch (e) {
      return urlField;
    }
  }
  // Next, try the canonical citation_url
  const citationUrl = citation.citation_url || '';
  if (citationUrl) {
    try {
      const domain = (new URL(citationUrl)).hostname.replace(/^www\./, '');
      return domain;
    } catch (e) {
      return citationUrl;
    }
  }
  // Fallback to previous logic
  return citation.source || citation.metadata?.source || 'Unknown';
};

const getNote = (citation) => {
  return citation.note || null;
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  // If the string matches YYYY or YYYY-MM-DD, return just the year
  const yearMatch = /^\d{4}/.exec(dateString);
  if (yearMatch) return yearMatch[0];
  try {
    const date = new Date(dateString);
    return date.getFullYear();
  } catch (err) {
    return dateString; // Return as-is if parsing fails
  }
};

const getSimilarityClass = (similarity) => {
  if (similarity >= 0.8) return 'high-similarity';
  if (similarity >= 0.6) return 'medium-similarity';
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

const formatParallelCitation = (parallel) => {
  if (!parallel) return '';
  
  // If it's a string, return as is
  if (typeof parallel === 'string') return parallel;
  
  // If it's an object, extract the citation text
  if (typeof parallel === 'object') {
    // Try to get the clean citation text from various possible properties
    if (parallel.citation) return parallel.citation;
    if (parallel.cite) return parallel.cite;
    if (parallel.text) return parallel.text;
    
    // If it has volume, reporter, page structure, format it
    if (parallel.volume || parallel.reporter || parallel.page) {
      const v = parallel.volume || '';
      const r = parallel.reporter || '';
      const p = parallel.page || '';
      const y = parallel.year || '';
      let citation = [v, r, p].filter(Boolean).join(' ');
      if (y && citation && !citation.includes(y)) citation += ` (${y})`;
      if (citation) return citation;
    }
    
    // Last resort: try to get a string representation
    return String(parallel);
  }
  
  return String(parallel);
};

// Helper function to get the main citation text for display
const getMainCitationText = (group) => {
  if (!group) return '';

  // Prefer 'citation' field
  let citation = group.citation;
  if (Array.isArray(citation)) {
    if (citation.length > 0) return citation[0];
  } else if (typeof citation === 'string') {
    return citation;
  }

  // Fallback to canonical_citation
  let canonical = group.canonical_citation;
  if (Array.isArray(canonical)) {
    if (canonical.length > 0) return canonical[0];
  } else if (typeof canonical === 'string') {
    return canonical;
  }

  // Fallback to any citation-like property
  if (group.cite) return group.cite;
  if (group.text) return group.text;

  return 'Citation not available';
};

// Helper function to get all parallel citations (excluding the main one)
const getOtherParallelCitations = (group) => {
  let citation = group.citation;
  if (Array.isArray(citation) && citation.length > 1) {
    return citation.slice(1);
  }
  // If canonical_citation is an array and citation is not, use canonical as parallel
  if (!Array.isArray(citation) && Array.isArray(group.canonical_citation) && group.canonical_citation.length > 1) {
    return group.canonical_citation.slice(1);
  }
  // If parallel_citations exists and is non-empty, use it
  if (Array.isArray(group.parallel_citations) && group.parallel_citations.length > 0) {
    return group.parallel_citations;
  }
  return [];
};

// Citation Details Modal Methods
const showCitationDetails = (citation) => {
  selectedCitation.value = citation;
};

const closeCitationDetails = () => {
  selectedCitation.value = null;
};

const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A';
  try {
    return new Date(timestamp).toLocaleString();
  } catch (e) {
    return timestamp;
  }
};

const formatJson = (jsonString) => {
  if (!jsonString) return 'N/A';
  try {
    const parsed = typeof jsonString === 'string' ? JSON.parse(jsonString) : jsonString;
    return JSON.stringify(parsed, null, 2);
  } catch (e) {
    return jsonString;
  }
};

const parseParallelCitations = (parallelCitations) => {
  if (!parallelCitations) return [];
  try {
    if (typeof parallelCitations === 'string') {
      return JSON.parse(parallelCitations);
    }
    return Array.isArray(parallelCitations) ? parallelCitations : [];
  } catch (e) {
    return [parallelCitations];
  }
};

const toggleCitationDetails = (citation) => {
  if (expandedCitations.value.has(citation.citation)) {
    expandedCitations.value.delete(citation.citation);
  } else {
    expandedCitations.value.add(citation.citation);
  }
};

const getScoreDescription = (score) => {
  const descriptions = {
    0: 'No verification data available',
    1: 'Limited verification - some data available',
    2: 'Good verification - case name found',
    3: 'Very good verification - case name and additional data',
    4: 'Excellent verification - all data matches'
  };
  return descriptions[score] || 'Unknown score';
};

const showScoreTooltip = (group) => {
  scoreTooltipGroup.value = group;
};

const hideScoreTooltip = () => {
  scoreTooltipGroup.value = null;
};

const toggleScoreTooltip = (group) => {
  scoreTooltipGroup.value = scoreTooltipGroup.value === group ? null : group;
};
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
  border: 1px solid #e9ecef;
  border-radius: 8px;
  margin-bottom: 1rem;
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
  border-bottom: 1px solid #e9ecef;
}

.citation-main {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.score-flag {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: bold;
  text-align: center;
  min-width: 40px;
  color: white;
}

.score-flag.score-green {
  background: #28a745;
}

.score-flag.score-yellow {
  background: #ffc107;
  color: #212529;
}

.score-flag.score-orange {
  background: #fd7e14;
}

.score-flag.score-red {
  background: #dc3545;
}

.case-name {
  font-weight: 600;
  color: #2c3e50;
  flex: 1;
  min-width: 0;
}

.citation-link {
  flex: 1;
  min-width: 0;
}

.citation-hyperlink {
  color: #007bff;
  text-decoration: none;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.citation-hyperlink:hover {
  text-decoration: underline;
  color: #0056b3;
}

.case-name-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 600;
}

.case-name-link:hover {
  text-decoration: underline;
  color: #0056b3;
}

.parallel-citation-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
  font-family: 'Courier New', monospace;
}

.parallel-citation-link:hover {
  text-decoration: underline;
  color: #0056b3;
}

.citation-text {
  font-weight: 600;
  color: #2c3e50;
  font-family: 'Courier New', monospace;
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
  display: inline-block;
  background: #f8f9fa;
  padding: 4px 8px;
  margin: 2px;
  border-radius: 4px;
  font-size: 0.9em;
  border: 1px solid #dee2e6;
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
  
  .citation-main {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .citation-details {
    grid-template-columns: 1fr;
  }
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 20px 0 20px;
  border-bottom: 1px solid #dee2e6;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.modal-close:hover {
  background-color: #f8f9fa;
  color: #333;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  padding: 0 20px 20px 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin-top: 10px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.detail-label {
  font-weight: 600;
  color: #666;
  font-size: 0.9em;
}

.detail-value {
  color: #333;
  word-break: break-word;
}

.detail-value.verified {
  color: #28a745;
  font-weight: 600;
}

.detail-value.invalid {
  color: #dc3545;
  font-weight: 600;
}

.raw-data {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 15px;
  margin-top: 10px;
  overflow-x: auto;
}

.raw-data pre {
  margin: 0;
  font-size: 0.85em;
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #5a6268;
}

.score-tooltip {
  position: absolute;
  top: 2.2rem;
  left: 0;
  background: #fff;
  border: 1px solid #1976d2;
  border-radius: 0.5rem;
  box-shadow: 0 2px 8px rgba(60,72,88,0.12);
  padding: 0.75rem 1rem;
  z-index: 10;
  min-width: 180px;
  font-size: 0.95rem;
  color: #222;
}

.text-success {
  color: #198754;
  font-weight: bold;
}

.context-box {
  background: #f7fafd;
  border-radius: 0.5rem;
  padding: 1rem;
  font-size: 1.05rem;
  color: #333;
  margin-bottom: 1rem;
  white-space: pre-line;
}

.group-header {
  font-size: 1.15rem;
  font-weight: 600;
  margin: 2rem 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.group-header.verified {
  color: #198754;
}
.group-header.unverified {
  color: #dc3545;
}
.group-icon {
  font-size: 1.3rem;
  margin-right: 0.5rem;
}
.group-title {
  font-size: 1.1rem;
}

/* Complex Citation Styles */
.complex-citation-info {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 15px;
  margin-top: 10px;
}

.parallel-citation-tag {
  display: inline-block;
  background: #e3f2fd;
  color: #1976d2;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.9em;
  margin: 2px 4px 2px 0;
  border: 1px solid #bbdefb;
}

.parallel-citation-tag:hover {
  background: #bbdefb;
  color: #1565c0;
}

.complex-citation-info .detail-row {
  margin-bottom: 8px;
}

.complex-citation-info .detail-row:last-child {
  margin-bottom: 0;
}

.complex-citation-info .detail-value {
  font-weight: 500;
}

/* Complex Citation Indicator */
.complex-indicator {
  font-size: 0.8rem;
  color: #6c757d;
  margin-left: 0.5rem;
}

/* Citation Clusters */
.citation-cluster {
  margin-bottom: 1.5rem;
  border: 2px solid #f8f9fa;
  border-radius: 12px;
  overflow: hidden;
}

.citation-cluster .citation-item {
  margin-bottom: 0;
  border-radius: 0;
  border-left: none;
  border-right: none;
  border-top: none;
}

.citation-cluster .citation-item:last-child {
  border-bottom: none;
}

/* Primary and Parallel Badges */
.primary-badge {
  display: inline-block;
  background: #007bff;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-right: 0.5rem;
}

.parallel-badge {
  display: inline-block;
  background: #6c757d;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-right: 0.5rem;
}

.inherited-badge {
  display: inline-block;
  background: #28a745;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-right: 0.5rem;
}

/* Parallel Citations Section */
.parallel-citations-section {
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.parallel-citations-section .citation-item {
  background: #f8f9fa;
  border: none;
  border-bottom: 1px solid #e9ecef;
  margin-bottom: 0;
  border-radius: 0;
}

.parallel-citations-section .citation-item:last-child {
  border-bottom: none;
}

.parallel-citations-section .citation-item:hover {
  background: #e9ecef;
  transform: none;
  box-shadow: none;
}

.parallel-item {
  padding: 0.75rem 1rem;
}

.parallel-item .citation-header {
  padding: 0;
}

.parallel-item .citation-main {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.parallel-item .case-name {
  font-weight: 500;
  color: #495057;
}

.parallel-item .citation-text {
  color: #6c757d;
  font-family: monospace;
}

/* Parallel Citation Items in Details */
.parallel-citation-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 0.25rem;
}

.parallel-citation-text {
  font-family: monospace;
  color: #495057;
}
</style>
