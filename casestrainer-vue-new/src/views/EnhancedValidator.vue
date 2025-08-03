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

    <!-- Loading State -->
    <div v-if="showLoading && !results" class="loading-container">
      <div class="loading-content">
        <div class="spinner-container">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Processing...</span>
          </div>
        </div>
        <h3>Processing Citations</h3>
        <p class="text-muted">Extracting and analyzing citations from your document...</p>
        
        <!-- Progress Bar -->
        <div v-if="showTimer" class="progress-section">
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
                :is-analyzing="showLoading"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content Layout -->
    <div v-else class="main-content-wrapper">
      <!-- Main Content Area -->
      <div class="main-content-area">
        <!-- Results -->
        <div v-if="results" class="results-container">
          <CitationResults 
            :results="results" 
            :show-loading="showLoading"
            :processing-time="elapsedTime"
            :show-details="true"
            :elapsed-time="elapsedTime"
            :remaining-time="remainingTime"
            :total-progress="totalProgress"
            :current-step="currentStep"
            :current-step-progress="currentStepProgress"
            :processing-steps="processingSteps"
            :citation-info="citationInfo"
            :rate-limit-info="rateLimitInfo"
            :processing-error="processingError"
            :can-retry="canRetry"
            :timeout="timeout"
            @apply-correction="applyCorrection"
            @copy-results="copyResults"
            @download-results="downloadResults"
            @toast="showToast"
          />
        </div>
        
        <!-- Input Form -->
        <div v-else-if="shouldShowInput" class="input-container">
          <UnifiedInput 
            @analyze="handleUnifiedAnalyze"
            :is-analyzing="showLoading"
          />
          
          <!-- Unified Progress Component -->
          <UnifiedProgress 
            @retry="handleProgressRetry"
            @reset="handleProgressReset"
            @complete="handleProgressComplete"
          />
        </div>
        
        <!-- No Results State -->
        <div v-else class="no-results-container">
          <div class="no-results-content">
            <div class="no-results-icon">
              <i class="bi bi-search"></i>
            </div>
            <h3>No Analysis Results</h3>
            <p class="lead">No results to display.<br />Please return to the home page to start a new analysis.</p>
          </div>
        </div>
      </div>

      <!-- Recent Inputs Sidebar - Temporarily Hidden -->
      <!-- <div class="recent-inputs-sidebar-container">
        <RecentInputs @load-input="loadRecentInput" />
      </div> -->
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick, onUnmounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useApi } from '@/composables/useApi';
import { useLoadingState } from '@/composables/useLoadingState';
import api, { analyze } from '@/api/api';
import { useCitationNormalization } from '@/composables/useCitationNormalization';
import { useUnifiedProgress } from '@/stores/progressStore';

// Components
import CitationResults from '@/components/CitationResults.vue';
import UnifiedInput from '@/components/UnifiedInput.vue';
import UnifiedProgress from '@/components/UnifiedProgress.vue';
import Toast from '@/components/Toast.vue';
import SkeletonLoader from '@/components/SkeletonLoader.vue';
// import RecentInputs from '@/components/RecentInputs.vue'; // Temporarily hidden

