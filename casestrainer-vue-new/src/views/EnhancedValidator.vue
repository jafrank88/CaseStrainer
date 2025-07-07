<template>
  <div class="enhanced-validator">
    <Toast v-if="toastMessage" :message="toastMessage" :type="toastType" @close="clearToast" />
    <!-- Header -->
    <div class="header text-center mb-4">
      <button class="btn btn-link back-btn" @click="goHome">
        <i class="bi bi-arrow-left"></i> Back to Home
      </button>
      <h1 class="results-title">Citation Verification Results</h1>
    </div>

    <!-- Main Content -->
    <div class="main-content">
      <!-- Progress Section -->
      <div v-if="showLoading && !results" class="progress-container">
        <SkeletonLoader :lines="4" height="6em" />
      </div>

      <!-- Processing Progress Section -->
      <div v-if="showLoading && !showTimer" class="processing-section mb-4">
        <div class="card processing-card">
          <div class="card-body text-center">
            <div class="processing-header">
              <div class="spinner-container">
                <div class="spinner-border text-primary" role="status">
                  <span class="visually-hidden">Processing...</span>
                </div>
              </div>
              <h5 class="card-title mt-3">
                <i class="fas fa-cog fa-spin me-2 text-primary"></i>
                <i class="bi bi-gear-fill spinning me-2 text-primary" style="display: none;"></i>
                Processing Citations
              </h5>
            </div>
            <div class="processing-content">
              <p class="text-muted mb-3">Extracting and analyzing citations from your document...</p>
              
              <!-- Animated progress dots -->
              <div class="progress-dots">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
              
              <!-- Processing steps -->
              <div class="processing-steps mt-4">
                <div class="step active">
                  <i class="bi bi-file-earmark-text text-primary"></i>
                  <span>Document Analysis</span>
                </div>
                <div class="step">
                  <i class="bi bi-search text-muted"></i>
                  <span>Citation Extraction</span>
                </div>
                <div class="step">
                  <i class="bi bi-check-circle text-muted"></i>
                  <span>Verification</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
            
      <!-- Enhanced Progress Bar for >20 citations -->
      <div v-if="showLoading && showTimer" class="processing-section mb-4">
        <div class="card processing-card">
          <div class="card-body text-center">
            <div class="processing-header">
              <div class="spinner-container">
                <div class="spinner-border text-primary" role="status">
                  <span class="visually-hidden">Processing...</span>
                </div>
              </div>
              <h5 class="card-title mt-3">
                <i class="fas fa-cog fa-spin me-2 text-primary"></i>
                <i class="bi bi-gear-fill spinning me-2 text-primary" style="display: none;"></i>
                Processing Citations
              </h5>
            </div>
            <div class="processing-content">
              <div class="progress-info mb-3">
                <div class="progress-stats">
                  <span class="stat">
                    <i class="bi bi-list-ol text-primary"></i>
                    {{ progressCurrent }} of {{ progressTotal }} citations
                  </span>
                  <span class="stat">
                    <i class="bi bi-clock text-primary"></i>
                    {{ formatTime(elapsedTime) }} elapsed
                  </span>
                </div>
              </div>
              
              <!-- Enhanced Progress Bar -->
              <div class="progress-container">
                <div class="progress" style="height: 1.5rem; border-radius: 0.75rem;">
                  <div 
                    class="progress-bar progress-bar-striped progress-bar-animated" 
                    :class="progressBarClass" 
                    role="progressbar"
                    :style="{ width: progressPercent + '%' }" 
                    :aria-valuenow="progressPercent" 
                    aria-valuemin="0" 
                    aria-valuemax="100"
                  >
                    <span class="progress-text">{{ progressPercent }}%</span>
                  </div>
                </div>
                <div class="progress-label mt-2">
                  <small class="text-muted">
                    {{ progressPercent === 100 ? 'Finalizing results...' : 'Processing citations...' }}
                  </small>
                </div>
              </div>
              
              <!-- Processing steps with progress -->
              <div class="processing-steps mt-4">
                <div class="step" :class="{ active: progressPercent < 33 }">
                  <i class="bi bi-file-earmark-text" :class="progressPercent < 33 ? 'text-primary' : 'text-success'"></i>
                  <span>Document Analysis</span>
                </div>
                <div class="step" :class="{ active: progressPercent >= 33 && progressPercent < 66 }">
                  <i class="bi bi-search" :class="progressPercent >= 33 && progressPercent < 66 ? 'text-primary' : progressPercent >= 66 ? 'text-success' : 'text-muted'"></i>
                  <span>Citation Extraction</span>
                </div>
                <div class="step" :class="{ active: progressPercent >= 66 }">
                  <i class="bi bi-check-circle" :class="progressPercent >= 66 ? 'text-primary' : 'text-muted'"></i>
                  <span>Verification</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Results Section -->
      <div v-if="results" class="results-container">
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
          
          <!-- File Upload Option for History Issues -->
          <div v-if="showFileUpload" class="mt-4">
            <div class="card">
              <div class="card-header bg-primary text-white">
                <h5 class="mb-0">
                  <i class="bi bi-file-earmark-arrow-up me-2"></i>
                  Re-upload File
                </h5>
              </div>
              <div class="card-body">
                <p class="text-muted mb-3">
                  To analyze your file, please upload it again using the form below.
                </p>
                <UnifiedInput 
                  @analyze="handleUnifiedAnalyze"
                  :is-analyzing="isLoading"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- No Results State -->
      <div v-if="!results && !showLoading && !error" class="no-results-state text-center mt-5">
        <p class="lead">No results to display.<br />Please return to the home page to start a new analysis.</p>
        
        <!-- Recent Inputs Section -->
        <div class="mt-4">
          <RecentInputs @load-input="loadRecentInput" />
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
import api, { analyze } from '@/api/api';
import { useProcessingTime } from '../composables/useProcessingTime';

