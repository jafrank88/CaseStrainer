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
              <CitationResults :citations="transformedValidationResult.citations" />
            </div>
          </div>
        </div>
      </div>
      
      <!-- Document Upload Tab -->
      <!-- Error Alert for Document Upload -->
      <div v-if="documentAnalysisResult && documentAnalysisResult.error" class="alert alert-danger mt-4">
        <strong>Error:</strong> {{ documentAnalysisResult.error }}
      </div>
      <EnhancedFileUpload v-show="activeTab === 'document'" />
      
      <!-- Text Paste Tab -->
      <!-- Error Alert for Text Paste -->
      <div v-if="textAnalysisResult && textAnalysisResult.error" class="alert alert-danger mt-4">
        <strong>Error:</strong> {{ textAnalysisResult.error }}
      </div>
      <EnhancedTextPaste v-show="activeTab === 'text'" />
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import EnhancedFileUpload from '../components/EnhancedFileUpload.vue';
import EnhancedTextPaste from '../components/EnhancedTextPaste.vue';
import CitationResults from '@/components/CitationResults.vue';

export default {
  name: 'EnhancedValidator',
  components: {
    CitationResults,
    EnhancedFileUpload,
    EnhancedTextPaste
  },
  data() {
    return {
      activeTab: 'single',
      // Single citation validation
      citationText: '',
      isValidating: false,
      validationResult: null,
      mlResult: null,
      correctionResult: null,
      citationContext: '',
      fileLink: '',
      useEnhanced: true,
      useML: true,
      useCorrection: true,
      contextResult: null,
      
      // Document upload
      isAnalyzing: false,
      documentAnalysisResult: null,
      
      // Text paste
      pastedText: '',
      textAnalysisResult: null,
      // URL check
      urlInput: '',
      isAnalyzingUrl: false,
      urlAnalysisResult: {
  citations: [],
  metadata: {},
  error: null
}
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
    // Transform single citation validation result
    transformedValidationResult() {
      if (!this.validationResult) return null;
      
      return {
        citations: [
          {
            citation_text: this.validationResult.citation,
            verified: this.validationResult.verified,
            validation_method: this.validationResult.validation_method,
            case_name: this.validationResult.case_name,
            source: this.validationResult.verified_by,
            confidence: this.validationResult.verified ? 1.0 : 0.0,
            error: this.validationResult.error,
            components: this.validationResult.components,
            url: null, // Not provided by Enhanced Validator
            contexts: Array.isArray(this.validationResult.contexts) ? this.validationResult.contexts : []
          }
        ]
      };
    },

    // Transform document analysis results
    transformedDocumentResults() {
      if (!this.documentAnalysisResult) return { citations: [] };
      return {
        citations: (this.documentAnalysisResult.citations || [])
          .filter(citation => citation && typeof citation === 'object')
          .map(citation => ({
            ...citation,
            contexts: Array.isArray(citation.contexts) ? citation.contexts : []
          }))
      };
    },

    // Transform text analysis results
    transformedTextResults() {
      if (!this.textAnalysisResult) return { citations: [] };
      return {
        citations: (this.textAnalysisResult.citations || [])
          .filter(citation => citation && typeof citation === 'object')
          .map(citation => ({
            ...citation,
            contexts: Array.isArray(citation.contexts) ? citation.contexts : []
          }))
      };
    },
    // Transform URL analysis results
    transformedUrlResults() {
      if (!this.urlAnalysisResult || typeof this.urlAnalysisResult !== 'object') {
        return { citations: [], validation_results: [] };
      }
      let citationsArray = Array.isArray(this.urlAnalysisResult.citations) ? this.urlAnalysisResult.citations : [];
      const processedCitations = citationsArray
        .filter(citation => citation && typeof citation === 'object')
        .map(citation => ({
          ...citation,
          contexts: Array.isArray(citation.contexts) ? citation.contexts : []
        }));
      return {
        citations: processedCitations,
        validation_results: processedCitations
      };
    },
  },
  methods: {
    async analyzeUrl() {
      this.isAnalyzingUrl = true;
      this.urlAnalysisResult = { citations: [], metadata: {}, eyecite_processed: false, error: null };

      try {
        const response = await axios.post('/casestrainer/api/analyze', {
          url: this.urlInput
        });
        if (response && response.data && typeof response.data === 'object') {
          const processedCitations = Array.isArray(response.data.citations)
            ? response.data.citations.map(citation => ({
                ...citation,
                url: citation && typeof citation.url !== 'undefined' ? citation.url : null
              }))
            : [];
          this.urlAnalysisResult = {
            ...response.data,
            citations: processedCitations,
            metadata: response.data.metadata || {},
            eyecite_processed: response.data.eyecite_processed || false
          };
        } else {
          this.urlAnalysisResult = { citations: [], metadata: {}, eyecite_processed: false, error: 'Malformed response from server.' };
        }
      } catch (error) {
        this.urlAnalysisResult = {
          citations: [],
          metadata: {},
          eyecite_processed: false,
          error: error.response?.data?.error || 'An error occurred while analyzing the URL.'
        };
      } finally {
        this.isAnalyzingUrl = false;
      }
    },
    async validateCitation() {
      if (!this.citationText || this.isValidating) return;
      this.isValidating = true;
      this.validationResult = null;
      this.mlResult = null;
      this.correctionResult = null;
      this.citationContext = '';
      this.fileLink = '';
      try {
        // Enhanced validation
        if (this.useEnhanced) {
          let response = await axios.post(`/casestrainer/api/enhanced-validate-citation`, {
            citation: this.citationText
          });
          if (response && response.status === 200) {
            this.validationResult = response.data;
            if (this.validationResult.verified) {
              await this.getCitationContext();
            }
          }
        }
        // ML classification
        if (this.useML) {
          let mlResponse;
          try {
            mlResponse = await axios.post(`${this.basePath}/classify-citation`, {
              citation: this.citationText
            });
          } catch (mlError) {
            try {
              mlResponse = await axios.post(`/api/classify-citation`, {
                citation: this.citationText
              });
            } catch (mlError2) {
              // fallback or handle error
            }
          }
          if (mlResponse && mlResponse.data) {
            this.mlResult = mlResponse.data;
          }
        }
        // Correction suggestion
        if (this.useCorrection) {
          let correctionResponse;
          try {
            correctionResponse = await axios.post(`${this.basePath}/suggest-citation-corrections`, {
              citation: this.citationText
            });
          } catch (corrError) {
            try {
              correctionResponse = await axios.post(`/api/suggest-citation-corrections`, {
                citation: this.citationText
              });
            } catch (corrError2) {
              // fallback or handle error
            }
          }
          if (correctionResponse && correctionResponse.status === 200) {
            this.correctionResult = correctionResponse.data;
          }
        }
      } catch (error) {
        // console.error('Error validating citation:', error);
        alert('Error validating citation. Please try again later.');
      } finally {
        this.isValidating = false;
      }
    },
    
    async getCitationContext() {
      try {
        let response;
        try {
          // Try the first API endpoint format
          response = await axios.post(`${this.basePath}/citation-context`, {
            citation: this.citationText
          });
        } catch (firstError) {
          console.warn('Citation context first endpoint failed, trying alternate:', firstError);
          try {
            // Try the second API endpoint format
            response = await axios.post(`/api/citation-context`, {
              citation: this.citationText
            });
          } catch (secondError) {
            console.warn('Citation context second endpoint failed, trying full path:', secondError);
            // Try the third API endpoint format with full path
            response = await axios.post(`/casestrainer/api/citation-context`, {
              citation: this.citationText
            });
          }
        }
        
        if (response && response.status === 200) {
          // // console.log('Citation context response:', response.data);
          this.contextResult = response.data;
          this.citationContext = response.data.context || '';
          this.fileLink = response.data.file_link || '';
        }
      } catch (error) {
        // console.error('Error getting citation context:', error);
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
        alert('Please select a file to upload');
        return;
      }
      const file = fileInput.files[0];
      this.isAnalyzing = true;
      this.documentAnalysisResult = null;
      const formData = new FormData();
      formData.append('file', file);
      try {
        const response = await axios.post('/casestrainer/api/analyze', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        this.documentAnalysisResult = response.data;
        // If backend returns error in response.data.error
        if (response.data && response.data.error) {
          this.documentAnalysisResult.error = response.data.error;
        }
      } catch (error) {
        this.documentAnalysisResult = {
          error: error.response?.data?.message || error.message || 'Unknown error'
        };
      } finally {
        this.isAnalyzing = false;
      }
    },
    // Patch text analysis error assignment
    async analyzeText() {
      if (!this.pastedText) {
        alert('Please paste some text to analyze');
        return;
      }
      this.isAnalyzing = true;
      this.textAnalysisResult = null;
      try {
        const response = await axios.post('/casestrainer/api/analyze', { text: this.pastedText });
        this.textAnalysisResult = response.data;
        if (response.data && response.data.error) {
          this.textAnalysisResult.error = response.data.error;
        }
      } catch (error) {
        this.textAnalysisResult = {
          error: error.response?.data?.message || error.message || 'Unknown error'
        };
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
