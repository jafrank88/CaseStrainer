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
        <div class="card">
          <div class="card-body text-center">
            <h5 class="card-title">
              <i class="fas fa-cog fa-spin me-2"></i>
              Processing Citations
            </h5>
            <div class="spinner-border text-info mt-3" role="status">
              <span class="visually-hidden">Processing...</span>
              </div>
            <div class="mt-2">Processing citations...</div>
                </div>
              </div>
            </div>
            
      <!-- Enhanced Progress Bar for >20 citations -->
      <div v-if="showLoading && showTimer" class="processing-section mb-4">
        <div class="card">
          <div class="card-body text-center">
            <h5 class="card-title">
              <i class="fas fa-cog fa-spin me-2"></i>
              Processing Citations
            </h5>
            <div class="spinner-border text-info mt-3" role="status">
              <span class="visually-hidden">Processing...</span>
            </div>
            <div class="mt-2">Processing {{ progressCurrent }} of {{ progressTotal }} citations...</div>
            <div class="progress mt-3" style="height: 1.5rem;">
              <div class="progress-bar progress-bar-striped progress-bar-animated" :class="progressBarClass" role="progressbar"
                :style="{ width: progressPercent + '%' }" :aria-valuenow="progressPercent" aria-valuemin="0" aria-valuemax="100">
                {{ progressPercent }}%
              </div>
            </div>
            <div v-if="progressPercent === 100 && !results" class="mt-2 text-muted">Finalizing results...</div>
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

      <!-- No Results State -->
      <div v-if="!results && !showLoading && !error" class="no-results-state text-center mt-5">
        <p class="lead">No results to display.<br />Please return to the home page to start a new analysis.</p>
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
      
      return (citations || []).map(citation => {
        // For the new backend structure, citations come directly with case_name, canonical_date, etc.
        // We need to add the verified property based on whether we have canonical data
        const hasCanonicalData = citation.case_name && citation.case_name !== 'N/A' && 
                                citation.canonical_date && citation.canonical_date !== 'N/A';
        
        // A citation is considered verified if it has canonical case name and date
        const isVerified = hasCanonicalData;
        
        // Calculate citation score (0-4)
        let score = 0;
        
        // 2 points for canonical case name found (increased from 1)
        if (citation.case_name && citation.case_name !== 'N/A') {
          score += 2;
        }
        
        // 1 point for hinted name similarity to canonical name
        if (citation.extracted_case_name && citation.extracted_case_name !== 'N/A' && 
            citation.case_name && citation.case_name !== 'N/A') {
          // Simple similarity check - if extracted name contains key parts of canonical name
          const canonicalWords = citation.case_name.toLowerCase().split(/\s+/).filter(w => w.length > 2);
          const extractedWords = citation.extracted_case_name.toLowerCase().split(/\s+/).filter(w => w.length > 2);
          const commonWords = canonicalWords.filter(word => extractedWords.includes(word));
          const similarity = commonWords.length / Math.max(canonicalWords.length, extractedWords.length);
          if (similarity >= 0.5) { // 50% similarity threshold
            score += 1;
          }
        }
        
        // 1 point for year matching between extracted and canonical
        if (citation.extracted_date && citation.canonical_date) {
          const extractedYear = citation.extracted_date.toString().substring(0, 4);
          const canonicalYear = citation.canonical_date.toString().substring(0, 4);
          if (extractedYear === canonicalYear && extractedYear.length === 4) {
            score += 1;
          }
        }
        
        // Determine score color (updated for 0-4 scale)
        let scoreColor = 'red';
        if (score === 4) scoreColor = 'green';
        else if (score === 3) scoreColor = 'green';
        else if (score === 2) scoreColor = 'yellow';
        else if (score === 1) scoreColor = 'orange';
        
        const normalizedCitation = {
          ...citation,
          // Ensure we have the citation text
          citation: citation.citation || citation.text || 'Unknown citation',
          // Add verification status
          verified: isVerified,
          valid: isVerified,
          // Add scoring
          score: score,
          scoreColor: scoreColor,
          // Map case name fields
          case_name: citation.case_name || 'N/A',
          extracted_case_name: citation.extracted_case_name || 'N/A',
          hinted_case_name: citation.hinted_case_name || 'N/A',
          // Map date fields
          canonical_date: citation.canonical_date || null,
          extracted_date: citation.extracted_date || null,
          // Add metadata for compatibility
          metadata: {
            case_name: citation.case_name,
            canonical_date: citation.canonical_date,
            court: citation.court,
            confidence: citation.confidence,
            method: citation.method,
            pattern: citation.pattern
          },
          // Add details for compatibility
          details: {
            case_name: citation.case_name,
            canonical_date: citation.canonical_date,
            court: citation.court,
            confidence: citation.confidence,
            method: citation.method,
            pattern: citation.pattern
          }
        };
        
        // Debug logging for case names
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
      onProcessingStart(); // Start fallback timer
    }

    // ===== LIFECYCLE HOOKS =====
    onMounted(() => {
      let input = { ...route.query };
      
      // Check for task_id first (async processing)
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
          input = JSON.parse(localStorage.getItem('lastCitationInput'));
        } catch (e) {
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
          // For files, we can't restore the actual file, so show an error
          error.value = 'File upload not available from history. Please upload the file again.';
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
