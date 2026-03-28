import { ref, computed, reactive, watch } from 'vue';
import { API_BASE_URL } from '@/config/api';

// Global progress state that persists across components and navigation
const progressState = reactive({
  // Core progress tracking
  isActive: false,
  taskId: null,
  startTime: null,
  estimatedTotalTime: 0,
  elapsedTime: null, // Real elapsed time from backend
  currentStep: '',
  stepProgress: 0,
  totalProgress: 0,
  
  // Processing steps and timing
  processingSteps: [],
  actualTimes: {},
  
  // Citation and rate limit info
  citationInfo: null,
  rateLimitInfo: null,
  
  // Error handling
  processingError: null,
  canRetry: false,
  isTimeout: false,
  
  // Upload context
  uploadType: null, // 'file', 'url', 'text'
  uploadData: null,
  
  // Results tracking
  hasResults: false,
  resultData: null,
  
  // Route-based scoping
  activeRoute: null,
  routeResults: {}, // Store results per route
  
  // Verification tracking
  verificationStatus: {
    isVerifying: false,
    progress: 0,
    currentMethod: '',
    citationsProcessed: 0,
    citationsCount: 0,
    status: 'idle' // idle, queued, running, completed, failed
  },
  
  // Real-time verification updates
  verificationStream: null,
  verificationResults: null,
  
  // Poll counter for Updates display
  pollCount: 0,
  heuristicTimerId: null,
  lastSseUpdateMs: 0,
  sseThrottleMs: 1000,
  // Cap for heuristic: bar must reflect backend progress, not polling/time
  maxProgressFromBackend: null
});

