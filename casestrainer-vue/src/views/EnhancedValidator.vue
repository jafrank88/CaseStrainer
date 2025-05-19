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
            <div v-if="urlAnalysisResult" class="mt-4">
              <CitationResults :citations="transformedUrlResults.citations" />
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
      
    <!-- Document Upload Tab -->
    <div v-show="activeTab === 'document'">

      <div class="card">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">Upload Document</h5>
        </div>
        <div class="card-body">
          <div class="form-group">
            <label for="document-upload">Upload a legal document:</label>
            <div class="input-group mb-3">
              <input 
                type="file" 
                class="form-control" 
                id="document-upload" 
                ref="documentUpload"
                accept=".txt,.pdf,.doc,.docx,.rtf,.odt,.html,.htm"
              />
              <div class="input-group-append">
                <button 
                  class="btn btn-primary" 
                  @click="analyzeDocument"
                  :disabled="isAnalyzing"
                >
                  <span v-if="isAnalyzing" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  Analyze
                </button>
              </div>
            </div>
            <small class="form-text text-muted">Supported formats: TXT, PDF, DOC, DOCX, RTF, ODT, HTML, HTM</small>
          </div>
          
          <!-- Analysis Results -->
          <div v-if="documentAnalysisResult" class="mt-4">
            <CitationResults :citations="transformedDocumentResults.citations" />
          </div>
        </div>
      </div>
    </div>
    
    <!-- Text Paste Tab -->
    <div v-show="activeTab === 'text'">

      <div class="card">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">Paste Text</h5>
        </div>
        <div class="card-body">
          <div class="form-group">
            <label for="text-input">Paste legal text:</label>
            <textarea
              id="text-input"
              class="form-control"
              v-model="pastedText"
              rows="10"
              placeholder="Paste your legal document text here..."
            ></textarea>
          </div>
          <button 
            class="btn btn-primary mt-3" 
            @click="analyzeText"
            :disabled="isAnalyzing || !pastedText"
          >
            <span v-if="isAnalyzing" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            Analyze Text
          </button>
          
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script>
import axios from 'axios';
import CitationResults from '@/components/CitationResults.vue';

