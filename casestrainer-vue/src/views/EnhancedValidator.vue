<template>
  <div class="enhanced-validator">
    <h2>Enhanced Citation Validator</h2>
    <p class="lead">
      This advanced tool validates legal citations using multiple sources and provides detailed citation information, context, and correction suggestions.
    </p>
    
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
        <FileUpload @results="handleDocumentResults" @error="handleDocumentError" />
      </div>
      
      <!-- Text Paste Tab -->
      <div v-show="activeTab === 'text'">
        <TextPaste @results="handleTextResults" @error="handleTextError" />
      </div>
    </div>
  </div>
</template>

<script>
import { getCurrentInstance } from 'vue';
import axios from 'axios';

// Components
import FileUpload from '@/components/FileUpload.vue';
import TextPaste from '@/components/TextPaste.vue';
import CitationResults from '@/components/CitationResults.vue';
import ReusableResults from '@/components/ReusableResults.vue';

// Get the current app instance for logging
const currentApp = getCurrentInstance()?.appContext?.app;

export default {
  name: 'EnhancedValidator',
  components: {
    FileUpload,
    TextPaste,
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
      
      // Document Upload
      documentAnalysisResult: null,
      
      // Text Paste
      textAnalysisResult: null,
      
      // URL Check
      urlInput: '',
      urlAnalysisResult: null,
      isAnalyzingUrl: false,
      
      dropZoneActive: false,
      isCheckingCitations: false,
      isValidating: false,
      isCorrecting: false,
      isGettingContext: false,
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
      urlResults: null
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
        const citations = (Array.isArray(analysis.citations) ? analysis.citations : [])
          .filter(citation => citation && typeof citation === 'object')
          .map(citation => ({
            ...citation,
            id: citation.id || `doc-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
            citation: citation.citation || citation.citation_text || 'Unknown',
            case_name: citation.case_name || citation.citation || 'Unknown Case',
            verified: !!citation.verified,
            status: citation.verified ? 'verified' : 'unverified',
            validation_method: citation.validation_method || 'Document Analysis',
            confidence: citation.confidence || 0.0,
            contexts: Array.isArray(citation.contexts) ? citation.contexts : [],
            context: citation.context || (Array.isArray(citation.contexts) && citation.contexts[0]?.text) || '',
            content: citation.content || citation.context || (Array.isArray(citation.contexts) && citation.contexts[0]?.text) || '',
            details: citation.details || {},
            error: citation.error || null,
            source: citation.source || 'Document Analysis',
            verified_by: citation.verified_by || (citation.verified ? 'Document Analysis' : 'Not Verified'),
            metadata: citation.metadata || {},
            suggestions: Array.isArray(citation.suggestions) ? citation.suggestions : []
          }));
        
        const verifiedCount = citations.filter(c => c.verified).length;
        const totalCitations = citations.length;
        const unverifiedCount = totalCitations - verifiedCount;
        
        // Transform document analysis results to match CitationResults expected format
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
      
      // Process citations from the text analysis result
      const citations = (this.textAnalysisResult.citations || [])
        .filter(citation => citation && typeof citation === 'object')
        .map(citation => ({
          ...citation,
          id: citation.id || `text-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
          citation: citation.citation || citation.citation_text || 'Unknown',
          case_name: citation.case_name || citation.citation || 'Unknown Case',
          verified: !!citation.verified,
          status: citation.verified ? 'verified' : 'unverified',
          validation_method: citation.validation_method || 'Text Analysis',
          confidence: citation.confidence || 0.0,
          contexts: Array.isArray(citation.contexts) ? citation.contexts : [],
          context: citation.context || (Array.isArray(citation.contexts) && citation.contexts[0]?.text) || '',
          content: citation.content || citation.context || (Array.isArray(citation.contexts) && citation.contexts[0]?.text) || '',
          details: citation.details || {},
          error: citation.error || null,
          source: citation.source || 'Text Analysis',
          verified_by: citation.verified_by || (citation.verified ? 'Text Analysis' : 'Not Verified'),
          metadata: citation.metadata || {},
          suggestions: Array.isArray(citation.suggestions) ? citation.suggestions : []
        }));
      
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
      
      console.log('Original URL analysis result:', JSON.parse(JSON.stringify(this.urlAnalysisResult)));
      
      // Process citations from the URL analysis result
      const citations = (Array.isArray(this.urlAnalysisResult.citations) ? this.urlAnalysisResult.citations : [])
        .filter(citation => citation && typeof citation === 'object')
        .map(citation => ({
          ...citation,
          id: citation.id || `url-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
          citation: citation.citation || citation.citation_text || 'Unknown',
          case_name: citation.case_name || citation.citation || 'Unknown Case',
          verified: !!citation.verified,
          status: citation.verified ? 'verified' : 'unverified',
          validation_method: citation.validation_method || 'URL Analysis',
          confidence: citation.confidence || 0.0,
          contexts: Array.isArray(citation.contexts) ? citation.contexts : [],
          context: citation.context || (Array.isArray(citation.contexts) && citation.contexts[0]?.text) || '',
          content: citation.content || citation.context || (Array.isArray(citation.contexts) && citation.contexts[0]?.text) || '',
          details: citation.details || {},
          error: citation.error || null,
          source: citation.source || 'URL Analysis',
          verified_by: citation.verified_by || (citation.verified ? 'URL Analysis' : 'Not Verified'),
          metadata: citation.metadata || {},
          suggestions: Array.isArray(citation.suggestions) ? citation.suggestions : []
        }));
      
      const confirmedCount = citations.filter(c => c.verified).length;
      const totalCitations = citations.length;
      const unverifiedCount = totalCitations - confirmedCount;
      
      const result = {
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
      
      console.log('Transformed URL results:', JSON.parse(JSON.stringify(result)));
      return result;
    },
  },
  methods: {
    // Handle document analysis results from FileUpload component
    handleDocumentResults(results) {
      console.log('Document analysis results:', results);
      this.documentAnalysisResult = results;
      // You can process the results further if needed
    },
    
    // Handle document analysis errors from FileUpload component
    handleDocumentError(error) {
      console.error('Document analysis error:', error);
      this.documentAnalysisResult = { error };
    },
    
    // Handle text analysis results from TextPaste component
    handleTextResults(results) {
      console.log('Text analysis results:', results);
      this.textAnalysisResult = results;
      // You can process the results further if needed
    },
    
    // Handle text analysis errors from TextPaste component
    handleTextError(error) {
      console.error('Text analysis error:', error);
      this.textAnalysisResult = { error };
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
        content: 'No citation content available',
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
    transformApiResponse(apiResponse) {
      try {
        console.log('[EnhancedValidator] Transforming API response for CitationResults');
        
        if (!apiResponse) {
          console.warn('[EnhancedValidator] Empty API response');
          return this.getEmptyResultsObject();
        }
        
        // If this is a correction suggestion response, handle it specially
        if (apiResponse.suggestions && Array.isArray(apiResponse.suggestions)) {
          console.log('[EnhancedValidator] Processing correction suggestions response');
          const transformedResults = this.getEmptyResultsObject();
          
          // Ensure all suggestions have required fields
          const processedSuggestions = apiResponse.suggestions.map(suggestion => ({
            corrected_citation: suggestion.corrected_citation || suggestion.citation || 'Unknown',
            similarity: typeof suggestion.similarity === 'number' ? suggestion.similarity : 0,
            explanation: suggestion.explanation || 'No explanation provided',
            correction_type: suggestion.correction_type || 'unknown',
            ...suggestion // Spread any additional properties
          }));
          
          // Create a citation object with all required fields
          const citation = {
            id: `citation-${Date.now()}`,
            citation: apiResponse.citation || this.citationText || 'Unknown',
            citation_text: apiResponse.citation || this.citationText || 'Unknown',
            case_name: 'Citation Correction Suggestions',
            verified: false,
            status: 'unverified',
            validation_method: 'Correction Engine',
            confidence: 0.0,
            source: 'correction_engine',
            verified_by: 'Correction Engine',
            contexts: [],
            context: '',
            details: {},
            metadata: {
              correction_suggestions: true,
              timestamp: new Date().toISOString(),
              source: 'correction_engine',
              verified: false
            },
            url: '',
            error: apiResponse.error || null,
            verification_steps: [],
            sources: {},
            // Add the processed suggestions array
            suggestions: processedSuggestions,
            // Add empty content property to prevent errors
            content: ''
          };
          
          transformedResults.validation_results = [citation];
          transformedResults.total_citations = 1;
          transformedResults.citations_count = 1;
          transformedResults.unverified_count = 1;
          transformedResults.citations = [citation]; // Add to citations array for backward compatibility
          
          console.log('[EnhancedValidator] Transformed correction suggestions:', transformedResults);
          return transformedResults;
        }
        
        // Handle regular validation results
        if (!apiResponse.validation_results) {
          console.warn('[EnhancedValidator] No validation_results in API response');
          return this.getEmptyResultsObject();
        }
        
        const transformedResults = {
          validation_results: [],
          total_citations: 0,
          verified_count: 0,
          unverified_count: 0,
          metadata: {}
        };
        
        // Process each validation result
        apiResponse.validation_results.forEach((result, index) => {
          const validation = result.validation || result;
          const isCourtListener = (validation.source === 'courtlistener') || 
                               String(validation.verified_by || '').toLowerCase().includes('courtlistener');
          
          // Safely get citation text with fallbacks
          const citationText = validation.citation || this.citationText || 'Unknown';
          
          // Create the citation object with all required fields for CitationResults
          const citation = {
            id: `citation-${Date.now()}-${index}`,
            citation: citationText,
            citation_text: validation.citation_text || citationText,
            // Try to get case name from multiple possible locations in the response
            case_name: validation.case_name || 
                      validation.details?.case_name || 
                      validation.metadata?.case_name || 
                      (validation.details?.title ? validation.details.title.replace(/<[^>]+>/g, '') : null) ||
                      (validation.contexts?.[0]?.case_name ? validation.contexts[0].case_name : null) ||
                      'Unknown Case',
            verified: !!validation.verified,
            status: validation.verified ? 'verified' : 'unverified',
            validation_method: validation.validation_method || (isCourtListener ? 'CourtListener' : 'Local Validation'),
            confidence: parseFloat(validation.confidence) || 0.0,
            source: validation.source || 'unknown',
            verified_by: validation.verified_by || (isCourtListener ? 'CourtListener' : 'Local'),
            contexts: Array.isArray(validation.contexts) ? validation.contexts : [],
            context: (Array.isArray(validation.contexts) && validation.contexts[0]?.text) ? 
                    validation.contexts[0].text : '',
            content: validation.content || 
                   (Array.isArray(validation.contexts) && validation.contexts[0]?.text) || 
                   validation.context || 
                   '',
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
          
          // Ensure case_name is properly formatted
          if (citation.case_name) {
            // Clean up any HTML tags and extra whitespace
            citation.case_name = citation.case_name
              .replace(/<[^>]+>/g, '') // Remove HTML tags
              .replace(/\s+/g, ' ')    // Replace multiple spaces with single space
              .trim();
            
            // If case_name is just a citation number, mark as unknown
            if (/^\d+\s+[A-Za-z0-9.]+\s+\d+$/.test(citation.case_name)) {
              citation.case_name = 'Unknown Case';
            }
          }
          
          // Log verification status for debugging
          console.log(`[transformApiResponse] Citation ${citation.citation} - ` +
                     `verified: ${citation.verified}, ` +
                     `status: ${citation.status}, ` +
                     `metadata.verified: ${citation.metadata.verified}`);
          
          // Update counts
          if (citation.verified) {
            transformedResults.verified_count++;
          } else {
            transformedResults.unverified_count++;
          }
          
          transformedResults.validation_results.push(citation);
        });
        
        // Set total citations count
        transformedResults.total_citations = transformedResults.validation_results.length;
        transformedResults.citations_count = transformedResults.total_citations;
        
        console.log('[EnhancedValidator] Transformed results:', transformedResults);
        return transformedResults;
        
      } catch (error) {
        console.error('[EnhancedValidator] Error transforming API response:', error);
        return this.getEmptyResultsObject();
      }
    },
    
    async analyzeUrl() {
      if (!this.urlInput) {
        this.urlAnalysisResult = {
          error: 'No URL provided',
          details: 'Please enter a URL to analyze',
          status: 400,
          citations: [],
          metadata: {},
          eyecite_processed: false
        };
        return;
      }
      
      // Basic URL validation
      try {
        new URL(this.urlInput);
      } catch (e) {
        this.urlAnalysisResult = {
          error: 'Invalid URL',
          details: 'Please enter a valid URL (e.g., https://example.com)',
          status: 400,
          citations: [],
          metadata: {},
          eyecite_processed: false
        };
        return;
      }
      
      this.isAnalyzingUrl = true;
      this.urlAnalysisResult = { 
        citations: [], 
        metadata: {}, 
        eyecite_processed: false, 
        error: null 
      };

      try {
        const response = await axios.post('/casestrainer/api/analyze', 
          { url: this.urlInput },
          {
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'XMLHttpRequest'
            },
            timeout: 300000 // 5 minutes timeout
          }
        );
        
        if (response && response.data && typeof response.data === 'object') {
          const processedCitations = Array.isArray(response.data.citations)
            ? response.data.citations.map(citation => ({
                ...citation,
                id: citation.id || `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                url: citation?.url || this.urlInput,
                contexts: Array.isArray(citation.contexts) ? citation.contexts : [],
                verified: citation.verified || false,
                verification_status: citation.verification_status || 
                                  (citation.verified ? 'confirmed_by_courtlistener' : 'unverified'),
                validation_method: citation.validation_method || 'url_analysis'
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
              citationCount: processedCitations.length
            },
            eyecite_processed: response.data.eyecite_processed || false,
            error: response.data.error || null
          };
        } else {
          throw new Error('Invalid response format from server');
        }
      } catch (error) {
        console.error('URL analysis error:', error);
        const errorResponse = error.response || {};
        this.urlAnalysisResult = {
          error: errorResponse.data?.message || error.message || 'Failed to analyze URL',
          details: errorResponse.data?.details || errorResponse.statusText || 'An error occurred while analyzing the URL',
          status: errorResponse.status || 500,
          code: error.code,
          citations: [],
          metadata: {
            url: this.urlInput,
            processedAt: new Date().toISOString()
          },
          eyecite_processed: false
        };
      } finally {
        this.isAnalyzingUrl = false;
      }
    },
    async validateCitation() {
      // Input validation and store citation in local constant
      const citationToValidate = this.citationText?.trim() || '';
      
      if (!citationToValidate) {
        this.validationResult = {
          error: 'No citation provided',
          details: 'Please enter a citation to validate',
          status: 400,
          verified: false,
          citation: ''
        };
        this.$toast.warning('Please enter a citation to validate');
        return;
      }

      this.isValidating = true;
      this.validationResult = null;
      this.mlResult = null;
      this.correctionResult = null;
      this.citationContext = '';
      this.fileLink = '';
      
      try {
        // Enhanced validation
        if (this.useEnhanced) {
          console.log('[EnhancedValidator] Sending request to validate citation:', citationToValidate);
          const response = await axios.post(
            '/casestrainer/api/verify-citation',
            { citation: citationToValidate },
            {
              headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
              },
              timeout: 30000 // 30 seconds timeout
            }
          );
          
          if (response?.data) {
            console.log('[EnhancedValidator] Received API response:', response.data);
            
            // The verify-citation endpoint returns a single citation result
            // Create a validation results object that matches the expected format
            const validationResult = {
              ...response.data,
              // Ensure we have all required fields
              citation: response.data.citation || citationToValidate,
              verified: response.data.verified || false,
              status: response.data.verified ? 'verified' : 'unverified',
              metadata: response.data.metadata || {}
            };
            
            console.log('[EnhancedValidator] Received validation result:', validationResult);
            
            // Update the validation result
            this.validationResult = validationResult;
            
            // Update the results for the ReusableResults component
            this.results = {
              validation_results: [validationResult],
              total_citations: 1,
              verified_count: validationResult.verified ? 1 : 0,
              unverified_count: validationResult.verified ? 0 : 1,
              citations_count: 1,
              unconfirmedCount: validationResult.verified ? 0 : 1,
              confirmed_count: validationResult.verified ? 1 : 0,
              metadata: validationResult.metadata || {}
            };
            
            // Log successful validation
            console.log('[EnhancedValidator] Processed validation result:', this.validationResult);
            
            // Get context if verified
            if (this.validationResult.verified) {
              await this.getCitationContext();
            }
            } else if (response.data.error) {
              // Handle API-level errors
              console.error('[EnhancedValidator] API returned error:', response.data.error);
              this.validationResult = {
                error: response.data.error,
                details: response.data.message || 'Failed to validate citation',
                status: response.status || 500,
                citation: citationToValidate,
                verified: false,
                source: 'api_error',
                metadata: {
                  error: response.data.error,
                  status: response.status || 500,
                  timestamp: new Date().toISOString()
                }
              };
              
              currentApp.logger.error('API Error:', this.validationResult);
            } else {
              // Handle empty or unexpected response format
              this.validationResult = {
                error: 'No validation results',
                details: 'The citation could not be validated. The response format was unexpected.',
                status: 404,
                citation: citationToValidate,
                verified: false,
                source: 'validation_error',
                metadata: {
                  response_data: response.data,
                  timestamp: new Date().toISOString()
                }
              };
              
              currentApp.logger.warn('Unexpected API response format:', response.data);
            }
          }
        }
        
        // ML classification (if enabled)
        if (this.useML) {
          try {
            const mlResponse = await axios.post(
              '/casestrainer/api/classify-citation',
              { citation: citationToValidate },
              {
                headers: { 'Content-Type': 'application/json' },
                timeout: 30000 // 30 seconds timeout
              }
            );
            if (mlResponse?.data) {
              this.mlResult = {
                ...mlResponse.data,
                processed_at: new Date().toISOString()
              };
            }
          } catch (mlError) {
            console.warn('ML classification failed:', mlError);
            // Non-fatal error, continue with other operations
          }
        }
        
        // Correction suggestions (if enabled)
        if (this.useCorrection) {
          try {
            const correctionResponse = await axios.post(
              '/casestrainer/api/suggest-citation-corrections',
              { citation: citationToValidate },
              {
                headers: { 'Content-Type': 'application/json' },
                timeout: 30000 // 30 seconds timeout
              }
            );
            
            if (correctionResponse?.data) {
              // Only set correction result if we have suggestions or an error
              if (correctionResponse.data.suggestions?.length > 0 || correctionResponse.data.error) {
                this.correctionResult = {
                  ...correctionResponse.data,
                  processed_at: new Date().toISOString()
                };
              } else if (correctionResponse.data.warning) {
                // Show warning to the user if the correction engine is not available
                this.$toast.warning(correctionResponse.data.warning, {
                  position: 'top-right',
                  timeout: 8000,
                  closeOnClick: true,
                  pauseOnFocusLoss: true,
                  pauseOnHover: true
                });
              }
            }
          } catch (corrError) {
            console.warn('Correction suggestion failed:', corrError);
            // Show error to the user
            this.$toast.error('Failed to get correction suggestions. ' + (corrError.response?.data?.error || corrError.message || ''), {
              position: 'top-right',
              timeout: 10000,
              closeOnClick: true,
              pauseOnFocusLoss: true,
              pauseOnHover: true
            });
            // Non-fatal error, continue with other operations
          }
        }
        
      } catch (error) {
        console.error('Citation validation error:', error);
        const errorResponse = error.response || {};
        this.validationResult = {
          error: errorResponse.data?.message || error.message || 'Failed to validate citation',
          details: errorResponse.data?.details || errorResponse.statusText || 'An unexpected error occurred',
          status: errorResponse.status || 500,
          code: error.code,
          citation: citationToValidate,
          verified: false,
          processed_at: new Date().toISOString()
        };
      } finally {
        this.isValidating = false;
      }
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
          error: 'Unexpected error retrieving context',
          details: error.message || 'An unexpected error occurred',
          status: error.response?.status || 500,
          citation: citationText,
          timestamp: new Date().toISOString()
        };
      } finally {
        // Ensure any loading states are reset
        if (this.validationResult) {
          this.validationResult.context_retrieval_complete = true;
        }
      }
    },
    
    applySuggestion(suggestion) {
      this.citationText = suggestion;
      this.validateCitation();
    },
    
    getBadgeClass(validationMethod) {
      // Return appropriate Bootstrap badge classes based on validation method
      switch(validationMethod) {
        case 'Landmark':
          return 'bg-primary';
        case 'CourtListener':
          return 'bg-success';
        case 'Multitool':
          return 'bg-info';
        case 'Other':
          return 'bg-secondary';
        default:
          return 'bg-dark';
      }
    },
    
    async analyzeDocument() {
      const fileInput = this.$refs.documentUpload;
      if (!fileInput.files || fileInput.files.length === 0) {
        this.documentAnalysisResult = {
          error: 'No file selected',
          details: 'Please select a file to upload',
          status: 400
        };
        return;
      }
      
      const file = fileInput.files[0];
      this.isAnalyzing = true;
      this.documentAnalysisResult = null;
      
      // Validate file type and size
      const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      const maxSize = 10 * 1024 * 1024; // 10MB
      
      if (!validTypes.includes(file.type)) {
        this.documentAnalysisResult = {
          error: 'Invalid file type',
          details: 'Please upload a PDF or Word document',
          status: 400
        };
        this.isAnalyzing = false;
        return;
      }
      
      if (file.size > maxSize) {
        this.documentAnalysisResult = {
          error: 'File too large',
          details: 'Maximum file size is 10MB',
          status: 400
        };
        this.isAnalyzing = false;
        return;
      }
      
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        const response = await axios.post('/casestrainer/api/analyze', formData, {
          headers: { 
            'Content-Type': 'multipart/form-data',
            'X-Requested-With': 'XMLHttpRequest'
          },
          timeout: 300000 // 5 minutes timeout
        });
        
        // Process successful response
        this.documentAnalysisResult = {
          ...response.data,
          metadata: {
            ...response.data.metadata,
            fileName: file.name,
            fileSize: file.size,
            fileType: file.type,
            processedAt: new Date().toISOString()
          },
          error: response.data.error || null
        };
        
      } catch (error) {
        // Enhanced error handling
        const errorResponse = error.response || {};
        this.documentAnalysisResult = {
          error: errorResponse.data?.message || error.message || 'Failed to process document',
          details: errorResponse.data?.details || errorResponse.statusText,
          status: errorResponse.status || 500,
          code: error.code,
          metadata: {
            fileName: file.name,
            fileSize: file.size,
            fileType: file.type
          }
        };
        console.error('Document analysis error:', error);
      } finally {
        this.isAnalyzing = false;
      }
    },
    // Enhanced text analysis with better error handling and response processing
    async analyzeText() {
      if (!this.pastedText) {
        this.textAnalysisResult = {
          error: 'No text provided',
          details: 'Please enter or paste some text to analyze',
          status: 400
        };
        return;
      }
      
      // Validate input length
      if (this.pastedText.length > 10000) {
        this.textAnalysisResult = {
          error: 'Text too long',
          details: 'Maximum text length is 10,000 characters',
          status: 400
        };
        return;
      }
      
      this.isAnalyzing = true;
      this.textAnalysisResult = null;
      
      try {
        const response = await axios.post('/casestrainer/api/analyze', 
          { text: this.pastedText },
          {
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'XMLHttpRequest'
            },
            timeout: 300000 // 5 minutes timeout
          }
        );
        
        // Process successful response
        this.textAnalysisResult = {
          ...response.data,
          metadata: {
            ...response.data.metadata,
            textLength: this.pastedText.length,
            processedAt: new Date().toISOString(),
            citationCount: response.data.citations?.length || 0
          },
          error: response.data.error || null
        };
        
      } catch (error) {
        // Enhanced error handling
        const errorResponse = error.response || {};
        this.textAnalysisResult = {
          error: errorResponse.data?.message || error.message || 'Failed to analyze text',
          details: errorResponse.data?.details || errorResponse.statusText,
          status: errorResponse.status || 500,
          code: error.code,
          metadata: {
            textLength: this.pastedText.length,
            processedAt: new Date().toISOString()
          }
        };
        console.error('Text analysis error:', error);
      } finally {
        this.isAnalyzing = false;
      }
    }
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