export function useUnifiedProgress() {
  // Computed properties
  const elapsedTime = computed(() => {
    // CRITICAL FIX: Always calculate elapsed time locally to avoid backend timestamp issues
    // Backend may send absolute timestamps instead of durations
    
    // Fallback to calculated elapsed time
    if (!progressState.startTime || typeof progressState.startTime !== 'number') {
      return 0;
    }
    
    // Only calculate if active, otherwise return 0
    if (!progressState.isActive) {
      return 0;
    }
    
    const elapsed = (Date.now() - progressState.startTime) / 1000;
    return isNaN(elapsed) || elapsed < 0 ? 0 : Math.floor(elapsed);
  });

  const remainingTime = computed(() => {
    if (!progressState.estimatedTotalTime || progressState.estimatedTotalTime <= 0 || !progressState.isActive) {
      return 0;
    }
    const remaining = Math.max(0, progressState.estimatedTotalTime - elapsedTime.value);
    return isNaN(remaining) ? 0 : Math.floor(remaining);
  });

  const progressPercent = computed(() => {
    // Use real progress from backend/heuristic; never use polling/time as the bar value.
    if (progressState.totalProgress !== undefined && progressState.totalProgress !== null && progressState.totalProgress >= 0) {
      const progress = Math.min(100, Math.max(0, Math.floor(progressState.totalProgress)));
      return isNaN(progress) ? 0 : progress;
    }
    // Only before any progress has been set: show minimal activity (heuristic will soon set totalProgress)
    if (progressState.isActive) {
      return Math.min(5, progressState.totalProgress ?? 0);
    }
    return 0;
  });

  const currentStepProgress = computed(() => {
    if (!progressState.processingSteps.length) return 0;
    const currentStepIndex = progressState.processingSteps.findIndex(
      step => step.step === progressState.currentStep
    );
    if (currentStepIndex === -1) return 0;
    
    const step = progressState.processingSteps[currentStepIndex];
    if (!step.estimated_time || step.estimated_time <= 0) return 0;
    
    const stepElapsed = elapsedTime.value - (step.startTime || 0);
    const progress = (stepElapsed / step.estimated_time) * 100;
    return isNaN(progress) ? 0 : Math.min(100, Math.max(0, progress));
  });

  const progressBarClass = computed(() => {
    if (progressState.processingError) return 'bg-danger';
    if (progressPercent.value >= 90) return 'bg-success';
    if (progressPercent.value >= 60) return 'bg-info';
    if (progressPercent.value >= 30) return 'bg-warning';
    return 'bg-primary';
  });

  // Utility functions
  const formatTime = (seconds) => {
    // Handle invalid input
    if (!seconds || isNaN(seconds) || seconds < 0) return '0s';
    
    const validSeconds = Math.floor(seconds);
    if (validSeconds < 60) {
      return `${validSeconds}s`;
    }
    const minutes = Math.floor(validSeconds / 60);
    const remainingSeconds = validSeconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  // Heuristic timer helpers
  // Calibrate using 160 seconds for 140 citations → ~1.143s per citation
  const PER_CITATION_SECONDS = 160 / 140;
  const updateEstimatedFromCitations = (count) => {
    const total = Number(count);
    if (!Number.isFinite(total) || total < 0) return;
    const estimate = Math.max(5, Math.ceil(PER_CITATION_SECONDS * total));
    // Only increase ETA as we learn about more citations; don't shrink
    const prev = Number(progressState.estimatedTotalTime) || 0;
    const nextEta = Math.max(prev, estimate);
    if (nextEta !== prev) {
      progressState.estimatedTotalTime = nextEta;
      // Re-arm heuristic timer with new interval tied to ETA
      if (progressState.isActive) {
        stopHeuristicTimer();
        startHeuristicTimer();
      }
    }
  };

  const startHeuristicTimer = () => {
    // Clear any existing timer
    if (progressState.heuristicTimerId) {
      clearInterval(progressState.heuristicTimerId);
      progressState.heuristicTimerId = null;
    }
    const getHeuristicStepMs = () => {
      // Use smaller increments (1%) for smoother progress → 100 steps to cap
      const etaSec = Math.max(5, Number(progressState.estimatedTotalTime) || 0);
      const stepsToCap = 100; // 100 / 1
      const ms = Math.floor((etaSec * 1000) / stepsToCap);
      // Keep within sensible bounds
      // Never faster than 1% every 2s (>=2000ms); allow slower for larger ETAs
      return Math.min(8000, Math.max(2000, ms));
    };

    // Step the progress deterministically: +1% each interval, but NEVER above last backend progress.
    // Bar must reflect backend job progress, not polling/time.
    const stepMs = getHeuristicStepMs();
    progressState.heuristicTimerId = setInterval(() => {
      if (!progressState.isActive) return;
      const backendCap = progressState.maxProgressFromBackend;
      const cap = progressState.hasResults ? 100 : (backendCap != null ? backendCap : 100);
      const next = Math.min(cap, (progressState.totalProgress || 0) + 1);
      if (next > progressState.totalProgress) {
        progressState.totalProgress = next;
      }
      // Friendly status while finalizing
      if (!progressState.hasResults && progressState.totalProgress >= 95) {
        progressState.currentStep = 'Finalizing results...';
      }
      // Stop on completion or error
      if (progressState.totalProgress >= 100 || progressState.processingError) {
        stopHeuristicTimer();
      }
    }, stepMs);
  };

  const stopHeuristicTimer = () => {
    if (progressState.heuristicTimerId) {
      clearInterval(progressState.heuristicTimerId);
      progressState.heuristicTimerId = null;
    }
  };

  // Core progress management functions
  const startProgress = (uploadType, uploadData, estimatedTime = 30) => {
    console.log('Starting unified progress tracking:', { uploadType, estimatedTime });
    
    // Ensure estimatedTime is a valid positive number
    const validEstimatedTime = Math.max(5, Math.floor(Number(estimatedTime)) || 30);
    const currentTime = Date.now();
    
    // Validate inputs
    if (!uploadType || !uploadData) {
      console.error('Invalid parameters for startProgress:', { uploadType, uploadData });
      throw new Error('Upload type and data are required');
    }
    
    // Reset all state with validated values
    Object.assign(progressState, {
      isActive: true,
      taskId: null,
      startTime: currentTime,
      estimatedTotalTime: validEstimatedTime,
      elapsedTime: null, // Reset to null so computed property calculates it
      currentStep: 'Initializing...',
      pollCount: 0,  // CRITICAL FIX: Reset poll count when starting new progress
      stepProgress: 0,
      totalProgress: 5, // Start with 5% to show immediate progress
      maxProgressFromBackend: null, // Bar reflects backend progress, not polling
      processingSteps: [],
      actualTimes: {},
      citationInfo: null,
      rateLimitInfo: null,
      processingError: null,
      canRetry: false,
      uploadType,
      uploadData,
      hasResults: false,
      resultData: null
    });
    // Reset SSE throttle timestamp on new run
    progressState.lastSseUpdateMs = 0;
    
    // Validate the state was set correctly
    if (!progressState.startTime || !progressState.estimatedTotalTime || progressState.estimatedTotalTime <= 0) {
      console.error('Progress state initialization failed:', {
        startTime: progressState.startTime,
        estimatedTotalTime: progressState.estimatedTotalTime
      });
      throw new Error('Failed to initialize progress state with valid values');
    }
    
    console.log('Progress state initialized successfully:', {
      startTime: progressState.startTime,
      estimatedTotalTime: progressState.estimatedTotalTime,
      uploadType: progressState.uploadType,
      isActive: progressState.isActive,
      totalProgress: progressState.totalProgress
    });

    // Start heuristic timer to animate progress while backend works
    startHeuristicTimer();
  };

  const setTaskId = (taskId) => {
    progressState.taskId = taskId;
    console.log('Progress tracking task ID set:', taskId);
  };

  const setSteps = (steps) => {
    progressState.processingSteps = steps.map((step, index) => ({
      ...step,
      index,
      startTime: progressState.startTime || Date.now() / 1000, // Use current time if startTime is not set
      completed: false
    }));
    console.log('Progress steps set:', progressState.processingSteps);
  };

  const updateProgress = (update) => {
    console.log('Updating progress:', update);
    
    // CRITICAL FIX: Increment poll count on every updateProgress call
    // This ensures the Updates counter increments even if progress values don't change
    if (!progressState.pollCount) {
      progressState.pollCount = 0
    }
    progressState.pollCount++
    
    if (update.step) {
      progressState.currentStep = update.step;
      
      // Mark current step as started
      const stepIndex = progressState.processingSteps.findIndex(
        s => s.step === update.step
      );
      if (stepIndex !== -1 && !progressState.processingSteps[stepIndex].startTime) {
        progressState.processingSteps[stepIndex].startTime = elapsedTime.value;
      }
    }
    
    if (update.progress !== undefined && update.progress !== null) {
      // CRITICAL FIX: Ensure step progress is monotonic - never allow it to decrease
      const newStepProgress = Math.max(0, Math.min(100, update.progress));
      if (newStepProgress > progressState.stepProgress) {
        progressState.stepProgress = newStepProgress;
      }
    }
    
    // Max increase per update so the bar doesn't jump too quickly
    const MAX_PROGRESS_STEP = 8;

    if (update.total_progress !== undefined && update.total_progress !== null) {
      // CRITICAL FIX: Ensure progress is monotonic - never allow it to decrease
      let newProgress = Math.max(0, Math.min(100, update.total_progress));
      // Store backend cap so heuristic doesn't exceed it
      progressState.maxProgressFromBackend = newProgress;
      if (newProgress > progressState.totalProgress) {
        // Smooth: don't jump more than MAX_PROGRESS_STEP per update
        const current = progressState.totalProgress ?? 0;
        const allowed = Math.min(current + MAX_PROGRESS_STEP, newProgress);
        progressState.totalProgress = Math.max(current, allowed);
      }
    } else if (update.overall_progress !== undefined && update.overall_progress !== null) {
      let newProgress = Math.max(0, Math.min(100, update.overall_progress));
      progressState.maxProgressFromBackend = newProgress;
      if (newProgress > progressState.totalProgress) {
        const current = progressState.totalProgress ?? 0;
        const allowed = progressState.hasResults
          ? newProgress
          : Math.min(current + MAX_PROGRESS_STEP, newProgress);
        progressState.totalProgress = Math.max(current, allowed);
      }
    }
    
    // If we're effectively done but waiting on final payload, show a friendlier status
    if (!progressState.hasResults && progressState.totalProgress >= 98) {
      const msg = (update.step || update.message || '').toString().toLowerCase();
      const looksLikeVerifyDone = msg.includes('verification completed') || msg.includes('verifying citations') || msg.includes('processed');
      if (looksLikeVerifyDone || !update.step) {
        progressState.currentStep = 'Finalizing results...';
      }
    }

    // CRITICAL FIX: Ignore backend elapsedTime updates - we calculate duration locally
    // Backend may send absolute timestamps instead of durations, causing clock time display
    
    if (update.citation_info) {
      progressState.citationInfo = update.citation_info;
      const total = update.citation_info.total || update.citation_info.count || update.citation_info.citations_count;
      if (Number.isFinite(total)) {
        updateEstimatedFromCitations(total);
      }
    }
    
    if (update.rate_limit_info) {
      progressState.rateLimitInfo = update.rate_limit_info;
    }
    
    // CRITICAL FIX: Ignore backend startTime updates - we use local startTime for consistent duration calculation
    
    // Update estimated total time (check both snake_case and camelCase)
    if (update.estimatedTotalTime && update.estimatedTotalTime > 0) {
      progressState.estimatedTotalTime = Math.max(5, update.estimatedTotalTime);
    } else if (update.estimated_total_time && update.estimated_total_time > 0) {
      progressState.estimatedTotalTime = Math.max(5, update.estimated_total_time);
    }
    
    // Update active state (check both snake_case and camelCase)
    if (update.isActive !== undefined) {
      progressState.isActive = update.isActive;
    } else if (update.is_active !== undefined) {
      progressState.isActive = update.is_active;
    }
  };

  const setError = (error, isTimeout = false) => {
    console.error('Progress error:', error);
    progressState.processingError = error;
    progressState.isTimeout = isTimeout;
    progressState.canRetry = true;
    progressState.isActive = false;
    stopHeuristicTimer();
  };
  
  const clearError = () => {
    console.log('Clearing progress error');
    progressState.processingError = null;
    progressState.isTimeout = false;
    progressState.canRetry = false;
  };

  const completeProgress = (resultData = null, route = null) => {
    console.log('Progress completed:', resultData, 'for route:', route);
    
    // Stop any active EventSource connections
    if (progressState.verificationStream) {
      console.log('Closing verification stream');
      progressState.verificationStream.close();
      progressState.verificationStream = null;
    }
    
    // CRITICAL: Stop heuristic timer FIRST before updating state
    stopHeuristicTimer();
    
    // Clear any previous error on success
    progressState.processingError = null;
    progressState.canRetry = false;
    progressState.isActive = false;
    progressState.currentStep = 'Completed';
    progressState.totalProgress = 100;
    
    // Scope results by route if provided
    if (route) {
      progressState.activeRoute = route;
      progressState.routeResults[route] = resultData;
      progressState.hasResults = !!resultData;
      progressState.resultData = resultData;
    } else {
      // Global results (for backward compatibility)
      progressState.hasResults = !!resultData;
      progressState.resultData = resultData;
    }
    
    // Mark all steps as completed
    progressState.processingSteps.forEach(step => {
      step.completed = true;
    });
  };

  const resetProgress = () => {
    console.log('Resetting progress state');
    
    // Stop any active EventSource connections
    if (progressState.verificationStream) {
      console.log('Closing verification stream during reset');
      progressState.verificationStream.close();
      progressState.verificationStream = null;
    }
    // Stop heuristic timer as well
    stopHeuristicTimer();
    
    Object.assign(progressState, {
      isActive: false,
      taskId: null,
      startTime: null,
      estimatedTotalTime: 0,
      elapsedTime: null,
      currentStep: '',
      stepProgress: 0,
      totalProgress: 0,
      maxProgressFromBackend: null,
      processingSteps: [],
      actualTimes: {},
      citationInfo: null,
      rateLimitInfo: null,
      processingError: null,
      canRetry: false,
      isTimeout: false,
      pollCount: 0,  // CRITICAL FIX: Reset poll count on progress reset
      uploadType: null,
      uploadData: null,
      hasResults: false,
      resultData: null,
      lastSseUpdateMs: 0
    });
  };

  const retryProgress = () => {
    if (!progressState.canRetry || !progressState.uploadData) {
      console.warn('Cannot retry: no retry data available');
      return false;
    }
    
    console.log('Retrying progress with:', progressState.uploadType, progressState.uploadData);
    
    // Reset error state and restart
    progressState.processingError = null;
    progressState.canRetry = false;
    startProgress(progressState.uploadType, progressState.uploadData, progressState.estimatedTotalTime);
    
    return true;
  };

  // Navigation helpers
  const shouldShowProgress = computed(() => {
    const isValid = progressState.isActive && 
                   !progressState.processingError && 
                   progressState.startTime && 
                   typeof progressState.startTime === 'number' &&
                   progressState.estimatedTotalTime && 
                   progressState.estimatedTotalTime > 0;
    
    console.log('shouldShowProgress check:', {
      isActive: progressState.isActive,
      hasError: !!progressState.processingError,
      hasStartTime: !!progressState.startTime,
      startTimeType: typeof progressState.startTime,
      hasEstimatedTime: !!progressState.estimatedTotalTime,
      estimatedTimeValue: progressState.estimatedTotalTime,
      result: isValid
    });
    
    return isValid;
  });

  const getProgressSummary = computed(() => {
    return {
      isActive: progressState.isActive,
      hasError: !!progressState.processingError,
      hasResults: progressState.hasResults,
      uploadType: progressState.uploadType,
      currentStep: progressState.currentStep,
      progress: progressPercent.value,
      elapsedTime: elapsedTime.value,
      remainingTime: remainingTime.value
    };
  });

  const getResultsForRoute = (route) => {
    if (route === progressState.activeRoute) {
      return progressState.resultData;
    }
    return progressState.routeResults[route] || null;
  };

  const hasResultsForRoute = (route) => {
    return route === progressState.activeRoute && !!progressState.resultData;
  };

  // Debug helper to check progress state validity
  const isProgressStateValid = computed(() => {
    return {
      hasStartTime: !!progressState.startTime,
      startTimeValue: progressState.startTime,
      hasEstimatedTime: !!progressState.estimatedTotalTime,
      estimatedTimeValue: progressState.estimatedTotalTime,
      elapsedTimeValue: elapsedTime.value,
      remainingTimeValue: remainingTime.value,
      progressPercentValue: progressPercent.value,
      isElapsedValid: !isNaN(elapsedTime.value),
      isRemainingValid: !isNaN(remainingTime.value),
      isProgressValid: !isNaN(progressPercent.value)
    };
  });
  
  // Watch for unexpected changes to progress state
  watch(() => progressState.startTime, (newVal, oldVal) => {
    if (oldVal !== null && newVal !== oldVal) {
      console.log('Progress debug: startTime changed unexpectedly:', { oldVal, newVal, stack: new Error().stack });
    }
  });
  
  watch(() => progressState.estimatedTotalTime, (newVal, oldVal) => {
    if (oldVal !== 0 && newVal !== oldVal) {
      console.log('Progress debug: estimatedTotalTime changed unexpectedly:', { oldVal, newVal, stack: new Error().stack });
    }
  });

  // Verification management methods
  const startVerificationStream = (requestId) => {
    if (progressState.verificationStream) {
      progressState.verificationStream.close();
    }

    try {
      const apiBase = API_BASE_URL;
      const eventSource = new EventSource(`${apiBase}/analyze/progress-stream/${requestId}`);

      eventSource.onopen = () => {
        console.log('Verification stream connected');
        progressState.verificationStatus.status = 'queued';
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Verification stream event:', data);

          // Determine if this is a terminal event; if so, bypass throttle
          const pdPeek = data.progress_data || null;
          const peekPercent = (pdPeek && typeof pdPeek === 'object') ? (pdPeek.progress ?? pdPeek.overall_progress ?? pdPeek.total_progress ?? 0) : 0;
          const t = data.type;
          const isTerminal = t === 'verification_complete' || t === 'stream_end' || t === 'error' || t === 'fatal_error' || (peekPercent >= 100);
          if (!isTerminal) {
            const nowMs = Date.now();
            const lastMs = progressState.lastSseUpdateMs || 0;
            if (nowMs - lastMs < (progressState.sseThrottleMs || 1000)) {
              return;
            }
            progressState.lastSseUpdateMs = nowMs;
          } else {
            progressState.lastSseUpdateMs = Date.now();
          }

          // Handle standard progress-stream payload: { request_id, progress_data: {...} }
          const pd = data.progress_data || null;
          if (pd && typeof pd === 'object') {
            const percent = (pd.progress ?? pd.overall_progress ?? pd.total_progress ?? 0);
            const message = pd.current_message || pd.message || 'Processing...';
            // Update main progress; only set total_progress when terminal
            updateProgress({
              step: message,
              progress: percent,
              total_progress: isTerminal ? percent : undefined
            });
            // Update verification status snapshot
            progressState.verificationStatus.status = percent >= 100 ? 'completed' : 'running';
            progressState.verificationStatus.progress = percent || 0;
            // Derive citation counts if provided
            const processed = pd.citations_processed ?? pd.citationsProcessed ?? pd.verified_count ?? 0;
            const total = pd.total_citations ?? pd.citations_count ?? pd.citation_count ?? 0;
            if ((processed || total) && (Number.isFinite(processed) || Number.isFinite(total))) {
              progressState.verificationStatus.citationsProcessed = processed || 0;
              progressState.verificationStatus.citationsCount = total || 0;
              progressState.citationInfo = { processed: processed || 0, total: total || 0 };
              // Update estimated total time with heuristic: base + 1.2s per citation
              if (Number.isFinite(total) && total >= 0) {
                updateEstimatedFromCitations(total);
              }
            }
          }

          switch (data.type) {
            case 'connection_established':
              progressState.verificationStatus.status = 'queued';
              break;

            case 'verification_status':
              progressState.verificationStatus.status = data.status;
              progressState.verificationStatus.progress = data.progress || 0;
              progressState.verificationStatus.currentMethod = data.current_method || '';
              progressState.verificationStatus.citationsProcessed = data.citations_processed || 0;
              progressState.verificationStatus.citationsCount = data.citations_count || 0;
              progressState.verificationStatus.isVerifying = data.status === 'running';
              break;
              
            case 'verification_complete':
              progressState.verificationStatus.status = 'completed';
              progressState.verificationStatus.progress = 100;
              progressState.verificationStatus.isVerifying = false;
              progressState.verificationResults = data.results;
              
              // Update the main results with verification data
              if (progressState.resultData && data.results) {
                progressState.resultData.clusters = data.results.clusters || progressState.resultData.clusters;
                progressState.resultData.citations = data.results.citations || progressState.resultData.citations;
              }
              
              eventSource.close();
              break;
              
            case 'verification_failed':
              progressState.verificationStatus.status = 'failed';
              progressState.verificationStatus.isVerifying = false;
              console.error('Verification failed:', data.error_message);
              eventSource.close();
              break;
              
            case 'stream_end':
            case 'error':
            case 'fatal_error':
              console.log('Verification stream ended:', data.type);
              eventSource.close();
              break;
          }
        } catch (e) {
          console.error('Error parsing verification stream event:', e);
        }
      };
      
      eventSource.onerror = (error) => {
        console.error('Verification stream error:', error);
        progressState.verificationStatus.status = 'failed';
        progressState.verificationStatus.isVerifying = false;
        eventSource.close();
      };
      
      progressState.verificationStream = eventSource;
      
    } catch (error) {
      console.error('Failed to start verification stream:', error);
      progressState.verificationStatus.status = 'failed';
    }
  };
  
  const stopVerificationStream = () => {
    if (progressState.verificationStream) {
      console.log('Closing verification stream');
      progressState.verificationStream.close();
      progressState.verificationStream = null;
    }
    progressState.verificationStatus.status = 'idle';
    progressState.verificationStatus.isVerifying = false;
    
    // Also reset the verification results
    progressState.verificationResults = null;
  };
  
  const updateVerificationStatus = (status) => {
    Object.assign(progressState.verificationStatus, status);
  };
  
  const getVerificationResults = () => {
    return progressState.verificationResults;
  };

  return {
    // State (reactive)
    progressState,
    
    // Computed properties
    elapsedTime,
    remainingTime,
    progressPercent,
    currentStepProgress,
    progressBarClass,
    shouldShowProgress,
    getProgressSummary,
    isProgressStateValid, // Debug helper
    
    // Functions
    formatTime,
    startProgress,
    setTaskId,
    setSteps,
    updateProgress,
    setError,
    clearError,
    completeProgress,
    resetProgress,
    retryProgress,
    
      // Route-scoped results
  getResultsForRoute,
  hasResultsForRoute,
  
  // Verification management
  startVerificationStream,
  stopVerificationStream,
  updateVerificationStatus,
  getVerificationResults
  };
}

// Export a singleton instance for global use
export const globalProgress = useUnifiedProgress();
