<template>
  <div class="enhanced-validator container-fluid py-3">
    <div class="row g-3">
      <!-- Main Content Area -->
      <div class="col-12">
        <div class="card shadow-sm">
          <div class="card-header bg-primary text-white py-3">
            <div class="d-flex flex-column">
              <h5 class="mb-3">
                <i class="bi bi-search me-2"></i>Citation Validator
              </h5>
              <div class="d-flex flex-wrap gap-2">
                <button 
                  class="btn d-flex align-items-center" 
                  :class="activeTab === 'single' ? 'btn-light' : 'btn-outline-light'"
                  @click="activeTab = 'single'"
                >
                  <i class="bi bi-quote me-1"></i>
                  <span>Single Citation</span>
                </button>
                <button 
                  class="btn d-flex align-items-center" 
                  :class="activeTab === 'document' ? 'btn-light' : 'btn-outline-light'"
                  @click="activeTab = 'document'"
                >
                  <i class="bi bi-upload me-1"></i>
                  <span>Upload Document</span>
                </button>
                <button 
                  class="btn d-flex align-items-center" 
                  :class="activeTab === 'text' ? 'btn-light' : 'btn-outline-light'"
                  @click="activeTab = 'text'"
                >
                  <i class="bi bi-text-paragraph me-1"></i>
                  <span>Paste Text</span>
                </button>
                <button 
                  class="btn d-flex align-items-center" 
                  :class="activeTab === 'url' ? 'btn-light' : 'btn-outline-light'"
                  @click="activeTab = 'url'"
                >
                  <i class="bi bi-link-45deg me-1"></i>
                  <span>From URL</span>
                </button>
              </div>
            </div>
          </div>
          
          <div class="card-body p-3">
            <!-- Error Alert -->
            <div v-if="error" class="alert alert-danger d-flex align-items-center py-2 mb-3" role="alert">
              <i class="bi bi-exclamation-triangle-fill me-2"></i>
              <div class="small">{{ error }}</div>
            </div>

            <!-- Single Citation Input -->
            <div v-if="activeTab === 'single'">
              <div class="mb-4">
                <label for="citationInput" class="form-label fw-semibold">Enter a legal citation to validate</label>
                <div class="input-group">
                  <input 
                    type="text" 
                    id="citationInput" 
                    class="form-control form-control-lg" 
                    v-model="citationText"
                    placeholder="e.g., 123 U.S. 456 (2023)"
                    @keyup.enter="validateCitation"
                    :disabled="showLoading"
                  >
                  <button 
                    class="btn btn-primary position-relative" 
                    type="button" 
                    @click="validateCitation"
                    :disabled="!citationText || showLoading || hasActiveRequest"
                  >
                    <span v-if="showLoading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    {{ showLoading ? 'Validating...' : 'Validate' }}
                    <span v-if="hasActiveRequest" class="position-absolute top-0 start-100 translate-middle p-2 bg-danger border border-light rounded-circle">
                      <span class="visually-hidden">Active request</span>
                    </span>
                  </button>
                </div>
                <div class="form-text text-muted mt-1">
                  Example formats: 123 U.S. 456 (2023), 456 F.3d 123, 123 S. Ct. 456
                </div>
              </div>
              
              <div class="row g-3 mb-4">
                <div class="col-md-4">
                  <div class="form-check form-switch">
                    <input 
                      class="form-check-input" 
                      type="checkbox" 
                      id="useEnhanced" 
                      v-model="useEnhanced"
                      :disabled="showLoading"
                    >
                    <label class="form-check-label" for="useEnhanced">
                      <i class="bi bi-shield-check me-1"></i>Enhanced Validation
                    </label>
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="form-check form-switch">
                    <input 
                      class="form-check-input" 
                      type="checkbox" 
                      id="useML" 
                      v-model="useML"
                      :disabled="showLoading"
                    >
                    <label class="form-check-label" for="useML">
                      <i class="bi bi-robot me-1"></i>ML Analysis
                    </label>
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="form-check form-switch">
                    <input 
                      class="form-check-input" 
                      type="checkbox" 
                      id="useCorrection" 
                      v-model="useCorrection"
                      :disabled="isLoading"
                    >
                    <label class="form-check-label" for="useCorrection">
                      <i class="bi bi-lightbulb me-1"></i>Suggest Corrections
                    </label>
                  </div>
                </div>
              </div>
              
              <!-- Results Tabs -->
              <div v-if="(validationResult || mlResult || correctionResult)" class="mt-3">
                <ul class="nav nav-tabs nav-fill" id="resultsTabs" role="tablist">
                  <li class="nav-item" role="presentation">
                    <button 
                      class="nav-link py-1 px-2" 
                      :class="{ 'active': activeResultTab === 'validation' }"
                      @click="activeResultTab = 'validation'"
                    >
                      <i class="bi bi-check2-circle me-1"></i>
                      Validation
                    </button>
                  </li>
                  <li class="nav-item" role="presentation">
                    <button 
                      class="nav-link py-1 px-2" 
                      :class="{ 'active': activeResultTab === 'analysis' }"
                      @click="activeResultTab = 'analysis'"
                    >
                      <i class="bi bi-graph-up me-1"></i>
                      Analysis
                    </button>
                  </li>
                  <li 
                    v-if="correctionResult && correctionResult.suggestions && correctionResult.suggestions.length > 0"
                    class="nav-item" 
                    role="presentation"
                  >
                    <button 
                      class="nav-link py-1 px-2" 
                      :class="{ 'active': activeResultTab === 'suggestions' }"
                      @click="activeResultTab = 'suggestions'"
                    >
                      <i class="bi bi-lightbulb me-1"></i>
                      Suggestions
                      <span class="badge bg-primary ms-1">
                        {{ correctionResult.suggestions.length }}
                      </span>
                    </button>
                  </li>
                </ul>
                
                <div class="border border-top-0 p-3 bg-white">
                  <!-- Validation Tab -->
                  <div v-if="activeResultTab === 'validation' && validationResult" class="small">
                    <div class="d-flex align-items-center mb-3">
                      <i :class="['bi', 'me-2', validationResult.valid ? 'bi-check-circle-fill text-success' : 'bi-exclamation-triangle-fill text-danger']"></i>
                      <div>
                        <h6 class="mb-0">{{ validationResult.valid ? 'Valid Citation' : 'Invalid Citation' }}</h6>
                        <small class="text-muted">{{ validationResult.message || 'Citation validation results' }}</small>
                      </div>
                    </div>
                    
                    <!-- Case Name -->
                    <div v-if="validationResult.details?.caseName && validationResult.details.caseName !== 'N/A'" class="mb-3 p-2 bg-light rounded">
                      <div class="text-muted small mb-1">Case Name</div>
                      <div class="fw-medium">{{ validationResult.details.caseName }}</div>
                    </div>
                    
                    <div class="row g-2 small">
                      <div class="col-6">
                        <div class="text-muted">Type</div>
                        <div>{{ validationResult.details?.type || 'N/A' }}</div>
                      </div>
                      <div class="col-6">
                        <div class="text-muted">Reporter</div>
                        <div>{{ validationResult.details?.reporter || 'N/A' }}</div>
                      </div>
                      <div class="col-6">
                        <div class="text-muted">Volume</div>
                        <div>{{ validationResult.details?.volume || 'N/A' }}</div>
                      </div>
                      <div class="col-6">
                        <div class="text-muted">Page</div>
                        <div>{{ validationResult.details?.page || 'N/A' }}</div>
                      </div>
                      <div class="col-6">
                        <div class="text-muted">Year</div>
                        <div>{{ validationResult.details?.year || 'N/A' }}</div>
                      </div>
                      <div class="col-6">
                        <div class="text-muted">Court</div>
                        <div>{{ validationResult.details?.court || 'N/A' }}</div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Analysis Tab -->
                  <div v-else-if="activeResultTab === 'analysis' && mlResult" class="small">
                    <div class="mb-3">
                      <h6 class="mb-2">Confidence Scores</h6>
                      <div v-for="(score, key) in mlResult.confidenceScores" :key="key" class="mb-2">
                        <div class="d-flex justify-content-between mb-1">
                          <span class="text-capitalize">{{ key.replace(/([A-Z])/g, ' $1').trim() }}</span>
                          <span class="fw-medium">{{ Math.round(score * 100) }}%</span>
                        </div>
                        <div class="progress" style="height: 6px;">
                          <div 
                            class="progress-bar" 
                            :class="getProgressBarClass(score)"
                            role="progressbar" 
                            :style="{ width: `${score * 100}%` }" 
                            :aria-valuenow="score * 100" 
                            aria-valuemin="0" 
                            aria-valuemax="100"
                          ></div>
                        </div>
                      </div>
                    </div>
                    <div v-if="mlResult.explanation">
                      <h6 class="mb-2">Explanation</h6>
                      <p class="mb-0">{{ mlResult.explanation }}</p>
                    </div>
                  </div>
                  
                  <!-- Suggestions Tab -->
                  <div v-else-if="activeResultTab === 'suggestions' && correctionResult?.suggestions" class="small">
                    <div class="list-group list-group-flush">
                      <div 
                        v-for="(suggestion, index) in correctionResult.suggestions" 
                        :key="index"
                        class="list-group-item border-0 px-0 py-2"
                      >
                        <div class="d-flex justify-content-between align-items-start">
                          <div>
                            <h6 class="mb-1">Suggestion {{ index + 1 }}</h6>
                            <p class="mb-1">{{ suggestion.text }}</p>
                            <small class="text-muted">Confidence: {{ Math.round(suggestion.confidence * 100) }}%</small>
                          </div>
                          <button 
                            class="btn btn-sm btn-outline-primary" 
                            @click="applySuggestion(suggestion)"
                          >
                            Apply
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div v-else class="text-muted text-center py-4">
                    <i class="bi bi-info-circle fs-4 d-block mb-2"></i>
                    No results available for the selected tab.
                  </div>
                </div>
              </div>
              
              <!-- Document/Text Analysis Results -->
              <div v-if="(activeTab === 'document' || activeTab === 'text' || activeTab === 'url') && (documentAnalysisResult || textAnalysisResult || urlAnalysisResult)" class="mt-3">
                <div class="card border-0 shadow-sm">
                  <div class="card-header bg-light">
                    <h5 class="mb-0">
                      <i class="bi bi-search me-2"></i>
                      {{ 
                        activeTab === 'document' ? 'Document' : 
                        activeTab === 'text' ? 'Text' : 'URL' 
                      }} Analysis Results
                    </h5>
                  </div>
                  <div class="card-body p-0">
                    <CitationResults 
                      :results="activeTab === 'document' ? documentAnalysisResult : 
                               activeTab === 'text' ? textAnalysisResult : urlAnalysisResult"
                      :loading="isAnalyzing"
                      @citation-click="handleCitationClick"
                    />
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Document Upload Tab -->
            <div v-else-if="activeTab === 'document'">
              <FileUpload 
                @results="handleDocumentResults" 
                @error="handleDocumentError"
                :api-base-url="apiBaseUrl"
              />
              <!-- Document Analysis Results will be shown in the dedicated section below -->
            </div>
            
            <!-- Text Paste Tab -->
            <div v-else-if="activeTab === 'text'">
              <TextPaste 
                @results="handleTextResults" 
                @error="handleTextError"
                :api-base-url="apiBaseUrl"
              />
              <!-- Text Analysis Results will be shown in the dedicated section below -->
            </div>
            
            <!-- URL Upload Tab -->
            <div v-else-if="activeTab === 'url'">
              <UrlUpload 
                @results="handleUrlResults" 
                @error="handleUrlError"
                :api-base-url="apiBaseUrl"
              />
              <!-- URL Analysis Results will be shown in the dedicated section below -->
            </div>
          </div>
        </div>
      </div>
      
      <!-- Results Sidebar -->
      <div v-if="activeTab !== 'document' && activeTab !== 'text' && activeTab !== 'url'" class="col-md-4 mt-4 mt-md-0">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-light">
            <h5 class="mb-0"><i class="bi bi-info-circle me-2"></i>About Citation Validation</h5>
          </div>
          <div class="card-body">
            <h6 class="fw-semibold">What can I validate?</h6>
            <p class="small">
              Our validator supports various legal citation formats including:
            </p>
            <ul class="small">
              <li>U.S. Supreme Court (e.g., 123 U.S. 456)</li>
              <li>Federal Courts (e.g., 456 F.3d 123)</li>
              <li>State Courts (e.g., 123 N.E.2d 456)</li>
              <li>Law Review Articles (e.g., 123 Harv. L. Rev. 456)</li>
            </ul>
            
            <h6 class="fw-semibold mt-4">Enhanced Validation</h6>
            <p class="small">
              When enabled, our system performs additional checks against legal databases to verify:
            </p>
            <ul class="small">
              <li>Case existence and correct citation format</li>
              <li>Parallel citations</li>
              <li>Subsequent history and negative treatment</li>
              <li>Statutory validity</li>
            </ul>
            
            <div class="alert alert-warning small mt-4">
              <i class="bi bi-exclamation-triangle-fill me-2"></i>
              <strong>Note:</strong> This tool is for informational purposes only and should not be considered legal advice.
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Results Display for Document and Text Analysis -->
    <div v-if="(activeTab === 'document' || activeTab === 'text' || activeTab === 'url') && (documentAnalysisResult || textAnalysisResult || urlAnalysisResult)" 
         class="row mt-4">
      <div class="col-12">
        <div class="card border-0 shadow-sm">
          <div class="card-header bg-light d-flex justify-content-between align-items-center">
            <h5 class="mb-0">
              <i :class="['bi', activeTab === 'document' ? 'bi-file-earmark-text' : activeTab === 'text' ? 'bi-text-paragraph' : 'bi-link', 'me-2']"></i>
              {{ 
                activeTab === 'document' ? 'Document Analysis Results' : 
                activeTab === 'text' ? 'Text Analysis Results' : 'URL Analysis Results' 
              }}
            </h5>
            <div class="btn-group">
              <button class="btn btn-sm btn-outline-secondary" @click="copyAllResults">
                <i class="bi bi-clipboard me-1"></i>Copy All
              </button>
              <button class="btn btn-sm btn-outline-secondary" @click="downloadResults">
                <i class="bi bi-download me-1"></i>Download
              </button>
            </div>
          </div>
          <div class="card-body p-0">
            <CitationResults 
              :results="activeTab === 'document' ? documentAnalysisResult : 
                       activeTab === 'text' ? textAnalysisResult : urlAnalysisResult"
              @apply-correction="applyCorrectionFromResults"
              class="border-0"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick, onUnmounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useApi } from '@/composables/useApi';
