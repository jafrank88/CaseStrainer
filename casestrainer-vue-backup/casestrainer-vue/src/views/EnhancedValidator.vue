<template>
  <div class="enhanced-validator">
    <h2>Enhanced Citation Validator</h2>
    <p class="lead">
      This advanced tool validates legal citations using multiple sources and provides detailed citation information, context, and correction suggestions.
    </p>
    <div class="alert alert-info mt-3">
      <strong>Note:</strong> For uploading files, pasting text, or entering a URL, please use the <router-link to="/">Unified Citation Analyzer</router-link> on the Home page.
    </div>
    <!-- Nav tabs for different validation methods -->
    <ul class="nav nav-tabs" id="validationTabs" role="tablist">
      <li class="nav-item" role="presentation">
        <button class="nav-link" :class="{ active: activeTab === 'single' }" @click="activeTab = 'single'" type="button">
          Single Citation
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" :class="{ active: activeTab === 'document' }" @click="activeTab = 'document'" type="button">
          Upload Document
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" :class="{ active: activeTab === 'text' }" @click="activeTab = 'text'" type="button">
          Paste Text
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" :class="{ active: activeTab === 'url' }" @click="activeTab = 'url'" type="button">
          URL Check
        </button>
      </li>
    </ul>
    <!-- Tab content -->
    <div class="tab-content" id="validationTabsContent">
      <!-- URL Check Tab -->
      <div v-show="activeTab === 'url'">
        <div class="card">
          <div class="card-header bg-primary text-white">
            <h5 class="mb-0">Check Citations from URL</h5>
          </div>
          <div class="card-body">
            <!-- Error Alert for URL Analysis -->
            <div v-if="urlAnalysisResult && urlAnalysisResult.error" class="alert alert-danger mt-4">
              <strong>Error:</strong> {{ urlAnalysisResult.error }}
            </div>
            <div class="form-group">
              <label for="url-input">Paste a URL to a legal document:</label>
              <input
                type="text"
                id="url-input"
                class="form-control"
                v-model="urlInput"
                placeholder="https://example.com/legal-document"
                @keyup.enter="analyzeUrl"
              />
            </div>
            <button
              class="btn btn-primary mt-3"
              @click="analyzeUrl"
              :disabled="isAnalyzingUrl || !urlInput"
            >
              <span v-if="isAnalyzingUrl" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              Analyze URL
            </button>
            <!-- URL Analysis Results -->
            <div v-if="urlAnalysisResult && transformedUrlResults">
              <ReusableResults :results="transformedUrlResults" />
            </div>
            <div v-else-if="urlAnalysisResult && (!transformedUrlResults || !Array.isArray(transformedUrlResults.citations))">
              <div class="alert alert-danger mt-4">
                Unable to display citation results. The server returned invalid or incomplete data.
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Single Citation Tab -->
      <div v-show="activeTab === 'single'">
      
        <div class="card">
          <div class="card-header bg-primary text-white">
            <h5 class="mb-0">Validate Citation</h5>
          </div>
          <div class="card-body">
        <div class="form-group">
          <label for="citation-input">Enter Citation:</label>
          <div class="input-group">
            <input
              type="text"
              id="citation-input"
              class="form-control"
              v-model="citationText"
              placeholder="e.g., 410 U.S. 113"
              @keyup.enter="validateCitation"
            />
            <div class="input-group-append">
              <button
                class="btn btn-primary"
                @click="validateCitation"
                :disabled="isValidating"
              >
                <span v-if="isValidating" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                Validate
              </button>
            </div>
          </div>
        </div>

        <!-- Validation Methods -->
        <div class="validation-methods mt-3" v-if="!isValidating">
          <div class="form-check form-check-inline">
            <input class="form-check-input" type="checkbox" id="use-enhanced" v-model="useEnhanced" checked>
            <label class="form-check-label" for="use-enhanced">Enhanced Validation</label>
          </div>
          <div class="form-check form-check-inline">
            <input class="form-check-input" type="checkbox" id="use-ml" v-model="useML" checked>
            <label class="form-check-label" for="use-ml">ML Classifier</label>
          </div>
          <div class="form-check form-check-inline">
            <input class="form-check-input" type="checkbox" id="use-correction" v-model="useCorrection" checked>
            <label class="form-check-label" for="use-correction">Suggest Corrections</label>
          </div>
        </div>

            <!-- Validation Results -->
            <div class="validation-results mt-4" v-if="validationResult">
              <div v-if="!transformedValidationResult" class="alert alert-info">
                <i class="fas fa-spinner fa-spin me-2"></i> Processing results...
              </div>
              <CitationResults 
                v-else 
                :results="transformedValidationResult"
                :correction-suggestions="correctionResult?.suggestions || []"
                :key="'citation-results-' + (validationResult.citation || 'none')"
              />
            </div>
          </div>
        </div>
      </div>
      
      <!-- Document Upload Tab -->
      <div v-show="activeTab === 'document'">
        <!-- Document upload UI -->
      </div>
      
      <!-- Text Paste Tab -->
      <div v-show="activeTab === 'text'">
        <!-- Text paste UI -->
      </div>
    </div>
  </div>
