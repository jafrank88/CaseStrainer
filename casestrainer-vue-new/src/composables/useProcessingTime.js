import { ref, computed } from 'vue';

export function useProcessingTime() {
  const startTime = ref(null);
  const estimatedTotalTime = ref(0);
  const currentStep = ref('');
  const stepProgress = ref(0);
  const processingSteps = ref([]);
  const actualTimes = ref({});
  
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
  };
  
  return {
    // State
    startTime,
    estimatedTotalTime,
    currentStep,
    stepProgress,
    processingSteps,
    actualTimes,
    
    // Computed
    elapsedTime,
    remainingTime,
    totalProgress,
    currentStepProgress,
    
    // Methods
    startProcessing,
    updateStep,
    completeStep,
    updateActualTimes,
    reset,
    formatTime
  };
} 