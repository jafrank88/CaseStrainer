<template>
  <div class="citation-results">
    <div v-if="loading" class="text-center my-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Analyzing citations...</p>
    </div>
    
    <!-- Progress Bar for Async Tasks -->
    <div v-else-if="taskProgress && taskProgress.status === 'queued'" class="progress-container my-4">
      <div class="card">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h6 class="mb-0">Processing Document</h6>
            <span class="badge bg-primary">{{ taskProgress.progress || 0 }}%</span>
          </div>
          
          <!-- Progress Bar -->
          <div class="progress mb-3" style="height: 20px;">
            <div 
              class="progress-bar progress-bar-striped progress-bar-animated" 
              :style="{ width: (taskProgress.progress || 0) + '%' }"
              role="progressbar"
              :aria-valuenow="taskProgress.progress || 0"
              aria-valuemin="0"
              aria-valuemax="100"
            >
              {{ taskProgress.progress || 0 }}%
            </div>
          </div>
          
          <!-- Status Message -->
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <p class="mb-1 text-muted">
                <i class="bi bi-info-circle me-1"></i>
                {{ taskProgress.status_message || 'Processing...' }}
              </p>
              <p class="mb-0 small text-muted">
                <i class="bi bi-gear me-1"></i>
                {{ taskProgress.current_step || 'Unknown step' }}
              </p>
            </div>
            <div v-if="taskProgress.estimated_time_remaining" class="text-end">
              <p class="mb-0 small text-muted">
                <i class="bi bi-clock me-1"></i>
                Est. {{ formatTimeRemaining(taskProgress.estimated_time_remaining) }}
              </p>
            </div>
          </div>
          
          <!-- Task Info -->
          <div class="mt-3 pt-3 border-top">
            <div class="row text-center">
              <div class="col-4">
                <div class="small text-muted">Task ID</div>
                <div class="font-monospace small">{{ taskProgress.task_id?.substring(0, 8) }}...</div>
              </div>
              <div class="col-4">
                <div class="small text-muted">Type</div>
                <div class="small">{{ taskProgress.metadata?.source_type || 'Unknown' }}</div>
              </div>
              <div class="col-4">
                <div class="small text-muted">Started</div>
                <div class="small">{{ formatTimestamp(taskProgress.metadata?.timestamp) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else-if="error" class="alert alert-danger">
      <h5 class="alert-heading">Error</h5>
      <p class="mb-0">{{ error }}</p>
    </div>
    
    <!-- Main Results Card -->
    <div v-else-if="results && results.citations && results.citations.length > 0" class="results-card">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="mb-0">Citation Analysis Results</h4>
        <div v-if="false">
          <span class="badge bg-primary me-2">
            Total: {{ results.citations.length }}
          </span>
          <span class="badge bg-success me-2">
            Verified: {{ validCount }}
          </span>
          <span class="badge bg-warning text-dark me-2" v-if="validButNotVerifiedCount > 0">
            Valid but Not Verified: {{ validButNotVerifiedCount }}
          </span>
          <span class="badge bg-danger">
            Invalid: {{ invalidCount }}
          </span>
        </div>
      </div>
      
      <!-- New: Stats summary card -->
      <div v-if="results.stats" class="card mb-3">
        <div class="card-header bg-light">
          <strong>Citation Processing Breakdown</strong>
        </div>
        <div class="card-body p-2">
          <ul class="list-group list-group-flush">
            <li class="list-group-item d-flex justify-content-between align-items-center">
              <span>Total Extracted</span>
              <span class="badge bg-secondary">{{ results.stats.total_extracted }}</span>
            </li>
            <li class="list-group-item d-flex justify-content-between align-items-center">
              <span>Deduplicated</span>
              <span class="badge bg-secondary">{{ results.stats.deduplicated }}</span>
            </li>
            <li class="list-group-item d-flex justify-content-between align-items-center">
              <span>Verified in Cache</span>
              <span class="badge bg-info">{{ results.stats.verified_in_cache }}</span>
            </li>
            <li class="list-group-item d-flex justify-content-between align-items-center">
              <span>Verified in JSON Array</span>
              <span class="badge bg-success">{{ results.stats.verified_in_json_array }}</span>
            </li>
            <li class="list-group-item d-flex justify-content-between align-items-center">
              <span>Verified in Text Blob</span>
              <span class="badge bg-primary">{{ results.stats.verified_in_text_blob }}</span>
            </li>
            <li class="list-group-item d-flex justify-content-between align-items-center">
              <span>Verified in Single Lookup</span>
              <span class="badge bg-warning text-dark">{{ results.stats.verified_in_single }}</span>
            </li>
            <li class="list-group-item d-flex justify-content-between align-items-center">
              <span>Verified in LangSearch</span>
              <span class="badge bg-dark">{{ results.stats.verified_in_langsearch }}</span>
            </li>
            <li class="list-group-item d-flex justify-content-between align-items-center">
              <span>Not Verified</span>
              <span class="badge bg-danger">{{ results.stats.not_verified }}</span>
            </li>
          </ul>
        </div>
      </div>
      <!-- End stats summary card -->
      
      <!-- Tab Navigation -->
      <div class="tab-navigation mb-3">
        <!-- Mobile: Dropdown for tabs -->
        <div class="d-md-none">
          <select class="form-select" v-model="activeTab" @change="activeTab = $event.target.value">
            <option value="all">All Citations ({{ results.citations.length }})</option>
            <option value="verified">Verified ({{ validCount }})</option>
            <option value="validButNotVerified">Valid but Not Verified ({{ validButNotVerifiedCount }})</option>
            <option value="caseNameMismatches">Case Name Mismatches ({{ caseNameMismatchCount }})</option>
            <option value="invalid">Invalid ({{ invalidCount }})</option>
          </select>
        </div>
        
        <!-- Desktop: Tab navigation -->
        <ul class="nav nav-tabs d-none d-md-flex" id="citationTabs" role="tablist">
          <li class="nav-item" role="presentation">
            <button 
              class="nav-link" 
              :class="{ active: activeTab === 'all' }"
              @click="activeTab = 'all'"
              type="button" 
              role="tab"
            >
              All Citations ({{ results.citations.length }})
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button 
              class="nav-link" 
              :class="{ active: activeTab === 'verified' }"
              @click="activeTab = 'verified'"
              type="button" 
              role="tab"
            >
              Verified ({{ validCount }})
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button 
              class="nav-link" 
              :class="{ active: activeTab === 'validButNotVerified' }"
              @click="activeTab = 'validButNotVerified'"
              type="button" 
              role="tab"
            >
              Valid but Not Verified ({{ validButNotVerifiedCount }})
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button 
              class="nav-link" 
              :class="{ active: activeTab === 'caseNameMismatches' }"
              @click="activeTab = 'caseNameMismatches'"
              type="button" 
              role="tab"
            >
              Case Name Mismatches ({{ caseNameMismatchCount }})
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button 
              class="nav-link" 
              :class="{ active: activeTab === 'invalid' }"
              @click="activeTab = 'invalid'"
              type="button" 
              role="tab"
            >
              Invalid ({{ invalidCount }})
            </button>
          </li>
        </ul>
      </div>
      
      <!-- Tab Content -->
      <div class="tab-content">
        <!-- All Citations Tab -->
        <div class="tab-pane fade" :class="{ 'show active': activeTab === 'all' }">
          <!-- Mobile: Card layout -->
          <div class="d-md-none">
            <div v-for="(citation, index) in sortedCitations" :key="index" class="card mb-3">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-end mt-2">
                  <button 
                    class="btn btn-sm btn-outline-primary"
                    @click="toggleDetails(index)"
                  >
                    {{ expandedCitation === index ? 'Hide' : 'View' }} Details
                  </button>
                  <span :class="['badge', getStatusBadgeClass(citation)]">
                    {{ getStatusText(citation) }}
                  </span>
                </div>
                
                <div class="d-flex justify-content-between align-items-start mb-2">
                  <div class="flex-grow-1">
                    <div class="d-flex align-items-center mb-1">
                      <template v-if="getCitationUrl(citation)">
                        <a :href="getCitationUrl(citation)" target="_blank" rel="noopener" class="citation-text">
                          {{ getCitationText(citation) }}
                        </a>
                      </template>
                      <template v-else>
                        <span class="citation-text">{{ getCitationText(citation) }}</span>
                      </template>
                      <button 
                        v-if="citation.correction"
                        class="btn btn-sm btn-outline-secondary ms-2"
                        @click="applyCorrection(citation)"
                        title="Apply correction"
                      >
                        <i class="bi bi-arrow-clockwise"></i>
                      </button>
                    </div>
                    <div v-if="citation.correction" class="text-muted small">
                      <i class="bi bi-lightbulb"></i> Suggested: {{ citation.correction }}
                    </div>
                  </div>
                </div>
                
                <div class="row g-2 mb-2">
                  <div class="col-6">
                    <small class="text-muted d-block">Extracted Case Name:</small>
                    <div :class="['case-name', { 'case-name-mismatch': isCaseNameMismatch(citation) }]">
                      <template v-if="getExtractedCaseName(citation) && getExtractedCaseName(citation).trim() !== '' && getExtractedCaseName(citation) !== 'Not extracted' && getExtractedCaseName(citation).toLowerCase() !== 'westlaw citation'">
                        <template v-if="getCitationUrl(citation)">
                          <a :href="getCitationUrl(citation)" target="_blank" rel="noopener">{{ getExtractedCaseName(citation) }}</a>
                        </template>
                        <template v-else>
                          {{ getExtractedCaseName(citation) }}
                        </template>
                      </template>
                      <template v-else>
                        <span class="text-muted">Not extracted</span>
                      </template>
                    </div>
                  </div>
                  <div class="col-6">
                    <small class="text-muted d-block">Verified Case Name:</small>
                    <div :class="['case-name', { 'case-name-mismatch': isCaseNameMismatch(citation) }]">
                      <template v-if="getVerifiedCaseName(citation) && getVerifiedCaseName(citation) !== 'Not verified' && getCitationUrl(citation)">
                        <a :href="getCitationUrl(citation)" target="_blank" rel="noopener">{{ getVerifiedCaseName(citation) }}</a>
                      </template>
                      <template v-else>
                        {{ getVerifiedCaseName(citation) }}
                      </template>
                      <div v-if="isCaseNameMismatch(citation)" class="text-warning small">
                        <i class="bi bi-exclamation-triangle"></i> Low similarity
                      </div>
                    </div>
                  </div>
                </div>
                
                <div v-if="isCaseNameMismatch(citation)" class="alert alert-warning py-2 mb-2">
                  <i class="bi bi-exclamation-triangle"></i> Low similarity
                </div>
              </div>
            </div>
          </div>
          
          <!-- Desktop: Table layout -->
          <div class="table-responsive d-none d-md-block">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>Citation</th>
                  <th>Extracted Case Name</th>
                  <th>Verified Case Name</th>
                  <th>Details</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(citation, index) in sortedCitations" :key="index" class="align-middle">
                  <td>
                    <div class="d-flex align-items-center">
                      <template v-if="getCitationUrl(citation)">
                        <a :href="getCitationUrl(citation)" target="_blank" rel="noopener" class="citation-text">
                          {{ getCitationText(citation) }}
                        </a>
                      </template>
                      <template v-else>
                        <span class="citation-text">{{ getCitationText(citation) }}</span>
                      </template>
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
                    <div :class="['case-name', { 'case-name-mismatch': isCaseNameMismatch(citation) }]">
                      <template v-if="getExtractedCaseName(citation) && getExtractedCaseName(citation).trim() !== '' && getExtractedCaseName(citation) !== 'Not extracted' && getExtractedCaseName(citation).toLowerCase() !== 'westlaw citation'">
                        <template v-if="getCitationUrl(citation)">
                          <a :href="getCitationUrl(citation)" target="_blank" rel="noopener">{{ getExtractedCaseName(citation) }}</a>
                        </template>
                        <template v-else>
                          {{ getExtractedCaseName(citation) }}
                        </template>
                      </template>
                      <template v-else>
                        <span class="text-muted">Not extracted</span>
                      </template>
                    </div>
                  </td>
                  <td>
                    <div :class="['case-name', { 'case-name-mismatch': isCaseNameMismatch(citation) }]">
                      <template v-if="getVerifiedCaseName(citation) && getVerifiedCaseName(citation) !== 'Not verified' && getCitationUrl(citation)">
                        <a :href="getCitationUrl(citation)" target="_blank" rel="noopener">{{ getVerifiedCaseName(citation) }}</a>
                      </template>
                      <template v-else>
                        {{ getVerifiedCaseName(citation) }}
                      </template>
                      <div v-if="isCaseNameMismatch(citation)" class="text-warning small">
                        <i class="bi bi-exclamation-triangle"></i> Low similarity
                      </div>
                    </div>
                  </td>
                  <td>
                    <button 
                      class="btn btn-sm btn-outline-primary"
                      @click="toggleDetails(index)"
                    >
                      {{ expandedCitation === index ? 'Hide' : 'View' }} Details
                    </button>
                  </td>
                  <td>
                    <span :class="['badge', getStatusBadgeClass(citation)]">
                      {{ getStatusText(citation) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Verified Citations Tab -->
        <div class="tab-pane fade" :class="{ 'show active': activeTab === 'verified' }">
          <div class="table-responsive">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>Citation</th>
                  <th>Status</th>
                  <th>Extracted Case Name</th>
                  <th>Verified Case Name</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(citation, index) in verifiedCitations" :key="'verified-' + index" class="align-middle">
                  <td>
                    <div class="d-flex align-items-center">
                      <template v-if="getCitationUrl(citation)">
                        <a :href="getCitationUrl(citation)" target="_blank" rel="noopener" class="citation-text">
                          {{ getCitationText(citation) }}
                        </a>
                      </template>
                      <template v-else>
                        <span class="citation-text">{{ getCitationText(citation) }}</span>
                      </template>
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
                    <div :class="['case-name', { 'case-name-mismatch': isCaseNameMismatch(citation) }]">
                      <template v-if="getExtractedCaseName(citation) && getExtractedCaseName(citation).trim() !== '' && getExtractedCaseName(citation) !== 'Not extracted' && getExtractedCaseName(citation).toLowerCase() !== 'westlaw citation'">
                        <template v-if="getCitationUrl(citation)">
                          <a :href="getCitationUrl(citation)" target="_blank" rel="noopener">{{ getExtractedCaseName(citation) }}</a>
                        </template>
                        <template v-else>
                          {{ getExtractedCaseName(citation) }}
                        </template>
                      </template>
                      <template v-else>
                        <span class="text-muted">Not extracted</span>
                      </template>
                    </div>
                  </td>
                  <td>
                    <div :class="['case-name', { 'case-name-mismatch': isCaseNameMismatch(citation) }]">
                      <template v-if="getVerifiedCaseName(citation) && getVerifiedCaseName(citation) !== 'Not verified' && getCitationUrl(citation)">
                        <a :href="getCitationUrl(citation)" target="_blank" rel="noopener">{{ getVerifiedCaseName(citation) }}</a>
                      </template>
                      <template v-else>
                        {{ getVerifiedCaseName(citation) }}
                      </template>
                      <div v-if="isCaseNameMismatch(citation)" class="text-warning small">
                        <i class="bi bi-exclamation-triangle"></i> Low similarity
                      </div>
                    </div>
                  </td>
                  <td>
                    <button 
                      class="btn btn-sm btn-outline-primary"
                      @click="toggleDetails('verified-' + index)"
                    >
                      {{ expandedCitation === 'verified-' + index ? 'Hide' : 'View' }} Details
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Valid but Not Verified Citations Tab -->
        <div class="tab-pane fade" :class="{ 'show active': activeTab === 'validButNotVerified' }">
          <div class="table-responsive">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>Citation</th>
                  <th>Status</th>
                  <th>Extracted Case Name</th>
                  <th>Verified Case Name</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(citation, index) in validButNotVerifiedCitations" :key="'validButNotVerified-' + index" class="align-middle">
                  <td>
                    <div class="d-flex align-items-center">
                      <template v-if="getCitationUrl(citation)">
                        <a :href="getCitationUrl(citation)" target="_blank" rel="noopener" class="citation-text">
                          {{ getCitationText(citation) }}
                        </a>
                      </template>
                      <template v-else>
                        <span class="citation-text">{{ getCitationText(citation) }}</span>
                      </template>
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
                    <div :class="['case-name', { 'case-name-mismatch': isCaseNameMismatch(citation) }]">
                      <template v-if="getExtractedCaseName(citation) && getExtractedCaseName(citation).trim() !== '' && getExtractedCaseName(citation) !== 'Not extracted' && getExtractedCaseName(citation).toLowerCase() !== 'westlaw citation'">
                        <template v-if="getCitationUrl(citation)">
                          <a :href="getCitationUrl(citation)" target="_blank" rel="noopener">{{ getExtractedCaseName(citation) }}</a>
                        </template>
                        <template v-else>
                          {{ getExtractedCaseName(citation) }}
                        </template>
                      </template>
                      <template v-else>
                        <span class="text-muted">Not extracted</span>
                      </template>
                    </div>
                  </td>
                  <td>
                    <div :class="['case-name', { 'case-name-mismatch': isCaseNameMismatch(citation) }]">
                      <template v-if="getVerifiedCaseName(citation) && getVerifiedCaseName(citation) !== 'Not verified' && getCitationUrl(citation)">
                        <a :href="getCitationUrl(citation)" target="_blank" rel="noopener">{{ getVerifiedCaseName(citation) }}</a>
                      </template>
                      <template v-else>
                        {{ getVerifiedCaseName(citation) }}
                      </template>
                      <div v-if="isCaseNameMismatch(citation)" class="text-warning small">
                        <i class="bi bi-exclamation-triangle"></i> Low similarity
                      </div>
                    </div>
                  </td>
                  <td>
                    <button 
                      class="btn btn-sm btn-outline-primary"
                      @click="toggleDetails('validButNotVerified-' + index)"
                    >
                      {{ expandedCitation === 'validButNotVerified-' + index ? 'Hide' : 'View' }} Details
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Case Name Mismatches Tab -->
        <div class="tab-pane fade" :class="{ 'show active': activeTab === 'caseNameMismatches' }">
          <div class="table-responsive">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>Citation</th>
                  <th>Status</th>
                  <th>Extracted Case Name</th>
                  <th>Verified Case Name</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(citation, index) in caseNameMismatches" :key="'caseNameMismatch-' + index" class="align-middle">
                  <td>
                    <div class="d-flex align-items-center">
                      <template v-if="getCitationUrl(citation)">
                        <a :href="getCitationUrl(citation)" target="_blank" rel="noopener" class="citation-text">
                          {{ getCitationText(citation) }}
                        </a>
                      </template>
                      <template v-else>
                        <span class="citation-text">{{ getCitationText(citation) }}</span>
                      </template>
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
                    <div :class="['case-name', { 'case-name-mismatch': isCaseNameMismatch(citation) }]">
                      <template v-if="getExtractedCaseName(citation) && getExtractedCaseName(citation).trim() !== '' && getExtractedCaseName(citation) !== 'Not extracted' && getExtractedCaseName(citation).toLowerCase() !== 'westlaw citation'">
                        <template v-if="getCitationUrl(citation)">
                          <a :href="getCitationUrl(citation)" target="_blank" rel="noopener">{{ getExtractedCaseName(citation) }}</a>
                        </template>
                        <template v-else>
                          {{ getExtractedCaseName(citation) }}
                        </template>
                      </template>
                      <template v-else>
                        <span class="text-muted">Not extracted</span>
                      </template>
                    </div>
                  </td>
                  <td>
                    <div :class="['case-name', { 'case-name-mismatch': isCaseNameMismatch(citation) }]">
                      <template v-if="getVerifiedCaseName(citation) && getVerifiedCaseName(citation) !== 'Not verified' && getCitationUrl(citation)">
                        <a :href="getCitationUrl(citation)" target="_blank" rel="noopener">{{ getVerifiedCaseName(citation) }}</a>
                      </template>
                      <template v-else>
                        {{ getVerifiedCaseName(citation) }}
                      </template>
                      <div v-if="isCaseNameMismatch(citation)" class="text-warning small">
                        <i class="bi bi-exclamation-triangle"></i> Low similarity
                      </div>
                    </div>
                  </td>
                  <td>
                    <button 
                      class="btn btn-sm btn-outline-primary"
                      @click="toggleDetails('caseNameMismatch-' + index)"
                    >
                      {{ expandedCitation === 'caseNameMismatch-' + index ? 'Hide' : 'View' }} Details
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Invalid Citations Tab -->
        <div class="tab-pane fade" :class="{ 'show active': activeTab === 'invalid' }">
          <div class="table-responsive">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>Citation</th>
                  <th>Status</th>
                  <th>Extracted Case Name</th>
                  <th>Verified Case Name</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(citation, index) in invalidCitations" :key="'invalid-' + index" class="align-middle">
                  <td>
                    <div class="d-flex align-items-center">
                      <template v-if="getCitationUrl(citation)">
                        <a :href="getCitationUrl(citation)" target="_blank" rel="noopener" class="citation-text">
                          {{ getCitationText(citation) }}
                        </a>
                      </template>
                      <template v-else>
                        <span class="citation-text">{{ getCitationText(citation) }}</span>
                      </template>
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
                    <div :class="['case-name', { 'case-name-mismatch': isCaseNameMismatch(citation) }]">
                      <template v-if="getExtractedCaseName(citation) && getExtractedCaseName(citation).trim() !== '' && getExtractedCaseName(citation) !== 'Not extracted' && getExtractedCaseName(citation).toLowerCase() !== 'westlaw citation'">
                        <template v-if="getCitationUrl(citation)">
                          <a :href="getCitationUrl(citation)" target="_blank" rel="noopener">{{ getExtractedCaseName(citation) }}</a>
                        </template>
                        <template v-else>
                          {{ getExtractedCaseName(citation) }}
                        </template>
                      </template>
                      <template v-else>
                        <span class="text-muted">Not extracted</span>
                      </template>
                    </div>
                  </td>
                  <td>
                    <div :class="['case-name', { 'case-name-mismatch': isCaseNameMismatch(citation) }]">
                      <template v-if="getVerifiedCaseName(citation) && getVerifiedCaseName(citation) !== 'Not verified' && getCitationUrl(citation)">
                        <a :href="getCitationUrl(citation)" target="_blank" rel="noopener">{{ getVerifiedCaseName(citation) }}</a>
                      </template>
                      <template v-else>
                        {{ getVerifiedCaseName(citation) }}
                      </template>
                      <div v-if="isCaseNameMismatch(citation)" class="text-warning small">
                        <i class="bi bi-exclamation-triangle"></i> Low similarity
                      </div>
                    </div>
                  </td>
                  <td>
                    <button 
                      class="btn btn-sm btn-outline-primary"
                      @click="toggleDetails('invalid-' + index)"
                    >
                      {{ expandedCitation === 'invalid-' + index ? 'Hide' : 'View' }} Details
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      <!-- Expanded Details Panels -->
      <div 
        v-for="(citation, index) in currentTabCitations" 
        :key="'detail-' + (activeTab + '-' + index)"
        v-show="expandedCitation === (activeTab + '-' + index)"
        class="card mb-3"
      >
        <div class="card-header">
          <h5 class="mb-0">Citation Details: {{ getCitationText(citation) }}</h5>
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
                    <span v-if="citation.data?.confidence < 0.7" class="ms-2 badge bg-warning text-dark">
                      Low Confidence ({{ Math.round(citation.data?.confidence * 100) }}%)
                    </span>
                  </dd>
                  
                  <dt class="col-sm-4">Source</dt>
                  <dd class="col-sm-8">
                    <span class="text-capitalize">{{ citation.data?.source || 'N/A' }}</span>
                    <a v-if="getCitationUrl(citation)" :href="getCitationUrl(citation)" target="_blank" class="ms-2">
                      <i class="bi bi-box-arrow-up-right"></i>
                    </a>
                  </dd>
                  
                  <dt class="col-sm-4">Case Name(s)</dt>
                  <dd class="col-sm-8">
                    <span v-if="citation.data?.case_name_verified && citation.data?.case_name_extracted && citation.data?.case_name_verified !== citation.data?.case_name_extracted">
                      <strong>Verified:</strong> {{ citation.data?.case_name_verified }}<br>
                      <span class="text-muted"><strong>Extracted:</strong> {{ citation.data?.case_name_extracted }}</span>
                    </span>
                    <span v-else-if="citation.data?.case_name_verified">
                      {{ citation.data?.case_name_verified }}
                    </span>
                    <span v-else-if="citation.data?.case_name_extracted">
                      {{ citation.data?.case_name_extracted }}
                    </span>
                    <span v-else>{{ getCaseName(citation) }}</span>
                  </dd>
                  
                  <dt class="col-sm-4">Confidence</dt>
                  <dd class="col-sm-8">
                    <div class="progress" style="height: 20px;">
                      <div 
                        class="progress-bar" 
                        :class="{
                          'bg-success': citation.data?.confidence >= 0.7,
                          'bg-warning': citation.data?.confidence >= 0.4 && citation.data?.confidence < 0.7,
                          'bg-danger': citation.data?.confidence < 0.4
                        }"
                        role="progressbar" 
                        :style="{ width: (citation.data?.confidence * 100) + '%' }"
                        :aria-valuenow="citation.data?.confidence * 100"
                        aria-valuemin="0"
                        aria-valuemax="100"
                      >
                        {{ Math.round(citation.data?.confidence * 100) }}%
                      </div>
                    </div>
                  </dd>
                </dl>
              </div>
              
              <div class="col-md-6">
                <h6>Additional Details</h6>
                <dl class="row">
                  <dt class="col-sm-4">Validation Method</dt>
                  <dd class="col-sm-8">{{ citation.data?.method || 'N/A' }}</dd>
                </dl>
              </div>
            </div>
            <div v-if="citation.data?.error_message" class="alert alert-warning mt-3">
              <i class="bi bi-exclamation-triangle me-2"></i>
              {{ citation.data?.error_message }}
            </div>
          
          <div v-if="citation.data?.metadata" class="mt-3">
            <h6>Additional Metadata</h6>
            <pre class="bg-light p-2 rounded">{{ JSON.stringify(citation.data?.metadata, null, 2) }}</pre>
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
    },
    taskProgress: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['new-analysis', 'apply-correction'],
  setup(props, { emit }) {
    const expandedCitation = ref(null);
    const activeTab = ref('all');
    
    const validCount = computed(() => {
      return props.results?.citations?.filter(c => c.valid || c.verified || c.found || c.exists).length || 0;
    });
    
    const validButNotVerifiedCitations = computed(() => {
      if (!props.results?.citations) return [];
      return props.results.citations.filter(c => !(c.valid || c.verified || c.found || c.exists) && isValidCitationFormat(c));
    });
    
    const validButNotVerifiedCount = computed(() => {
      return validButNotVerifiedCitations.value.length;
    });
    
    const invalidCount = computed(() => {
      return props.results?.citations?.filter(c => !(c.valid || c.verified || c.found || c.exists) && !isValidCitationFormat(c)).length || 0;
    });
    
    const lowConfidenceCount = computed(() => {
      return props.results?.citations?.filter(c => (c.confidence ?? 0) >= 0.4 && (c.confidence ?? 0) < 0.7).length || 0;
    });
    
    const verifiedCitations = computed(() => {
      if (!props.results?.citations) return [];
      return props.results.citations.filter(c => c.valid || c.verified || c.found || c.exists);
    });
    
    const invalidCitations = computed(() => {
      if (!props.results?.citations) return [];
      return props.results.citations.filter(c => !(c.valid || c.verified || c.found || c.exists));
    });
    
    const caseNameMismatches = computed(() => {
      return sortedCitations.value.filter(citation => isCaseNameMismatch(citation));
    });
    
    const caseNameMismatchCount = computed(() => {
      return caseNameMismatches.value.length;
    });
    
    const currentTabCitations = computed(() => {
      switch (activeTab.value) {
        case 'verified':
          return verifiedCitations.value;
        case 'validButNotVerified':
          return validButNotVerifiedCitations.value;
        case 'caseNameMismatches':
          return caseNameMismatches.value;
        case 'invalid':
          return invalidCitations.value;
        default:
          return sortedCitations.value;
      }
    });
    
    const showResults = computed(() => {
      return props.results && props.results.citations && props.results.citations.length > 0;
    });
    
    const sortedCitations = computed(() => {
      if (!props.results?.citations) return [];
      return [...props.results.citations].sort((a, b) => {
        // Assign a sort rank: 0 = Red (Invalid), 1 = Yellow (Valid but Not Verified), 2 = Green (Verified)
        function getBadgeRank(citation) {
          if (citation.valid || citation.verified || citation.found || citation.exists) {
            return 2; // Green
          } else if (isValidCitationFormat(citation)) {
            return 1; // Yellow
          } else {
            return 0; // Red
          }
        }
        const aRank = getBadgeRank(a);
        const bRank = getBadgeRank(b);
        if (aRank !== bRank) {
          return aRank - bRank; // Lower rank (Red) first
        }
        // If same rank, sort by confidence descending
        const aConf = a.confidence ?? 0;
        const bConf = b.confidence ?? 0;
        return bConf - aConf;
      });
    });
    
    function getCitationText(citation) {
      return citation.citation || citation.text || citation.citation_text || 'Unknown Citation';
    }
    
    function getCluster(citation) {
      return citation.data?.details?.[0]?.clusters?.[0] || null;
    }
    
    function getCaseName(citation) {
      const cluster = getCluster(citation);
      return cluster?.case_name || 'N/A';
    }
    
    function getCourtInfo(citation) {
      const cluster = getCluster(citation);
      return cluster?.court || 'N/A';
    }
    
    function getDateFiled(citation) {
      const cluster = getCluster(citation);
      return cluster?.date_filed || 'N/A';
    }
    
    function getPrecedentialStatus(citation) {
      const cluster = getCluster(citation);
      return cluster?.precedential_status || 'N/A';
    }
    
    function getCitationUrl(citation) {
      // Prefer absolute_url from cluster, then resource_uri, then url
      const cluster = getCluster(citation);
      if (cluster?.absolute_url) {
        // If already a full URL, use as is; otherwise, prepend CourtListener domain
        return cluster.absolute_url.startsWith('http') ? cluster.absolute_url : `https://www.courtlistener.com${cluster.absolute_url}`;
      }
      if (cluster?.resource_uri) {
        return cluster.resource_uri.startsWith('http') ? cluster.resource_uri : `https://www.courtlistener.com${cluster.resource_uri}`;
      }
      if (citation.url) {
        return citation.url;
      }
      return null;
    }
    
    function getStatusBadgeClass(citation) {
      if (citation.valid || citation.verified || citation.found || citation.exists) {
        return 'bg-success';
      } else if (isValidCitationFormat(citation)) {
        return 'bg-warning text-dark';
      } else {
        return 'bg-danger';
      }
    }
    
    function getStatusText(citation) {
      if (citation.valid || citation.verified || citation.found || citation.exists) {
        return 'Verified';
      } else if (isValidCitationFormat(citation)) {
        return 'Valid but Not Verified';
      } else {
        return 'Invalid';
      }
    }
    
    function isValidCitationFormat(citation) {
      const citationText = getCitationText(citation);
      
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
    }
    
    const toggleDetails = (index) => {
      expandedCitation.value = expandedCitation.value === index ? null : index;
    };
    
    const startNewAnalysis = () => {
      emit('new-analysis');
    };
    
    const applyCorrection = (citation) => {
      emit('apply-correction', citation);
    };
    
    const downloadResults = (format) => {
      console.log(`Downloading results as ${format}`);
    };
    
    const copyToClipboard = () => {
      console.log('Copying results to clipboard');
    };
    
    // Helper methods for progress tracking
    const formatTimeRemaining = (seconds) => {
      if (!seconds || seconds <= 0) return 'Complete';
      if (seconds < 60) return `${seconds}s`;
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes}m ${remainingSeconds}s`;
    };
    
    const formatTimestamp = (timestamp) => {
      if (!timestamp) return 'Unknown';
      try {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
      } catch {
        return 'Invalid';
      }
    };
    
    function getExtractedCaseName(citation) {
      return citation.case_name_extracted && citation.case_name_extracted.trim() !== '' ? citation.case_name_extracted : 'Not extracted';
    }
    
    function getVerifiedCaseName(citation) {
      if (citation.data?.case_name) {
        return citation.data.case_name;
      } else if (citation.verified_case_name) {
        return citation.verified_case_name;
      } else if (citation.case_name) {
        return citation.case_name;
      }
      return 'Not verified';
    }
    
    function isCaseNameMismatch(citation) {
      const extracted = getExtractedCaseName(citation);
      const verified = getVerifiedCaseName(citation);
      
      // If either is missing, not a mismatch
      if (extracted === 'Not extracted' || verified === 'Not verified') {
        return false;
      }
      
      // Check if citation has similarity score
      if (citation.case_name_similarity !== undefined) {
        return citation.case_name_similarity < 0.3; // Low similarity threshold
      }
      
      // Fallback: check if names are very different
      const extractedWords = extracted.toLowerCase().split(/\s+/).filter(word => word.length > 2);
      const verifiedWords = verified.toLowerCase().split(/\s+/).filter(word => word.length > 2);
      
      const commonWords = extractedWords.filter(word => verifiedWords.includes(word));
      const similarity = commonWords.length / Math.max(extractedWords.length, verifiedWords.length);
      
      return similarity < 0.3;
    }
    
    return {
      expandedCitation,
      activeTab,
      validCount,
      validButNotVerifiedCitations,
      validButNotVerifiedCount,
      invalidCount,
      lowConfidenceCount,
      showResults,
      sortedCitations,
      verifiedCitations,
      invalidCitations,
      currentTabCitations,
      getCitationText,
      getCaseName,
      getExtractedCaseName,
      getVerifiedCaseName,
      isCaseNameMismatch,
      getCourtInfo,
      getDateFiled,
      getPrecedentialStatus,
      getCitationUrl,
      getStatusBadgeClass,
      getStatusText,
      toggleDetails,
      startNewAnalysis,
      applyCorrection,
      downloadResults,
      copyToClipboard,
      formatTimeRemaining,
      formatTimestamp,
      caseNameMismatches,
      caseNameMismatchCount
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
  word-break: break-all;
}

.case-name {
  font-weight: 500;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  word-break: break-word;
  font-size: 0.875rem;
}

.case-name-mismatch {
  background-color: #fff3cd;
  border-color: #ffc107;
  color: #856404;
}

.case-name-mismatch a {
  color: #856404;
  text-decoration: underline;
}

.case-name-mismatch a:hover {
  color: #533f03;
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

/* Mobile-specific improvements */
@media (max-width: 768px) {
  .citation-results {
    margin: 0 -1rem;
  }
  
  .results-container {
    padding: 0 1rem;
  }
  
  /* Tab navigation */
  .tab-navigation {
    margin-bottom: 1rem;
  }
  
  .form-select {
    font-size: 1rem;
    padding: 0.75rem 1rem;
    border-radius: 0.375rem;
  }
  
  /* Card layout for mobile */
  .card {
    border: 1px solid #dee2e6;
    border-radius: 0.5rem;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  }
  
  .card-body {
    padding: 1rem;
  }
  
  /* Citation text */
  .citation-text {
    font-size: 0.875rem;
    line-height: 1.4;
  }
  
  /* Case names */
  .case-name {
    font-size: 0.8rem;
    padding: 0.375rem 0.5rem;
    margin-bottom: 0.25rem;
  }
  
  /* Buttons */
  .btn {
    min-height: 44px;
    font-size: 0.875rem;
    padding: 0.5rem 1rem;
  }
  
  .btn-sm {
    min-height: 36px;
    font-size: 0.8rem;
    padding: 0.375rem 0.75rem;
  }
  
  /* Badges */
  .badge {
    font-size: 0.75rem;
    padding: 0.375rem 0.5rem;
  }
  
  /* Alerts */
  .alert {
    font-size: 0.8rem;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.75rem;
  }
  
  /* Stats summary */
  .card .list-group-item {
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
  }
  
  /* Progress bar */
  .progress {
    height: 1.5rem;
  }
  
  .progress-bar {
    font-size: 0.75rem;
    line-height: 1.5rem;
  }
  
  /* Hide table on mobile */
  .table-responsive {
    display: none;
  }
}

/* Tablet improvements */
@media (min-width: 769px) and (max-width: 1024px) {
  .citation-text {
    font-size: 0.9rem;
  }
  
  .case-name {
    font-size: 0.85rem;
  }
  
  .btn {
    min-height: 40px;
  }
}

/* Desktop improvements */
@media (min-width: 1025px) {
  .citation-text {
    font-size: 1rem;
  }
  
  .case-name {
    font-size: 0.9rem;
  }
}

/* Touch improvements */
@media (hover: none) and (pointer: coarse) {
  .btn {
    min-height: 48px;
  }
  
  .btn-sm {
    min-height: 40px;
  }
  
  .card {
    cursor: pointer;
  }
  
  .card:hover {
    transform: none;
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
  
  .case-name {
    background-color: #2c3034;
    border-color: #495057;
    color: #e9ecef;
  }
  
  .card {
    background-color: #2c3034;
    border-color: #495057;
  }
}

/* Accessibility improvements */
@media (prefers-reduced-motion: reduce) {
  .results-container {
    animation: none;
  }
  
  .card {
    transition: none;
  }
}

/* Print styles */
@media print {
  .btn, .badge {
    border: 1px solid #000;
    background: white !important;
    color: black !important;
  }
  
  .card {
    border: 1px solid #000;
    box-shadow: none;
  }
}

.results-card {
  background: #e6f7fb;
  border: 2px solid #b6e6fa;
  border-radius: 0.75rem;
  padding: 2rem 1rem 1.5rem 1rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.05);
}
</style>