</template>

<script>
import { getCurrentInstance } from 'vue';
import axios from 'axios';
import api from '@/api/api';  // Import the configured API instance
import { formatCitation, transformCitations } from '@/utils/citationFormatter.js';

// Components
import CitationResults from '@/components/CitationResults.vue';
import ReusableResults from '@/components/ReusableResults.vue';

// Get the current app instance for logging
const currentApp = getCurrentInstance()?.appContext?.app;

export default {
  name: 'EnhancedValidator',
  components: {
    CitationResults,
    ReusableResults
  },
  data() {
    return {
      activeTab: 'single',
      
      // Single Citation
      citationText: '',
      validationResult: null,
      mlResult: null,
      correctionResult: null,
      citationContext: '',
      fileLink: '',
      useEnhanced: true,
      useML: true,
      useCorrection: true,
      isValidating: false,
      
      // Document Upload
      documentAnalysisResult: null,
      
      // Text Paste
      textAnalysisResult: null,
      pastedText: '',
      isAnalyzingText: false,
      
      // URL Check
      urlInput: 'http://localhost:5000/casestrainer/enhanced-validator',
      urlAnalysisResult: null,
      isAnalyzingUrl: false,
      
      // General
      dropZoneActive: false,
      isCheckingCitations: false,
      apiBaseUrl: '/casestrainer/api',
      error: null,
      results: {
        validation_results: [],
        totalCitations: 0,
        confirmedCount: 0,
        unconfirmedCount: 0,
        citations_count: 0,
        confirmed_count: 0,
        unconfirmed_count: 0,
        metadata: {}
      },
      documentResults: null,
      textResults: null,
      urlResults: null,
      citationCache: new Map(), // Cache for verified citations
      citationCacheKey: 'citation_verification_cache',
    };
  },

  computed: {
    formattedContext() {
      if (!this.contextResult || !this.contextResult.context) {
        return '';
      }
      
      // Split the context into paragraphs
      const paragraphs = this.contextResult.context.split('\n\n');
      
      // Format each paragraph
      return paragraphs.map(p => {
        // Highlight the citation
        if (this.citationText && p.includes(this.citationText)) {
          return p.replace(new RegExp(this.citationText, 'g'), `<mark>${this.citationText}</mark>`);
        }
        return p;
      }).join('<br><br>');
    },
    basePath() {
      // Determine the base path for API calls
      // Try multiple paths to ensure compatibility
      const paths = [
        '/casestrainer/api'
      ];
      
      // Always use /casestrainer/api in production and as a default
      return '/casestrainer/api';
    },
    // Transform single citation validation result into the format expected by CitationResults
    transformedValidationResult() {
      // Return a properly structured empty result if no validation result
      if (!this.validationResult) {
        return this.getEmptyResultsObject();
      }
      
      try {
        console.log('[EnhancedValidator] Starting transformation of validation result');
        const validation = this.validationResult || {};
        
        // Transform single validation result to match CitationResults expected format
        const isCourtListener = (validation.source === 'courtlistener') || 
                             String(validation.verified_by || '').toLowerCase().includes('courtlistener');
        
        // Safely get citation text with fallbacks
        const citationText = validation.citation || this.citationText || 'Unknown';
        
        // Create the citation object with all required fields for CitationResults
        const citation = {
          id: `citation-${Date.now()}`,
          citation: citationText,
          citation_text: validation.citation_text || citationText,
          case_name: validation.case_name || citationText,
          verified: !!validation.verified,
          status: validation.verified ? 'verified' : 'unverified',
          validation_method: validation.validation_method || (isCourtListener ? 'CourtListener' : 'Local Validation'),
          confidence: parseFloat(validation.confidence) || 0.0,
          source: validation.source || 'unknown',
          verified_by: validation.verified_by || (isCourtListener ? 'CourtListener' : 'Local'),
          contexts: Array.isArray(validation.contexts) ? validation.contexts : [],
          context: (Array.isArray(validation.contexts) && validation.contexts[0]?.text) ? 
                  validation.contexts[0].text : '',
          content: validation.content || (Array.isArray(validation.contexts) && validation.contexts[0]?.text) || 
                 validation.citation_text || citationText,
          details: validation.details || {},
          metadata: {
            ...(validation.metadata || {}),
            url: validation.details?.url || validation.url || '',
            source: validation.source || 'unknown',
            verified: !!validation.verified,
            timestamp: validation.timestamp || new Date().toISOString()
          },
          url: validation.details?.url || validation.url || '',
          error: validation.error || null,
          verification_steps: Array.isArray(validation.verification_steps) ? validation.verification_steps : [],
          sources: validation.sources || {},
          suggestions: Array.isArray(validation.suggestions) ? validation.suggestions : []
        };
        
        // Count verified vs unverified
        const verifiedCount = citation.verified ? 1 : 0;
        const unverifiedCount = citation.verified ? 0 : 1;
        
        // Return results in the format expected by CitationResults
        const result = {
          validation_results: [{
            ...citation,
            // Ensure required fields for CitationResults
            status: citation.verified ? 'verified' : 'unverified',
            source: citation.source || 'unknown',
            verified: !!citation.verified,
            metadata: {
              ...(citation.metadata || {}),
              url: citation.url || '',
              source: citation.source || 'unknown',
              verified: !!citation.verified,
              timestamp: citation.timestamp || new Date().toISOString()
            }
          }],
          citations: [{
            ...citation,
            // Ensure required fields for CitationResults
            status: citation.verified ? 'verified' : 'unverified',
            source: citation.source || 'unknown',
            verified: !!citation.verified,
            content: citation.content || citation.context || (Array.isArray(citation.contexts) && citation.contexts[0]?.text) || citation.citation_text || citation.citation || '',
            metadata: {
              ...(citation.metadata || {}),
              url: citation.url || '',
              source: citation.source || 'unknown',
              verified: !!citation.verified,
              timestamp: citation.timestamp || new Date().toISOString()
            },
            suggestions: Array.isArray(citation.suggestions) ? citation.suggestions : []
          }],
          total_citations: 1,
          verified_count: verifiedCount,
          unverified_count: unverifiedCount,
          status: 'completed',
          execution_time: 0,
          // Add any additional metadata that might be expected
          metadata: {
            ...(citation.metadata || {}),
            timestamp: citation.timestamp || new Date().toISOString()
          }
        };
        
        console.log('[EnhancedValidator] Transformed validation result:', result);
        return result;
      } catch (error) {
        console.error('[EnhancedValidator] Error transforming validation result:', error);
        return this.getEmptyResultsObject();
      }
    },
    

    
    // Document analysis results transformation
    transformedDocumentResults() {
      if (!this.documentAnalysisResult) {
        return this.getEmptyResultsObject();
      }
      try {
        console.log('[EnhancedValidator] Transforming document analysis results');
        const analysis = this.documentAnalysisResult || {};
        const citations = transformCitations(analysis.citations, {
          source: 'Document Analysis',
          fileName: analysis.metadata?.fileName,
          fileType: analysis.metadata?.fileType
        });
        const verifiedCount = citations.filter(c => c.verified).length;
        const totalCitations = citations.length;
        const unverifiedCount = totalCitations - verifiedCount;
        return {
          ...this.getEmptyResultsObject(),
          validation_results: citations,
          citations: citations,
          metadata: {
            ...(analysis.metadata || {}),
            source: 'Document Analysis',
            verified: verifiedCount > 0,
            timestamp: new Date().toISOString()
          },
          status: analysis.status || 'completed',
          execution_time: analysis.execution_time || 0,
          verified_count: verifiedCount,
          unverified_count: unverifiedCount,
          total_citations: totalCitations,
          citations_count: totalCitations
        };
      } catch (error) {
        console.error('[EnhancedValidator] Error transforming document results:', error);
        return this.getEmptyResultsObject();
      }
    },

    // Transform text analysis results
    transformedTextResults() {
      if (!this.textAnalysisResult) {
        return this.getEmptyResultsObject();
      }
      const citations = transformCitations(this.textAnalysisResult.citations, {
        source: 'Text Analysis',
        fileName: this.textAnalysisResult.metadata?.fileName,
        fileType: this.textAnalysisResult.metadata?.fileType
      });
      const confirmedCount = citations.filter(c => c.verified).length;
      const totalCitations = citations.length;
      const unverifiedCount = totalCitations - confirmedCount;
      return {
        ...this.getEmptyResultsObject(),
        citations,
        validation_results: citations,
        confirmedCount,
        totalCitations,
        confirmed_count: confirmedCount,
        citations_count: totalCitations,
        unverified_count: unverifiedCount,
        verified_count: confirmedCount,
        total_citations: totalCitations,
        metadata: {
          ...(this.textAnalysisResult.metadata || {}),
          source: 'Text Analysis',
          verified: confirmedCount > 0,
          timestamp: new Date().toISOString()
        },
        error: this.textAnalysisResult.error || null
      };
    },
    // Transform URL analysis results
    transformedUrlResults() {
      if (!this.urlAnalysisResult || typeof this.urlAnalysisResult !== 'object') {
        return this.getEmptyResultsObject();
      }
      const citations = transformCitations(this.urlAnalysisResult.citations, {
        source: 'URL Analysis',
        url: this.urlAnalysisResult.url || '',
        fileName: this.urlAnalysisResult.metadata?.fileName,
        fileType: this.urlAnalysisResult.metadata?.fileType
      });
      const confirmedCount = citations.filter(c => c.verified).length;
      const totalCitations = citations.length;
      const unverifiedCount = totalCitations - confirmedCount;
      return {
        ...this.getEmptyResultsObject(),
        citations,
        validation_results: citations,
        confirmedCount,
        totalCitations,
        confirmed_count: confirmedCount,
        citations_count: totalCitations,
        unverifiedCount,
        unverified_count: unverifiedCount,
        verified_count: confirmedCount,
        total_citations: totalCitations,
        metadata: {
          ...(this.urlAnalysisResult.metadata || {}),
          source: 'URL Analysis',
          verified: confirmedCount > 0,
          timestamp: new Date().toISOString(),
          url: this.urlAnalysisResult.url || ''
        },
        error: this.urlAnalysisResult.error || null
      };
    },
  },
  methods: {
    // Load citation cache from localStorage
    loadCitationCache() {
      try {
        const cachedData = localStorage.getItem(this.citationCacheKey);
        if (cachedData) {
          const parsedCache = JSON.parse(cachedData);
          this.citationCache = new Map(Object.entries(parsedCache));
          console.log('[EnhancedValidator] Loaded citation cache:', this.citationCache.size, 'entries');
        }
      } catch (error) {
        console.warn('[EnhancedValidator] Error loading citation cache:', error);
        this.citationCache = new Map();
      }
    },

    // Save citation cache to localStorage
    saveCitationCache() {
      try {
        const cacheObject = Object.fromEntries(this.citationCache);
        localStorage.setItem(this.citationCacheKey, JSON.stringify(cacheObject));
        console.log('[EnhancedValidator] Saved citation cache:', this.citationCache.size, 'entries');
      } catch (error) {
        console.warn('[EnhancedValidator] Error saving citation cache:', error);
      }
    },

    // Check if a citation is in the cache
    getCachedCitation(citationText) {
      const normalizedCitation = this.normalizeCitation(citationText);
      return this.citationCache.get(normalizedCitation);
    },

    // Add a citation to the cache
    cacheCitation(citationText, verificationResult) {
      const normalizedCitation = this.normalizeCitation(citationText);
      if (verificationResult.verified && verificationResult.verified_by === 'CourtListener') {
        this.citationCache.set(normalizedCitation, verificationResult);
        this.saveCitationCache();
      }
    },

    // Normalize citation text for consistent caching
    normalizeCitation(citationText) {
      return citationText
        .toLowerCase()
        .replace(/\s+/g, ' ')
        .trim();
    },

    // Modify validateCitation to use cache
    async validateCitation(citation) {
      console.group('validateCitation - Start');
      console.log('Input citation:', citation || this.citationText);
      
      const citationToValidate = citation || this.citationText;
      
      if (!citationToValidate?.trim()) {
        const errorObj = {
          error: 'No citation provided',
          details: 'Please enter a citation to validate',
          status: 400
        };
        console.warn('Validation failed - no citation provided');
        this.validationResult = errorObj;
        console.groupEnd();
        return;
      }

      this.isValidating = true;
      this.validationResult = null;
      this.correctionResult = null;
      this.error = null;

      try {
        const requestData = { 
          citation: citationToValidate.trim(),
          use_enhanced: this.useEnhanced,
          use_ml: this.useML
        };
        
        console.log('Sending request to /casestrainer/api/verify-citation with data:', requestData);

        const startTime = performance.now();
        const response = await api.post('/casestrainer/api/verify-citation', requestData);
        const endTime = performance.now();
        
        console.log('Raw API Response:', {
          status: response.status,
          statusText: response.statusText,
          headers: response.headers,
          data: response.data
        });

        if (!response.data) {
          throw new Error('Empty response from server');
        }

        // Process the validation result
        const validationResult = {
          ...response.data,
          metadata: {
            ...(response.data.metadata || {}),
            citation: citationToValidate,
            processedAt: new Date().toISOString(),
            validatedWith: [
              this.useEnhanced && 'enhanced',
              this.useML && 'ml',
              this.useCorrection && 'corrections'
            ].filter(Boolean).join(', '),
            responseTime: `${(endTime - startTime).toFixed(2)}ms`
          }
        };
        
        console.log('Processed validation result before transformation:', validationResult);
        
        // Transform the result for CitationResults
        const transformedResult = this.transformApiResponse(validationResult);
        console.log('Transformed result for CitationResults:', transformedResult);
        
        this.validationResult = transformedResult;

        // Get correction suggestions if enabled
        if (this.useCorrection) {
          await this.getCorrectionSuggestions();
        }

      } catch (err) {
        console.error('Error validating citation:', err);
        this.error = err.message || 'Failed to validate citation';
        this.validationResult = null;
      } finally {
        this.isValidating = false;
        console.groupEnd();
      }
    },
    
    // Get correction suggestions for a citation
    async getCorrectionSuggestions() {
      if (!this.citationText) return;

      try {
        const response = await api.post('/suggest_corrections', { citation: this.citationText });
        this.correctionResult = response.data;
      } catch (error) {
        console.error('Error getting correction suggestions:', error);
        // Don't show error to user for suggestions - it's a non-critical feature
        this.correctionResult = { suggestions: [] };
      }
    },
    
    /**
     * Returns an empty results object with the correct structure
     * @returns {Object} Empty results object with all required fields
     */
    getEmptyResultsObject() {
      const emptyCitation = {
        id: `empty-${Date.now()}`,
        citation: '',
        citation_text: '',
        case_name: 'No results',
        verified: false,
        status: 'unverified',
        validation_method: 'none',
        confidence: 0.0,
        source: 'none',
        verified_by: 'none',
        contexts: [],
        context: '',
        details: {},
        metadata: {
          url: '',
          source: 'none',
          verified: false,
          timestamp: new Date().toISOString()
        },
        url: '',
        error: null,
        verification_steps: [],
        sources: {},
        suggestions: []
      };
      
      const emptyResult = {
        validation_results: [{
          ...emptyCitation,
          status: 'unverified',
          verified: false
        }],
        citations: [{
          ...emptyCitation,
          status: 'unverified',
          verified: false
        }],
        total_citations: 0,
        citations_count: 0,
        verified_count: 0,
        unverified_count: 0,
        status: 'completed',
        execution_time: 0,
        metadata: {
          timestamp: new Date().toISOString(),
          source: 'none',
          verified: false,
          url: ''
        },
        local_search: [],
        multitool: [],
        error: null,
        warnings: []
      };
      
      console.log('[EnhancedValidator] Returning empty results object');
      return JSON.parse(JSON.stringify(emptyResult)); // Return a deep copy
    },
    
    /**
     * Transforms the API response to match the CitationResults component's expected format
     * @param {Object} apiResponse - The raw API response
     * @returns {Object} Transformed results object
     */
    transformApiResponse(response) {
      if (!response) return null;
      
      // Handle error cases
      if (response.error) {
        console.error('API Error:', response.error);
        return null;
      }

      // Ensure we have citations data
      const citations = Array.isArray(response.citations) ? response.citations : 
                       Array.isArray(response) ? response : 
                       response.citation ? [response] : [];

      if (!citations.length) {
        console.warn('No citations found in response:', response);
        return null;
      }

      // Transform each citation to ensure consistent structure
      const transformedCitations = citations.map(citation => ({
        citation_text: citation.citation_text || citation.citation || '',
        case_name: citation.case_name || '',
        source: citation.source || 'Unknown',
        validation_method: citation.validation_method || 'Unknown',
        status: citation.status || 'unknown',
        verified: citation.verified || false,
        suggestions: citation.suggestions || [],
        metadata: {
          volume: citation.volume || '',
          reporter: citation.reporter || '',
          page: citation.page || '',
          court: citation.court || '',
          year: citation.year || '',
          parallel_citations: citation.parallel_citations || []
        }
      }));

      return {
        citations: transformedCitations,
        total_citations: transformedCitations.length,
        verified_count: transformedCitations.filter(c => c.verified).length,
        unverified_count: transformedCitations.filter(c => !c.verified).length,
        courtlistener_count: transformedCitations.filter(c => c.source === 'CourtListener').length,
        other_verified_count: transformedCitations.filter(c => c.verified && c.source !== 'CourtListener').length
      };
    },
    

    /**
     * Fetches additional context for a validated citation
     * @returns {Promise<void>}
     */
    async getCitationContext() {
      if (!this.validationResult?.verified) {
        console.warn('Cannot get context for unverified citation');
        return;
      }
      
      const citationText = this.citationText?.trim();
      if (!citationText) {
        console.warn('No citation text available for context lookup');
        return;
      }
      
      // Prepare the request data
      const requestData = {
        citation: citationText,
        case_name: this.validationResult.case_name,
        citation_id: this.validationResult.id || null,
        source: this.validationResult.source || 'unknown'
      };
      
      // Configure request options
      const requestOptions = {
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        timeout: 30000, // 30 seconds timeout
        validateStatus: status => status >= 200 && status < 500
      };
      
      try {
        // Try endpoints in order of preference
        const endpoints = [
          '/casestrainer/api/citation-context',
          '/api/citation-context',
          `${this.basePath}/citation-context`
        ];
        
        let lastError = null;
        
        for (const endpoint of endpoints) {
          try {
            // Build URL with query parameters
            const params = new URLSearchParams({
              citation: encodeURIComponent(citationText),
              case_name: encodeURIComponent((this.validationResult?.case_name || ''))
            });
            const url = `${endpoint}?${params.toString()}`;
            
            // Use GET instead of POST
            const response = await axios.get(url, requestOptions);
            
            // Process successful response
            if (response.status === 200 && response.data) {
              const responseData = response.data;
              this.contextResult = responseData;
              this.citationContext = responseData.context || '';
              this.fileLink = responseData.file_link || '';
              
              // Update validation result with context metadata
              if (this.validationResult) {
                this.validationResult.context_available = true;
                this.validationResult.context_retrieved_at = new Date().toISOString();
                this.validationResult.context_source = responseData.source || endpoint;
              }
              
              return; // Success, exit the loop
            } else if (response.status === 404) {
              // Endpoint not found, try next one
              lastError = new Error('Context endpoint not found');
              continue;
            } else {
              // Other error status, log and try next endpoint
              lastError = new Error(response.data?.message || `HTTP ${response.status}`);
              continue;
            }
          } catch (error) {
            // Network or other error, log and try next endpoint
            lastError = error;
            console.warn(`Context lookup failed at ${endpoint}:`, error);
          }
        }
        
        // If we get here, all endpoints failed
        console.error('All context endpoints failed:', lastError);
        this.contextResult = {
          error: 'Failed to retrieve citation context',
          details: lastError?.message || 'All context endpoints failed',
          status: lastError?.response?.status || 500,
          citation: citationText,
          timestamp: new Date().toISOString()
        };
      } catch (error) {
        // This should only catch unexpected errors in the retry logic
        console.error('Unexpected error in getCitationContext:', error);
        this.contextResult = {
          error: 'Unexpected error',
          details: error.message || 'An unexpected error occurred',
          status: 500,
          citation: citationText,
          timestamp: new Date().toISOString()
        };
      }
    },
    
    // Analyze URL for citations
    async analyzeUrl() {
      console.group('analyzeUrl - Start');
      console.log('Input URL:', this.urlInput);
    
    if (!this.urlInput) {
      const errorObj = { 
        error: 'No URL provided', 
        details: 'Please enter a URL to analyze',
        status: 400 
      };
      console.warn('URL analysis failed - no URL provided');
      this.urlAnalysisResult = errorObj;
      console.groupEnd();
      return;
    }

    // Basic URL validation
    try {
      new URL(this.urlInput);
    } catch (e) {
      const errorObj = { 
        error: 'Invalid URL', 
        details: 'Please enter a valid URL (e.g., https://example.com)',
        status: 400 
      };
      console.warn('URL validation failed:', e.message);
      this.urlAnalysisResult = errorObj;
      console.groupEnd();
      return;
    }

    this.isAnalyzingUrl = true;
    this.urlAnalysisResult = null;
    this.error = null;

    try {
      const requestData = { url: this.urlInput };
      const requestConfig = {
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-Forwarded-Prefix': '/casestrainer'
        },
        timeout: 300000, // 5 minutes timeout
        withCredentials: true
      };
      
      console.log('Sending request to /analyze with data:', {
        url: `${this.apiBaseUrl}/analyze`,
        data: requestData,
        config: requestConfig
      });
      
      const startTime = performance.now();
      const response = await axios.post(
        `${this.apiBaseUrl}/analyze`,
        requestData,
        requestConfig
      );
      const endTime = performance.now();
      
      console.log(`URL Analysis Response (${(endTime - startTime).toFixed(2)}ms):`, {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        data: response.data
      });

      if (!response.data) {
        throw new Error('Empty response from server');
      }

      // Process the response data
      const processedCitations = Array.isArray(response.data.citations)
        ? response.data.citations.map(citation => ({
            ...citation,
            id: citation.id || `url-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            url: citation?.url || this.urlInput,
            contexts: Array.isArray(citation.contexts) ? citation.contexts : [],
            verified: citation.verified || false,
            verification_status: citation.verification_status || 
                             (citation.verified ? 'confirmed_by_courtlistener' : 'unverified'),
            validation_method: citation.validation_method || 'url_analysis',
            source: citation.source || 'url_analysis',
            metadata: {
              ...(citation.metadata || {}),
              url: citation?.url || this.urlInput,
              processedAt: new Date().toISOString()
            }
          }))
        : [];
        
      this.urlAnalysisResult = {
        ...response.data,
        citations: processedCitations,
        validation_results: processedCitations,
        metadata: {
          ...(response.data.metadata || {}),
          url: this.urlInput,
          processedAt: new Date().toISOString(),
          citationCount: processedCitations.length,
          source: 'url_analysis',
          responseTime: `${(endTime - startTime).toFixed(2)}ms`
        },
        eyecite_processed: response.data.eyecite_processed || false,
        error: response.data.error || null
      };
      
      // Update the active tab to show URL results
      console.log(`Processed ${processedCitations.length} citations from URL`);
      this.activeTab = 'url';
      
    } catch (error) {
      console.error('URL analysis error:', error);
      const errorResponse = error.response || {};
      const errorMessage = errorResponse.data?.message || error.message || 'Failed to analyze URL';
      const errorDetails = errorResponse.data?.details || errorResponse.statusText || 'An error occurred while analyzing the URL';
      
      console.error('URL analysis failed with error:', {
        error: errorMessage,
        details: errorDetails,
        status: errorResponse.status || 500,
        url: this.urlInput,
        timestamp: new Date().toISOString()
      });
      
      this.error = errorMessage;
      this.urlAnalysisResult = {
        error: errorMessage,
        details: errorDetails,
        status: errorResponse.status || 500,
        url: this.urlInput,
        processedAt: new Date().toISOString()
      };
      
      // Set validation result for the error case
      this.validationResult = {
        error: 'URL Analysis Failed',
        details: errorDetails,
        status: errorResponse.status || 500,
        verified: false,
        source: 'url_analysis_error',
        metadata: {
          error: errorMessage,
          url: this.urlInput,
          timestamp: new Date().toISOString()
        }
      };
      
    } finally {
      this.isAnalyzingUrl = false;
      console.groupEnd();
    }
},

// Analyze uploaded document for citations
async analyzeDocument() {
  const fileInput = this.$refs.documentUpload;
  if (!fileInput.files || fileInput.files.length === 0) {
    this.documentAnalysisResult = {
      error: 'No file selected',
      details: 'Please select a file to upload',
      status: 400,
      citations: [],
      validation_results: [],
      metadata: {}
    };
    return;
  }
  
  const file = fileInput.files[0];
  this.isAnalyzingDocument = true;
  this.documentAnalysisResult = null;
  this.error = null;
      
      // Validate file type and size
      const validTypes = [
        'application/pdf', 
        'application/msword', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'text/rtf',
        'application/rtf'
      ];
      
      const maxSize = 10 * 1024 * 1024; // 10MB
      
      if (!validTypes.some(type => file.type.includes(type.replace('application/', '').split('.')[0]))) {
        this.documentAnalysisResult = {
          error: 'Invalid file type',
          details: 'Please upload a PDF, Word document, or text file',
          status: 400,
          citations: [],
          validation_results: [],
          metadata: {
            fileName: file.name,
            fileSize: file.size,
            fileType: file.type,
            error: 'invalid_file_type'
          }
        };
        this.isAnalyzingDocument = false;
        this.activeTab = 'document';
        return;
      }
      
      if (file.size > maxSize) {
        this.documentAnalysisResult = {
          error: 'File too large',
          details: `File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds maximum allowed (10 MB)`,
          status: 400,
          citations: [],
          validation_results: [],
          metadata: {
            fileName: file.name,
            fileSize: file.size,
            fileType: file.type,
            error: 'file_too_large'
          }
        };
        this.isAnalyzingDocument = false;
        this.activeTab = 'document';
        return;
      }
      
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        const start = Date.now();
        console.log('[analyzeDocument] Sending request to /analyze at', new Date(start).toISOString());
        const response = await axios.post(
          `${this.apiBaseUrl}/analyze`, 
          formData, 
          {
            headers: { 
              'Content-Type': 'multipart/form-data',
              'X-Requested-With': 'XMLHttpRequest',
              'X-Forwarded-Prefix': '/casestrainer'
            },
            timeout: 300000, // 5 minutes timeout
            withCredentials: true
          }
        );
        const received = Date.now();
        console.log('[analyzeDocument] Received response from /analyze at', new Date(received).toISOString(), 'Elapsed:', (received - start) + 'ms');
        // Process successful response
        const processedCitations = Array.isArray(response.data?.citations)
          ? response.data.citations.map(citation => ({
              ...citation,
              id: citation.id || `doc-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              verified: citation.verified || false,
              validation_method: citation.validation_method || 'document_analysis',
              contexts: Array.isArray(citation.contexts) ? citation.contexts : [],
              source: citation.source || 'document_analysis',
              metadata: {
                ...(citation.metadata || {}),
                fileName: file.name,
                fileType: file.type,
                processedAt: new Date().toISOString()
              }
            }))
          : [];
        const processed = Date.now();
        console.log('[analyzeDocument] Finished processing response at', new Date(processed).toISOString(), 'Elapsed:', (processed - received) + 'ms');
        this.documentAnalysisResult = {
          ...response.data,
          citations: processedCitations,
          validation_results: processedCitations,
          metadata: {
            ...(response.data.metadata || {}),
            fileName: file.name,
            fileSize: file.size,
            fileType: file.type,
            processedAt: new Date().toISOString(),
            citationCount: processedCitations.length,
            source: 'document_analysis'
          },
          error: response.data.error || null
        };
        // Update the active tab to show document results
        this.activeTab = 'document';
        
      } catch (error) {
        // Enhanced error handling
        const errorResponse = error.response || {};
        const errorMessage = errorResponse.data?.message || error.message || 'Failed to process document';
        const errorDetails = errorResponse.data?.details || errorResponse.statusText || 'An unexpected error occurred';
        
        this.error = errorMessage;
        this.documentAnalysisResult = {
          error: errorMessage,
          details: errorDetails,
          status: errorResponse.status || 500,
          code: error.code,
          citations: [],
          validation_results: [],
          metadata: {
            fileName: file.name,
            fileSize: file.size,
            fileType: file.type,
            processedAt: new Date().toISOString(),
            error: true
          }
        };
        
        console.error('Document analysis error:', error);
        // Ensure we're on the document tab to show the error
        this.activeTab = 'document';
      } finally {
        this.isAnalyzingDocument = false;
      }
    },
    // Apply a suggested correction to the citation input
    applySuggestion(suggestion) {
      if (suggestion && suggestion.corrected_citation) {
        this.citationText = suggestion.corrected_citation;
        // Small delay to ensure the input updates before validating
        this.$nextTick(() => {
          this.validateCitation();
        });
      }
    },
    
    // Get badge class based on validation method
    getBadgeClass(validationMethod) {
      const method = (validationMethod || '').toLowerCase();
      
      if (method.includes('courtlistener') || method.includes('enhanced')) {
        return 'bg-success';
      } else if (method.includes('ml') || method.includes('machine learning')) {
        return 'bg-info';
      } else if (method.includes('local') || method.includes('basic')) {
        return 'bg-secondary';
      } else if (method.includes('error') || method.includes('failed')) {
        return 'bg-danger';
      } else {
        return 'bg-primary';
      }
    }
  },
  
  // Lifecycle hooks
  created() {
    // Set default URL if in development or local environment
    if (process.env.NODE_ENV === 'development' || window.location.hostname === 'localhost') {
      this.urlInput = 'http://localhost:5000/casestrainer/enhanced-validator';
    }
    // Load citation cache from localStorage on component creation
    this.loadCitationCache();
  }
};
</script>

<style>
.enhanced-validator {
  margin-bottom: 2rem;
  margin-bottom: 2rem;
}

.highlight-citation {
  background-color: #fffacd;
  font-weight: bold;
  padding: 2px;
  border-radius: 3px;
}

.context-text {
  font-family: Georgia, serif;
  line-height: 1.6;
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 5px;
  border-left: 4px solid #007bff;
}
</style>
