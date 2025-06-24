<template>
  <div class="enhanced-validator container-fluid py-3">
    <div class="row">
      <div class="col-12">
        <h2 class="mb-4">Citation Validator</h2>
        
        <!-- Tabs Navigation -->
        <ul class="nav nav-tabs mb-4" role="tablist">
          <li v-for="tab in tabs" :key="tab.id" class="nav-item" role="presentation">
            <button
              class="nav-link"
              :class="{ active: activeTab === tab.id }"
              @click="activeTab = tab.id"
              type="button"
              role="tab"
              :aria-selected="activeTab === tab.id"
            >
              {{ tab.label }}
            </button>
          </li>
        </ul>

        <!-- Tab Content -->
        <div class="tab-content p-3 border border-top-0 rounded-bottom">
          <!-- Single Citation Tab -->
          <div v-if="activeTab === 'single'" class="tab-pane fade show active">
            <div class="mb-3">
              <label for="citationInput" class="form-label">Enter Citation</label>
              <div class="input-group">
                <input
                  type="text"
                  class="form-control"
                  id="citationInput"
                  v-model="citationInput"
                  placeholder="e.g., 410 U.S. 113 (1973)"
                  @keyup.enter="validateCitation(citationInput)"
                >
                <button
                  class="btn btn-primary"
                  type="button"
                  @click="validateCitation(citationInput)"
                  :disabled="!citationInput.trim() || isLoading"
                >
                  <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  {{ isLoading ? 'Validating...' : 'Validate' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Document Upload Tab -->
          <div v-else-if="activeTab === 'document'" class="tab-pane fade show active">
            <FileUpload
              @results="handleDocumentResults"
              @error="handleDocumentError"
              @progress="handleDocumentProgress"
              :is-loading="isLoading"
              @loading="isLoading = $event"
            />
          </div>

          <!-- Text Paste Tab -->
          <div v-else-if="activeTab === 'text'" class="tab-pane fade show active">
            <TextPaste
              @results="handleTextResults"
              @error="handleTextError"
              @progress="handleTextProgress"
              :is-loading="isLoading"
              @loading="isLoading = $event"
            />
          </div>

          <!-- URL Upload Tab -->
          <div v-else-if="activeTab === 'url'" class="tab-pane fade show active">
            <UrlUpload
              @results="handleUrlResults"
              @error="handleUrlError"
              @progress="handleUrlProgress"
              :is-loading="isLoading"
              @loading="isLoading = $event"
            />
          </div>
        </div>

        <!-- Results Section -->
        <div v-if="activeTab === 'single'">
          <CitationResults
            v-if="validationResult && validationResult.citations && validationResult.citations.length"
            :results="validationResult"
            :active-tab="activeTab"
            @apply-correction="applyCorrection"
            @copy-results="copyResults"
            @download-results="downloadResults"
          />
          <div v-else-if="showLoading" class="alert alert-info mt-4 d-flex align-items-center justify-content-center">
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Analysis in progress... Please wait.
          </div>
          <div v-else class="alert alert-info mt-4">
            No results to display. Please enter a citation and click Analyze.
          </div>
        </div>

        <!-- Document Upload Results -->
        <div v-else-if="activeTab === 'document'">
          <CitationResults
            v-if="documentAnalysisResult && documentAnalysisResult.citations && documentAnalysisResult.citations.length"
            :results="documentAnalysisResult"
            :active-tab="activeTab"
            @apply-correction="applyCorrection"
            @copy-results="copyResults"
            @download-results="downloadResults"
          />
          <div v-else-if="showLoading" class="alert alert-info mt-4 d-flex align-items-center justify-content-center">
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Analysis in progress... Please wait.
          </div>
          <div v-else class="alert alert-info mt-4">
            No results to display. Please upload a document and wait for analysis.
          </div>
        </div>

        <!-- Text Paste Results -->
        <div v-else-if="activeTab === 'text'">
          <CitationResults
            v-if="textAnalysisResult && textAnalysisResult.citations && textAnalysisResult.citations.length"
            :results="textAnalysisResult"
            :active-tab="activeTab"
            @apply-correction="applyCorrection"
            @copy-results="copyResults"
            @download-results="downloadResults"
          />
          <div v-else-if="showLoading" class="alert alert-info mt-4 d-flex align-items-center justify-content-center">
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Analysis in progress... Please wait.
          </div>
          <div v-else class="alert alert-info mt-4">
            No results to display. Please paste text and wait for analysis.
          </div>
        </div>

        <!-- URL Upload Results -->
        <div v-else-if="activeTab === 'url'">
          <CitationResults
            v-if="urlAnalysisResult && urlAnalysisResult.citations && urlAnalysisResult.citations.length"
            :results="urlAnalysisResult"
            :active-tab="activeTab"
            @apply-correction="applyCorrection"
            @copy-results="copyResults"
            @download-results="downloadResults"
          />
          <div v-else-if="showLoading" class="alert alert-info mt-4 d-flex align-items-center justify-content-center">
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Analysis in progress... Please wait.
          </div>
          <div v-else class="alert alert-info mt-4">
            No results to display. Please enter a URL and wait for analysis.
          </div>
        </div>

        <!-- Recent Validations -->
        <div v-if="false && recentValidations.length > 0" class="mt-5">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h5>Recent Validations</h5>
            <button class="btn btn-sm btn-outline-danger" @click="clearRecentValidations">
              Clear All
            </button>
          </div>
          <ul class="list-group">
            <li v-for="item in recentValidations" :key="item.id" class="list-group-item d-flex justify-content-between align-items-center">
              <div>
                <span class="fw-bold">{{ item.citation }}</span>
                <span
                  v-if="item.result && item.result.citations && item.result.citations.length"
                  class="badge ms-2"
                  :class="isCitationValid(item.result.citations[0]) ? 'bg-success' : 'bg-danger'"
                >
                  {{ isCitationValid(item.result.citations[0]) ? 'Valid' : 'Invalid' }}
                </span>
              </div>
              <div>
                <button class="btn btn-sm btn-outline-secondary me-1" @click="copyToClipboard(item.citation, 'Citation copied!')">
                  <i class="bi bi-clipboard"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" @click="removeRecentValidation(item.id)">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </li>
          </ul>
        </div>

        <!-- Processing Overlay -->
        <div v-if="showLoading" class="processing-overlay">
          <ProcessingProgress
            v-if="showLoading"
            :elapsed-time="elapsedTime"
            :remaining-time="remainingTime"
            :total-progress="totalProgress"
            :current-step="currentStep"
            :current-step-progress="currentStepProgress"
            :processing-steps="processingSteps"
            :actual-times="actualTimes"
            :citation-info="citationInfo"
            :rate-limit-info="rateLimitInfo"
            :timeout="timeout"
            :error="processingError"
            :can-retry="canRetry"
            @retry="retryProcessing"
          />
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
import citationsApi from '@/api/citations';  // Import the citations API module
import { useProcessingTime } from '../composables/useProcessingTime';
import ProcessingProgress from '../components/ProcessingProgress.vue';

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
    CitationResults,
    ProcessingProgress
  },
  setup() {
    // ===== REACTIVE STATE =====
    // Router and route
    const route = useRoute();
    const router = useRouter();
    
    // UI State
    const tabs = [
      { id: 'single', label: 'Single Citation' },
      { id: 'document', label: 'Upload Document' },
      { id: 'text', label: 'Paste Text' },
      { id: 'url', label: 'URL Upload' }
    ];
    
    const activeTab = ref('single');
    const activeResultTab = ref('validation');
    const showBasicValidation = ref(true);
    const showMLAnalysis = ref(true);
    const showCorrections = ref(true);
    
    // Feature Toggles
    const useEnhanced = ref(true);
    const useML = ref(true);
    const useCorrection = ref(true);
    
    // Data State
    const citationInput = ref('');  // For single citation input
    const citationText = ref('');    // For text paste content
    const validationResult = ref(null);
    const mlResult = ref(null);
    const correctionResult = ref(null);
    const documentAnalysisResult = ref(null);
    const textAnalysisResult = ref(null);
    const urlAnalysisResult = ref(null);
    const recentValidations = ref([]);
    const suggestions = ref([]);     // For storing correction suggestions
    const error = ref(null);         // For error messages
    
    // API State
    const { 
      execute: executeApi, 
      data: apiData,
      isLoading,
      error: apiError,
      status: apiStatus,
      cancel: cancelValidation
    } = useApi({
      loadingMessage: 'Validating citation...',
      showLoading: true
    });
    
    const hasActiveRequest = ref(false);
    const { isLoading: isGlobalLoading } = useLoadingState();
    const showLoading = computed(() => isLoading.value || isGlobalLoading.value || hasActiveRequest.value);
    const apiBaseUrl = ref(import.meta.env.VITE_API_BASE_URL || '');

    // Composables
    const {
      elapsedTime,
      remainingTime,
      totalProgress,
      currentStep,
      currentStepProgress,
      processingSteps,
      actualTimes,
      citationInfo,
      rateLimitInfo,
      timeout,
      processingError,
      canRetry,
      startProcessing,
      stopProcessing,
      updateProgress,
      setSteps,
      resetProcessing,
      setProcessingError
    } = useProcessingTime();

    // Add new reactive state for enhanced progress tracking
    const queuePosition = ref(0);
    const estimatedQueueTime = ref(null);
    const activeRequestId = ref(null);

    const pollInterval = ref(null);

    // ===== HELPER FUNCTIONS =====
    // Formatting Helpers
    function formatDate(dateString) {
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
    }
    
    function formatCitation(citation) {
      if (!citation) return '';
      return citation.replace(/\s+/g, ' ').trim();
    }
    
    // UI Helpers
    function getAlertClass(isValid) {
      if (isValid === undefined || isValid === null) return 'alert-info';
      return isValid ? 'alert-success' : 'alert-danger';
    }
    
    function getConfidenceClass(confidence) {
      if (confidence >= 0.8) return 'bg-success';
      if (confidence >= 0.5) return 'bg-warning';
      return 'bg-danger';
    }
    
    function getProgressBarClass(value) {
      if (value >= 0.8) return 'bg-success';
      if (value >= 0.5) return 'bg-info';
      if (value >= 0.3) return 'bg-warning';
      return 'bg-danger';
    }
    
    function getValidationIcon(isValid) {
      if (isValid === undefined || isValid === null) return 'bi-question-circle';
      return isValid ? 'bi-check-circle' : 'bi-x-circle';
    }
    
    function getValidationColor(isValid) {
      if (isValid === undefined || isValid === null) return 'text-info';
      return isValid ? 'text-success' : 'text-danger';
    }
    
    function getValidationLabel(isValid) {
      if (isValid === undefined || isValid === null) return 'Unknown';
      return isValid ? 'Valid' : 'Invalid';
    }
    
    function getCorrectionIcon(correction) {
      if (!correction) return 'bi-question-circle';
      return correction.confidence > 0.7 ? 'bi-lightbulb' : 'bi-lightbulb-off';
    }
    
    function getCorrectionColor(correction) {
      if (!correction) return 'text-muted';
      return correction.confidence > 0.7 ? 'text-warning' : 'text-muted';
    }
    
    function getCorrectionLabel(correction) {
      if (!correction) return 'No suggestions';
      return correction.confidence > 0.7 ? 'Suggested' : 'Low confidence';
    }
    
    function getMLLabel(mlResult) {
      if (!mlResult) return 'N/A';
      return mlResult.prediction || 'Unknown';
    }
    
    function getMLColor(mlResult) {
      if (!mlResult) return 'text-muted';
      return mlResult.confidence > 0.7 ? 'text-success' : 
             mlResult.confidence > 0.4 ? 'text-warning' : 'text-danger';
    }
    
    function getMLIcon(mlResult) {
      if (!mlResult) return 'bi-question-circle';
      return mlResult.confidence > 0.7 ? 'bi-check-circle' : 
             mlResult.confidence > 0.4 ? 'bi-exclamation-circle' : 'bi-x-circle';
    }
    
    // Time formatting function
    function formatTime(seconds) {
      if (!seconds || seconds < 0) return '--:--';
      
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const secs = Math.floor(seconds % 60);
      
      if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
      } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
      }
    }
    
    // ===== CORE FUNCTIONS =====
    // Clear all results and reset form
    function clearResults() {
      validationResult.value = null;
      mlResult.value = null;
      correctionResult.value = null;
      documentAnalysisResult.value = null;
      textAnalysisResult.value = null;
      urlAnalysisResult.value = null;
      error.value = null;
      citationText.value = '';
    }
    
    // Process validation response from API
    function processValidationResponse(response) {
      try {
        console.log('Processing validation response:', response);
        
        // Reset states
        validationResult.value = null;
        mlResult.value = null;
        correctionResult.value = null;
        error.value = null;
        
        // Extract data from response
        const data = response?.data || response || {};
        console.log('Response data:', data);
        
        // Process and set validation result
        if (data.verified !== undefined) {
          validationResult.value = {
            valid: data.verified,
            message: data.message || (data.verified ? 'Citation is valid' : 'Citation is invalid'),
            details: data.details || {},
            timestamp: new Date().toISOString()
          };
        }
        
        // Handle errors
        if (data.error) {
          error.value = data.error;
          return;
        }
        
        // Process ML results if available
        if (data.ml_analysis) {
          mlResult.value = {
            prediction: data.ml_analysis.prediction,
            confidence: data.ml_analysis.confidence,
            details: data.ml_analysis.details,
            timestamp: new Date().toISOString()
          };
        }
        
        // Process correction suggestions if available
        if (data.corrections?.suggestions?.length) {
          correctionResult.value = {
            suggestions: data.corrections.suggestions.map((suggestion, index) => ({
              id: index,
              original: data.citation,
              corrected_text: suggestion.text,
              explanation: suggestion.reason,
              confidence: suggestion.confidence || 0.8,
              timestamp: new Date().toISOString()
            }))
          };
        }
      } catch (err) {
        console.error('Error processing validation response:', err);
        error.value = 'Failed to process validation response. Please try again.';
      }
    }
    
    // Reset all state variables
    const resetAll = () => {
      validationResult.value = null;
      mlResult.value = null;
      correctionResult.value = null;
      documentAnalysisResult.value = null;
      textAnalysisResult.value = null;
      urlAnalysisResult.value = null;
      error.value = null;
      suggestions.value = [];
      hasActiveRequest.value = false;
      activeRequestId.value = null;
      queuePosition.value = 0;
      estimatedQueueTime.value = null;
      citationInfo.value = null;
      rateLimitInfo.value = null;
      timeout.value = null;
      processingError.value = null;
      canRetry.value = false;
    };

    // Add recent validation to local storage
    const addRecentValidation = (citation, result) => {
      try {
        const validation = {
          id: Date.now(),
          citation: citation.trim(),
          result: result,
          timestamp: new Date().toISOString()
        };
        
        recentValidations.value.unshift(validation);
        
        // Keep only the last 10 validations
        if (recentValidations.value.length > 10) {
          recentValidations.value = recentValidations.value.slice(0, 10);
        }
        
        // Save to localStorage
        localStorage.setItem('recentValidations', JSON.stringify(recentValidations.value));
      } catch (err) {
        console.error('Error adding recent validation:', err);
      }
    };

    // Handle validation errors
    const handleError = (error) => {
      console.error('Validation error:', error);
      error.value = error.message || 'An error occurred during validation. Please try again.';
      validationResult.value = null;
    };

    const validateCitation = async (citation) => {
      if (!citation || isLoading.value) return;
      
      resetAll();
      resetProcessing();
      setSteps([
        { step: 'Validating Citation', estimated_time: 10 },
      ]);
      startProcessing();

      try {
        const response = await citationsApi.validateCitation(citation);
        
        // Check if this is an async response with task_id
        if (response.data.status === 'processing' && response.data.task_id) {
          // Handle async processing
          hasActiveRequest.value = true;
          activeRequestId.value = response.data.task_id;
          startPolling(response.data.task_id, handleSingleCitationResults);
        } else {
          // Handle immediate response (fallback)
          validationResult.value = response.data;
          addRecentValidation(citation, response.data);
          stopProcessing();
        }
      } catch (error) {
        handleError(error);
        stopProcessing();
      }
    };

    // ===== API HANDLER FUNCTIONS =====
    const handleDocumentResults = (results) => {
      try {
        const rawCitations = (Array.isArray(results.validation_results) && results.validation_results.length > 0)
          ? results.validation_results
          : (results.citations || []);
        documentAnalysisResult.value = {
          ...results,
          citations: normalizeCitations(rawCitations),
          timestamp: new Date().toISOString()
        };
        isLoading.value = false;
        error.value = null;
        addToRecentValidations(documentAnalysisResult.value);
        nextTick(() => {
          const resultsElement = document.querySelector('.results-section');
          if (resultsElement) {
            resultsElement.scrollIntoView({ behavior: 'smooth' });
          }
        });

        // Complete processing
        updateStep('Document analysis', 100);
        completeStep('Document analysis');
        hasActiveRequest.value = false;
        activeRequestId.value = null;
        
        // Start processing time tracking
        if (results.metadata?.time_estimate) {
          startProcessing(results.metadata.time_estimate);
        }
        
        // Update processing steps as they complete
        if (results.metadata?.processing_steps) {
          for (const step of results.metadata.processing_steps) {
            if (step.actual_time > 0) {
              completeStep(step.step);
            }
          }
        }
        
        // Update actual times
        if (results.metadata?.actual_times) {
          updateActualTimes(results.metadata.actual_times);
        }
      } catch (err) {
        console.error('Error handling document results:', err);
        error.value = 'Failed to process document results';
        isLoading.value = false;
      }
    };

    const handleTextResults = (results) => {
      try {
        const rawCitations = (Array.isArray(results.validation_results) && results.validation_results.length > 0)
          ? results.validation_results
          : (results.citations || []);
        textAnalysisResult.value = {
          ...results,
          citations: normalizeCitations(rawCitations),
          timestamp: new Date().toISOString()
        };
        isLoading.value = false;
        error.value = null;
        addToRecentValidations(textAnalysisResult.value);
        nextTick(() => {
          const resultsElement = document.querySelector('.results-section');
          if (resultsElement) {
            resultsElement.scrollIntoView({ behavior: 'smooth' });
          }
        });

        // Complete processing
        updateStep('Text analysis', 100);
        completeStep('Text analysis');
        hasActiveRequest.value = false;
        activeRequestId.value = null;
        
        // Start processing time tracking
        if (results.metadata?.time_estimate) {
          startProcessing(results.metadata.time_estimate);
        }
        
        // Update processing steps as they complete
        if (results.metadata?.processing_steps) {
          for (const step of results.metadata.processing_steps) {
            if (step.actual_time > 0) {
              completeStep(step.step);
            }
          }
        }
        
        // Update actual times
        if (results.metadata?.actual_times) {
          updateActualTimes(results.metadata.actual_times);
        }
      } catch (err) {
        console.error('Error handling text results:', err);
        error.value = 'Failed to process text results';
        isLoading.value = false;
      }
    };

    const handleUrlResults = (results) => {
      try {
        console.log('URL analysis results:', results); // Debug: log the backend response
        const rawCitations = (Array.isArray(results.validation_results) && results.validation_results.length > 0)
          ? results.validation_results
          : (results.citations || []);
        urlAnalysisResult.value = {
          ...results,
          citations: normalizeCitations(rawCitations),
          timestamp: new Date().toISOString()
        };
        isLoading.value = false;
        error.value = null;
        addToRecentValidations(urlAnalysisResult.value);
        nextTick(() => {
          const resultsElement = document.querySelector('.results-section');
          if (resultsElement) {
            resultsElement.scrollIntoView({ behavior: 'smooth' });
          }
        });

        // Complete processing
        completeStep('URL analysis');
        hasActiveRequest.value = false;
        activeRequestId.value = null;
        
        // Start processing time tracking
        if (results.metadata?.time_estimate) {
          startProcessing(results.metadata.time_estimate);
        }
        
        // Update processing steps as they complete
        if (results.metadata?.processing_steps) {
          for (const step of results.metadata.processing_steps) {
            if (step.actual_time > 0) {
              completeStep(step.step);
            }
          }
        }
        
        // Update actual times
        if (results.metadata?.actual_times) {
          updateActualTimes(results.metadata.actual_times);
        }
      } catch (err) {
        console.error('Error handling URL analysis results:', err);
        error.value = 'Failed to process URL analysis results.';
        isLoading.value = false;
      }
    };

    const handleSingleCitationResults = (results) => {
      try {
        console.log('Single citation analysis results:', results); // Debug: log the backend response
        const rawCitations = (Array.isArray(results.validation_results) && results.validation_results.length > 0)
          ? results.validation_results
          : (results.citations || []);
        validationResult.value = {
          ...results,
          citations: normalizeCitations(rawCitations),
          timestamp: new Date().toISOString()
        };
        isLoading.value = false;
        error.value = null;
        addToRecentValidations(validationResult.value);
        nextTick(() => {
          const resultsElement = document.querySelector('.results-section');
          if (resultsElement) {
            resultsElement.scrollIntoView({ behavior: 'smooth' });
          }
        });

        // Complete processing
        completeStep('Citation validation');
        hasActiveRequest.value = false;
        activeRequestId.value = null;
        
        // Start processing time tracking
        if (results.metadata?.time_estimate) {
          startProcessing(results.metadata.time_estimate);
        }
        
        // Update processing steps as they complete
        if (results.metadata?.processing_steps) {
          for (const step of results.metadata.processing_steps) {
            if (step.actual_time > 0) {
              completeStep(step.step);
            }
          }
        }
        
        // Update actual times
        if (results.metadata?.actual_times) {
          updateActualTimes(results.metadata.actual_times);
        }
      } catch (err) {
        console.error('Error handling single citation results:', err);
        error.value = 'Failed to process single citation results.';
        isLoading.value = false;
      }
    };

    const handleDocumentError = (error) => {
      console.error('Document analysis error:', error);
      
      // Ensure error is an object with the expected properties
      const errorObj = typeof error === 'string' ? { message: error } : error;
      
      documentAnalysisResult.value = {
        error: errorObj.message || 'An error occurred while analyzing the document',
        details: errorObj.details || null,
        status: errorObj.status || 500,
        timestamp: new Date().toISOString()
      };
      
      isLoading.value = false;
      error.value = documentAnalysisResult.value.error;
      
      // Reset progress tracking
      hasActiveRequest.value = false;
      activeRequestId.value = null;
      processingError.value = errorObj.message || 'Document analysis failed';
      canRetry.value = true;
      
      // Scroll to results to show error
      nextTick(() => {
        const resultsElement = document.querySelector('.results-section');
        if (resultsElement) {
          resultsElement.scrollIntoView({ behavior: 'smooth' });
        }
      });
    };

    const handleTextError = (error) => {
      console.error('Text analysis error:', error);
      textAnalysisResult.value = {
        error: error.message || 'An error occurred while analyzing the text',
        timestamp: new Date().toISOString()
      };
      isLoading.value = false;
      error.value = 'Failed to analyze text. Please try again.';
      
      // Reset progress tracking
      hasActiveRequest.value = false;
      activeRequestId.value = null;
      processingError.value = error.message || 'Text analysis failed';
      canRetry.value = true;
    };

    const handleUrlError = (error) => {
      console.error('URL analysis error:', error);
      urlAnalysisResult.value = {
        error: error.message || 'An error occurred while analyzing the URL',
        timestamp: new Date().toISOString()
      };
      isLoading.value = false;
      error.value = 'Failed to analyze URL. Please check the URL and try again.';
      
      // Reset progress tracking
      hasActiveRequest.value = false;
      activeRequestId.value = null;
      processingError.value = error.message || 'URL analysis failed';
      canRetry.value = true;
    };

    // ===== PROGRESS HANDLER FUNCTIONS =====
    const handleDocumentProgress = (progress) => {
      if (progress.task_id && !pollInterval.value) {
        setSteps(progress.steps);
        startProcessing();
        startPolling(progress.task_id, handleDocumentResults);
      } else {
        updateProgress(progress);
      }
    };

    const handleTextProgress = (progress) => {
      if (progress.task_id && !pollInterval.value) {
        setSteps(progress.steps);
        startProcessing();
        startPolling(progress.task_id, handleTextResults);
      } else {
        updateProgress(progress);
      }
    };

    const handleUrlProgress = (progress) => {
      if (progress.task_id && !pollInterval.value) {
        setSteps(progress.steps);
        startProcessing();
        startPolling(progress.task_id, handleUrlResults);
      } else {
        updateProgress(progress);
      }
    };

    // Start polling for task results
    const startPolling = (taskId, resultHandler) => {
      if (pollInterval.value) {
        clearInterval(pollInterval.value);
      }
      
      pollInterval.value = setInterval(async () => {
        try {
          const response = await api.get(`/task_status/${taskId}`);
          
          if (response.data.status === 'completed') {
            clearInterval(pollInterval.value);
            pollInterval.value = null;
            stopProcessing();
            resultHandler(response.data);
          } else if (response.data.status === 'failed') {
            clearInterval(pollInterval.value);
            pollInterval.value = null;
            stopProcessing();
            error.value = response.data.error || 'Task failed';
            canRetry.value = true;
          } else if (response.data.progress) {
            updateProgress(response.data.progress);
          }
        } catch (err) {
          console.error('Polling error:', err);
          clearInterval(pollInterval.value);
          pollInterval.value = null;
          stopProcessing();
          error.value = 'Failed to check task status';
          canRetry.value = true;
        }
      }, 2000); // Poll every 2 seconds
    };

    const addToRecentValidations = (citation, result) => {
      // Only add if result is a valid citation object (not a raw JSON string or debug output)
      if (typeof result === 'object' && result !== null && !Array.isArray(result) && result.text !== 'Unknown citation') {
        const validation = {
          citation,
          result,
          timestamp: new Date().toISOString()
        };
        // Add to the beginning of the array
        recentValidations.value.unshift(validation);
        // Keep only the last 10 validations
        if (recentValidations.value.length > 10) {
          recentValidations.value = recentValidations.value.slice(0, 10);
        }
        // Save to localStorage
        try {
          localStorage.setItem('recentValidations', JSON.stringify(recentValidations.value));
        } catch (error) {
          console.warn('[EnhancedValidator] Error saving recent validations:', error);
        }
      }
    };

    const clearRecentValidations = () => {
      try {
        recentValidations.value = [];
        localStorage.removeItem('recentValidations');
      } catch (err) {
        console.error('Error clearing recent validations:', err);
      }
    };

    const removeRecentValidation = (id) => {
      try {
        recentValidations.value = recentValidations.value.filter(item => item.id !== id);
        localStorage.setItem('recentValidations', JSON.stringify(recentValidations.value));
      } catch (err) {
        console.error('Error removing recent validation:', err);
      }
    };

    /**
     * Copies the given text to the clipboard
     * @param {string} text - The text to copy
     * @param {string} successMessage - Optional success message to show
     * @returns {Promise<boolean>} - Whether the copy was successful
     */
    const copyToClipboard = async (text, successMessage = 'Copied to clipboard!') => {
      try {
        await navigator.clipboard.writeText(text);
        if (successMessage) {
          // You might want to show a toast notification here
          console.log(successMessage);
        }
        return true;
      } catch (err) {
        console.error('Failed to copy text:', err);
        // Fallback for older browsers
        try {
          const textarea = document.createElement('textarea');
          textarea.value = text;
          textarea.style.position = 'fixed';
          document.body.appendChild(textarea);
          textarea.select();
          document.execCommand('copy');
          document.body.removeChild(textarea);
          if (successMessage) {
            console.log(successMessage);
          }
          return true;
        } catch (fallbackErr) {
          console.error('Fallback copy failed:', fallbackErr);
          return false;
        }
      }
    };

    // ===== HELPER FUNCTIONS CONTINUED =====
    const copyResults = async () => {
      try {
        // Get the current results based on the active tab
        let resultsToCopy = '';
        
        if (activeTab.value === 'document' && documentAnalysisResult.value) {
          resultsToCopy = formatResultsForCopy(documentAnalysisResult.value);
        } else if (activeTab.value === 'text' && textAnalysisResult.value) {
          resultsToCopy = formatResultsForCopy(textAnalysisResult.value);
        } else if (activeTab.value === 'url' && urlAnalysisResult.value) {
          resultsToCopy = formatResultsForCopy(urlAnalysisResult.value);
        } else if (activeTab.value === 'single' && validationResult.value) {
          resultsToCopy = formatResultsForCopy(validationResult.value);
        }
        
        if (resultsToCopy) {
          await navigator.clipboard.writeText(resultsToCopy);
          // You might want to show a success message here
          console.log('Results copied to clipboard');
        }
      } catch (err) {
        console.error('Failed to copy results:', err);
        error.value = 'Failed to copy results to clipboard';
      }
    };

    const downloadResults = () => {
      try {
        let resultsToDownload = '';
        let filename = 'validation-results.txt';
        
        if (activeTab.value === 'document' && documentAnalysisResult.value) {
          resultsToDownload = formatResultsForCopy(documentAnalysisResult.value);
          filename = 'document-validation.txt';
        } else if (activeTab.value === 'text' && textAnalysisResult.value) {
          resultsToDownload = formatResultsForCopy(textAnalysisResult.value);
          filename = 'text-validation.txt';
        } else if (activeTab.value === 'url' && urlAnalysisResult.value) {
          resultsToDownload = formatResultsForCopy(urlAnalysisResult.value);
          filename = 'url-validation.txt';
        } else if (activeTab.value === 'single' && validationResult.value) {
          resultsToDownload = formatResultsForCopy(validationResult.value);
          filename = 'citation-validation.txt';
        }
        
        if (resultsToDownload) {
          const blob = new Blob([resultsToDownload], { type: 'text/plain' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }
      } catch (err) {
        console.error('Failed to download results:', err);
        error.value = 'Failed to download results';
      }
    };

    const formatResultsForCopy = (results) => {
      // Format the results as text for copying/downloading
      if (!results) return '';
      
      let formatted = `Validation Results\n`;
      formatted += `Generated: ${new Date().toLocaleString()}\n\n`;
      
      if (results.citation) {
        formatted += `Citation: ${results.citation}\n`;
      }
      
      if (results.valid !== undefined) {
        formatted += `Valid: ${results.valid ? 'Yes' : 'No'}\n`;
      }
      
      if (results.confidence) {
        formatted += `Confidence: ${(results.confidence * 100).toFixed(1)}%\n`;
      }
      
      if (results.suggestions && results.suggestions.length > 0) {
        formatted += '\nSuggestions:\n';
        results.suggestions.forEach((suggestion, index) => {
          formatted += `${index + 1}. ${suggestion.text}\n`;
          if (suggestion.reason) {
            formatted += `   Reason: ${suggestion.reason}\n`;
          }
          if (suggestion.confidence) {
            formatted += `   Confidence: ${(suggestion.confidence * 100).toFixed(1)}%\n`;
          }
          formatted += '\n';
        });
      }
      
      return formatted;
    };

    const applyCorrection = (correction) => {
      if (!correction) return;
      
      // Update the current citation with the corrected text
      if (activeTab.value === 'single') {
        citationInput.value = correction.corrected_text;
      }
      
      // If there are any suggestions, update them as well
      if (suggestions.value) {
        suggestions.value = suggestions.value.map(s => 
          s.id === correction.id ? { ...s, applied: true } : s
        );
      }
      
      // Show success message
      // You can add a toast or notification here if needed
      console.log('Correction applied:', correction);
    };

    const applyCorrectionFromResults = (results) => {
      if (!results || !results.suggestions || results.suggestions.length === 0) {
        return false;
      }
      
      // Get the first suggestion with high confidence
      const highConfidenceSuggestion = results.suggestions.find(
        s => s.confidence && s.confidence > 0.7
      );
      
      if (highConfidenceSuggestion) {
        applyCorrection(highConfidenceSuggestion);
        return true;
      }
      
      return false;
    };

    const handleRouteChange = () => {
      const { tab } = route.query;
      if (tab && tabs.some(t => t.id === tab)) {
        activeTab.value = tab;
      }
      
      // Auto-validate if there's a citation in the URL
      const { citation } = route.query;
      if (citation && typeof citation === 'string') {
        citationInput.value = citation;
        validateCitation(citation);
      }
    };
    
    // Watch for route changes
    watch(() => route.query, handleRouteChange);
    
    // ===== LIFECYCLE HOOKS =====
    onMounted(() => {
      loadRecentValidations();
      nextTick(handleRouteChange);
    });
    
    onUnmounted(() => {
      if (hasActiveRequest.value) {
        cancelValidation();
      }
      if (pollInterval.value) {
        clearInterval(pollInterval.value);
        pollInterval.value = null;
      }
    });
    
    // Watch for route changes
    watch(() => route.query, (newQuery, oldQuery) => {
      if (JSON.stringify(newQuery) !== JSON.stringify(oldQuery)) {
        handleRouteChange();
      }
    });
    
    // ===== RETURN STATEMENT =====
    function isCitationValid(citation) {
      if (!citation) return false;
      return citation.status === 'verified' || citation.verified === true;
    }

    const validCount = computed(() => {
      const citations = getCurrentCitations();
      return citations.filter(c => c.valid || c.verified || c.data?.valid || c.data?.found || c.exists).length;
    });
    const invalidCount = computed(() => {
      const citations = getCurrentCitations();
      return citations.filter(c => !(c.valid || c.verified || c.data?.valid || c.data?.found || c.exists)).length;
    });
    // Helper to get the current citations array for the active tab
    function getCurrentCitations() {
      if (activeTab.value === 'single' && validationResult.value && validationResult.value.citations) {
        return validationResult.value.citations;
      } else if (activeTab.value === 'document' && documentAnalysisResult.value && documentAnalysisResult.value.citations) {
        return documentAnalysisResult.value.citations;
      } else if (activeTab.value === 'text' && textAnalysisResult.value && textAnalysisResult.value.citations) {
        return textAnalysisResult.value.citations;
      } else if (activeTab.value === 'url' && urlAnalysisResult.value && urlAnalysisResult.value.citations) {
        return urlAnalysisResult.value.citations;
      }
      return [];
    }

    // Helper: Normalize citations for frontend display
    function normalizeCitations(citations) {
      return (citations || []).map(citation => {
        const cluster = citation.clusters && citation.clusters.length > 0 ? citation.clusters[0] : {};
        // Map absolute_url to url for direct linking
        const url = cluster.absolute_url ? `https://www.courtlistener.com${cluster.absolute_url}` : undefined;
        
        // Determine verification status based on backend response structure
        const isVerified = citation.data?.valid || citation.data?.found || citation.exists || 
                          citation.status === 'verified' || citation.verified === true;
        
        return {
          ...citation,
          metadata: { ...cluster, url },
          details: { ...cluster, url },
          valid: isVerified,
          verified: isVerified,
        };
      });
    }

    // Add method to handle retry
    const retryProcessing = async () => {
      if (!activeRequestId.value) return;
      
      try {
        processingError.value = null;
        canRetry.value = false;
        resetProcessing();
        
        // Cancel the current request if it exists
        await api.cancelRequest(activeRequestId.value);
        
        // Start a new request with the same parameters
        const currentRequest = api.getRequestStatus(activeRequestId.value);
        if (currentRequest) {
          const { type, input } = currentRequest;
          await analyzeInput(input, type);
        }
      } catch (error) {
        processingError.value = `Failed to retry: ${error.message}`;
        canRetry.value = true;
      }
    };

    // Update the analyzeInput method
    const analyzeInput = async (input, type) => {
      try {
        hasActiveRequest.value = true;
        processingError.value = null;
        canRetry.value = false;
        citationInfo.value = null;
        timeout.value = null;
        
        // Start processing time tracking
        const response = await api.analyze(input, type);
        activeRequestId.value = response.requestId;
        
        // Update citation information
        if (response.metadata?.citation_count) {
          citationInfo.value = {
            total: response.metadata.citation_count,
            unique: response.metadata.unique_citations,
            processed: 0
          };
        }
        
        // Update queue information
        if (response.status === 'queued') {
          queuePosition.value = response.queuePosition;
          estimatedQueueTime.value = response.estimatedWaitTime;
        }
        
        // Update rate limit information if available
        if (response.metadata?.rate_limit_info) {
          rateLimitInfo.value = response.metadata.rate_limit_info;
        }
        
        // Update timeout information
        if (response.metadata?.timeout) {
          timeout.value = response.metadata.timeout;
        }
        
        // Start processing time tracking
        if (response.metadata?.time_estimate) {
          startProcessing(response.metadata.time_estimate);
        }
        
        // Update processing steps as they complete
        if (response.metadata?.processing_steps) {
          for (const step of response.metadata.processing_steps) {
            if (step.actual_time > 0) {
              completeStep(step.step);
              // Update citation processing count if this is a citation verification step
              if (step.step.includes('Verifying citations') && citationInfo.value) {
                const match = step.step.match(/Verifying citations (\d+)-(\d+) of (\d+)/);
                if (match) {
                  const [, start, end] = match.map(Number);
                  citationInfo.value.processed = Math.max(citationInfo.value.processed, end);
                }
              }
            }
          }
        }
        
        // Update actual times
        if (response.metadata?.actual_times) {
          updateActualTimes(response.metadata.actual_times);
        }
        
        // Handle the final result
        if (response.status === 'completed') {
          if (type === 'url') {
            handleUrlResults(response);
          } else if (type === 'text') {
            handleTextResults(response);
          } else if (type === 'file') {
            handleDocumentResults(response);
          }
          
          // Update final citation count
          if (citationInfo.value) {
            citationInfo.value.processed = citationInfo.value.unique;
          }
        }
        
      } catch (error) {
        if (error.response?.status === 504) {
          processingError.value = `Request timed out after ${timeout.value} seconds. The document contains ${citationInfo.value?.unique || 0} unique citations, which may take longer than expected to process.`;
        } else {
          processingError.value = error.message || 'An error occurred during processing';
        }
        canRetry.value = true;
        console.error('Analysis error:', error);
      } finally {
        hasActiveRequest.value = false;
        activeRequestId.value = null;
        queuePosition.value = 0;
        estimatedQueueTime.value = null;
        timeout.value = null;
        resetProcessing();
      }
    };

    // Add cleanup on component unmount
    onUnmounted(() => {
      if (activeRequestId.value) {
        api.cancelRequest(activeRequestId.value);
      }
    });

    // Load recent validations from localStorage
    const loadRecentValidations = () => {
      try {
        const stored = localStorage.getItem('recentValidations');
        recentValidations.value = stored ? JSON.parse(stored) : [];
      } catch (e) {
        console.error('Error loading recent validations:', e);
        recentValidations.value = [];
      }
    };

    // Add missing functions
    const updateStep = (stepName, progress) => {
      if (processingSteps.value) {
        const step = processingSteps.value.find(s => s.step === stepName);
        if (step) {
          step.progress = progress;
        }
      }
    };

    const completeStep = (stepName) => {
      if (processingSteps.value) {
        const step = processingSteps.value.find(s => s.step === stepName);
        if (step) {
          step.progress = 100;
          step.completed = true;
        }
      }
    };

    const updateActualTimes = (times) => {
      if (actualTimes.value && times) {
        Object.assign(actualTimes.value, times);
      }
    };

    return {
      // State
      activeTab,
      activeResultTab,
      citationInput,
      citationText,
      validationResult,
      mlResult,
      correctionResult,
      documentAnalysisResult,
      textAnalysisResult,
      urlAnalysisResult,
      recentValidations,
      suggestions,
      error,
      isLoading: showLoading,
      showLoading,
      hasActiveRequest,
      useEnhanced,
      useML,
      useCorrection,
      showBasicValidation,
      showMLAnalysis,
      showCorrections,
      apiBaseUrl,
      tabs,
      
      // Methods
      clearResults,
      validateCitation,
      applyCorrection,
      copyResults,
      downloadResults,
      handleDocumentResults,
      handleTextResults,
      handleUrlResults,
      handleSingleCitationResults,
      handleDocumentError,
      handleTextError,
      handleUrlError,
      handleDocumentProgress,
      handleTextProgress,
      handleUrlProgress,
      applyCorrectionFromResults,
      loadRecentValidations,
      clearRecentValidations,
      removeRecentValidation,
      copyToClipboard,
      formatDate,
      
      // Helper functions
      getAlertClass,
      getConfidenceClass,
      getProgressBarClass,
      formatCitation,
      getValidationIcon,
      getValidationColor,
      getValidationLabel,
      getCorrectionIcon,
      getCorrectionColor,
      getCorrectionLabel,
      getMLLabel,
      getMLColor,
      getMLIcon,
      isCitationValid,
      validCount,
      invalidCount,
      
      // Processing time tracking
      elapsedTime,
      remainingTime,
      totalProgress,
      currentStep,
      currentStepProgress,
      processingSteps,
      actualTimes,
      formatTime,
      
      // Enhanced progress tracking
      citationInfo,
      queuePosition,
      estimatedQueueTime,
      rateLimitInfo,
      timeout,
      processingError,
      canRetry,
      retryProcessing,
      
      // Missing functions
      updateStep,
      completeStep,
      updateActualTimes
    };
  }
};
</script>

<style scoped>
.processing-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 2rem;
}

.processing-overlay .processing-progress {
  max-width: 600px;
  width: 100%;
  background-color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
