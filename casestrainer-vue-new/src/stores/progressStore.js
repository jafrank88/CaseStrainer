import { ref, computed, reactive } from 'vue';

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
  resultData: null
});

export function useUnifiedProgress() {
  // Computed properties
  const elapsedTime = computed(() => {
    if (!progressState.startTime) {
      console.log('Progress debug: No startTime, returning 0');
      return 0;
    }
    const elapsed = (Date.now() - progressState.startTime) / 1000;
    const result = isNaN(elapsed) ? 0 : Math.max(0, elapsed);
    console.log('Progress debug: elapsedTime computed:', { startTime: progressState.startTime, elapsed, result });
    return result;
  });

  const remainingTime = computed(() => {
    if (!progressState.estimatedTotalTime || progressState.estimatedTotalTime <= 0) {
      console.log('Progress debug: Invalid estimatedTotalTime, returning 0:', progressState.estimatedTotalTime);
      return 0;
    }
    const remaining = progressState.estimatedTotalTime - elapsedTime.value;
    const result = isNaN(remaining) ? 0 : Math.max(0, remaining);
    console.log('Progress debug: remainingTime computed:', { estimatedTotalTime: progressState.estimatedTotalTime, elapsedTime: elapsedTime.value, remaining, result });
    return result;
  });

  const progressPercent = computed(() => {
    if (!progressState.estimatedTotalTime || progressState.estimatedTotalTime <= 0) {
      console.log('Progress debug: Invalid estimatedTotalTime for progress, returning 0:', progressState.estimatedTotalTime);
      return 0;
    }
    const percent = (elapsedTime.value / progressState.estimatedTotalTime) * 100;
    const result = isNaN(percent) ? 0 : Math.min(100, Math.max(0, percent));
    console.log('Progress debug: progressPercent computed:', { estimatedTotalTime: progressState.estimatedTotalTime, elapsedTime: elapsedTime.value, percent, result });
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
    
    console.log('Progress state initialized:', {
      startTime: progressState.startTime,
      estimatedTotalTime: progressState.estimatedTotalTime,
      uploadType: progressState.uploadType
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
      startTime: null,
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
    }
  };

  const setError = (error) => {
    console.error('Progress error:', error);
    progressState.processingError = error;
    progressState.canRetry = true;
    progressState.isActive = false;
  };

  const completeProgress = (resultData = null) => {
    console.log('Progress completed:', resultData);
    progressState.isActive = false;
    progressState.currentStep = 'Completed';
    progressState.totalProgress = 100;
    progressState.hasResults = !!resultData;
    progressState.resultData = resultData;
    
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
    return progressState.isActive || progressState.processingError;
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
    completeProgress,
    resetProgress,
    retryProgress
  };
}

// Export a singleton instance for global use
export const globalProgress = useUnifiedProgress();