export default {
  name: 'EnhancedValidator',
  components: {
    CitationResults,
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
      urlAnalysisResult: null
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
        '/api',
        '/casestrainer/api'
      ];
      
      // In production, prioritize the /casestrainer/api path
      if (process.env.NODE_ENV === 'production') {
        return '/casestrainer/api';
      }
      return '/api';
    },
    // Transform single citation validation result
    transformedValidationResult() {
      if (!this.validationResult) return null;
      
      return {
        citations: [{
          citation_text: this.validationResult.citation,
          verified: this.validationResult.verified,
          validation_method: this.validationResult.validation_method,
          case_name: this.validationResult.case_name,
          source: this.validationResult.verified_by,
          confidence: this.validationResult.verified ? 1.0 : 0.0,
          error: this.validationResult.error,
          components: this.validationResult.components,
          url: null // Not provided by Enhanced Validator
        }]
      };
    },

    // Transform document analysis results
    transformedDocumentResults() {
      if (!this.documentAnalysisResult) return { citations: [] };
      return {
        citations: this.documentAnalysisResult.citations || []
      };
    },

    // Transform text analysis results
    transformedTextResults() {
      if (!this.textAnalysisResult) return { citations: [] };
      return {
        citations: this.textAnalysisResult.citations || []
      };
    },
    // Transform URL analysis results
    transformedUrlResults() {
      if (!this.urlAnalysisResult) return { citations: [] };
      return {
        citations: this.urlAnalysisResult.citations || []
      };
    }
  },
  methods: {
    async analyzeUrl() {
      if (!this.urlInput) return;
      this.isAnalyzingUrl = true;
      this.urlAnalysisResult = null;
      try {
        const response = await axios.post(this.basePath + '/api/analyze', {
          url: this.urlInput
        });
        this.urlAnalysisResult = response.data;
      } catch (error) {
        this.urlAnalysisResult = {
          citations: [],
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
          let response;
          try {
            // Try the first API endpoint format
            response = await axios.post(`${this.basePath}/enhanced-validate-citation`, {
              citation: this.citationText
            });
          } catch (firstError) {
            console.warn('First endpoint attempt failed, trying alternate endpoint:', firstError);
            try {
              // Try the second API endpoint format
              response = await axios.post(`/api/enhanced-validate-citation`, {
                citation: this.citationText
              });
            } catch (secondError) {
              console.warn('Second endpoint attempt failed, trying full path:', secondError);
              // Try the third API endpoint format with full path
              response = await axios.post(`/casestrainer/api/enhanced-validate-citation`, {
                citation: this.citationText
              });
            }
          }
          
          if (response && response.status === 200) {
            console.log('Enhanced validation response:', response.data);
            this.validationResult = response.data;
            
            // Get citation context and file link if available
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
            console.warn('ML classification first endpoint failed, trying alternate:', mlError);
            try {
              mlResponse = await axios.post(`/api/classify-citation`, {
                citation: this.citationText
              });
            } catch (mlError2) {
              console.warn('ML classification second endpoint failed, trying full path:', mlError2);
              mlResponse = await axios.post(`/casestrainer/api/classify-citation`, {
                citation: this.citationText
              });
            }
          }
          
          if (mlResponse && mlResponse.status === 200) {
            console.log('ML classification response:', mlResponse.data);
            this.mlResult = mlResponse.data;
          }
        }
        
        // Correction suggestions
        if (this.useCorrection && (!this.validationResult || !this.validationResult.verified)) {
          let correctionResponse;
          try {
            correctionResponse = await axios.post(`${this.basePath}/suggest-citation-corrections`, {
              citation: this.citationText
            });
          } catch (corrError) {
            console.warn('Correction suggestions first endpoint failed, trying alternate:', corrError);
            try {
              correctionResponse = await axios.post(`/api/suggest-citation-corrections`, {
                citation: this.citationText
              });
            } catch (corrError2) {
              console.warn('Correction suggestions second endpoint failed, trying full path:', corrError2);
              correctionResponse = await axios.post(`/casestrainer/api/suggest-citation-corrections`, {
                citation: this.citationText
              });
            }
          }
          
          if (correctionResponse && correctionResponse.status === 200) {
            console.log('Correction suggestions response:', correctionResponse.data);
            this.correctionResult = correctionResponse.data;
          }
        }
      } catch (error) {
        console.error('Error validating citation:', error);
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
          console.log('Citation context response:', response.data);
          this.contextResult = response.data;
          this.citationContext = response.data.context || '';
          this.fileLink = response.data.file_link || '';
        }
      } catch (error) {
        console.error('Error getting citation context:', error);
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
    
    // Method to analyze uploaded document
    analyzeDocument() {
      // Check if a file was selected
      const fileInput = this.$refs.documentUpload;
      if (!fileInput.files || fileInput.files.length === 0) {
        alert('Please select a file to upload');
        return;
      }
      
      const file = fileInput.files[0];
      this.isAnalyzing = true;
      this.documentAnalysisResult = null;
      
      // Create form data
      const formData = new FormData();
      formData.append('file', file);
      
      // Send request to API
      axios.post(`${this.basePath}/enhanced-analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      .then(response => {
        this.documentAnalysisResult = response.data;
        console.log('Document analysis result:', this.documentAnalysisResult);
      })
      .catch(error => {
        console.error('Error analyzing document:', error);
        alert(`Error analyzing document: ${error.response?.data?.message || error.message || 'Unknown error'}`);
      })
      .finally(() => {
        this.isAnalyzing = false;
      });
    },
    
    // Method to analyze pasted text
    analyzeText() {
      if (!this.pastedText) {
        alert('Please paste some text to analyze');
        return;
      }
      
      this.isAnalyzing = true;
      this.textAnalysisResult = null;
      
      // Create form data
      const formData = new FormData();
      formData.append('text', this.pastedText);
      
      // Send request to API
      axios.post(`${this.basePath}/enhanced-analyze`, formData)
      .then(response => {
        this.textAnalysisResult = response.data;
        console.log('Text analysis result:', this.textAnalysisResult);
      })
      .catch(error => {
        console.error('Error analyzing text:', error);
        alert(`Error analyzing text: ${error.response?.data?.message || error.message || 'Unknown error'}`);
      })
      .finally(() => {
        this.isAnalyzing = false;
      });
    }
  }
};
</script>

<style scoped>
.enhanced-validator {
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
