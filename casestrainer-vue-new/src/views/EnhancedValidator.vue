<template>
  <div class="enhanced-validator">
    <!-- DEPRECATION NOTICE -->
    <div class="alert alert-warning mb-4" role="alert">
      <h4 class="alert-heading">⚠️ Component Deprecated</h4>
      <p><strong>EnhancedValidator.vue</strong> has been deprecated and is no longer used in the application routing.</p>
      <p class="mb-0">All functionality has been migrated to <strong>HomeView.vue</strong> with enhanced async polling, better error handling, and improved processing mode detection.</p>
      <hr>
      <p class="mb-0"><small>This component is kept for reference only and should not be used in production.</small></p>
    </div>

    <!-- Header -->
    <div class="header text-center mb-4">
      <h1 class="results-title">{{ headerTitle }}</h1>

    </div>

    <!-- Loading State -->
    <div v-if="showLoading" class="loading-container">
      <div class="loading-content">
        <div class="loading-spinner">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
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
            <p class="progress-text">{{ globalProgress.progressPercent }}% complete</p>
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
        <!-- EnhancedValidator Results Section -->
        <div class="results-section-header">
          <h2 class="results-title">
            <i class="bi bi-shield-check me-2"></i>
            EnhancedValidator Citation Analysis Results
          </h2>
          <p class="results-subtitle">Results from EnhancedValidator analysis interface</p>
        </div>
        
        <CitationResults 
          :results="results"
          :show-loading="showLoading"
          :error="error"
          component-id="enhanced-validator"
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
                  globalProgress.completeProgress(null, 'enhanced-validator');
                }
              }
            } catch (error) {
              console.warn('Progress polling error:', error);
            }
          }, 500); // Poll every 500ms for more responsive sync progress
        };

        // Start polling immediately for sync progress feedback
        startProgressPolling();

        // Cleanup function to stop polling
        const cleanupProgressPolling = () => {
          if (progressPollingInterval) {
            clearInterval(progressPollingInterval);
            progressPollingInterval = null;
          }
        };

        // Async job polling function
        const pollAsyncJob = async (jobId) => {
          console.log('🔄 Polling async job:', jobId);
          
          const maxAttempts = 60; // 5 minutes max (60 * 5 seconds)
          let attempts = 0;
          
          const poll = async () => {
            try {
              attempts++;
              console.log(`📊 Polling attempt ${attempts}/${maxAttempts} for job ${jobId}`);
              
              const statusResponse = await axios.get(`/casestrainer/api/task_status/${jobId}`);
              const jobData = statusResponse.data;
              
              console.log('📋 Job status:', jobData.status);
              
              if (jobData.status === 'completed') {
                console.log('✅ Async job completed successfully');
                
                // Update results with completed job data
                results.value = {
                  citations: jobData.citations || [],
                  clusters: jobData.clusters || []
                };
                
                // Complete global progress
                globalProgress.completeProgress(jobData, 'enhanced-validator');
                
                return true;
              } else if (jobData.status === 'failed') {
                console.error('❌ Async job failed:', jobData.error);
                globalProgress.setError(jobData.error || 'Async processing failed');
                return false;
              } else if (attempts >= maxAttempts) {
                console.error('❌ Async job polling timeout');
                globalProgress.setError('Processing timeout - please try again');
                return false;
              } else {
                // Job still running, continue polling
                console.log('⏳ Job still running, continuing to poll...');
                setTimeout(poll, 5000); // Poll every 5 seconds
                return null; // Continue polling
              }
            } catch (error) {
              console.error('❌ Error polling async job:', error);
              if (attempts >= maxAttempts) {
                globalProgress.setError('Error checking job status');
                return false;
              } else {
                // Retry on error
                setTimeout(poll, 5000);
                return null;
              }
            }
          };
          
          return await poll();
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
        
        // Check processing mode to handle progress appropriately
        const processingMode = result.metadata?.processing_mode;
        console.log('🔍 Processing mode detected:', processingMode);
        
        if (processingMode === 'immediate') {
          // For immediate/sync processing, complete progress immediately
          globalProgress.completeProgress(result, 'enhanced-validator');
        } else if (processingMode === 'queued') {
          // For async processing, poll for job completion
          const jobId = result.metadata?.job_id;
          if (jobId) {
            console.log('🔄 Starting async job polling for:', jobId);
            await pollAsyncJob(jobId);
          } else {
            console.error('❌ No job_id found for queued processing');
            globalProgress.setError('No job ID found for async processing');
          }
        }
        
        // Update results - handle flat structure from backend
        // Backend now returns flat structure: { citations: [...], clusters: [...] }
        if (result.citations || result.clusters) {
          // Direct flat structure (current API format)
          results.value = {
            citations: result.citations || [],
            clusters: result.clusters || []
          };
        } else if (result.result) {
          // Legacy nested structure fallback
          if (result.result.clusters || result.result.citations) {
            results.value = result.result;
          } else {
            results.value = {
              clusters: result.result.clusters || [],
              citations: result.result.citations || []
            };
          }
        } else {
          // Fallback for any other structure
          results.value = {
            citations: [],
            clusters: []
          };
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
