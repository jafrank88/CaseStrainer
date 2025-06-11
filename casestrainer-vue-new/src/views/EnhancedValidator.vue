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
              :is-loading="isLoading"
              @loading="isLoading = $event"
            />
          </div>

          <!-- Text Paste Tab -->
          <div v-else-if="activeTab === 'text'" class="tab-pane fade show active">
            <TextPaste
              @results="handleTextResults"
              @error="handleTextError"
              :is-loading="isLoading"
              @loading="isLoading = $event"
            />
          </div>

          <!-- URL Upload Tab -->
          <div v-else-if="activeTab === 'url'" class="tab-pane fade show active">
            <UrlUpload
              @results="handleUrlResults"
              @error="handleUrlError"
              :is-loading="isLoading"
              @loading="isLoading = $event"
            />
          </div>
        </div>

        <!-- Results Section -->
        <div v-if="(activeTab === 'single' && validationResult) || 
                  (activeTab === 'document' && documentAnalysisResult) ||
                  (activeTab === 'text' && textAnalysisResult) ||
                  (activeTab === 'url' && urlAnalysisResult)" 
             class="mt-4 results-section">
          <CitationResults
            :result="activeTab === 'single' ? validationResult : 
                     activeTab === 'document' ? documentAnalysisResult :
                     activeTab === 'text' ? textAnalysisResult :
                     urlAnalysisResult"
            :active-tab="activeTab"
            @apply-correction="applyCorrection"
            @copy-results="copyResults"
            @download-results="downloadResults"
          />
        </div>

        <!-- Recent Validations -->
        <div v-if="recentValidations.length > 0" class="mt-5">
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
                <span class="badge ms-2" :class="item.valid ? 'bg-success' : 'bg-danger'">
                  {{ item.valid ? 'Valid' : 'Invalid' }}
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
    
    // ... [rest of the functions] ...
    
    // ===== HELPER FUNCTIONS =====
    const loadRecentValidations = () => {
      try {
        const saved = localStorage.getItem('recentValidations');
        if (saved) {
          recentValidations.value = JSON.parse(saved);
        }
      } catch (err) {
        console.error('Error loading recent validations:', err);
      }
    };

    const handleValidationSuccess = (data) => {
      validationResult.value = data;
      error.value = null;
    };

    const validateCitation = async (citation) => {
      if (!citation?.trim()) {
        error.value = 'Please enter a citation to validate';
        return;
      }

      isLoading.value = true;
      error.value = null;

      try {
        const response = await citationsApi.validateCitation(citation.trim());
        handleValidationSuccess(response.data);
      } catch (err) {
        error.value = err.response?.data?.message || 'Failed to validate citation';
        console.error('Validation error:', err);
      } finally {
        isLoading.value = false;
      }
    };

    // ===== API HANDLER FUNCTIONS =====
    const handleDocumentResults = (results) => {
      try {
        documentAnalysisResult.value = {
          ...results,
          timestamp: new Date().toISOString()
        };
        isLoading.value = false;
        error.value = null;
        
        // Add to recent validations
        addToRecentValidations(documentAnalysisResult.value);
        
        // Scroll to results
        nextTick(() => {
          const resultsElement = document.querySelector('.results-section');
          if (resultsElement) {
            resultsElement.scrollIntoView({ behavior: 'smooth' });
          }
        });
      } catch (err) {
        console.error('Error handling document results:', err);
        error.value = 'Failed to process document results';
        isLoading.value = false;
      }
    };

    const handleTextResults = (results) => {
      try {
        textAnalysisResult.value = {
          ...results,
          timestamp: new Date().toISOString()
        };
        isLoading.value = false;
        error.value = null;
        
        // Add to recent validations
        addToRecentValidations(textAnalysisResult.value);
        
        // Scroll to results
        nextTick(() => {
          const resultsElement = document.querySelector('.results-section');
          if (resultsElement) {
            resultsElement.scrollIntoView({ behavior: 'smooth' });
          }
        });
      } catch (err) {
        console.error('Error handling text results:', err);
        error.value = 'Failed to process text results';
        isLoading.value = false;
      }
    };

    const handleUrlResults = (results) => {
      try {
        urlAnalysisResult.value = {
          ...results,
          timestamp: new Date().toISOString()
        };
        isLoading.value = false;
        error.value = null;
        
        // Add to recent validations
        addToRecentValidations(urlAnalysisResult.value);
        
        // Scroll to results
        nextTick(() => {
          const resultsElement = document.querySelector('.results-section');
          if (resultsElement) {
            resultsElement.scrollIntoView({ behavior: 'smooth' });
          }
        });
      } catch (err) {
        console.error('Error handling URL results:', err);
        error.value = 'Failed to process URL results';
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
    };

    const handleUrlError = (error) => {
      console.error('URL analysis error:', error);
      urlAnalysisResult.value = {
        error: error.message || 'An error occurred while analyzing the URL',
        timestamp: new Date().toISOString()
      };
      isLoading.value = false;
      error.value = 'Failed to analyze URL. Please check the URL and try again.';
    };

    const addToRecentValidations = (result) => {
      try {
        if (!result) return;
        
        // Create a simplified version of the result for recent validations
        const recent = {
          id: Date.now(),
          citation: result.citation || 'Untitled',
          valid: result.valid,
          confidence: result.confidence,
          timestamp: result.timestamp || new Date().toISOString(),
          type: result.type || 'citation'
        };
        
        // Add to the beginning of the array (most recent first)
        recentValidations.value = [recent, ...recentValidations.value].slice(0, 10); // Keep only the 10 most recent
        
        // Save to localStorage
        localStorage.setItem('recentValidations', JSON.stringify(recentValidations.value));
      } catch (err) {
        console.error('Error adding to recent validations:', err);
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
    });
    
    // Watch for route changes
    watch(() => route.query, (newQuery, oldQuery) => {
      if (JSON.stringify(newQuery) !== JSON.stringify(oldQuery)) {
        handleRouteChange();
      }
    });
    
    // ===== RETURN STATEMENT =====
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
      handleDocumentError,
      handleTextError,
      handleUrlError,
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
      getMLIcon
    };
  }
};
</script>

<style scoped>
/* Your existing styles here */
</style>