// Components
import CitationResults from '@/components/CitationResults.vue';
import UnifiedInput from '@/components/UnifiedInput.vue';
import Toast from '@/components/Toast.vue';
import SkeletonLoader from '@/components/SkeletonLoader.vue';
import RecentInputs from '@/components/RecentInputs.vue';

export default {
  name: 'EnhancedValidator',
  components: {
    CitationResults,
    UnifiedInput,
    Toast,
    SkeletonLoader,
    RecentInputs
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
      setProcessingError,
      estimatedTotalTime
    } = useProcessingTime();

    // Add new reactive state for enhanced progress tracking
    const queuePosition = ref(0);
    const estimatedQueueTime = ref(null);
    const activeRequestId = ref(null);
    const pollInterval = ref(null);
    let lastPolledTaskId = ref(null);

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

    // Fallback timer state
    const fallbackTimeout = ref(null);
    const fallbackTimeoutMs = 120000; // 2 minutes

    // Error state for fallback
    const fallbackError = ref('');

    // Add showTimer computed property
    const showTimer = computed(() => {
      return citationInfo.value && citationInfo.value.total >= 35;
    });

    // Progress bar state
    const progressCurrent = ref(0);
    const progressTotal = computed(() => (citationInfo.value && citationInfo.value.total) ? citationInfo.value.total : 0);
    const progressPercent = computed(() => {
      if (!progressTotal.value) return 0;
      return Math.min(100, Math.round((progressCurrent.value / progressTotal.value) * 100));
    });
    const progressBarClass = computed(() => {
      if (progressPercent.value >= 80) return 'bg-success';
      if (progressPercent.value >= 50) return 'bg-info';
      if (progressPercent.value >= 30) return 'bg-warning';
      return 'bg-danger';
    });
    let progressTimer = null;

    // Add showFileUpload reactive state
    const showFileUpload = ref(false);

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
      console.log('Normalizing citations:', citations);
      console.log('Citations type:', typeof citations);
      console.log('Citations length:', citations ? citations.length : 'null/undefined');
      
      return (citations || []).map(citation => {
        // Convert citation array to string
        let citationText = citation.citation;
        if (Array.isArray(citationText)) {
          citationText = citationText.join('; ');
        }

        // Convert verified to boolean
        let verified = false;
        if (typeof citation.verified === 'string') {
          verified = citation.verified === 'true' || citation.verified === 'true_by_parallel';
        } else {
          verified = !!citation.verified;
        }

        // Calculate citation score (0-4)
        let score = 0;
        if (citation.case_name && citation.case_name !== 'N/A') {
          score += 2;
        }
        if (citation.extracted_case_name && citation.extracted_case_name !== 'N/A' && 
            citation.case_name && citation.case_name !== 'N/A') {
          const canonicalWords = citation.case_name.toLowerCase().split(/\s+/).filter(w => w.length > 2);
          const extractedWords = citation.extracted_case_name.toLowerCase().split(/\s+/).filter(w => w.length > 2);
          const commonWords = canonicalWords.filter(word => extractedWords.includes(word));
          const similarity = commonWords.length / Math.max(canonicalWords.length, extractedWords.length);
          if (similarity >= 0.5) {
            score += 1;
          }
        }
        if (citation.extracted_date && citation.canonical_date) {
          const extractedYear = citation.extracted_date.toString().substring(0, 4);
          const canonicalYear = citation.canonical_date.toString().substring(0, 4);
          if (extractedYear === canonicalYear && extractedYear.length === 4) {
            score += 1;
          }
        }
        let scoreColor = 'red';
        if (score === 4) scoreColor = 'green';
        else if (score === 3) scoreColor = 'green';
        else if (score === 2) scoreColor = 'yellow';
        else if (score === 1) scoreColor = 'orange';

        const normalizedCitation = {
          ...citation,
          citation: citationText,
          verified: verified,
          valid: verified,
          score: score,
          scoreColor: scoreColor,
          case_name: citation.case_name || 'N/A',
          extracted_case_name: citation.extracted_case_name || 'N/A',
          hinted_case_name: citation.hinted_case_name || 'N/A',
          canonical_date: citation.canonical_date || null,
          extracted_date: citation.extracted_date || null,
          metadata: {
            case_name: citation.case_name,
            canonical_date: citation.canonical_date,
            court: citation.court,
            confidence: citation.confidence,
            method: citation.method,
            pattern: citation.pattern
          },
          details: {
            case_name: citation.case_name,
            canonical_date: citation.canonical_date,
            court: citation.court,
            confidence: citation.confidence,
            method: citation.method,
            pattern: citation.pattern
          }
        };
        console.log('Normalized citation:', {
          citation: normalizedCitation.citation,
          case_name: normalizedCitation.case_name,
          extracted_case_name: normalizedCitation.extracted_case_name,
          verified: normalizedCitation.verified,
          score: normalizedCitation.score
        });
        return normalizedCitation;
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
            let debugMsg = 'No citations found in the provided text or document.';
            if (data.status_message && data.status_message.toLowerCase().includes('rate limit')) {
              debugMsg += ' (Possible cause: search engine rate limiting)';
            }
            if (data.error) {
              debugMsg += ` (Backend error: ${data.error})`;
            }
            error.value = debugMsg;
          }

          // Debug: Show raw backend response if debug flag is set
          if (window && window.localStorage && window.localStorage.getItem('debugMode') === 'true') {
            error.value += '\n[DEBUG] Raw backend response: ' + JSON.stringify(data, null, 2);
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
            if (lastPolledTaskId.value !== taskId) {
              startProcessing({
                estimated_total_time: data.estimated_total_time,
                steps: data.steps
              });
              lastPolledTaskId.value = taskId;
            }
          } else if (data.estimated_total_time) {
            if (lastPolledTaskId.value !== taskId) {
              startProcessing(data.estimated_total_time);
              lastPolledTaskId.value = taskId;
            }
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
        
        onProgressOrResult(); // Clear fallback timer on any progress
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
        lastPolledTaskId.value = null;
        
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
          await handleFileAnalyze(input);
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
        console.log('handleResults called with:', responseData);
        
        // --- FIX: Always use citations or validation_results ---
        let rawCitations = [];
        if (Array.isArray(responseData.citations) && responseData.citations.length > 0) {
          rawCitations = responseData.citations;
        } else if (Array.isArray(responseData.validation_results) && responseData.validation_results.length > 0) {
          rawCitations = responseData.validation_results;
        }
        
        results.value = {
          ...responseData,
          citations: normalizeCitations(rawCitations),
          timestamp: new Date().toISOString()
        };
        
        console.log('Results set to:', results.value);
        
        isLoading.value = false;
        error.value = null;
        hasActiveRequest.value = false;
        activeRequestId.value = null;
        
        console.log('Loading states after setting results:');
        console.log('- isLoading.value:', isLoading.value);
        console.log('- isGlobalLoading.value:', isGlobalLoading.value);
        console.log('- hasActiveRequest.value:', hasActiveRequest.value);
        console.log('- showLoading.value:', showLoading.value);
        
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
        // Use the analyze function which handles async responses properly
        const responseData = await analyze({
          text: text,
          type: 'text'
        });
        
        // The analyze function handles polling internally, so we just need to handle the results
        handleResults(responseData);
        isLoading.value = false;
      } catch (err) {
        handleError(err);
      }
    };

    const handleFileAnalyze = async (input) => {
      isLoading.value = true;
      error.value = null;
      results.value = null;
      try {
        let formData;
        if (input instanceof FormData) {
          formData = input;
        } else {
          formData = new FormData();
          formData.append('file', input.file);
          formData.append('type', 'file');
        }
        
        // Use the analyze function which handles async responses properly
        const responseData = await analyze(formData);
        
        // The analyze function handles polling internally, so we just need to handle the results
        handleResults(responseData);
        isLoading.value = false;
      } catch (err) {
        handleError(err);
      }
    };

    const handleUrlAnalyze = async ({ url }) => {
      isLoading.value = true;
      error.value = null;
      results.value = null;
      
      try {
        // Use the analyze function which handles async responses properly
        const responseData = await analyze({
          url: url,
          type: 'url'
        });
        
        // The analyze function handles polling internally, so we just need to handle the results
        handleResults(responseData);
        isLoading.value = false;
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
      onProcessingStart(); // Start fallback timer
    }

    // ===== LIFECYCLE HOOKS =====
    onMounted(() => {
      let input = { ...route.query };
      
      // Check for results in router state first (from HomeView)
      if (router.currentRoute.value.state && router.currentRoute.value.state.results) {
        console.log('Found results in router state:', router.currentRoute.value.state.results);
        const responseData = router.currentRoute.value.state.results;
        // --- FIX: Always use citations or validation_results ---
        let rawCitations = [];
        if (Array.isArray(responseData.citations) && responseData.citations.length > 0) {
          rawCitations = responseData.citations;
        } else if (Array.isArray(responseData.validation_results) && responseData.validation_results.length > 0) {
          rawCitations = responseData.validation_results;
        }
        if (rawCitations.length > 0) {
          results.value = {
            ...responseData,
            citations: normalizeCitations(rawCitations),
            total_citations: rawCitations.length,
            verified_count: rawCitations.filter(c => c.verified || c.valid || c.data?.valid || c.data?.found).length,
            unverified_count: rawCitations.filter(c => !(c.verified || c.valid || c.data?.valid || c.data?.found)).length
          };
          showToast('Citation analysis completed successfully!', 'success');
        } else {
          error.value = 'No citations found in the provided text or document.';
        }
        return;
      }
      
      // Check for task_id (async processing)
      if (input.task_id) {
        console.log('Found task_id, starting polling:', input.task_id);
        activeRequestId.value = input.task_id;
        hasActiveRequest.value = true;
        pollTaskStatus(input.task_id);
        return;
      }
      
      // Check localStorage for recent input if no query params
      if ((!input.text && !input.url && !input.fileName) && localStorage.getItem('lastCitationInput')) {
        try {
          const storedInput = JSON.parse(localStorage.getItem('lastCitationInput'));
          
          // Don't restore file uploads from localStorage since they can't be properly restored
          if (storedInput.fileName) {
            console.log('Found file upload in localStorage, skipping restoration:', storedInput.fileName);
            // Clear the fileName to prevent future issues
            delete storedInput.fileName;
            if (Object.keys(storedInput).length === 0) {
              localStorage.removeItem('lastCitationInput');
            } else {
              localStorage.setItem('lastCitationInput', JSON.stringify(storedInput));
            }
            input = {};
          } else {
            input = storedInput;
          }
        } catch (e) {
          console.warn('Error parsing localStorage input:', e);
          input = {};
        }
      }
      
      // If we have input, trigger analysis
      if (input.text || input.url || input.fileName) {
        console.log('Triggering analysis with input:', input);
        
        // Clear any existing results
        clearResults();
        
        // Trigger analysis based on input type
        if (input.text) {
          handleTextAnalyze({ text: input.text });
        } else if (input.url) {
          handleUrlAnalyze({ url: input.url });
        } else if (input.fileName) {
          // This should not happen anymore since we prevent file uploads from being loaded from localStorage
          // But just in case, handle it gracefully
          console.warn('Unexpected file upload in input:', input.fileName);
          error.value = `File "${input.fileName}" was previously uploaded but cannot be restored from history. Please upload the file again to analyze it.`;
          showFileUpload.value = true;
        }
      } else {
        // No input found, show no results
        results.value = null;
      }

      // Watch for citation count and start progress if needed
      if (showTimer.value && progressTotal.value > 20) {
        progressCurrent.value = 0;
        if (progressTimer) clearInterval(progressTimer);
        progressTimer = setInterval(() => {
          if (progressCurrent.value < progressTotal.value) {
            progressCurrent.value++;
          }
        }, 2000); // 2 seconds per citation
      }

      // Check if Font Awesome is loaded
      setTimeout(() => {
        const faIcons = document.querySelectorAll('.fas.fa-cog.fa-spin');
        const biIcons = document.querySelectorAll('.bi.bi-gear-fill.spinning');
        
        faIcons.forEach((faIcon, index) => {
          if (getComputedStyle(faIcon).fontFamily.indexOf('FontAwesome') === -1) {
            // Font Awesome not loaded, show Bootstrap icon
            faIcon.style.display = 'none';
            if (biIcons[index]) {
              biIcons[index].style.display = 'inline-block';
            }
          }
        });
      }, 100);
    });
    
    onUnmounted(() => {
      if (hasActiveRequest.value) {
        cancelValidation();
      }
      if (pollInterval.value) {
        clearInterval(pollInterval.value);
        pollInterval.value = null;
      }
      clearFallbackTimer();
      if (progressTimer) clearInterval(progressTimer);
    });

    // Jump to 100% when results are ready
    watch(() => results.value, (val) => {
      if (val && progressTimer) {
        progressCurrent.value = progressTotal.value;
        clearInterval(progressTimer);
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

    // Start fallback timer
    function startFallbackTimer() {
      clearFallbackTimer();
      fallbackTimeout.value = setTimeout(() => {
        fallbackError.value = 'Processing timed out. No response from server.';
        setProcessingError(fallbackError.value);
        hasActiveRequest.value = false;
        // Optionally, show a toast or error UI
        showToast(fallbackError.value, 'error');
      }, fallbackTimeoutMs);
    }

    // Clear fallback timer
    function clearFallbackTimer() {
      if (fallbackTimeout.value) {
        clearTimeout(fallbackTimeout.value);
        fallbackTimeout.value = null;
      }
    }

    // When processing starts, start fallback timer
    function onProcessingStart() {
      fallbackError.value = '';
      startFallbackTimer();
    }

    // When progress or results are received, clear fallback timer
    function onProgressOrResult() {
      clearFallbackTimer();
    }

    // Handle loading recent input
    const loadRecentInput = (input) => {
      // Navigate back to home with the input data
      router.push({ 
        path: '/', 
        query: { 
          tab: input.tab,
          ...(input.tab === 'paste' && input.text ? { text: input.text } : {}),
          ...(input.tab === 'url' && input.url ? { url: input.url } : {})
        }
      });
    };

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
      
      // Fallback timer
      fallbackError,
      
      // Show timer computed property
      showTimer,
      
      // Progress bar state
      progressCurrent,
      progressTotal,
      progressPercent,
      progressBarClass,
      
      // Recent inputs
      loadRecentInput,

      // Show file upload option
      showFileUpload,
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

.processing-card {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border-radius: 1rem;
  overflow: hidden;
}

.processing-header {
  margin-bottom: 2rem;
}

.spinner-container {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.spinner-border {
  width: 3rem;
  height: 3rem;
  border-width: 0.25rem;
}

.processing-content {
  max-width: 600px;
  margin: 0 auto;
}

.progress-dots {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin: 1rem 0;
}

.dot {
  width: 8px;
  height: 8px;
  background-color: #007bff;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}

.processing-steps {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 0.75rem;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border-radius: 0.5rem;
  transition: all 0.3s ease;
  opacity: 0.6;
}

.step.active {
  opacity: 1;
  background: rgba(0, 123, 255, 0.1);
  transform: scale(1.05);
}

.step i {
  font-size: 1.5rem;
}

.step span {
  font-size: 0.8rem;
  font-weight: 500;
  text-align: center;
  white-space: nowrap;
}

.progress-info {
  margin-bottom: 1.5rem;
}

.progress-stats {
  display: flex;
  justify-content: space-around;
  gap: 1rem;
  flex-wrap: wrap;
}

.stat {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
}

.progress-container {
  margin: 1.5rem 0;
}

.progress {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid rgba(0, 123, 255, 0.2);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
}

.progress-bar {
  background: linear-gradient(90deg, #007bff, #0056b3);
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.3);
  position: relative;
  overflow: hidden;
}

.progress-text {
  font-weight: 600;
  font-size: 0.9rem;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.progress-label {
  text-align: center;
}

/* Enhanced spinner animation */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.spinner-border {
  animation: spin 1s linear infinite !important;
}

/* Font Awesome spinning animation */
.fa-spin {
  animation: spin 2s linear infinite !important;
}

/* Additional spinning animations */
.spinning {
  animation: spin 1.5s linear infinite;
}

/* Enhanced pulse animation for dots */
@keyframes pulse {
  0%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}

.dot {
  width: 8px;
  height: 8px;
  background-color: #007bff;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

/* Card hover effects */
.processing-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

/* Responsive design */
@media (max-width: 768px) {
  .processing-steps {
    flex-direction: column;
    gap: 1rem;
  }
  
  .step {
    flex-direction: row;
    width: 100%;
    justify-content: flex-start;
  }
  
  .progress-stats {
    flex-direction: column;
    align-items: center;
  }
  
  .stat {
    width: 100%;
    justify-content: center;
  }
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

.results-title {
  font-size: 2.2rem;
  font-weight: 700;
  color: #1976d2;
  letter-spacing: 0.01em;
}

.back-btn {
  font-size: 1.1rem;
  color: #1976d2;
  text-decoration: none;
  margin-bottom: 1rem;
}

.back-btn i {
  margin-right: 0.5rem;
}
</style>
