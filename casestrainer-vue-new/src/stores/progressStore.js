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
    if (!progressState.startTime) return 0;
    return (Date.now() - progressState.startTime) / 1000;
  });

  const remainingTime = computed(() => {
    if (!progressState.estimatedTotalTime) return 0;
    return Math.max(0, progressState.estimatedTotalTime - elapsedTime.value);
  });

  const progressPercent = computed(() => {
    if (!progressState.estimatedTotalTime) return 0;
    return Math.min(100, (elapsedTime.value / progressState.estimatedTotalTime) * 100);
  });

  const currentStepProgress = computed(() => {
    if (!progressState.processingSteps.length) return 0;
    const currentStepIndex = progressState.processingSteps.findIndex(
      step => step.step === progressState.currentStep
    );
    if (currentStepIndex === -1) return 0;
    
    const step = progressState.processingSteps[currentStepIndex];
    const stepElapsed = elapsedTime.value - (step.startTime || 0);
    return Math.min(100, (stepElapsed / step.estimated_time) * 100);
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
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  // Core progress management functions
  const startProgress = (uploadType, uploadData, estimatedTime = 30) => {
    console.log('Starting unified progress tracking:', { uploadType, estimatedTime });
    
    // Reset all state
    Object.assign(progressState, {
      isActive: true,
      taskId: null,
      startTime: Date.now(),
      estimatedTotalTime: estimatedTime,
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
