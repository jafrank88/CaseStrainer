<template>
  <div class="enhanced-validator">
    <!-- Header -->
    <div class="header text-center mb-4">
      <h1 class="results-title">{{ headerTitle }}</h1>

    </div>

    <!-- Loading State -->
    <div v-if="showLoading && !results" class="loading-container">
      <div class="loading-content">
        <div class="spinner-container">
          <div class="custom-spinner" role="status" ref="spinnerElement">
            <div class="spinner-circle" ref="spinnerCircle"></div>
            <span class="visually-hidden">Processing...</span>
          </div>
        </div>
        <h3>Processing Citations</h3>
        <p class="text-muted">Extracting and analyzing citations from your document...</p>
        <div class="loading-info">
          <p class="timeout-info">This may take up to 30 seconds. Please don't close this page.</p>
          <div class="progress-indicator">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: globalProgress.progressPercent + '%' }"></div>
            </div>
            <span class="progress-text">{{ globalProgress.progressState.currentStep || 'Processing...' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error && !showLoading" class="error-container">
      <div class="error-content">
        <div class="error-icon">
          <i class="bi bi-exclamation-triangle"></i>
        </div>
        <h3>Analysis Failed</h3>
        <p>{{ error }}</p>
      </div>
    </div>

    <!-- Main Content Layout -->
    <div v-else class="main-content-wrapper">
      <!-- Input Form Section -->
      <div v-if="shouldShowInput" class="input-section">
        <UnifiedInput :isAnalyzing="showLoading" @analyze="handleUnifiedAnalyze" />
      </div>

      <!-- Results Section -->
      <div v-if="results" class="results-section">
        <CitationResults 
          :results="results"
          :show-loading="showLoading"
          :error="error"
          @copy-results="copyResults"
          @download-results="downloadResults"
          @toast="showToast"
          @new-analysis="startNewAnalysis"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue';
import axios from 'axios';
import UnifiedInput from '@/components/UnifiedInput.vue';
import CitationResults from '@/components/CitationResults.vue';
import { globalProgress } from '@/stores/progressStore';

export default {
  name: 'EnhancedValidator',
  components: {
    UnifiedInput,
    CitationResults
  },
  setup() {
    // ===== REACTIVE STATE =====
    const results = ref(null);
    const error = ref(null);
    const simpleLoading = ref(false);
    const hasActiveRequest = ref(false);
    
    // Watch for results changes
    watch(results, (newVal) => {
      // Handle results changes if needed
    });
    
    // Component mounted hook
    onMounted(() => {
      // Component initialization code here
    });

    // Computed property to determine loading state
    const showLoading = computed(() => {
      return simpleLoading.value || hasActiveRequest.value || globalProgress.progressState.isActive;
    });

    // Computed property to determine when to show input form
    const shouldShowInput = computed(() => {
      return !results.value && !error.value && !showLoading.value;
    });

    // Computed property for dynamic header title
    const headerTitle = computed(() => {
      return results.value ? 'Citation Verification Results' : 'Citation Verification';
    });

    // Handler for unified analyze requests
    const handleUnifiedAnalyze = async (data) => {
      
      try {
        // Set loading state
        simpleLoading.value = true;
        hasActiveRequest.value = true;
        error.value = null;
        // Start global progress tracking
        globalProgress.startProgress('document', {});

        // Start progress polling for synchronous processing
        let progressPollingInterval;
        const startProgressPolling = () => {
          progressPollingInterval = setInterval(async () => {
            try {
              const progressResponse = await axios.get('/casestrainer/api/processing_progress');
              if (progressResponse.data) {
                const progressData = progressResponse.data;
                console.log('Progress update:', progressData);
                
                // Update global progress state
                if (progressData.status === 'processing') {
                  globalProgress.updateProgress(progressData.current_step, progressData.progress, progressData.message);
                } else if (progressData.status === 'waiting') {
                  globalProgress.updateProgress('waiting', progressData.progress, progressData.message);
                }
                
                // Stop polling if complete
                if (progressData.is_complete) {
                  clearInterval(progressPollingInterval);
                  globalProgress.completeProgress();
                }
              }
            } catch (error) {
              console.warn('Progress polling error:', error);
            }
          }, 1000); // Poll every second
        };

        // Start polling immediately
        startProgressPolling();

        // Cleanup function to stop polling
        const cleanupProgressPolling = () => {
          if (progressPollingInterval) {
            clearInterval(progressPollingInterval);
            progressPollingInterval = null;
          }
        };

        let response;
        let formData = new FormData();
        let endpoint = '';

        // All requests go to the same analyze endpoint with the /casestrainer prefix
        endpoint = '/casestrainer/api/analyze';

        // Prepare request based on input type
        if (data instanceof FormData) {
          // For file uploads and URL requests, data is already a FormData object
          formData = data;
        } else if (data.type === 'text') {
          formData.append('text', data.text);
          formData.append('type', 'text');
          // Add source and other metadata if available
          if (data.source) formData.append('source', data.source);
          if (data.fileName) formData.append('fileName', data.fileName);
          if (data.fileSize) formData.append('fileSize', data.fileSize);
        } else if (data.type === 'url') {
          // URL input
          console.log('🌐 URL input data:', data);
          formData.append('url', data.url);
          formData.append('type', 'url');
        }

        // Prepare request data

        // Use axios instead of fetch to leverage the configured base URL
        try {
          response = await axios.post(endpoint, formData, {
            timeout: 600000, // 10 minute timeout for complex citation processing
            headers: {
              'X-Requested-With': 'XMLHttpRequest',
              // Let axios set the Content-Type for FormData with boundary
              'Accept': 'application/json, text/plain, */*'
            },
            transformRequest: (data, headers) => {
              // Let axios handle the FormData content type with boundary
              if (data instanceof FormData) {
                // Remove any existing Content-Type to let the browser set it with the boundary
                delete headers['Content-Type'];
              }
              return data;
            },
            withCredentials: true // Include cookies in the request
          });
        } catch (axiosError) {
          console.error('Axios error details:', {
            message: axiosError.message,
            code: axiosError.code,
            status: axiosError.response?.status,
            statusText: axiosError.response?.statusText,
            responseData: axiosError.response?.data,
            config: {
              url: axiosError.config?.url,
              method: axiosError.config?.method,
              headers: axiosError.config?.headers,
              data: axiosError.config?.data
            }
          });
          
          if (axiosError.code === 'ECONNABORTED') {
            throw new Error('Request timed out. The server is taking too long to respond.');
          } else if (axiosError.response) {
            // The request was made and the server responded with a status code
            // that falls out of the range of 2xx
            const { status, data } = axiosError.response;
            console.error('Server responded with error:', { status, data });
            
            if (status === 400) {
              throw new Error(data?.message || 'Bad request. Please check your input and try again.');
            } else if (status === 401) {
              throw new Error('Session expired. Please refresh the page and try again.');
            } else if (status === 403) {
              throw new Error('You do not have permission to perform this action.');
            } else if (status === 404) {
              throw new Error('The requested resource was not found.');
            } else if (status >= 500) {
              throw new Error('A server error occurred. Please try again later.');
            } else {
              throw new Error(`Request failed with status code ${status}`);
            }
          } else if (axiosError.request) {
            // The request was made but no response was received
            console.error('No response received:', axiosError.request);
            throw new Error('No response from server. Please check your network connection.');
          } else {
            // Something happened in setting up the request that triggered an Error
            console.error('Request setup error:', axiosError.message);
            throw new Error(`Request failed: ${axiosError.message}`);
          }
        }

        if (response.status >= 400) {
          const errorData = response.data || {};
          throw new Error(errorData.message || `Server returned ${response.status}: ${response.statusText}`);
        }

        const result = response.data;
        
        // Update results - handle nested structure from backend
        if (result.result) {
          // Backend returns nested structure: { result: { citations: [...], clusters: [...] } }
          // Ensure we have the expected structure with clusters and citations
          if (result.result.clusters || result.result.citations) {
            results.value = result.result;
          } else {
            // If the structure is different, try to normalize it
            results.value = {
              clusters: result.result.clusters || [],
              citations: result.result.citations || []
            };
          }
        } else {
          // Fallback for direct structure
          results.value = result;
        }
        
      } catch (err) {
        console.error('❌ Error in handleUnifiedAnalyze:', err);
        error.value = err.message || 'An error occurred while processing your request';
        // Set error in global progress store
        globalProgress.setError(err.message || 'An error occurred while processing your request');
      } finally {
        // Reset loading state
        simpleLoading.value = false;
        hasActiveRequest.value = false;
        // Stop progress polling
        cleanupProgressPolling();
        // Stop global progress tracking
        // globalProgress tracking is handled by the API response
      }
    };

    // Placeholder methods - implement as needed
    const copyResults = () => console.log('Copy results');
    const downloadResults = () => console.log('Download results');
    const showToast = (message) => console.log('Toast:', message);
    const startNewAnalysis = () => {
      results.value = null;
      error.value = null;
    };

    // Initialization complete

    return {
      // State
      results,
      error,
      simpleLoading,
      hasActiveRequest,
      // loadingProgress and loadingProgressText are now handled by globalProgress store
      // loadingProgress,
      // loadingProgressText,
      
      // Computed
      showLoading,
      shouldShowInput,
      headerTitle,
      
      // Methods
      handleUnifiedAnalyze,
      copyResults,
      downloadResults,
      showToast,
      startNewAnalysis
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

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.error-container {
  text-align: center;
  padding: 20px;
  color: #dc3545;
}

.main-content-wrapper {
  margin-top: 20px;
}

.input-section, .results-section {
  margin-bottom: 30px;
}
</style>
