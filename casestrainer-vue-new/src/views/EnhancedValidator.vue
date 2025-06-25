<template>
  <div class="enhanced-validator">
    <Toast v-if="toastMessage" :message="toastMessage" :type="toastType" @close="clearToast" />
    <!-- Header -->
    <div class="header">
      <h1>Citation Validator</h1>
      <p class="subtitle">Analyze legal documents, text, or URLs for citation verification</p>
    </div>

    <!-- Main Content -->
    <div class="main-content">
      <!-- Input Section -->
      <div class="input-container">
        <UnifiedInput
          :isAnalyzing="isLoading"
          @analyze="handleUnifiedAnalyze"
        />
      </div>

      <!-- Progress Section -->
      <div v-if="showLoading && !results" class="progress-container">
        <SkeletonLoader :lines="4" height="6em" />
      </div>

      <!-- Processing Progress Section -->
      <div v-if="showLoading" class="processing-section mb-4">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">
              <i class="fas fa-cog fa-spin me-2"></i>
              Processing Citations
            </h5>
            
            <!-- Overall Progress -->
            <div class="progress mb-3" style="height: 25px;">
              <div 
                class="progress-bar progress-bar-striped progress-bar-animated" 
                :class="getProgressBarClass(totalProgress / 100)"
                :style="{ width: `${totalProgress}%` }"
                role="progressbar"
                :aria-valuenow="totalProgress"
                aria-valuemin="0"
                aria-valuemax="100"
              >
                {{ Math.round(totalProgress) }}%
              </div>
            </div>
            
            <!-- Time Information -->
            <div class="row text-center mb-3">
              <div class="col-md-4">
                <div class="time-info">
                  <small class="text-muted">Elapsed</small>
                  <div class="fw-bold">{{ formatTime(elapsedTime) }}</div>
                </div>
              </div>
              <div class="col-md-4">
                <div class="time-info">
                  <small class="text-muted">Remaining</small>
                  <div class="fw-bold">{{ formatTime(remainingTime) }}</div>
                </div>
              </div>
              <div class="col-md-4">
                <div class="time-info">
                  <small class="text-muted">Total Estimate</small>
                  <div class="fw-bold">{{ formatTime(estimatedTotalTime) }}</div>
                </div>
              </div>
            </div>
            
            <!-- Current Step -->
            <div v-if="currentStep" class="current-step mb-3">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="fw-semibold">Current Step:</span>
                <span class="text-primary">{{ currentStep }}</span>
              </div>
              <div class="progress" style="height: 15px;">
                <div 
                  class="progress-bar bg-info" 
                  :style="{ width: `${currentStepProgress}%` }"
                  role="progressbar"
                  :aria-valuenow="currentStepProgress"
                  aria-valuemin="0"
                  aria-valuemax="100"
                ></div>
              </div>
            </div>
            
            <!-- Citation Processing Stats -->
            <div v-if="citationInfo" class="citation-stats mb-3">
              <div class="row text-center">
                <div class="col-md-3">
                  <div class="stat-item">
                    <small class="text-muted">Total Citations</small>
                    <div class="fw-bold">{{ citationInfo.total }}</div>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="stat-item">
                    <small class="text-muted">Unique</small>
                    <div class="fw-bold">{{ citationInfo.unique }}</div>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="stat-item">
                    <small class="text-muted">Processed</small>
                    <div class="fw-bold">{{ citationInfo.processed }}</div>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="stat-item">
                    <small class="text-muted">Rate</small>
                    <div class="fw-bold">{{ citationInfo.processed > 0 ? Math.round(citationInfo.processed / elapsedTime) : 0 }}/sec</div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Processing Steps -->
            <div v-if="processingSteps.length > 0" class="processing-steps">
              <h6 class="mb-2">Processing Steps:</h6>
              <div class="steps-list">
                <div 
                  v-for="(step, index) in processingSteps" 
                  :key="index"
                  class="step-item d-flex justify-content-between align-items-center py-1"
                  :class="{ 'text-muted': step.progress === 0, 'text-success': step.progress === 100 }"
                >
                  <span class="step-name">{{ step.step }}</span>
                  <span class="step-status">
                    <span v-if="step.progress === 100" class="text-success">
                      <i class="fas fa-check"></i> Complete
                    </span>
                    <span v-else-if="step.progress > 0" class="text-primary">
                      {{ Math.round(step.progress) }}%
                    </span>
                    <span v-else class="text-muted">Pending</span>
                  </span>
                </div>
              </div>
            </div>
            
            <!-- Error Information -->
            <div v-if="processingError" class="alert alert-danger mt-3">
              <i class="fas fa-exclamation-triangle me-2"></i>
              {{ processingError }}
              <button v-if="canRetry" @click="handleRetry" class="btn btn-sm btn-outline-danger ms-2">
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Results Section -->
      <div v-if="results && !showLoading" class="results-container">
        <CitationResults
          :results="results"
          @apply-correction="applyCorrection"
          @copy-results="copyResults"
          @download-results="downloadResults"
          @toast="showToast"
        />
      </div>

      <!-- Error Display -->
      <div v-if="error && !showLoading" class="error-container">
        <div class="error-card">
          <i class="error-icon">❌</i>
          <h3>Analysis Failed</h3>
          <p>{{ error }}</p>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="!results && !showLoading && !error" class="empty-state">
        <div class="empty-content">
          <div class="empty-icon">📄</div>
          <h2>Ready to Analyze</h2>
          <p>Choose your input method above to get started</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useApi } from '@/composables/useApi';
