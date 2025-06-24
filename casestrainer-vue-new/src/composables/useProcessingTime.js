import { ref, computed } from 'vue';

export function useProcessingTime() {
  const startTime = ref(null);
  const estimatedTotalTime = ref(0);
  const currentStep = ref('');
  const stepProgress = ref(0);
  const processingSteps = ref([]);
  const actualTimes = ref({});
  
  // Add missing reactive variables
  const citationInfo = ref(null);
  const rateLimitInfo = ref(null);
  const timeout = ref(null);
  const processingError = ref(null);
  const canRetry = ref(false);
  
  const elapsedTime = computed(() => {
    if (!startTime.value) return 0;
    return (Date.now() - startTime.value) / 1000;
  });
  
  const remainingTime = computed(() => {
    if (!estimatedTotalTime.value) return 0;
    return Math.max(0, estimatedTotalTime.value - elapsedTime.value);
  });
  
  const totalProgress = computed(() => {
    if (!estimatedTotalTime.value) return 0;
    return Math.min(100, (elapsedTime.value / estimatedTotalTime.value) * 100);
  });
  
  const currentStepProgress = computed(() => {
    if (!processingSteps.value.length) return 0;
    const currentStepIndex = processingSteps.value.findIndex(step => step.step === currentStep.value);
    if (currentStepIndex === -1) return 0;
    
    const step = processingSteps.value[currentStepIndex];
    const stepElapsed = elapsedTime.value - (step.startTime || 0);
    return Math.min(100, (stepElapsed / step.estimated_time) * 100);
  });
  
  const formatTime = (seconds) => {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };
  
  const startProcessing = (timeEstimate) => {
    startTime.value = Date.now();
    if (typeof timeEstimate === 'object' && timeEstimate !== null && Array.isArray(timeEstimate.steps)) {
      estimatedTotalTime.value = timeEstimate.estimated_total_time;
      processingSteps.value = timeEstimate.steps.map(step => ({
        step: step[0],
        estimated_time: step[1],
        startTime: null,
        progress: 0
      }));
      currentStep.value = processingSteps.value[0]?.step || '';
    } else if (typeof timeEstimate === 'number') {
      estimatedTotalTime.value = timeEstimate;
      processingSteps.value = [];
      currentStep.value = '';
    } else {
      estimatedTotalTime.value = 0;
      processingSteps.value = [];
      currentStep.value = '';
    }
    stepProgress.value = 0;
  };
  
  // Add missing functions
  const stopProcessing = () => {
    startTime.value = null;
    estimatedTotalTime.value = 0;
    currentStep.value = '';
    stepProgress.value = 0;
  };
  
  const updateProgress = (progress) => {
    if (typeof progress === 'object' && progress.step) {
      updateStep(progress.step, progress.progress || 0);
    } else if (typeof progress === 'number') {
      stepProgress.value = progress;
    }
  };
  
  const setSteps = (steps) => {
    if (Array.isArray(steps)) {
      processingSteps.value = steps.map(step => ({
        step: typeof step === 'string' ? step : step.step,
        estimated_time: typeof step === 'object' ? step.estimated_time : 10,
        startTime: null,
        progress: 0
      }));
    }
  };
  
  const resetProcessing = () => {
    startTime.value = null;
    estimatedTotalTime.value = 0;
    currentStep.value = '';
    stepProgress.value = 0;
    processingSteps.value = [];
    actualTimes.value = {};
    citationInfo.value = null;
    rateLimitInfo.value = null;
    timeout.value = null;
    processingError.value = null;
    canRetry.value = false;
  };
  
  const setProcessingError = (error) => {
    processingError.value = error;
    canRetry.value = true;
  };
  
  const updateStep = (stepName, progress) => {
    const stepIndex = processingSteps.value.findIndex(step => step.step === stepName);
    if (stepIndex === -1) return;
    
    if (stepIndex === 0 || processingSteps.value[stepIndex - 1].progress === 100) {
      currentStep.value = stepName;
      if (!processingSteps.value[stepIndex].startTime) {
        processingSteps.value[stepIndex].startTime = Date.now();
      }
    }
    
    processingSteps.value[stepIndex].progress = progress;
    stepProgress.value = progress;
  };
  
  const completeStep = (stepName) => {
    updateStep(stepName, 100);
    const nextStepIndex = processingSteps.value.findIndex(step => step.step === stepName) + 1;
    if (nextStepIndex < processingSteps.value.length) {
      currentStep.value = processingSteps.value[nextStepIndex].step;
      processingSteps.value[nextStepIndex].startTime = Date.now();
    }
  };
  
  const updateActualTimes = (times) => {
    actualTimes.value = times;
  };
  
  const reset = () => {
    startTime.value = null;
    estimatedTotalTime.value = 0;
    currentStep.value = '';
    stepProgress.value = 0;
    processingSteps.value = [];
    actualTimes.value = {};
    citationInfo.value = null;
    rateLimitInfo.value = null;
    timeout.value = null;
    processingError.value = null;
    canRetry.value = false;
  };
  
  return {
    // State
    startTime,
    estimatedTotalTime,
    currentStep,
    stepProgress,
    processingSteps,
    actualTimes,
    citationInfo,
    rateLimitInfo,
    timeout,
    processingError,
    canRetry,
    
    // Computed
    elapsedTime,
    remainingTime,
    totalProgress,
    currentStepProgress,
    
    // Methods
    startProcessing,
    stopProcessing,
    updateProgress,
    setSteps,
    resetProcessing,
    setProcessingError,
    updateStep,
    completeStep,
    updateActualTimes,
    reset,
    formatTime
  };
} 