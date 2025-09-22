import { ref, computed, reactive, watch } from 'vue';

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
  verificationResults: null
});

export function useUnifiedProgress() {
  // Computed properties
  const elapsedTime = computed(() => {
    // Use real elapsed time from backend if available
    if (progressState.elapsedTime !== undefined && progressState.elapsedTime !== null && progressState.elapsedTime >= 0) {
      return Math.max(0, Math.floor(progressState.elapsedTime));
    }
    
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
    // Use real progress data from backend if available
    if (progressState.totalProgress !== undefined && progressState.totalProgress !== null && progressState.totalProgress >= 0) {
      const progress = Math.min(100, Math.max(0, Math.floor(progressState.totalProgress)));
      return isNaN(progress) ? 0 : progress;
    }
    
    // Fallback to time-based estimation if no real progress available
    if (!progressState.isActive || !progressState.startTime || !progressState.estimatedTotalTime || progressState.estimatedTotalTime <= 0) {
      return 0;
    }
    
    const elapsed = elapsedTime.value;
    if (elapsed <= 0 || isNaN(elapsed)) return 0;
    
    const percent = (elapsed / progressState.estimatedTotalTime) * 100;
    const result = Math.min(100, Math.max(0, Math.floor(percent)));
    return isNaN(result) ? 0 : result;
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
      stepProgress: 0,
      totalProgress: 5, // Start with 5% to show immediate progress
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
      progressState.stepProgress = Math.max(0, Math.min(100, update.progress));
    }
    
    if (update.total_progress !== undefined && update.total_progress !== null) {
      progressState.totalProgress = Math.max(0, Math.min(100, update.total_progress));
    }
    
    // Update elapsed time from backend if provided (check both snake_case and camelCase)
    if (update.elapsedTime !== undefined && update.elapsedTime !== null) {
      progressState.elapsedTime = Math.max(0, update.elapsedTime);
    } else if (update.elapsed_time !== undefined && update.elapsed_time !== null) {
      progressState.elapsedTime = Math.max(0, update.elapsed_time);
    }
    
    if (update.citation_info) {
      progressState.citationInfo = update.citation_info;
    }
    
    if (update.rate_limit_info) {
      progressState.rateLimitInfo = update.rate_limit_info;
    }
    
    // Update start time from backend if provided (check both snake_case and camelCase)
    if (update.startTime !== undefined && update.startTime !== null) {
      progressState.startTime = update.startTime;
    } else if (update.start_time !== undefined && update.start_time !== null) {
      progressState.startTime = update.start_time;
    }
    
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

  const setError = (error) => {
    console.error('Progress error:', error);
    progressState.processingError = error;
    progressState.canRetry = true;
    progressState.isActive = false;
  };
  
  const clearError = () => {
    console.log('Clearing progress error');
    progressState.processingError = null;
    progressState.canRetry = false;
  };

  const completeProgress = (resultData = null, route = null) => {
    console.log('Progress completed:', resultData, 'for route:', route);
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
    Object.assign(progressState, {
      isActive: false,
      taskId: null,
      startTime: null,
      estimatedTotalTime: 0,
      elapsedTime: null,
      currentStep: '',
      stepProgress: 0,
      totalProgress: 0,
      processingSteps: [],
      actualTimes: {},
      citationInfo: null,
      rateLimitInfo: null,
      processingError: null,
      canRetry: false,
      uploadType: null,
      uploadData: null,
      hasResults: false,
      resultData: null
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
      const eventSource = new EventSource(`/casestrainer/api/analyze/verification-stream/${requestId}`);
      
      eventSource.onopen = () => {
        console.log('Verification stream connected');
        progressState.verificationStatus.status = 'queued';
      };
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Verification stream event:', data);
          
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
      progressState.verificationStream.close();
      progressState.verificationStream = null;
    }
    progressState.verificationStatus.status = 'idle';
    progressState.verificationStatus.isVerifying = false;
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