import { useLoadingState } from '@/composables/useLoadingState';
import api from '@/api/api';
import { useProcessingTime } from '../composables/useProcessingTime';

// Components
import CitationResults from '@/components/CitationResults.vue';
import UnifiedInput from '@/components/UnifiedInput.vue';
import Toast from '@/components/Toast.vue';
import SkeletonLoader from '@/components/SkeletonLoader.vue';

export default {
  name: 'EnhancedValidator',
  components: {
    CitationResults,
    UnifiedInput,
    Toast,
    SkeletonLoader
  },
  setup() {
    // ===== REACTIVE STATE =====
    const route = useRoute();
    const router = useRouter();
    
    // Data State
    const results = ref(null);
    const error = ref(null);
    
    // API State
    const { 
      execute, 
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

    // Toast state
    const toastMessage = ref('');
    const toastType = ref('info');
    const showToast = (msg, type = 'info') => {
      toastMessage.value = msg;
      toastType.value = type;
    };
    const clearToast = () => {
      toastMessage.value = '';
    };

    // ===== HELPER FUNCTIONS =====
    function formatTime(seconds) {
      if (!seconds || seconds < 0) return '0s';
      
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const secs = Math.floor(seconds % 60);
      
      if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
      } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
      }
    }
    
    function getProgressBarClass(value) {
      if (value >= 0.8) return 'bg-success';
      if (value >= 0.5) return 'bg-info';
      if (value >= 0.3) return 'bg-warning';
      return 'bg-danger';
    }
    
    // ===== CORE FUNCTIONS =====
    // Clear all results and reset form
    function clearResults() {
      results.value = null;
      error.value = null;
      resetProcessing();
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

    // Enhanced progress tracking function
    async function pollTaskStatus(taskId) {
      if (!taskId) return;
      
      try {
        const response = await api.get(`/task_status/${taskId}`);
        const data = response.data;
        
        if (data.status === 'completed') {
          // Task completed successfully
          // Use the 'results' field directly, fallback to 'citations' for legacy
          const citationResults = Array.isArray(data.results) ? data.results : (data.citations || []);
          
          // Create the proper structure expected by CitationResults component
          results.value = {
            citations: normalizeCitations(citationResults),
            metadata: data.metadata || {},
            total_citations: citationResults.length,
            verified_count: citationResults.filter(c => c.verified || c.valid || c.data?.valid || c.data?.found).length,
            unverified_count: citationResults.filter(c => !(c.verified || c.valid || c.data?.valid || c.data?.found)).length
          };
          
          hasActiveRequest.value = false;
          stopProcessing();
          isLoading.value = false;
          if (typeof isGlobalLoading !== 'undefined' && isGlobalLoading.value !== undefined) {
            isGlobalLoading.value = false;
          }
          
          // Show success toast
          showToast('Citation analysis completed successfully!', 'success');
          
          // Clear polling
          if (pollInterval.value) {
            clearInterval(pollInterval.value);
            pollInterval.value = null;
          }
          
          // Show a message if no results
          if (citationResults.length === 0) {
            error.value = 'No citations found in the provided text or document.';
          }
        } else if (data.status === 'failed') {
          // Task failed
          error.value = data.error || 'Processing failed';
          hasActiveRequest.value = false;
          setProcessingError(data.error || 'Processing failed');
          
          // Show error toast
          showToast(`Processing failed: ${data.error || 'Unknown error'}`, 'error');
          
          // Clear polling
          if (pollInterval.value) {
            clearInterval(pollInterval.value);
            pollInterval.value = null;
          }
          
        } else {
          // Task is still processing - update progress
          hasActiveRequest.value = true;
          
          // Update processing time with backend data
          if (data.estimated_total_time && data.steps) {
            startProcessing({
              estimated_total_time: data.estimated_total_time,
              steps: data.steps
            });
          } else if (data.estimated_total_time) {
            startProcessing(data.estimated_total_time);
          }
          
          // Update current step and progress
          if (data.current_step) {
            updateProgress({
              step: data.current_step,
              progress: data.progress || 0
            });
          }
          
          // Update citation info if available
          if (data.total_citations !== undefined) {
            citationInfo.value = {
              total: data.total_citations,
              processed: data.processed_citations || 0,
              unique: data.unique_citations || 0
            };
          }
          
          // Continue polling
          if (!pollInterval.value) {
            pollInterval.value = setInterval(() => pollTaskStatus(taskId), 2000);
          }
        }
        
      } catch (err) {
        console.error('Error polling task status:', err);
        error.value = 'Failed to check processing status';
        hasActiveRequest.value = false;
        setProcessingError('Failed to check processing status');
        
        // Clear polling on error
        if (pollInterval.value) {
          clearInterval(pollInterval.value);
          pollInterval.value = null;
        }
      }
    }

    // Enhanced form submission with immediate progress feedback
    async function handleSubmit(formData) {
      try {
        clearResults();
        hasActiveRequest.value = true;
        
        // Start processing immediately with default estimates
        startProcessing(30); // Default 30 seconds estimate
        updateProgress({
          step: 'Submitting request...',
          progress: 5
        });
        
        const response = await execute(() => api.post('/analyze', formData));
        
        if (response && response.task_id) {
          activeRequestId.value = response.task_id;
          
          // Update progress to show task created
          updateProgress({
            step: 'Task created, starting processing...',
            progress: 10
          });
          
          // Start polling for status updates
          await pollTaskStatus(response.task_id);
          
        } else {
          // Direct response (no async task)
          const citationResults = response?.citations || [];
          results.value = {
            citations: normalizeCitations(citationResults),
            metadata: response?.metadata || {},
            total_citations: citationResults.length,
            verified_count: citationResults.filter(c => c.verified || c.valid || c.data?.valid || c.data?.found).length,
            unverified_count: citationResults.filter(c => !(c.verified || c.valid || c.data?.valid || c.data?.found)).length
          };
          hasActiveRequest.value = false;
          stopProcessing();
          isLoading.value = false;
          if (typeof isGlobalLoading !== 'undefined' && isGlobalLoading.value !== undefined) {
            isGlobalLoading.value = false;
          }
          showToast('Citation analysis completed!', 'success');
        }
        
      } catch (err) {
        console.error('Error submitting form:', err);
        error.value = err.message || 'Failed to submit request';
        hasActiveRequest.value = false;
        setProcessingError(err.message || 'Failed to submit request');
        showToast(`Error: ${err.message || 'Failed to submit request'}`, 'error');
      }
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

    // Add method to analyze input
    const analyzeInput = async (input, type) => {
      try {
        if (type === 'file') {
          await handleFileAnalyze({ file: input });
        } else if (type === 'url') {
          await handleUrlAnalyze({ url: input });
        } else if (type === 'text') {
          await handleTextAnalyze({ text: input });
        }
      } catch (error) {
        processingError.value = `Failed to analyze input: ${error.message}`;
        canRetry.value = true;
      }
    };

    // ===== RESULT HANDLERS =====
    const handleResults = (responseData) => {
      try {
        const rawCitations = (Array.isArray(responseData.validation_results) && responseData.validation_results.length > 0)
          ? responseData.validation_results
          : (responseData.citations || []);
        
        results.value = {
          ...responseData,
          citations: normalizeCitations(rawCitations),
          timestamp: new Date().toISOString()
        };
        
        isLoading.value = false;
        error.value = null;
        hasActiveRequest.value = false;
        activeRequestId.value = null;
        
        // Complete processing
        if (typeof isGlobalLoading !== 'undefined' && isGlobalLoading.value !== undefined) {
          isGlobalLoading.value = false;
        }
        
        // Scroll to results
        nextTick(() => {
          const resultsElement = document.querySelector('.results-container');
          if (resultsElement) {
            resultsElement.scrollIntoView({ behavior: 'smooth' });
          }
        });
        
      } catch (err) {
        console.error('Error handling results:', err);
        error.value = 'Failed to process results';
        isLoading.value = false;
      }
    };

    const handleError = (err) => {
      console.error('Analysis error:', err);
      error.value = err.message || 'An error occurred during analysis';
      isLoading.value = false;
      hasActiveRequest.value = false;
      activeRequestId.value = null;
      processingError.value = err.message || 'Analysis failed';
      canRetry.value = true;
      showToast(error.value, 'error');
    };

    // ===== API HANDLER FUNCTIONS =====
    const handleTextAnalyze = async ({ text, options }) => {
      isLoading.value = true;
      error.value = null;
      results.value = null;
      
      try {
        // Send text data to the analyze endpoint
        const response = await api.post('/analyze', {
          text: text,
          type: 'text'
        }, {
          timeout: 300000 // 5 minutes for text processing
        });
        
        // Check if this is an async response with task_id
        if (response.data.status === 'processing' && response.data.task_id) {
          // Handle async processing
          hasActiveRequest.value = true;
          activeRequestId.value = response.data.task_id;
          // Start polling for status updates
          if (!pollInterval.value) {
            pollInterval.value = setInterval(() => pollTaskStatus(response.data.task_id), 2000);
          }
        } else {
          // Handle immediate response
          handleResults(response.data);
          isLoading.value = false;
        }
      } catch (err) {
        handleError(err);
      }
    };

    const handleFileAnalyze = async ({ file }) => {
      isLoading.value = true;
      error.value = null;
      results.value = null;
      
      try {
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('file', file);
        
        // Send file directly to the analyze endpoint
        const response = await api.post('/analyze', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 300000 // 5 minutes for file processing
        });
        
        // Check if this is an async response with task_id
        if (response.data.status === 'processing' && response.data.task_id) {
          // Handle async processing
          hasActiveRequest.value = true;
          activeRequestId.value = response.data.task_id;
          // Start polling for status updates
          if (!pollInterval.value) {
            pollInterval.value = setInterval(() => pollTaskStatus(response.data.task_id), 2000);
          }
        } else {
          // Handle immediate response
          handleResults(response.data);
          isLoading.value = false;
        }
      } catch (err) {
        handleError(err);
      }
    };

    const handleUrlAnalyze = async ({ url }) => {
      isLoading.value = true;
      error.value = null;
      results.value = null;
      
      try {
        // Send URL data to the analyze endpoint
        const response = await api.post('/analyze', {
          url: url,
          type: 'url'
        }, {
          timeout: 300000 // 5 minutes for URL processing
        });
        
        // Check if this is an async response with task_id
        if (response.data.status === 'processing' && response.data.task_id) {
          // Handle async processing
          hasActiveRequest.value = true;
          activeRequestId.value = response.data.task_id;
          // Start polling for status updates
          if (!pollInterval.value) {
            pollInterval.value = setInterval(() => pollTaskStatus(response.data.task_id), 2000);
          }
        } else {
          // Handle immediate response
          handleResults(response.data);
          isLoading.value = false;
        }
      } catch (err) {
        handleError(err);
      }
    };

    // Unified handler for all input types
    function handleUnifiedAnalyze(payload) {
      console.log('handleUnifiedAnalyze payload:', payload);
      // Reset and start progress tracking for all input types
      resetProcessing();
      setSteps([
        { step: 'Preparing analysis', estimated_time: 5 },
        { step: 'Processing content', estimated_time: 30 },
        { step: 'Verifying citations', estimated_time: 60 }
      ]);
      startProcessing();
      hasActiveRequest.value = true;
      error.value = null;
      results.value = null;
      
      if (payload.file) {
        handleFileAnalyze(payload);
      } else if (payload.url) {
        handleUrlAnalyze(payload);
      } else if (payload.text) {
        // If quick mode, treat as single citation
        if (payload.quick) {
          handleTextAnalyze({ text: payload.text, options: { mode: 'single' } });
        } else {
          handleTextAnalyze({ text: payload.text, options: { mode: 'multi' } });
        }
      }
    }

    // ===== LIFECYCLE HOOKS =====
    onMounted(() => {
      // Auto-validate if there's a citation in the URL
      const { citation } = route.query;
      if (citation && typeof citation === 'string') {
        handleUnifiedAnalyze({ text: citation });
      }
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

    // Add a placeholder for copyResults to fix ReferenceError
    function copyResults() {
      console.log('copyResults called');
    }

    // Add a placeholder for downloadResults to fix ReferenceError
    function downloadResults() {
      console.log('downloadResults called');
    }

    // ===== RETURN STATEMENT =====
    return {
      // State
      results,
      error,
      isLoading: showLoading,
      showLoading,
      hasActiveRequest,
      
      // Methods
      clearResults,
      handleUnifiedAnalyze,
      retryProcessing,
      cancelValidation,
      copyResults,
      downloadResults,
      
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
      
      // Helper functions
      getProgressBarClass,
      
      // Stub methods for CitationResults component
      applyCorrection: () => {},
      
      // Toast
      toastMessage,
      toastType,
      clearToast,
    };
  }
};
</script>

<style scoped>
.enhanced-validator {
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  background: #f8f9fa;
  padding: 2rem;
  text-align: center;
}

.main-content {
  padding: 2rem;
}

.input-container {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
}

.progress-container {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
}

.progress-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

.progress-header {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.progress-bar-container {
  margin-bottom: 1.5rem;
}

.progress-bar {
  background: #f3f3f3;
  border-radius: 10px;
  height: 20px;
}

.progress-fill {
  background: #007bff;
  border-radius: 10px;
  height: 100%;
}

.progress-text {
  text-align: center;
  font-weight: bold;
}

.current-step {
  text-align: center;
  margin-bottom: 1.5rem;
}

.time-info {
  text-align: center;
  margin-bottom: 1.5rem;
}

.error-message {
  text-align: center;
  margin-bottom: 1.5rem;
}

.retry-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
}

.results-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

.error-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

.empty-state {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 3rem 1.5rem;
}

.empty-content {
  text-align: center;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
}

.error-icon {
  color: #dc3545;
  margin-right: 0.5rem;
}
</style>