import { useLoadingState } from '@/composables/useLoadingState';
import api from '@/api/api';

// Components
import FileUpload from '@/components/FileUpload.vue';
import TextPaste from '@/components/TextPaste.vue';
import UrlUpload from '@/components/UrlUpload.vue';
import CitationResults from '@/components/CitationResults.vue';

export default {
  name: 'EnhancedValidator',
  components: {
    FileUpload,
    TextPaste,
    UrlUpload,
    CitationResults
  },
  setup() {
    const route = useRoute();
    const router = useRouter();
    
    // Tabs configuration
    const tabs = [
      { id: 'single', label: 'Single Citation' },
      { id: 'document', label: 'Upload Document' },
      { id: 'text', label: 'Paste Text' },
      { id: 'url', label: 'URL Upload' }
    ];
    
    // State for active tab and UI toggles
    const activeTab = ref('single');
    const activeResultTab = ref('validation');
    const showBasicValidation = ref(true);
    const showMLAnalysis = ref(true);
    const showCorrections = ref(true);
    
    // Feature toggles
    const useEnhanced = ref(true);
    const useML = ref(true);
    const useCorrection = ref(true);
    
    // Single Citation State
    const citationText = ref('');
    const validationResult = ref(null);
    const mlResult = ref(null);
    const correctionResult = ref(null);
    
    // Analysis results
    const documentAnalysisResult = ref(null);
    const textAnalysisResult = ref(null);
    const urlAnalysisResult = ref(null);
    
    // API call with loading and error states
    const { 
      execute: executeApi, 
      data: apiData,
      isLoading,
      error,
      status: apiStatus,
      cancel: cancelValidation
    } = useApi({
      loadingMessage: 'Validating citation...',
      showLoading: true
    });
    
    // Loading state management
    const hasActiveRequest = ref(false);
    const { isLoading: isGlobalLoading } = useLoadingState();
    
    // Combined loading state that considers both API and global loading states
    const showLoading = computed(() => isLoading.value || isGlobalLoading.value || hasActiveRequest.value);
    
    // Clear all results and reset form
    const clearResults = () => {
      validationResult.value = null;
      mlResult.value = null;
      correctionResult.value = null;
      documentAnalysisResult.value = null;
      textAnalysisResult.value = null;
      urlAnalysisResult.value = null;
      error.value = null;
      citationText.value = '';
    };
    
    // Analyze document function
    const analyzeDocument = async (file) => {
      hasActiveRequest.value = true;
      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await api.post('/analyze', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        documentAnalysisResult.value = response.data;
        return response.data;
      } catch (err) {
        console.error('Error analyzing document:', err);
        error.value = 'Failed to analyze document. Please try again.';
        throw err;
      } finally {
        hasActiveRequest.value = false;
      }
    };
    
    // Analyze text function
    const analyzeText = async (text) => {
      hasActiveRequest.value = true;
      try {
        const response = await api.post('/analyze', { text });
        textAnalysisResult.value = response.data;
        return response.data;
      } catch (err) {
        console.error('Error analyzing text:', err);
        error.value = 'Failed to analyze text. Please try again.';
        throw err;
      } finally {
        hasActiveRequest.value = false;
      }
    };
    
    // Analyze URL function
    const analyzeUrl = async (url) => {
      hasActiveRequest.value = true;
      try {
        const response = await api.post('/analyze', { url });
        urlAnalysisResult.value = response.data;
        return response.data;
      } catch (err) {
        console.error('Error analyzing URL:', err);
        error.value = 'Failed to analyze URL. Please try again.';
        throw err;
      } finally {
        hasActiveRequest.value = false;
      }
    };
    
    // Create a post request function
    const executePostRequest = async (data, options = {}) => {
      hasActiveRequest.value = true;
      try {
        const response = await executeApi(
          async () => {
            const response = await api.post('/verify-citation', data, {
              ...options,
              headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
              }
            });
            return response;
          },
          options
        );
        return response;
      } finally {
        hasActiveRequest.value = false;
      }
    };
    
    // Wrap the post request to handle success/error
    const validateCitationApi = async (data) => {
      hasActiveRequest.value = true;
      try {
        console.log('Sending validation request with data:', data);
        const response = await executePostRequest(data, {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        });
        console.log('Received validation response:', response);
        
        // Handle the response structure properly
        if (response && typeof response === 'object') {
          // If the response already has a data property, use it as is
          // Otherwise, wrap the response in a data property for consistency
          const responseData = response.data !== undefined ? response : { data: response };
          handleValidationSuccess(responseData);
          return responseData;
        }
        
        // If we get here, the response format is unexpected
        throw new Error('Unexpected response format from server');
      } catch (err) {
        console.error('Error in validateCitationApi:', err);
        handleValidationError(err);
        throw err;
      } finally {
        hasActiveRequest.value = false;
      }
    };
    
    // Helper functions for validation display
    const getValidationIcon = (isValid) => {
      return isValid ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill';
    };
    
    const getValidationColor = (isValid) => {
      return isValid ? 'success' : 'danger';
    };
    
    const getValidationLabel = (isValid) => {
      return isValid ? 'Valid' : 'Invalid';
    };
    
    const getCorrectionIcon = (correction) => {
      if (!correction) return '';
      return correction.suggested_correction ? 'bi-lightbulb' : 'bi-check';
    };
    
    const getCorrectionColor = (correction) => {
      if (!correction) return 'secondary';
      return correction.suggested_correction ? 'warning' : 'success';
    };
    
    const getCorrectionLabel = (correction) => {
      if (!correction) return 'No correction';
      return correction.suggested_correction ? 'Suggested' : 'Correct';
    };
    
    const getMLLabel = (mlResult) => {
      if (!mlResult) return 'N/A';
      return mlResult.prediction || 'Unknown';
    };
    
    const getMLColor = (mlResult) => {
      if (!mlResult) return 'secondary';
      return mlResult.confidence > 0.7 ? 'success' : 'warning';
    };
    
    const getMLIcon = (mlResult) => {
      if (!mlResult) return 'bi-question-circle';
      return mlResult.confidence > 0.7 ? 'bi-check-circle' : 'bi-exclamation-circle';
    };
    
    // Cancel any pending requests when component unmounts
    onUnmounted(() => {
      if (hasActiveRequest.value) {
        cancelValidation();
      }
    });
    
    // API Base URL - Get from environment or use relative path
    const apiBaseUrl = ref(import.meta.env.VITE_API_BASE_URL || '');
    
    // Handle document analysis results
    const handleDocumentResults = (results) => {
      console.log('Document analysis results:', results);
      documentAnalysisResult.value = results;
      isLoading.value = false;
      error.value = null;
      
      // Scroll to results after a short delay to ensure DOM is updated
      setTimeout(() => {
        const resultsElement = document.querySelector('.results-section');
        if (resultsElement) {
          resultsElement.scrollIntoView({ behavior: 'smooth' });
        }
        const analysisResultsElement = document.querySelector('.analysis-results');
        if (analysisResultsElement) {
          analysisResultsElement.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    };
    
    // Handle text analysis results
    const handleTextResults = (results) => {
      console.log('Text analysis results:', results);
      textAnalysisResult.value = results;
      // Scroll to results
      setTimeout(() => {
        const resultsElement = document.querySelector('.results-section');
        if (resultsElement) {
          resultsElement.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    };
    

    // Handle document analysis errors
    const handleDocumentError = (error) => {
      console.error('Document analysis error:', error);
      documentAnalysisResult.value = { 
        error: error.message || 'An error occurred while analyzing the document',
        timestamp: new Date().toISOString()
      };
    };
    

    // Recent validations history
    const recentValidations = ref([]);
    
    // Load recent validations from local storage
    const loadRecentValidations = () => {
      try {
        const saved = localStorage.getItem('recentValidations');
        if (saved) {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed)) {
            // Ensure we have valid data
            recentValidations.value = parsed
              .filter(item => item && item.citation && typeof item.isValid === 'boolean')
              .slice(0, 10); // Only keep up to 10 items
            
            // Update localStorage with cleaned data if needed
            if (recentValidations.value.length !== parsed.length) {
              localStorage.setItem('recentValidations', JSON.stringify(recentValidations.value));
            }
          }
        }
      } catch (err) {
        console.error('Error loading recent validations:', err);
        // Clear invalid data
        try {
          localStorage.removeItem('recentValidations');
        } catch (e) {
          console.error('Failed to clear invalid recent validations:', e);
        }
        recentValidations.value = [];
      }
    };
    
    // Handle route changes
    const handleRouteChange = () => {
      // Handle tab parameter
      if (route.query.tab) {
        const validTabs = ['single', 'document', 'text', 'url'];
        if (validTabs.includes(route.query.tab)) {
          activeTab.value = route.query.tab;
        }
      }
      
      // Handle citation parameter
      if (route.query.citation) {
        citationText.value = route.query.citation;
        activeTab.value = 'single';
        // Auto-validate if citation is provided
        if (citationText.value.trim()) {
          validateCitation();
        }
      }
    };
    
    // Watch for route changes
    watch(() => route.query, (newQuery, oldQuery) => {
      if (JSON.stringify(newQuery) !== JSON.stringify(oldQuery)) {
        handleRouteChange();
      }
    });
    
    // Initial setup
    onMounted(() => {
      // Load recent validations first
      loadRecentValidations();
      
      // Then handle route parameters
      nextTick(handleRouteChange);
    });
    
    // Helper function to get alert class based on validity
    const getAlertClass = (isValid) => {
      if (isValid === undefined || isValid === null) return 'alert-info';
      return isValid ? 'alert-success' : 'alert-danger';
    };
    
    // Helper function to get confidence class for badges and progress bars
    const getConfidenceClass = (confidence) => {
      if (confidence >= 0.8) return 'bg-success';
      if (confidence >= 0.5) return 'bg-warning';
      return 'bg-danger';
    };
    
    // Helper function to get progress bar color based on value
    const getProgressBarClass = (value) => {
      if (value >= 0.8) return 'bg-success';
      if (value >= 0.5) return 'bg-info';
      if (value >= 0.3) return 'bg-warning';
      return 'bg-danger';
    };
    
    // Format citation for display
    const formatCitation = (citation) => {
      if (!citation) return '';
      // Add any formatting logic here
      return citation;
    };
    
    // Process validation response from API
    const processValidationResponse = (response) => {
      try {
        console.log('Processing validation response:', response);
        
        // Reset results
        validationResult.value = null;
        mlResult.value = null;
        correctionResult.value = null;
        error.value = null;
        
        // Safely get the response data with fallbacks
        const data = response?.data || response || {};
        console.log('Response data:', data);
        
        // Extract citation parts from the API response
        const citationParts = data.details?.citation_parts || {};
        const metadata = data.metadata || {};
        
        // Set validation results if available
        if (data.verified !== undefined) {
          validationResult.value = {
            valid: data.verified,
            message: data.verified ? 'Citation is valid' : 'Citation is not valid',
            details: {
              type: metadata.case_name ? 'Case' : 'N/A',
              reporter: citationParts.reporter || 'N/A',
              volume: citationParts.volume || 'N/A',
              page: citationParts.page || 'N/A',
              year: data.details?.date_filed ? new Date(data.details.date_filed).getFullYear() : 'N/A',
              court: data.details?.court || 'N/A',
              caseName: metadata.case_name || 'N/A',
              docketNumber: data.details?.docket_number || 'N/A',
              citation: data.citation || 'N/A'
            },
            metadata: metadata
          };
        }
        
        // Handle any error message from the response
        if (data.error) {
          error.value = data.error;
        }
        
        // Set ML results if available (not in current backend response but keeping for compatibility)
        if (data.ml_analysis) {
          mlResult.value = {
            prediction: data.ml_analysis.prediction,
            confidence: data.ml_analysis.confidence,
            is_valid: data.ml_analysis.is_valid,
            details: data.ml_analysis.explanation || 'No ML analysis available'
          };
        }
        
        // Set correction suggestions if available (not in current backend response but keeping for compatibility)
        if (data.corrections?.suggestions?.length) {
          correctionResult.value = {
            suggestions: data.corrections.suggestions.map((suggestion, index) => ({
              id: `suggestion-${index}`,
              corrected_text: suggestion.corrected_text,
              explanation: suggestion.explanation || 'No explanation provided',
              confidence: suggestion.confidence || 0
            }))
          };
        }
      } catch (err) {
        console.error('Error processing validation response:', err);
        error.value = 'Failed to process validation response. Please try again.';
      }
    }
    
    // Handle successful validation response
    function handleValidationSuccess(response) {
      console.log('API Response:', JSON.stringify(response, null, 2)); // Log the full response
      
      try {
        processValidationResponse(response);
        
        // Safely get the verification status with fallbacks
        const isVerified = response?.data?.verified || false;
        addToRecentValidations(citationText.value.trim(), isVerified);
      } catch (err) {
        console.error('Error in handleValidationSuccess:', err);
        error.value = 'Error processing validation response. Please try again.';
      } finally {
        // Reset active request flag
        hasActiveRequest.value = false;
      }
    }
    
    // Handle validation error
    function handleValidationError(err) {
      console.error('Error validating citation:', err);
      error.value = err.message || 'Failed to validate citation. Please try again.';
      hasActiveRequest.value = false;
    }
    
    // Validation Methods
    const validateCitation = async () => {
      if (!citationText.value.trim() || hasActiveRequest.value) return;
      
      // Reset states
      error.value = null;
      validationResult.value = null;
      mlResult.value = null;
      correctionResult.value = null;
      
      // Reset UI states
      showBasicValidation.value = true;
      showMLAnalysis.value = true;
      showCorrections.value = true;
      
      // Set active request flag
      hasActiveRequest.value = true;
      
      try {
        // Make the API call using the API utility
        await validateCitationApi({
          citation: citationText.value.trim(),
          enhanced: useEnhanced.value,
          use_ml: useML.value,
          suggest_corrections: useCorrection.value
        });
      } catch (err) {
        // Error is already handled by the error handler
        console.error('Unexpected error in validateCitation:', err);
      }
    };
    
    // Apply correction to citation input
    const applyCorrection = (correctedText) => {
      if (correctedText) {
        citationText.value = correctedText;
        // Optionally re-validate with the corrected text
        validateCitation();
      }
    };
    
    
    // Copy results to clipboard
    const copyResults = () => {
      const results = [];
      
      if (validationResult.value) {
        results.push('=== VALIDATION ===');
        results.push(`Status: ${validationResult.value.valid ? 'Valid' : 'Invalid'}`);
        if (validationResult.value.message) {
          results.push(`Message: ${validationResult.value.message}`);
        }
      }
      
      if (mlResult.value) {
        results.push('\n=== ML ANALYSIS ===');
        results.push(`Prediction: ${mlResult.value.prediction || 'N/A'}`);
        results.push(`Confidence: ${(mlResult.value.confidence * 100).toFixed(2)}%`);
        if (mlResult.value.details) {
          results.push(`Details: ${mlResult.value.details}`);
        }
      }
      
      if (correctionResult.value?.suggestions?.length) {
        results.push('\n=== SUGGESTED CORRECTIONS ===');
        correctionResult.value.suggestions.forEach((suggestion, index) => {
          results.push(`\nSuggestion ${index + 1}: ${suggestion.corrected_text}`);
          results.push(`   ${suggestion.explanation}`);
        });
      }
      
      const textToCopy = results.join('\n');
      
      navigator.clipboard.writeText(textToCopy).then(() => {
        // Show success message (you might want to use a toast notification here)
        console.log('Results copied to clipboard');
      }).catch(err => {
        console.error('Failed to copy results:', err);
      });
    };
    
    // Download results as a text file
    const downloadResults = () => {
      const results = [];
      
      results.push('CaseStrainer - Citation Validation Results\n');
      results.push(`Citation: ${citationText.value}\n`);
      results.push(`Validated on: ${new Date().toLocaleString()}\n`);
      
      if (validationResult.value) {
        results.push('\n=== VALIDATION ===');
        results.push(`Status: ${validationResult.value.valid ? 'Valid' : 'Invalid'}`);
        if (validationResult.value.message) {
          results.push(`Message: ${validationResult.value.message}`);
        }
        
        if (validationResult.value.details && Object.keys(validationResult.value.details).length > 0) {
          results.push('\nDetails:');
          Object.entries(validationResult.value.details).forEach(([key, value]) => {
            results.push(`- ${key.replace(/([A-Z])/g, ' $1').trim()}: ${value}`);
          });
        }
      }
      
      if (mlResult.value) {
        results.push('\n=== ML ANALYSIS ===');
        results.push(`Prediction: ${mlResult.value.prediction || 'N/A'}`);
        results.push(`Confidence: ${(mlResult.value.confidence * 100).toFixed(2)}%`);
        if (mlResult.value.details) {
          results.push(`\nAnalysis:\n${mlResult.value.details}`);
        }
      }
      
      if (correctionResult.value?.suggestions?.length) {
        results.push('\n=== SUGGESTED CORRECTIONS ===');
        correctionResult.value.suggestions.forEach((suggestion, index) => {
          results.push(`\nSuggestion ${index + 1}:`);
          results.push(`- Corrected Text: ${suggestion.corrected_text}`);
          results.push(`- Explanation: ${suggestion.explanation}`);
          if (suggestion.confidence) {
            results.push(`- Confidence: ${(suggestion.confidence * 100).toFixed(2)}%`);
          }
        });
      }
      
      const blob = new Blob([results.join('\n')], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `casestrainer-results-${new Date().toISOString().slice(0, 10)}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    };
    
    // Copy all results from document/text analysis
    const copyAllResults = () => {
      const results = activeTab.value === 'document' ? documentAnalysisResult : 
                     activeTab.value === 'text' ? textAnalysisResult : urlAnalysisResult;
      if (!results) return;
      
      const textToCopy = JSON.stringify(results, null, 2);
      navigator.clipboard.writeText(textToCopy).then(() => {
        console.log('All results copied to clipboard');
      }).catch(err => {
        console.error('Failed to copy results:', err);
      });
    };
    
    // Handle file upload results
    const handleFileUploaded = (results) => {
      documentAnalysisResult.value = results;
      isLoading.value = false;
      error.value = null;
      
      // Scroll to results after a short delay to ensure DOM is updated
      setTimeout(() => {
        const resultsElement = document.querySelector('.analysis-results');
        if (resultsElement) {
          resultsElement.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    };
    
    // Handle text submission results
    const handleTextSubmitted = (results) => {
      textAnalysisResult.value = results;
      isLoading.value = false;
      error.value = null;
      
      // Scroll to results after a short delay to ensure DOM is updated
      setTimeout(() => {
        const resultsElement = document.querySelector('.analysis-results');
        if (resultsElement) {
          resultsElement.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    };
    
    // Handle general errors
    const handleError = (error, context = 'validation') => {
      console.error(`Error during ${context}:`, error);
      error.value = error.message || `An error occurred during ${context}. Please try again.`;
      isLoading.value = false;
      
      // Clear any existing results
      if (context === 'document') {
        documentAnalysisResult.value = null;
      } else if (context === 'text') {
        textAnalysisResult.value = null;
      } else {
        validationResult.value = null;
        mlResult.value = null;
        correctionResult.value = null;
      }
    };
    
    // Handle text analysis errors
    const handleTextError = (error) => {
      console.error('Text analysis error:', error);
      textAnalysisResult.value = { 
        error: error.message || 'An error occurred while analyzing the text',
        timestamp: new Date().toISOString()
      };
      isLoading.value = false;
    };
    
    // Handle URL analysis results
    const handleUrlResults = (results) => {
      urlAnalysisResult.value = results;
      isLoading.value = false;
      error.value = null;
      
      // Scroll to results after a short delay to ensure DOM is updated
      setTimeout(() => {
        const resultsElement = document.querySelector('.analysis-results');
        if (resultsElement) {
          resultsElement.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    };
    
    // Handle URL analysis errors
    const handleUrlError = (error) => {
      console.error('URL analysis error:', error);
      urlAnalysisResult.value = { 
        error: error.message || 'An error occurred while analyzing the URL',
        timestamp: new Date().toISOString()
      };
      isLoading.value = false;
    };
    
    // Apply correction from results
    const applyCorrectionFromResults = (correction) => {
      if (activeTab.value === 'single') {
        citationText.value = correction;
        validateCitation();
      } else if (activeTab.value === 'document' && documentAnalysisResult.value?.citations) {
        // Find and update the citation in document results
        const updatedCitations = documentAnalysisResult.value.citations.map(citation => {
          if (citation.original === correction.original) {
            return { ...citation, ...correction };
          }
          return citation;
        });
        documentAnalysisResult.value = { ...documentAnalysisResult.value, citations: updatedCitations };
      } else if (activeTab.value === 'text' && textAnalysisResult.value?.citations) {
        // Find and update the citation in text results
        const updatedCitations = textAnalysisResult.value.citations.map(citation => {
          if (citation.original === correction.original) {
            return { ...citation, ...correction };
          }
          return citation;
        });
        textAnalysisResult.value = { ...textAnalysisResult.value, citations: updatedCitations };
      }
    };
    
    // Load a recent validation by index
    const loadRecentValidation = (index) => {
      if (recentValidations.value && recentValidations.value[index]) {
        const validation = recentValidations.value[index];
        validationResult.value = validation.result;
        citationText.value = validation.citation || '';
        activeTab.value = 'single';
        
        // Scroll to the top of the results
        setTimeout(() => {
          const resultsElement = document.querySelector('.analysis-results');
          if (resultsElement) {
            resultsElement.scrollIntoView({ behavior: 'smooth' });
          }
        }, 100);
      }
    };
    
    // Clear recent validations
    const clearRecent = () => {
      recentValidations.value = [];
      // Optionally clear from localStorage as well
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem('recentValidations');
      }
    };
    
    // Make sure all functions are defined before returning them
    const addToRecentValidations = (citation, isValid) => {
      try {
        const newItem = { citation, isValid, timestamp: new Date().toISOString() };
        const current = [...recentValidations.value];
        
        // Remove if already exists (to update its position)
        const existingIndex = current.findIndex(item => item.citation === citation);
        if (existingIndex !== -1) {
          current.splice(existingIndex, 1);
        }
        
        // Add to beginning
        current.unshift(newItem);
        
        // Keep only the last 10 items
        recentValidations.value = current.slice(0, 10);
        
        // Save to localStorage
        localStorage.setItem('recentValidations', JSON.stringify(recentValidations.value));
      } catch (err) {
        console.error('Error adding to recent validations:', err);
      }
    };

    // Clear recent validations
    const clearRecentValidations = () => {
      recentValidations.value = [];
      try {
        localStorage.removeItem('recentValidations');
      } catch (e) {
        console.error('Failed to clear recent validations:', e);
      }
    };

    // Remove a specific validation from recent validations by index
    const removeRecentValidation = (index) => {
      if (recentValidations.value && recentValidations.value[index]) {
        recentValidations.value.splice(index, 1);
        try {
          localStorage.setItem('recentValidations', JSON.stringify(recentValidations.value));
        } catch (e) {
          console.error('Failed to update recent validations:', e);
        }
      }
    };

    // Copy text to clipboard
    const copyToClipboard = (text) => {
      if (!text) return;
      navigator.clipboard.writeText(text).then(() => {
        // Optional: show a success message
      }).catch(err => {
        console.error('Failed to copy text:', err);
      });
    };

    // Format date for display
    const formatDate = (dateString) => {
      if (!dateString) return '';
      try {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          hour12: true
        }).format(date);
      } catch (e) {
        console.error('Error formatting date:', e);
        return dateString || '';
      }
    };

    return {
      // State
      activeTab,
      activeResultTab,
      citationText,
      validationResult,
      mlResult,
      correctionResult,
      documentAnalysisResult,
      textAnalysisResult,
      recentValidations,
      error,
      isLoading,
      showLoading,
      hasActiveRequest,
      useEnhanced,
      useML,
      useCorrection,
      showBasicValidation,
      showMLAnalysis,
      showCorrections,
      apiBaseUrl,
      
      // Methods
      handleValidationSuccess,
      handleValidationError,
      validateCitation,
      analyzeDocument,
      analyzeText,
      clearResults,
      copyToClipboard,
      formatDate,
      getCorrectionLabel,
      getMLLabel,
      getMLColor,
      getMLIcon,
      loadRecentValidations,
      addToRecentValidations,
      removeRecentValidation,
      clearRecentValidations,
      handleRouteChange,
      handleDocumentResults,
      handleDocumentError,
      handleTextError
    };
  }
};
</script>

<style scoped>
.enhanced-validator {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.tabs-container {
  margin-top: 20px;
}

.tabs {
  display: flex;
  border-bottom: 1px solid #dee2e6;
  margin-bottom: 20px;
}

.tab {
  padding: 10px 20px;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  font-weight: 500;
  color: #6c757d;
  transition: all 0.3s ease;
}

.tab:hover {
  color: #0d6efd;
  border-bottom-color: #0d6efd;
}

.tab.active {
  color: #0d6efd;
  border-bottom-color: #0d6efd;
  font-weight: 600;
}

.tab-pane {
  padding: 20px 0;
}

.alert {
  padding: 1rem;
  margin-bottom: 1rem;
  border: 1px solid transparent;
  border-radius: 0.25rem;
}

.alert-success {
  color: #0f5132;
  background-color: #d1e7dd;
  border-color: #badbcc;
}

.alert-danger {
  color: #842029;
  background-color: #f8d7da;
  border-color: #f5c2c7;
}

.alert-warning {
  color: #664d03;
  background-color: #fff3cd;
  border-color: #ffecb5;
}

.alert-info {
  color: #055160;
  background-color: #cff4fc;
  border-color: #b6effb;
}

.form-control {
  display: block;
  width: 100%;
  padding: 0.375rem 0.75rem;
  font-size: 1rem;
  font-weight: 400;
  line-height: 1.5;
  color: #212529;
  background-color: #fff;
  background-clip: padding-box;
  border: 1px solid #ced4da;
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  border-radius: 0.25rem;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-control:focus {
  color: #212529;
  background-color: #fff;
  border-color: #86b7fe;
  outline: 0;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.btn {
  display: inline-block;
  font-weight: 400;
  line-height: 1.5;
  color: #212529;
  text-align: center;
  text-decoration: none;
  vertical-align: middle;
  cursor: pointer;
  -webkit-user-select: none;
  -moz-user-select: none;
  user-select: none;
  background-color: transparent;
  border: 1px solid transparent;
  padding: 0.375rem 0.75rem;
  font-size: 1rem;
  border-radius: 0.25rem;
  transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.btn-primary {
  color: #fff;
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.btn-primary:hover {
  color: #fff;
  background-color: #0b5ed7;
  border-color: #0a58ca;
}

.btn:disabled, .btn[disabled] {
  opacity: 0.65;
  pointer-events: none;
}

.card {
  position: relative;
  display: flex;
  flex-direction: column;
  min-width: 0;
  word-wrap: break-word;
  background-color: #fff;
  background-clip: border-box;
  border: 1px solid rgba(0, 0, 0, 0.125);
  border-radius: 0.25rem;
  margin-bottom: 1.5rem;
}

.card-header {
  padding: 0.5rem 1rem;
  margin-bottom: 0;
  background-color: rgba(0, 0, 0, 0.03);
  border-bottom: 1px solid rgba(0, 0, 0, 0.125);
}

.card-header:first-child {
  border-radius: calc(0.25rem - 1px) calc(0.25rem - 1px) 0 0;
}

.card-body {
  flex: 1 1 auto;
  padding: 1rem 1rem;
}

.bg-primary {
  background-color: #0d6efd !important;
  color: white;
}

.text-white {
  color: white !important;
}

.mb-0 {
  margin-bottom: 0 !important;
}

.mb-3 {
  margin-bottom: 1rem !important;
}

.mt-4 {
  margin-top: 1.5rem !important;
}

.form-label {
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-check {
  display: block;
  min-height: 1.5rem;
  padding-left: 1.5em;
  margin-bottom: 0.125rem;
}

.form-check .form-check-input {
  float: left;
  margin-left: -1.5em;
}

.form-check-input {
  width: 1em;
  height: 1em;
  margin-top: 0.25em;
  vertical-align: top;
  background-color: #fff;
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
  border: 1px solid rgba(0, 0, 0, 0.25);
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  -webkit-print-color-adjust: exact;
  color-adjust: exact;
}

.form-check-input[type=checkbox] {
  border-radius: 0.25em;
}

.form-check-input:checked {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.form-switch .form-check-input {
  width: 2em;
  margin-left: -2.5em;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='-4 -4 8 8'%3e%3ccircle r='3' fill='rgba%280, 0, 0, 0.25%29'/%3e%3c/svg%3e");
  background-position: left center;
  border-radius: 2em;
  transition: background-position 0.15s ease-in-out;
}

.form-switch .form-check-input:checked {
  background-position: right center;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='-4 -4 8 8'%3e%3ccircle r='3' fill='%23fff'/%3e%3c/svg%3e");
}

.list-group {
  display: flex;
  flex-direction: column;
  padding-left: 0;
  margin-bottom: 0;
  border-radius: 0.25rem;
}

.list-group-item {
  position: relative;
  display: block;
  padding: 0.5rem 1rem;
  color: #212529;
  text-decoration: none;
  background-color: #fff;
  border: 1px solid rgba(0, 0, 0, 0.125);
}

.list-group-item:first-child {
  border-top-left-radius: inherit;
  border-top-right-radius: inherit;
}

.list-group-item:last-child {
  border-bottom-right-radius: inherit;
  border-bottom-left-radius: inherit;
}

.list-group-item + .list-group-item {
  border-top-width: 0;
}

.list-group-item + .list-group-item {
  margin-top: -1px;
}

.spinner-border {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  vertical-align: -0.125em;
  border: 0.2em solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  -webkit-animation: 0.75s linear infinite spinner-border;
  animation: 0.75s linear infinite spinner-border;
}

@keyframes spinner-border {
  to { transform: rotate(360deg); }
}

@-webkit-keyframes spinner-border {
  to { -webkit-transform: rotate(360deg); }
}

.me-2 {
  margin-right: 0.5rem !important;
}

pre {
  margin-top: 0;
  margin-bottom: 1rem;
  overflow: auto;
  -ms-overflow-style: scrollbar;
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
  font-family: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}
</style>
