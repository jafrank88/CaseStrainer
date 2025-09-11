import { ref, computed, reactive, watch } from 'vue';

// Global progress state that persists across components and navigation
const progressState = reactive({
  // Core progress tracking
  isActive: false,
  taskId: null,
  startTime: null,
  estimatedTotalTime: 0,
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
    if (!progressState.startTime || typeof progressState.startTime !== 'number') {
      console.log('Progress debug: Invalid startTime, returning 0:', progressState.startTime);
      return 0;
    }
    const elapsed = (Date.now() - progressState.startTime) / 1000;
    const result = isNaN(elapsed) ? 0 : Math.max(0, elapsed);
    console.log('Progress debug: elapsedTime computed:', { startTime: progressState.startTime, elapsed, result });
    return result;
  });

  const remainingTime = computed(() => {
    if (!progressState.estimatedTotalTime || progressState.estimatedTotalTime <= 0 || typeof progressState.estimatedTotalTime !== 'number') {
      console.log('Progress debug: Invalid estimatedTotalTime, returning 0:', progressState.estimatedTotalTime);
      return 0;
    }
    const remaining = progressState.estimatedTotalTime - elapsedTime.value;
    const result = isNaN(remaining) ? 0 : Math.max(0, remaining);
    console.log('Progress debug: remainingTime computed:', { estimatedTotalTime: progressState.estimatedTotalTime, elapsedTime: elapsedTime.value, remaining, result });
    return result;
  });

  const progressPercent = computed(() => {
    // Additional safety check for startTime
    if (!progressState.startTime || !progressState.estimatedTotalTime || progressState.estimatedTotalTime <= 0) {
      console.log('Progress debug: Invalid progress state, returning 0:', { 
        startTime: progressState.startTime, 
        estimatedTotalTime: progressState.estimatedTotalTime 
      });
      return 0;
    }
    const percent = (elapsedTime.value / progressState.estimatedTotalTime) * 100;
    const result = isNaN(percent) ? 0 : Math.min(100, Math.max(0, percent));
    console.log('Progress debug: progressPercent computed:', { 
      startTime: progressState.startTime,
      estimatedTotalTime: progressState.estimatedTotalTime, 
      elapsedTime: elapsedTime.value, 
      percent, 
      result,
      startTimeType: typeof progressState.startTime,
      estimatedTimeType: typeof progressState.estimatedTotalTime
    });
    return result;
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
    const validEstimatedTime = Math.max(1, Math.floor(estimatedTime) || 30);
    
    // Reset all state
    Object.assign(progressState, {
      isActive: true,
      taskId: null,
      startTime: Date.now(),
      estimatedTotalTime: validEstimatedTime,
      currentStep: 'Initializing...',
      stepProgress: 0,
      totalProgress: 0,
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
    
    // Ensure the state is properly set before proceeding
    if (!progressState.startTime || !progressState.estimatedTotalTime) {
      console.error('Progress state initialization failed');
      throw new Error('Failed to initialize progress state');
    }
    
    console.log('Progress state initialized:', {
      startTime: progressState.startTime,
      estimatedTotalTime: progressState.estimatedTotalTime,
      uploadType: progressState.uploadType,
      startTimeType: typeof progressState.startTime,
      estimatedTimeType: typeof progressState.estimatedTotalTime
    });
    
    // Additional validation
    console.log('Progress validation check:', {
      hasStartTime: !!progressState.startTime,
      startTimeValid: progressState.startTime && typeof progressState.startTime === 'number',
      hasEstimatedTime: !!progressState.estimatedTotalTime,
      estimatedTimeValid: progressState.estimatedTotalTime && progressState.estimatedTotalTime > 0 && typeof progressState.estimatedTotalTime === 'number'
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
    
    if (update.progress !== undefined) {
      progressState.stepProgress = update.progress;
    }
    
    if (update.total_progress !== undefined) {
      progressState.totalProgress = update.total_progress;
    }
    
    if (update.citation_info) {
      progressState.citationInfo = update.citation_info;
    }
    
    if (update.rate_limit_info) {
      progressState.rateLimitInfo = update.rate_limit_info;
    }
    
    if (update.estimated_total_time) {
      progressState.estimatedTotalTime = update.estimated_total_time;
      
      // Debug: Check if estimatedTotalTime is being modified
      console.log('Progress debug: estimatedTotalTime updated:', {
        oldValue: progressState.estimatedTotalTime,
        newValue: update.estimated_total_time,
        type: typeof update.estimated_total_time
      });
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
    return progressState.isActive && !progressState.processingError && progressState.startTime && progressState.estimatedTotalTime > 0;
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
