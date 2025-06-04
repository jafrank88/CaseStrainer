<template>
  <div class="citation-results">
    <!-- Correction Suggestions Modal -->
    <div class="modal fade" id="correctionSuggestionsModal" tabindex="-1" aria-labelledby="correctionSuggestionsModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="correctionSuggestionsModalLabel">Citation Correction Suggestions</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div v-if="selectedCitation">
              <h6>Original Citation:</h6>
              <p class="font-monospace">{{ selectedCitation.citation_text || selectedCitation.citation || 'N/A' }}</p>
              
              <div v-if="selectedCitation.suggestions && selectedCitation.suggestions.length > 0" class="mt-4">
                <h6>Suggested Corrections:</h6>
                <div class="list-group">
                  <div v-for="(suggestion, idx) in selectedCitation.suggestions" :key="'suggestion-'+idx" 
                       class="list-group-item list-group-item-action suggestion-item">
                    <div class="d-flex w-100 justify-content-between align-items-center">
                      <h6 class="mb-1">{{ suggestion.corrected_citation || 'No correction available' }}</h6>
                      <span class="badge bg-primary rounded-pill">
                        {{ (suggestion.similarity * 100).toFixed(1) }}% match
                      </span>
                    </div>
                    <p class="mb-1 small text-muted" v-if="suggestion.explanation">
                      <i class="fas fa-info-circle me-1"></i>{{ suggestion.explanation }}
                    </p>
                    <small class="text-muted" v-if="suggestion.correction_type">
                      Type: {{ suggestion.correction_type.replace('_', ' ') }}
                    </small>
                  </div>
                </div>
              </div>
              <div v-else class="alert alert-info">
                No correction suggestions available for this citation.
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Main Results -->
    <!-- Progress Bar for Loading -->
    <div v-if="loading" class="mb-3">
      <div class="progress">
        <div class="progress-bar progress-bar-striped progress-bar-animated bg-info" role="progressbar" style="width: 100%">
          Loading citation results...
        </div>
      </div>
    </div>
    
    <!-- Technical Error Alert -->
    <div v-if="hasTechnicalError" class="alert alert-warning">
      <i class="fas fa-exclamation-triangle me-2"></i>
      Some citations could not be verified due to technical issues (such as a timeout or service error). 
      Please try again later or contact support if the problem persists.
    </div>
    
    <!-- Error message if results are not in expected format -->
    <div v-if="!isValidResults" class="alert alert-warning">
      <i class="fas fa-exclamation-triangle me-2"></i>
      Unable to display citation results. The data format is invalid or missing.
    </div>
    
    <div v-else>
      <!-- Summary Section -->
      <div class="card mt-4">
        <div class="card-header">
          <h5>Analysis Results</h5>
        </div>
        <div class="card-body">
          <div class="alert alert-success mb-3">
            <h5>Analysis complete!</h5>
            <p>Found {{ totalCitations }} citations.</p>
          </div>
          <div class="mt-3">
            <h6>Citation Summary:</h6>
            <ul class="list-group">
              <li class="list-group-item d-flex justify-content-between align-items-center">
                Confirmed Citations
                <span class="badge bg-success rounded-pill">{{ verifiedCount }}</span>
              </li>
              <li class="list-group-item d-flex justify-content-between align-items-center" v-if="unverifiedCount > 0">
                Unconfirmed Citations
                <span class="badge bg-warning rounded-pill text-dark">{{ unverifiedCount }}</span>
              </li>
              <li class="list-group-item d-flex justify-content-between align-items-center" v-if="multitoolCount > 0">
                Verified with Multi-tool
                <span class="badge bg-info rounded-pill">{{ multitoolCount }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Summary Bar -->
      <div class="alert" :class="summaryAlertClass">
        <div class="d-flex flex-column">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h5 class="mb-0">
              <i class="fas" :class="summaryIcon"></i>
              Found {{ totalCitations }} Citations
              <span v-if="verifiedCount > 0" class="ms-2">
                <span class="badge bg-success">{{ verifiedCount }} Verified</span>
              </span>
              <span v-if="unverifiedCount > 0" class="ms-2">
                <span class="badge bg-warning text-dark">{{ unverifiedCount }} Unverified</span>
              </span>
              <span v-if="unlikelyCount > 0" class="ms-2">
                <span class="badge bg-danger">{{ unlikelyCount }} Unlikely</span>
              </span>
            </h5>
          </div>
        </div>
      </div>

      <!-- Tabs Navigation -->
      <ul class="nav nav-tabs mb-4" role="tablist">
        <li class="nav-item" role="presentation">
          <button 
            class="nav-link" 
            :class="{ active: activeTab === 'verified' }" 
            @click="activeTab = 'verified'"
            type="button"
          >
            <i class="fas fa-check-circle me-2"></i>
            Verified
            <span class="badge bg-success ms-2">{{ verifiedCount }}</span>
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button 
            class="nav-link" 
            :class="{ active: activeTab === 'unverified' }" 
            @click="activeTab = 'unverified'"
            type="button"
          >
            <i class="fas fa-question-circle me-2"></i>
            Unverified
            <span class="badge bg-warning text-dark ms-2">{{ unverifiedCount }}</span>
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button 
            class="nav-link" 
            :class="{ active: activeTab === 'unlikely' }" 
            @click="activeTab = 'unlikely'"
            type="button"
          >
            <i class="fas fa-exclamation-triangle me-2"></i>
            Unlikely
            <span v-if="unlikelyCount > 0" class="badge bg-danger ms-2">{{ unlikelyCount }}</span>
          </button>
        </li>
      </ul>

      <!-- Tab Content -->
      <div class="tab-content mt-3">
        <!-- Citations Found Tab -->
        <div class="tab-pane fade" :class="{ show: activeTab === 'citations', active: activeTab === 'citations' }">
          <div v-if="allCitations.length > 0" class="table-responsive">
            <table class="table table-striped table-hover">
              <thead>
                <tr>
                  <th>Citation</th>
                  <th>Status</th>
                  <th>Verified By</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(citation, index) in allCitations" :key="'citation-'+index">
                  <td>{{ formatCitation(citation) }}</td>
                  <td>
                    <span class="badge" :class="getStatusBadgeClass(citation)">
                      {{ getStatusText(citation) }}
                    </span>
                  </td>
                  <td>
                    <template v-if="citation.validation_method">
                      <span class="badge" :class="getBadgeClass(citation.validation_method)">
                        {{ citation.validation_method }}
                      </span>
                    </template>
                  </td>
                  <td>
                    <button class="btn btn-sm btn-outline-primary" @click="showCitationDetails(citation)">
                      <i class="fas fa-eye"></i> View
                    </button>
                    <button class="btn btn-sm btn-outline-secondary ms-1" @click="showCitationSuggestions(citation)">
                      <i class="fas fa-info-circle"></i> Details
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="alert alert-info">
            No citations found in this document.
          </div>
        </div>

        <!-- Unlikely Citations Tab -->
        <div class="tab-pane fade" :class="{ show: activeTab === 'unlikely', active: activeTab === 'unlikely' }">
          <div v-if="unlikelyCitations.length > 0" class="table-responsive">
            <table class="table table-striped table-hover">
              <thead>
                <tr>
                  <th>Citation</th>
                  <th>Reason</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(citation, index) in unlikelyCitations" :key="'unlikely-'+index">
                  <td>{{ formatCitation(citation) }}</td>
                  <td>{{ citation.reason || 'Not a valid citation' }}</td>
                  <td>
                    <button class="btn btn-sm btn-outline-primary" @click="showCitationDetails(citation)">
                      <i class="fas fa-eye"></i> View
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="alert alert-info">
            No unlikely citations found.
          </div>
        </div>

        <!-- Verified Citations Tab -->
        <div v-show="activeTab === 'verified'" class="tab-pane fade">
          <div v-if="verifiedCitations.length > 0" class="table-responsive">
            <table class="table table-striped table-hover">
              <thead>
                <tr>
                  <th>Citation</th>
                  <th>Status</th>
                  <th>Validation Method</th>
                  <th>Case Name</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(citation, index) in verifiedCitations" :key="'verified-'+index">
                  <td>
                    <button class="btn btn-sm btn-outline-secondary" @click="showCitationContext(citation)">
                      <i class="fas fa-eye"></i> View
                    </button>
                  </td>
                  <td>
                    <button class="btn btn-sm btn-outline-info" @click="showCitationDetails(citation)">
                      <i class="fas fa-info-circle"></i> Details
                    </button>
                  </td>
                  <td>
                    <span class="badge" :class="getBadgeClass(citation.validation_method)">
                      {{ citation.validation_method || 'Unknown' }}
                    </span>
                  </td>
                  <td>{{ citation.case_name || 'N/A' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="alert alert-info">
            No verified citations found.
          </div>
        </div>

        <!-- Unverified Citations Tab -->
        <div v-show="activeTab === 'unverified'" class="tab-pane fade">
          <div v-if="unverifiedCitations.length > 0" class="table-responsive">
            <table class="table table-striped table-hover">
              <thead>
                <tr>
                  <th>Citation</th>
                  <th>Status</th>
                  <th>Validation Method</th>
                  <th>Case Name</th>
                  <th>Error</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(citation, index) in unverifiedCitations" :key="'unverified-'+index">
                  <td v-html="formatCitation(citation.citation || citation.citation_text)"></td>
                  <td>
                    <span class="badge bg-warning text-dark">
                      <i class="fas fa-exclamation-triangle me-1"></i>
                      Unverified
                    </span>
                  </td>
                  <td>
                    <span class="badge" :class="getBadgeClass(citation.validation_method)">
                      {{ citation.validation_method || 'Unknown' }}
                    </span>
                  </td>
                  <td>{{ citation.case_name || 'N/A' }}</td>
                  <td>
                    <span v-if="citation.metadata?.explanation" class="text-danger small">
                      <i class="fas fa-info-circle me-1"></i>
                      {{ citation.metadata.explanation }}
                    </span>
                    <span v-else>-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="alert alert-info">
            No unverified citations found.
          </div>
        </div>

        <!-- Unlikely Citations Tab -->
        <div v-show="activeTab === 'unlikely'" class="tab-pane fade">
          <div v-if="unlikelyCitations.length > 0" class="table-responsive">
            <table class="table table-striped table-hover">
              <thead>
                <tr>
                  <th>Citation Text</th>
                  <th>Reason</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(citation, index) in unlikelyCitations" :key="'unlikely-'+index">
                  <td>{{ citation.citation || citation.citation_text || citation.text || 'N/A' }}</td>
                  <td>
                    <span class="badge bg-danger">
                      {{ citation.metadata?.invalid_reason || 'Invalid format' }}
                    </span>
                  </td>
                  <td>
                    <div v-if="citation.metadata" class="small text-muted">
                      <div v-for="(value, key) in citation.metadata" :key="key">
                        <strong>{{ key }}:</strong> {{ value }}
                      </div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="alert alert-info">
            No unlikely citations detected.
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Citation Details Modal -->
  <div class="modal fade" id="citationDetailsModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Citation Details</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body" v-if="selectedCitation">
          <div class="row">
            <div class="col-md-6">
              <h6>Citation Information</h6>
              <p><strong>Citation:</strong> {{ selectedCitation.citation_text }}</p>
              <p><strong>Case Name:</strong> {{ selectedCitation.case_name || 'N/A' }}</p>
              <p><strong>Source:</strong> {{ selectedCitation.source }}</p>
              <p><strong>Validation Method:</strong> {{ selectedCitation.validation_method }}</p>
            </div>
            <div class="col-md-6">
              <h6>Additional Details</h6>
              <p v-if="selectedCitation.volume"><strong>Volume:</strong> {{ selectedCitation.volume }}</p>
              <p v-if="selectedCitation.reporter"><strong>Reporter:</strong> {{ selectedCitation.reporter }}</p>
              <p v-if="selectedCitation.page"><strong>Page:</strong> {{ selectedCitation.page }}</p>
              <p v-if="selectedCitation.court"><strong>Court:</strong> {{ selectedCitation.court }}</p>
              <p v-if="selectedCitation.year"><strong>Year:</strong> {{ selectedCitation.year }}</p>
            </div>
          </div>
          <div v-if="selectedCitation.parallel_citations && selectedCitation.parallel_citations.length > 0" class="mt-3">
            <h6>Parallel Citations</h6>
            <ul class="list-group">
              <li v-for="citation in selectedCitation.parallel_citations" :key="citation" class="list-group-item">
                {{ citation }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Citation Suggestions Modal -->
  <div class="modal fade" id="citationSuggestionsModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Citation Suggestions</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body" v-if="selectedCitation">
          <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle me-2"></i>
            This citation could not be verified. Here are some suggestions:
          </div>
          <div v-if="selectedCitation.suggestions && selectedCitation.suggestions.length > 0">
            <div v-for="(suggestion, index) in selectedCitation.suggestions" :key="index" class="card mb-3">
              <div class="card-body">
                <h6 class="card-title">Suggestion {{ index + 1 }}</h6>
                <p class="card-text">{{ suggestion.explanation }}</p>
                <div v-if="suggestion.citation" class="mt-2">
                  <strong>Suggested Citation:</strong> {{ suggestion.citation }}
                </div>
              </div>
            </div>
          </div>
          <div v-else class="alert alert-info">
            No specific suggestions available for this citation.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as bootstrap from 'bootstrap';
import { formatCitation } from '@/utils/citationFormatter';
import { Modal } from 'bootstrap';

export default {
  methods: {
    /**
     * Validates the structure of citation data
     * @returns {boolean} True if data is valid, false otherwise
     */
    validateCitationData() {
      this.validationErrors = [];
      
      if (!this.results) {
        this.validationErrors.push('No results data provided');
        return false;
      }
      
      const citations = this.results.validation_results || this.results.citations || [];
      
      if (!citations.length) {
        this.validationErrors.push('No citations found in results');
        return false;
      }
      
      // Check required fields in the first citation
      const sampleCitation = citations[0];
      const requiredFields = ['citation', 'citation_text', 'case_name', 'status'];
      const missingFields = requiredFields.filter(field => !(field in sampleCitation));
      
      if (missingFields.length > 0) {
        this.validationErrors.push(
          `Missing required fields in citation data: ${missingFields.join(', ')}`
        );
        return false;
      }
      
      return true;
    },
    
    /**
     * Process citations and update the cache
     */
    updateProcessedCitations() {
      try {
        this.validationErrors = [];
        
        // Handle case where validation_results might be in a nested structure
        const citations = this.results?.validation_results || this.results?.citations || [];
        
        if (!citations.length) {
          console.warn('[CitationResults] No citations found in results:', this.results);
          this.processedCitationsCache = [];
          return [];
        }
        
        // Create a cache for deduplication
        const citationCache = new Map();
        
        // Process citations
        const processed = citations.map((citation) => {
          if (!citation) return null;
          
          // Create a safe citation object with all required properties
          const safeCitation = {
            // Required fields with defaults
            id: citation.id || `citation-${Math.random().toString(36).substr(2, 9)}`,
            citation: citation.citation || '',
            citation_text: citation.citation_text || citation.citation || '',
            case_name: citation.case_name || 'Unknown Case',
            status: citation.status || 'unknown',
            
            // Metadata with deep merge to preserve nested properties
            metadata: {
              // Default metadata values
              url: '',
              source: 'unknown',
              verified: false,
              timestamp: new Date().toISOString(),
              // Merge any existing metadata
              ...(citation.metadata || {}),
              // Ensure required metadata fields have values
              url: citation.metadata?.url || citation.url || '',
              source: citation.metadata?.source || citation.source || 'unknown',
              verified: citation.metadata?.verified || citation.verified || false,
              timestamp: citation.metadata?.timestamp || citation.timestamp || new Date().toISOString()
            },
            
            // Content and context with fallbacks
            context: citation.context || citation.metadata?.context || '',
            content: citation.content || citation.context || citation.metadata?.context || '',
            
            // Validation and verification info
            validation_method: citation.validation_method || citation.metadata?.validation_method || 'unknown',
            verified: citation.verified || false,
            
            // Spread the original citation to include any additional properties
            ...citation,
            
            // Ensure these are always arrays to prevent iteration errors
            contexts: Array.isArray(citation.contexts) ? citation.contexts : [],
            verification_steps: Array.isArray(citation.verification_steps) ? citation.verification_steps : [],
            sources: citation.sources || {},
            suggestions: Array.isArray(citation.suggestions) ? citation.suggestions : [],
            
            // Ensure all required citation fields have values
            volume: citation.volume || '',
            reporter: citation.reporter || '',
            page: citation.page || '',
            court: citation.court || '',
            year: citation.year || '',
            parallel_citations: Array.isArray(citation.parallel_citations) ? citation.parallel_citations : [],
            confidence: typeof citation.confidence === 'number' ? citation.confidence : 0,
            error: citation.error || null,
            details: citation.details || {}
          };
          
          // Ensure case_name is properly formatted
          if (safeCitation.case_name) {
            safeCitation.case_name = safeCitation.case_name
              .replace(/<[^>]+>/g, '') // Remove HTML tags
              .replace(/\s+/g, ' ')    // Replace multiple spaces with single space
              .trim();
              
            // If case_name is just a citation number, mark as unknown
            if (/^\d+\s+[A-Za-z0-9.]+\s+\d+$/.test(safeCitation.case_name)) {
              safeCitation.case_name = 'Unknown Case';
            }
          }
          
          // Use the citation text as the cache key to detect duplicates
          const cacheKey = safeCitation.citation_text.toLowerCase().trim();
          
          // If we've already processed this citation, return the cached version
          if (citationCache.has(cacheKey)) {
            return citationCache.get(cacheKey);
          }
          
          // Otherwise, cache this citation and return it
          citationCache.set(cacheKey, safeCitation);
          return safeCitation;
        }).filter(Boolean); // Remove any null/undefined citations
        
        // Update cache
        this.processedCitationsCache = processed;
        
        // Log first citation for debugging
        if (processed.length > 0) {
          console.log('[CitationResults] First processed citation:', JSON.parse(JSON.stringify(processed[0])));
        }
        
        return processed;
      } catch (error) {
        console.error('[CitationResults] Error processing citations:', error);
        this.validationErrors = this.validationErrors || [];
        this.validationErrors.push(`Error processing citations: ${error.message}`);
        this.processedCitationsCache = [];
        return [];
      }
    },

    showCitationDetails(citation) {
      if (!citation || typeof citation !== 'object') {
        console.warn('Invalid citation provided to showCitationDetails:', citation);
        return;
      }
      
      try {
        // Create a safe copy of the citation with all required fields
        this.selectedCitation = {
          // Required fields with defaults
          id: citation.id || `citation-${Math.random().toString(36).substr(2, 9)}`,
          citation: citation.citation || '',
          citation_text: citation.citation_text || citation.citation || '',
          case_name: citation.case_name || 'Unknown Case',
          status: citation.status || 'unverified',
          source: citation.source || 'unknown',
          validation_method: citation.validation_method || 'unknown',
          
          // Content and context with fallbacks
          context: citation.context || citation.metadata?.context || '',
          content: citation.content || citation.context || citation.metadata?.context || '',
          
          // Citation details
          verified: citation.verified || false,
          volume: citation.volume || '',
          reporter: citation.reporter || '',
          page: citation.page || '',
          court: citation.court || '',
          year: citation.year || '',
          
          // Ensure these are always arrays to prevent iteration errors
          contexts: Array.isArray(citation.contexts) ? citation.contexts : [],
          verification_steps: Array.isArray(citation.verification_steps) ? citation.verification_steps : [],
          parallel_citations: Array.isArray(citation.parallel_citations) ? citation.parallel_citations : [],
          suggestions: Array.isArray(citation.suggestions) ? citation.suggestions : [],
          
          // Sources and details
          sources: citation.sources || {},
          details: citation.details || {},
          
          // Confidence and error handling
          confidence: typeof citation.confidence === 'number' ? citation.confidence : 0,
          error: citation.error || null,
          
          // Metadata with deep merge to preserve nested properties
          metadata: {
            // Default metadata values
            url: '',
            source: 'unknown',
            verified: false,
            timestamp: new Date().toISOString(),
            // Merge any existing metadata
            ...(citation.metadata || {}),
            // Ensure required metadata fields have values
            url: citation.metadata?.url || citation.url || '',
            source: citation.metadata?.source || citation.source || 'unknown',
            verified: citation.metadata?.verified || citation.verified || false,
            timestamp: citation.metadata?.timestamp || citation.timestamp || new Date().toISOString()
          },
          
          // Spread the original citation to include any additional properties
          ...citation
        };
        
        // Set current context for display
        this.currentContext = this.selectedCitation.context;
        this.showSuggestions = false;
        
        // Show the modal
        this.$nextTick(() => {
          const modalElement = document.getElementById('citationDetailsModal');
          if (modalElement) {
            const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
            if (modal) {
              modal.show();
            } else {
              console.warn('Could not initialize modal');
            }
          } else {
            console.warn('Modal element not found');
          }
        });
        
      } catch (error) {
        console.error('Error in showCitationDetails:', error);
        // Fallback to a minimal safe citation if something goes wrong
        this.selectedCitation = {
          id: `error-${Date.now()}`,
          citation: 'Error loading citation',
          citation_text: 'Error loading citation details',
          case_name: 'Error',
          status: 'error',
          content: 'An error occurred while loading citation details.',
          verified: false,
          error: error.message || 'Unknown error'
        };
      }
    },
    showCitationSuggestions(citation) {
      if (!citation || typeof citation !== 'object') {
        console.warn('Invalid citation provided to showCitationSuggestions:', citation);
        return;
      }
      
      try {
        // Create a safe copy of the citation with all required fields
        this.selectedCitation = {
          // Required fields with defaults
          id: citation.id || `suggestion-${Math.random().toString(36).substr(2, 9)}`,
          citation: citation.citation || '',
          citation_text: citation.citation_text || citation.citation || '',
          case_name: citation.case_name || 'Unknown Case',
          status: citation.status || 'unverified',
          source: citation.source || 'unknown',
          validation_method: citation.validation_method || 'unknown',
          
          // Content and context with fallbacks
          context: citation.context || citation.metadata?.context || '',
          content: citation.content || citation.context || citation.metadata?.context || '',
          
          // Citation details
          verified: citation.verified || false,
          
          // Ensure these are always arrays to prevent iteration errors
          contexts: Array.isArray(citation.contexts) ? citation.contexts : [],
          verification_steps: Array.isArray(citation.verification_steps) ? citation.verification_steps : [],
          suggestions: Array.isArray(citation.suggestions) ? citation.suggestions : [],
          
          // Sources and details
          sources: citation.sources || {},
          details: citation.details || {},
          
          // Confidence and error handling
          confidence: typeof citation.confidence === 'number' ? citation.confidence : 0,
          error: citation.error || null,
          
          // Metadata with deep merge to preserve nested properties
          metadata: {
            // Default metadata values
            url: '',
            source: 'unknown',
            verified: false,
            timestamp: new Date().toISOString(),
            // Merge any existing metadata
            ...(citation.metadata || {}),
            // Ensure required metadata fields have values
            url: citation.metadata?.url || citation.url || '',
            source: citation.metadata?.source || citation.source || 'unknown',
            verified: citation.metadata?.verified || citation.verified || false,
            timestamp: citation.metadata?.timestamp || citation.timestamp || new Date().toISOString()
          },
          
          // Spread the original citation to include any additional properties
          ...citation
        };
        
        // Handle correction suggestions
        this.suggestedCorrections = [];
        
        // First, check if we have explicit correction suggestions
        if (this.correctionSuggestions && Array.isArray(this.correctionSuggestions) && this.correctionSuggestions.length > 0) {
          this.suggestedCorrections = this.correctionSuggestions.map(suggestion => ({
            corrected_citation: suggestion.corrected_citation || suggestion.citation || 'Unknown',
            similarity: typeof suggestion.similarity === 'number' ? suggestion.similarity : 0,
            explanation: suggestion.explanation || 'No explanation provided',
            correction_type: suggestion.correction_type || 'unknown',
            ...suggestion
          }));
        } 
        // Fall back to citation suggestions if no explicit corrections
        else if (citation.suggestions && Array.isArray(citation.suggestions) && citation.suggestions.length > 0) {
          this.suggestedCorrections = citation.suggestions.map(suggestion => ({
            corrected_citation: suggestion.corrected_citation || suggestion.citation || 'Unknown',
            similarity: typeof suggestion.similarity === 'number' ? suggestion.similarity : 0,
            explanation: suggestion.explanation || 'No explanation provided',
            correction_type: suggestion.correction_type || 'unknown',
            ...suggestion
          }));
        }
        
        // Initialize the modal
        this.$nextTick(() => {
          const modalElement = document.getElementById('correctionSuggestionsModal');
          if (modalElement) {
            const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
            if (modal) {
              modal.show();
            } else {
              console.warn('Could not initialize suggestions modal');
            }
          } else {
            console.warn('Suggestions modal element not found');
          }
        });
        
      } catch (error) {
        console.error('Error in showCitationSuggestions:', error);
        // Fallback to a minimal safe citation if something goes wrong
        this.selectedCitation = {
          id: `error-${Date.now()}`,
          citation: 'Error loading suggestions',
          citation_text: 'Error loading citation suggestions',
          case_name: 'Error',
          status: 'error',
          content: 'An error occurred while loading citation suggestions.',
          verified: false,
          error: error.message || 'Unknown error',
          suggestions: []
        };
        this.suggestedCorrections = [];
      }
    },
    copyToClipboard(text) {
      navigator.clipboard.writeText(text).then(() => {
        // Optional: Show a tooltip or toast notification
        console.log('Copied to clipboard');
      }).catch(err => {
        console.error('Could not copy text: ', err);
      });
    },
    
    /**
     * Get the appropriate badge class for a citation status
     * @param {Object} citation - The citation object
     * @returns {string} The CSS class for the status badge
     */
    getStatusBadgeClass(citation) {
      if (!citation) return 'bg-secondary';
      
      // Check verified status from root level or metadata
      const isVerified = citation.verified === true || 
                      (citation.metadata && citation.metadata.verified === true) ||
                      citation.status === 'verified';
      
      const isUnlikely = citation.status === 'unlikely' || (citation.metadata && citation.metadata.is_unlikely);
      const isError = citation.status === 'error' || (citation.metadata && citation.metadata.error);
      
      if (isVerified) {
        return 'bg-success';
      } else if (isUnlikely) {
        return 'bg-secondary';
      } else if (isError) {
        return 'bg-danger';
      } else {
        return 'bg-warning'; // Default to warning for unverified citations
      }
    },
    
    /**
     * Get the display text for a citation status
     * @param {Object} citation - The citation object
     * @returns {string} The status text to display
     */
    getStatusText(citation) {
      if (!citation) return 'Unverified';
      
      // Check verified status from root level or metadata
      const isVerified = citation.verified === true || 
                      (citation.metadata && citation.metadata.verified === true) ||
                      citation.status === 'verified';
      
      if (isVerified) {
        return 'Verified';
      } else if (citation.status === 'unlikely' || (citation.metadata && citation.metadata.is_unlikely)) {
        return 'Unlikely';
      } else if (citation.status === 'error' || (citation.metadata && citation.metadata.error)) {
        return 'Error';
      } else {
        return 'Unverified'; // Default to Unverified for anything not explicitly verified
      }
    },
    /**
     * Get the appropriate badge class for a validation method
     * @param {string} method - The validation method name
     * @returns {string} The CSS class for the method badge
     */
    getBadgeClass(method) {
      if (!method) return 'bg-secondary';
      
      const methodLower = method.toLowerCase();
      if (methodLower.includes('courtlistener')) {
        return 'bg-primary';
      } else if (methodLower.includes('local') || methodLower.includes('search')) {
        return 'bg-info text-dark';
      } else if (methodLower.includes('multitool')) {
        return 'bg-purple';
      }
      return 'bg-secondary';
    }
  },

  name: 'CitationResults',
  /**
   * The citation validation results to display
   * @type {Object}
   * @property {Array} validation_results - Array of citation validation results
   * @property {number} total_citations - Total number of citations
   * @property {number} verified_count - Number of verified citations
   * @property {number} unverified_count - Number of unverified citations
   */
  props: {
    results: {
      type: Object,
      required: true,
      validator: (value) => {
        const hasValidationResults = Array.isArray(value?.validation_results) || Array.isArray(value?.citations);
        if (!hasValidationResults) {
          console.error('[CitationResults] Invalid results prop: missing validation_results or citations array', value);
        }
        return hasValidationResults;
      },
      default: () => ({
        validation_results: [],
        citations: [],
        total_citations: 0,
        verified_count: 0,
        unverified_count: 0
      })
    },
    correctionSuggestions: {
      type: Array,
      default: () => []
    }
  },
  data() {
    // Log initial props for debugging
    console.log('[CitationResults] Initializing with results:', this.results);
    
    return {
      activeTab: 'citations',
      selectedCitation: null,
      detailsModal: null,
      suggestionsModal: null,
      loading: false,
      showDebug: false,
      debugInfo: '',
      currentSuggestions: [],
      showSuggestions: false,
      currentContext: '',
      validationErrors: [],
      processedCitationsCache: []
    };
  },
  computed: {
    hasTechnicalError() {
      if (!this.results || !this.results.validation_results) return false;
      return this.results.validation_results.some(r => 
        r.metadata && r.metadata.explanation && 
        r.metadata.explanation.toLowerCase().includes('technical error')
      );
    },
    
    allCitations() {
      if (!this.results?.validation_results) return [];
      return this.results.validation_results.filter(c => !this.isUnlikelyCitation(c));
    },
    
    unlikelyCitations() {
      if (!this.results?.validation_results) return [];
      return this.results.validation_results.filter(c => this.isUnlikelyCitation(c));
    },
    
    multitoolCount() {
      return this.allCitations.filter(c => 
        c.validation_method && 
        c.validation_method.toLowerCase().includes('multitool')
      ).length;
    },
    
    isUnlikelyCitation() {
      return (citation) => {
        return citation.status === 'unlikely' || 
               (citation.metadata && citation.metadata.is_unlikely);
      };
    },
    /**
     * Get processed citations from cache
     */
    processedCitations() {
      return this.processedCitationsCache;
    },
    
    /**
     * Get safe citations from processed cache
     */
    safeCitations() {
      return this.processedCitationsCache;
    },
    // Total number of citations
    totalCitations() {
      if (this.results?.total_citations !== undefined) {
        return this.results.total_citations;
      } else if (this.results?.citations_count !== undefined) {
        return this.results.citations_count;
      }
      return this.safeCitations.length;
    },
    // Number of verified citations
    verifiedCount() {
      if (this.results?.confirmed_count !== undefined) {
        return this.results.confirmed_count;
      }
      return this.safeCitations.filter(c => {
        const isVerified = c.status === 'verified' || c.verified === true || (c.metadata && c.metadata.verified === true);
        return isVerified;
      }).length;
    },
    // Number of citations confirmed by CourtListener
    confirmedByCL() {
      if (this.results?.confirmed_count !== undefined) {
        return this.results.confirmed_count;
      }
      return this.safeCitations.filter(c => 
        c.status === 'verified' && 
        c.validation_method === 'CourtListener'
      ).length;
    },
    // Number of citations confirmed by Local Search
    confirmedByLS() {
      if (this.results?.local_search_count !== undefined) {
        return this.results.local_search_count;
      }
      return this.safeCitations.filter(c => 
        c.status === 'verified' && 
        c.validation_method === 'LocalSearch'
      ).length;
    },
    // Number of unverified citations
    unverifiedCount() {
      if (this.results?.unverified_count !== undefined) {
        return this.results.unverified_count;
      } else if (this.results?.unconfirmed_count !== undefined) {
        return this.results.unconfirmed_count;
      }
      return this.safeCitations.filter(c => {
        const isVerified = c.status === 'verified' || c.verified === true || (c.metadata && c.metadata.verified === true);
        return !isVerified;
      }).length;
    },
    // Number of unlikely citations
    unlikelyCount() {
      if (this.results?.unlikely_count !== undefined) {
        return this.results.unlikely_count;
      }
      return this.safeCitations.filter(c => 
        c.status === 'unlikely' || (c.metadata && c.metadata.is_unlikely)
      ).length;
    },
    // Get all verified citations
    verifiedCitations() {
      return this.safeCitations.filter(c => {
        // A citation is considered verified if:
        // 1. The root verified property is explicitly true, OR
        // 2. The status is 'verified' AND metadata.verified is true
        const isVerified = 
          c.verified === true || 
          (c.status === 'verified' && c.metadata?.verified === true);
          
        console.log(`[CitationResults] Citation ${c.citation} - ` +
                   `verified: ${c.verified}, ` +
                   `status: ${c.status}, ` +
                   `metadata.verified: ${c.metadata?.verified}, ` +
                   `isVerified: ${isVerified}`);
        
        return isVerified;
      });
    },
    // Legacy properties for backward compatibility
    courtListenerCitations() {
      return this.safeCitations.filter(c => 
        c.status === 'verified' && c.validation_method === 'CourtListener'
      );
    },
    elsewhereCitations() {
      return this.safeCitations.filter(c => 
        c.status === 'verified' && c.validation_method !== 'CourtListener'
      );
    },
    notFoundCitations() {
      return this.safeCitations.filter(c => c.status === 'not_found');
    },
    courtListenerCount() {
      return this.confirmedByCL;
    },
    elsewhereCount() {
      return this.confirmedByLS;
    },
    notFoundCount() {
      return this.unverifiedCount;
    },
    // Get appropriate badge class based on status
    summaryAlertClass() {
      if (this.unverifiedCount > 0 || this.unlikelyCount > 0) {
        return 'alert-warning';
      }
      return 'alert-success';
    },
    // Get appropriate icon based on status
    summaryIcon() {
      if (this.unlikelyCount > 0) {
        return 'fa-exclamation-triangle text-warning';
      } else if (this.unverifiedCount > 0) {
        return 'fa-question-circle text-warning';
      }
      return 'fa-check-circle text-success';
    },
  },

  watch: {
    // Watch for changes in results and update processed citations
    results: {
      handler() {
        this.updateProcessedCitations();
      },
      deep: true,
      immediate: true
    }
  },
  
  mounted() {
    try {
      // Initialize modals when component is mounted
      const detailsModalEl = document.getElementById('citationDetailsModal');
      const suggestionsModalEl = document.getElementById('correctionSuggestionsModal');
      
      if (!detailsModalEl || !suggestionsModalEl) {
        throw new Error('Required modal elements not found in DOM');
      }
      
      this.detailsModal = new bootstrap.Modal(detailsModalEl);
      this.suggestionsModal = new bootstrap.Modal(suggestionsModalEl);
      
      // Log successful initialization
      console.log('[CitationResults] Component mounted with modals initialized');
      
      // Process initial citations
      this.updateProcessedCitations();
      
      // Set default tab based on available data
      if (this.unlikelyCount > 0) {
        this.activeTab = 'unlikely';
      } else if (this.unverifiedCount > 0) {
        this.activeTab = 'unverified';
      } else if (this.verifiedCount > 0) {
        this.activeTab = 'verified';
      } else {
        this.activeTab = 'citations';
      }
      
      // Log initial data validation
      this.validateCitationData();
    } catch (error) {
      console.error('[CitationResults] Error initializing component:', error);
      this.validationErrors = this.validationErrors || [];
      this.validationErrors.push(`Initialization error: ${error.message}`);
    }
  },
  
  beforeUnmount() {
    console.log('[CitationResults] Component unmounting');
    // Clean up modals when component is destroyed
    try {
      if (this.detailsModal) {
        this.detailsModal.dispose();
        console.log('[CitationResults] Details modal disposed');
      }
      if (this.suggestionsModal) {
        this.suggestionsModal.dispose();
        console.log('[CitationResults] Suggestions modal disposed');
      }
    } catch (error) {
      console.error('[CitationResults] Error during cleanup:', error);
    }
  }
}
</script>

<style scoped>
.citation-results {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.progress {
  height: 1.5rem;
  margin: 1rem 0;
}

.progress-bar {
  font-size: 0.9rem;
  line-height: 1.5rem;
}

.alert h5 {
  margin-bottom: 0.5rem;
}

.badge {
  font-weight: 500;
  padding: 0.35em 0.65em;
}

.table th {
  font-weight: 600;
  color: #495057;
  background-color: #f8f9fa;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.nav-tabs {
  border-bottom: 1px solid #dee2e6;
}

.nav-tabs .nav-link {
  border: 1px solid transparent;
  border-top-left-radius: 0.25rem;
  border-top-right-radius: 0.25rem;
  color: #495057;
  font-weight: 500;
}

.nav-tabs .nav-link.active {
  color: #0d6efd;
  background-color: #fff;
  border-color: #dee2e6 #dee2e6 #fff;
}

.modal-content {
  border: none;
  border-radius: 0.5rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.modal-header {
  border-bottom: 1px solid #dee2e6;
  padding: 1rem 1.5rem;
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  border-top: 1px solid #dee2e6;
  padding: 1rem 1.5rem;
}

.citation-details pre {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 0.25rem;
  max-height: 300px;
  overflow-y: auto;
}

.suggestion-item {
  padding: 0.75rem 1rem;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
  background-color: #f8f9fa;
}

.suggestion-item:hover {
  background-color: #e9ecef;
  cursor: pointer;
}

.suggestion-item.active {
  border-color: #0d6efd;
  background-color: #e7f1ff;
}

.citation-card {
  transition: all 0.3s ease;
  margin-bottom: 1rem;
  border: 1px solid rgba(0, 0, 0, 0.125);
  border-radius: 0.25rem;
  overflow: hidden;
}

.citation-header {
  cursor: pointer;
  padding: 0.75rem 1.25rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid rgba(0, 0, 0, 0.125);
}

.citation-body {
  padding: 1.25rem;
  background-color: #fff;
}

.nav-tabs .badge {
  font-size: 0.8em;
}

.table th {
  white-space: nowrap;
}

.modal-body {
  max-height: 70vh;
  overflow-y: auto;
}

.table th, .table td {
  vertical-align: middle;
}

.suggestion-item {
  cursor: pointer;
  transition: background-color 0.2s;
  border-left: 3px solid transparent;
}

.suggestion-item:hover {
  background-color: #f8f9fa;
  border-left-color: #0d6efd;
}

.suggestion-item h6 {
  color: #0d6efd;
  font-weight: 500;
}

.modal-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.modal-title {
  font-weight: 600;
  color: #212529;
}

.font-monospace {
  font-family: 'Courier New', Courier, monospace;
  background-color: #f8f9fa;
  padding: 0.5rem;
  border-radius: 0.25rem;
  border: 1px solid #dee2e6;
}

.badge {
  font-weight: 500;
}
</style>