export default {
  name: 'EnhancedValidator',
  components: {
    CitationResults,
    UnifiedInput,
    UnifiedProgress,
    Toast,
    SkeletonLoader
    // RecentInputs // Temporarily hidden
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

    // Unified Progress System
    const {
      progressState,
      elapsedTime,
      remainingTime,
      progressPercent,
      progressBarClass,
      shouldShowProgress,
      formatTime: unifiedFormatTime,
      startProgress,
      setTaskId,
      setSteps,
      updateProgress,
      setError,
      completeProgress,
      resetProgress
    } = useUnifiedProgress();
    
    // Legacy progress system removed - using unified progress only

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
    
    // Missing variables that were removed during modernization but still referenced
    const citationInfo = ref(null);
    const rateLimitInfo = ref(null);
    const processingError = ref(null);
    const canRetry = ref(false);
    const timeout = ref(null);
    const totalProgress = ref(0);
    const currentStep = ref('');
    const currentStepProgress = ref(0);
    const processingSteps = ref([]);
    
    // Missing function that was removed during modernization
    const resetProcessing = () => {
      citationInfo.value = null;
      rateLimitInfo.value = null;
      processingError.value = null;
      canRetry.value = false;
      timeout.value = null;
      totalProgress.value = 0;
      currentStep.value = '';
      currentStepProgress.value = 0;
      processingSteps.value = [];
      resetProgress(); // Use unified progress reset
    };
    
    // Additional missing variables causing Vue warnings
    const progressTimer = ref(null);
    const progressTotal = ref(100);
    const progressCurrent = ref(0);
    const formatTime = (seconds) => {
      if (!seconds || seconds < 0) return '00:00';
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.floor(seconds % 60);
      return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    };
    
    // Use unified progress values but provide fallbacks for legacy template references
    const legacyProgressPercent = computed(() => progressPercent?.value || 0);
    const legacyElapsedTime = computed(() => elapsedTime?.value || 0);

    // Add showTimer computed property
    // Always show the progress bar for clarity
    const showTimer = computed(() => true);

    // Legacy progress state removed - using unified progress system

    // Add showFileUpload reactive state
    const showFileUpload = ref(true); // Show input form by default
    
    // Computed property to determine when to show input form
    const shouldShowInput = computed(() => {
      // Show input if no results, no error, and not loading
      // Also show input if we're in the initial state
      return !results.value && !error.value && !showLoading.value;
    });

    // In setup()
    const { normalizeCitations, calculateCitationScore } = useCitationNormalization();

    // ===== HELPER FUNCTIONS =====
    // formatTime is now imported from useProcessingTime composable
    
    function getProgressBarClass(value) {
      if (value >= 0.8) return 'bg-success';
      if (value >= 0.5) return 'bg-info';
      if (value >= 0.3) return 'bg-warning';
      return 'bg-danger';
    }

    // Function to create clusters from citations
    function createClustersFromCitations(citations) {
      const clusters = new Map();
      
      citations.forEach(citation => {
        // Use canonical citation as the primary key for clustering
        const primaryCitation = citation.canonical_citation || citation.citation || citation.primary_citation;
        
        if (!clusters.has(primaryCitation)) {
          clusters.set(primaryCitation, {
            cluster_id: `cluster_${primaryCitation.replace(/[^a-zA-Z0-9]/g, '_')}`,
            canonical_name: citation.canonical_name || 'N/A',
            canonical_date: citation.canonical_date || null,
            extracted_case_name: citation.extracted_case_name || 'N/A',
            extracted_date: citation.extracted_date || null,
            url: citation.url || null,
            citations: []
          });
        }
        
        const cluster = clusters.get(primaryCitation);
        cluster.citations.push(citation);
      });
      
      // Convert Map to array and add size property
      return Array.from(clusters.values()).map(cluster => ({
        ...cluster,
        size: cluster.citations.length
      }));
    }
    
    // ===== CORE FUNCTIONS =====
    // Clear all results and reset form
    function clearResults() {
      results.value = null;
      error.value = null;
      resetProcessing();
    }
    
    // Enhanced progress tracking function
    async function pollTaskStatus(taskId) {
      if (!taskId) return;
      
      try {
        // Poll both task status AND processing progress for complete information
        const [statusResponse, progressResponse] = await Promise.allSettled([
          api.get(`/task_status/${taskId}`),
          api.get(`/processing_progress?task_id=${taskId}`)
        ]);
        
        const data = statusResponse.status === 'fulfilled' ? statusResponse.value.data : {};
        const progressData = progressResponse.status === 'fulfilled' ? progressResponse.value.data : {};
        
        // DEBUG: Log the raw responses to see what we're getting
        console.log('🔍 RAW RESPONSE DEBUG:', {
          statusResponse: statusResponse,
          progressResponse: progressResponse,
          statusResponseValue: statusResponse.status === 'fulfilled' ? statusResponse.value : null,
          progressResponseValue: progressResponse.status === 'fulfilled' ? progressResponse.value : null,
          data: data,
          progressData: progressData
        });
        
        if (data.status === 'completed') {
          // Task completed successfully
          // DEBUG: Log the actual backend response structure
          console.log('🔍 BACKEND RESPONSE DEBUG:', {
            dataKeys: Object.keys(data),
            hasResult: !!data.result,
            hasResults: !!data.results,
            hasCitations: !!data.citations,
            hasClusters: !!data.clusters,
            resultType: typeof data.result,
            resultsType: Array.isArray(data.results) ? 'array' : typeof data.results,
            citationsType: Array.isArray(data.citations) ? 'array' : typeof data.citations,
            clustersType: Array.isArray(data.clusters) ? 'array' : typeof data.clusters,
            resultKeys: data.result ? Object.keys(data.result) : [],
            resultsLength: data.results?.length || 0,
            citationsLength: data.citations?.length || 0,
            clustersLength: data.clusters?.length || 0,
            sampleData: {
              firstResult: data.results?.[0],
              firstCitation: data.citations?.[0],
              firstCluster: data.clusters?.[0]
            }
          });
          
          // Backend returns data in the 'result' field, not directly in 'citations'
          const resultData = data.result || data;
          const citationResults = Array.isArray(resultData.citations) ? resultData.citations : (resultData.results || []);
          
          // DEBUG: Log the result data structure
          console.log('🔍 RESULT DATA DEBUG:', {
            resultData: resultData,
            citationResults: citationResults,
            citationResultsLength: citationResults.length,
            citationResultsType: Array.isArray(citationResults) ? 'array' : typeof citationResults
          });
          
          // DEBUG: Log citation processing
          console.log('🔍 CITATION PROCESSING DEBUG:', {
            citationResultsLength: citationResults.length,
            firstCitationSample: citationResults[0],
            normalizationAvailable: typeof normalizeCitations === 'function'
          });
          
          // Create the proper structure expected by CitationResults component
          const normalizedCitations = normalizeCitations ? normalizeCitations(citationResults) : citationResults;
          
          results.value = {
            citations: normalizedCitations,
            clusters: resultData.clusters || createClustersFromCitations(citationResults), // Use backend clusters first
            metadata: resultData.metadata || {},
            total_citations: citationResults.length,
            verified_count: citationResults.filter(c => c.verified || c.valid || c.data?.valid || c.data?.found).length,
            unverified_count: citationResults.filter(c => !(c.verified || c.valid || c.data?.valid || c.data?.found)).length
          };
          
          // DEBUG: Log final results structure
          console.log('🔍 FINAL RESULTS DEBUG:', {
            resultKeys: Object.keys(results.value),
            citationsCount: results.value.citations?.length || 0,
            clustersCount: results.value.clusters?.length || 0,
            totalCitations: results.value.total_citations,
            verifiedCount: results.value.verified_count,
            unverifiedCount: results.value.unverified_count,
            sampleCitation: results.value.citations?.[0],
            sampleCluster: results.value.clusters?.[0]
          });
          
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
          
          // Prioritize progress data from /processing_progress endpoint
          const activeData = progressData.status === 'success' ? progressData : data;
          
          // Update processing time with backend data (prefer progress endpoint)
          if (activeData.estimated_total_time && activeData.steps) {
            if (lastPolledTaskId.value !== taskId) {
              startProcessing({
                estimated_total_time: activeData.estimated_total_time,
                steps: activeData.steps
              });
              lastPolledTaskId.value = taskId;
            }
          } else if (activeData.estimated_total_time) {
            if (lastPolledTaskId.value !== taskId) {
              startProcessing(activeData.estimated_total_time);
              lastPolledTaskId.value = taskId;
            }
          }
          
          // Update current step and progress (prefer progress endpoint)
          if (activeData.current_step) {
            updateProgress({
              step: activeData.current_step,
              progress: activeData.progress || 0
            });
          }
          
          // Update citation info from progress data (more accurate than task status)
          if (progressData.status === 'success' && progressData.total_citations !== undefined) {
            citationInfo.value = {
              total: progressData.total_citations,
              processed: progressData.processed_citations || 0,
              unique: progressData.unique_citations || 0
            };
            
            // Update our local progress counters for the progress bar
            progressCurrent.value = progressData.processed_citations || 0;
            
            console.log('Enhanced-validator: Updated progress from /processing_progress:', {
              total: progressData.total_citations,
              processed: progressData.processed_citations,
              percent: progressPercent.value
            });
          } else if (data.total_citations !== undefined) {
            // Fallback to task status data if progress endpoint unavailable
            citationInfo.value = {
              total: data.total_citations,
              processed: data.processed_citations || 0,
              unique: data.unique_citations || 0
            };
          }
          
          // Don't set results during processing - keep it null so input form shows
          // Only set results when processing is complete
          
          console.log('EnhancedValidator: Updated results with progress data:', results.value);
          
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
        setProcessingError(err.message || 'Failed to check processing status');
        
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
          const responseData = response?.result || response;
          const citationResults = responseData?.citations || [];
          results.value = {
            citations: normalizeCitations(citationResults),
            clusters: responseData?.clusters || createClustersFromCitations(citationResults), // Use backend clusters first
            metadata: responseData?.metadata || {},
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
        
        // --- FIX: Handle new API response structure with result field ---
        let rawCitations = [];
        if (responseData.result && Array.isArray(responseData.result.citations) && responseData.result.citations.length > 0) {
          rawCitations = responseData.result.citations;
        } else if (Array.isArray(responseData.citations) && responseData.citations.length > 0) {
          rawCitations = responseData.citations;
        } else if (Array.isArray(responseData.validation_results) && responseData.validation_results.length > 0) {
          rawCitations = responseData.validation_results;
        }
        
        results.value = {
          ...responseData,
          citations: normalizeCitations(rawCitations),
          clusters: (responseData.result && responseData.result.clusters) || responseData.clusters || createClustersFromCitations(rawCitations), // Use backend clusters first
          total_citations: rawCitations.length,
          verified_count: rawCitations.filter(c => c.verified || c.valid || c.data?.valid || c.data?.found).length,
          unverified_count: rawCitations.filter(c => !(c.verified || c.valid || c.data?.valid || c.data?.found)).length,
          timestamp: new Date().toISOString()
        };
        
        console.log('Results set to:', results.value);
        console.log('shouldShowInput computed value:', shouldShowInput.value);
        console.log('showLoading value:', showLoading.value);
        console.log('error value:', error.value);
        
        isLoading.value = false;
        error.value = null;
        hasActiveRequest.value = false;
        activeRequestId.value = null;
        
        console.log('Loading states after setting results:');
        console.log('- isLoading.value:', isLoading.value);
        console.log('- isGlobalLoading.value:', isGlobalLoading.value);
        console.log('- hasActiveRequest.value:', hasActiveRequest.value);
        console.log('- showLoading.value:', showLoading.value);
        
        // Complete unified progress tracking
        completeProgress(results.value);
        
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
      const errorMessage = err.message || 'An error occurred during analysis';
      
      // Update unified progress with error
      setError(errorMessage);
      
      // Update core state
      error.value = errorMessage;
      isLoading.value = false;
      hasActiveRequest.value = false;
      activeRequestId.value = null;
      canRetry.value = true;
      showToast(errorMessage, 'error');
    };

    // ===== API HANDLER FUNCTIONS =====
    const handleTextAnalyze = async ({ text, options }) => {
      // Prevent duplicate submissions
      if (hasActiveRequest.value) {
        console.log('Request already in progress, ignoring duplicate text analysis');
        return;
      }
      
      console.log('handleTextAnalyze called with:', { text, options });
      isLoading.value = true;
      error.value = null;
      results.value = null;
      
      try {
        // Use the analyze function which handles async responses properly
        console.log('Calling analyze function...');
        const responseData = await analyze({
          text: text,
          type: 'text'
        });
        
        console.log('Analyze function returned:', responseData);
        
        // The analyze function handles polling internally, so we just need to handle the results
        handleResults(responseData);
        isLoading.value = false;
      } catch (err) {
        console.error('Error in handleTextAnalyze:', err);
        handleError(err);
      }
    };

    const handleFileAnalyze = async (input) => {
      // Prevent duplicate submissions
      if (hasActiveRequest.value) {
        console.log('Request already in progress, ignoring duplicate file analysis');
        return;
      }
      
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
      // Prevent duplicate submissions
      if (hasActiveRequest.value) {
        console.log('Request already in progress, ignoring duplicate URL analysis');
        return;
      }
      
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

    // Unified handler for all input types with unified progress system
    function handleUnifiedAnalyze(payload) {
      console.log('handleUnifiedAnalyze payload:', payload);
      
      // Prevent duplicate submissions
      if (hasActiveRequest.value) {
        console.log('Request already in progress, ignoring duplicate submission');
        showToast('A request is already in progress. Please wait for it to complete.', 'warning');
        return;
      }
      
      // Determine upload type and data for unified progress
      let uploadType, uploadData;
      if (payload.file) {
        uploadType = 'file';
        uploadData = payload;
      } else if (payload.url) {
        uploadType = 'url';
        uploadData = payload;
      } else if (payload.text) {
        uploadType = 'text';
        uploadData = payload;
      }
      
      // Start unified progress tracking
      startProgress(uploadType, uploadData, 95); // 95 seconds estimated
      setSteps([
        { step: 'Preparing analysis', estimated_time: 5 },
        { step: 'Processing content', estimated_time: 30 },
        { step: 'Verifying citations', estimated_time: 60 }
      ]);
      
      // Legacy progress system for backward compatibility
      resetProcessing();
      startProcessing();
      
      // Set request state
      hasActiveRequest.value = true;
      error.value = null;
      results.value = null;
      
      // Route to appropriate handler
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
        console.log('[EnhancedValidator] Using results from router state, skipping new analysis.');
        const responseData = router.currentRoute.value.state.results;
        // --- FIX: Handle new API response structure with result field ---
        let rawCitations = [];
        if (responseData.result && Array.isArray(responseData.result.citations) && responseData.result.citations.length > 0) {
          rawCitations = responseData.result.citations;
        } else if (Array.isArray(responseData.citations) && responseData.citations.length > 0) {
          rawCitations = responseData.citations;
        } else if (Array.isArray(responseData.validation_results) && responseData.validation_results.length > 0) {
          rawCitations = responseData.validation_results;
        }
        if (rawCitations.length > 0) {
          results.value = {
            ...responseData,
            citations: normalizeCitations(rawCitations),
            clusters: (responseData.result && responseData.result.clusters) || responseData.clusters || createClustersFromCitations(rawCitations), // Use backend clusters first
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

    // ===== UNIFIED PROGRESS EVENT HANDLERS =====
    const handleProgressRetry = (retryData) => {
      console.log('Progress retry requested:', retryData);
      if (retryData && retryData.uploadType && retryData.uploadData) {
        handleUnifiedAnalyze(retryData.uploadData);
      }
    };

    const handleProgressReset = () => {
      console.log('Progress reset requested');
      resetProgress();
      clearResults();
    };

    const handleProgressComplete = () => {
      console.log('Progress completion acknowledged');
      // Optional: Add any completion logic here
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
      
      // Unified Progress Event Handlers
      handleProgressRetry,
      handleProgressReset,
      handleProgressComplete,
      
      // Enhanced progress tracking
      citationInfo,
      queuePosition,
      estimatedQueueTime,
      rateLimitInfo,
      timeout,
      canRetry,
      processingError,
      totalProgress,
      currentStep,
      currentStepProgress,
      processingSteps,
      resetProcessing,
      progressTimer,
      progressTotal,
      progressCurrent,
      formatTime,
      progressBarClass,
      progressPercent: legacyProgressPercent,
      elapsedTime: legacyElapsedTime,
      
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
      
      // Recent inputs
      loadRecentInput,

      // Show file upload option
      showFileUpload,
      shouldShowInput,
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

/* Main Layout */
.main-content-wrapper {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 0;
}

.main-content-area {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 24px 0 rgba(60, 72, 88, 0.12);
  border: 1px solid rgba(75, 46, 131, 0.1);
}

.recent-inputs-sidebar-container {
  align-self: start;
  position: sticky;
  top: 2rem;
}

/* Loading State */
.loading-container {
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
  padding: 3rem 2rem;
}

.loading-content {
  background: white;
  border-radius: 16px;
  padding: 3rem 2rem;
  box-shadow: 0 4px 24px 0 rgba(60, 72, 88, 0.12);
  border: 1px solid rgba(75, 46, 131, 0.1);
}

.spinner-container {
  margin-bottom: 2rem;
}

.spinner-container .spinner-border {
  width: 3rem;
  height: 3rem;
  color: #4b2e83;
}

.loading-content h3 {
  color: #4b2e83;
  font-weight: 600;
  margin-bottom: 1rem;
}

.progress-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #e9ecef;
}

/* Error State */
.error-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.error-content {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 24px 0 rgba(60, 72, 88, 0.12);
  border: 1px solid rgba(75, 46, 131, 0.1);
  text-align: center;
}

.error-icon {
  font-size: 3rem;
  color: #dc3545;
  margin-bottom: 1rem;
  display: block;
}

.error-content h3 {
  color: #dc3545;
  font-weight: 600;
  margin-bottom: 1rem;
}

/* No Results State */
.no-results-container {
  text-align: center;
  padding: 3rem 2rem;
}

.no-results-content {
  background: #f8f9fa;
  border-radius: 16px;
  padding: 3rem 2rem;
  border: 1px solid #e9ecef;
}

.no-results-icon {
  font-size: 4rem;
  color: #6c757d;
  margin-bottom: 1.5rem;
}

.no-results-content h3 {
  color: #495057;
  font-weight: 600;
  margin-bottom: 1rem;
}

/* Input Container */
.input-container {
  max-width: 800px;
  margin: 0 auto;
}

/* Results Container */
.results-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .main-content-wrapper {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .recent-inputs-sidebar-container {
    position: static;
    order: -1;
  }
}

@media (max-width: 768px) {
  .main-content-area {
    padding: 1.5rem;
  }
  
  .loading-content {
    padding: 2rem 1.5rem;
  }
  
  .error-content {
    padding: 1.5rem;
  }
  
  .no-results-content {
    padding: 2rem 1.5rem;
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

@media (max-width: 480px) {
  .main-content-area {
    padding: 1rem;
  }
  
  .loading-content {
    padding: 1.5rem 1rem;
  }
  
  .error-content {
    padding: 1rem;
  }
  
  .no-results-content {
    padding: 1.5rem 1rem;
  }
}
</style>
