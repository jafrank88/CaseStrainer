<template>
  <div v-if="shouldShowProgress" class="unified-progress-container">
    <!-- Progress Card -->
    <div class="progress-card" :class="{ 'error-state': progressState.processingError }">
      <!-- Header -->
      <div class="progress-header">
        <div class="progress-icon">
          <div v-if="progressState.processingError" class="error-icon">
            <i class="bi bi-exclamation-triangle"></i>
          </div>
          <div v-else-if="progressState.hasResults" class="success-icon">
            <i class="bi bi-check-circle-fill"></i>
          </div>
          <div v-else class="loading-icon">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Processing...</span>
            </div>
          </div>
        </div>
        
        <div class="progress-title-section">
          <h3 class="progress-title">
            <span v-if="progressState.processingError">Processing Failed</span>
            <span v-else-if="progressState.hasResults">Processing Complete</span>
            <span v-else>Processing {{ getUploadTypeLabel() }}</span>
          </h3>
          <p class="progress-subtitle">
            <span v-if="progressState.processingError">{{ progressState.processingError }}</span>
            <span v-else-if="progressState.hasResults">Analysis completed successfully</span>
            <span v-else>{{ progressState.currentStep }}</span>
          </p>
        </div>
      </div>

      <!-- Progress Content -->
      <div v-if="!progressState.processingError" class="progress-content">
        <!-- Progress Stats -->
        <div class="progress-stats">
          <div class="stat-item">
            <i class="bi bi-clock text-primary"></i>
            <span class="stat-label">Elapsed:</span>
            <span class="stat-value">{{ formatTime(elapsedTime) }}</span>
          </div>
          
          <div v-if="progressState.isActive && remainingTime > 0" class="stat-item">
            <i class="bi bi-hourglass-split text-info"></i>
            <span class="stat-label">Remaining:</span>
            <span class="stat-value">{{ formatTime(remainingTime) }}</span>
          </div>
          
          <div v-if="progressState.citationInfo" class="stat-item">
            <i class="bi bi-list-ol text-success"></i>
            <span class="stat-label">Citations:</span>
            <span class="stat-value">
              {{ progressState.citationInfo.processed || 0 }} of {{ progressState.citationInfo.total || 0 }}
            </span>
          </div>
        </div>

        <!-- Main Progress Bar -->
        <div class="main-progress-section">
          <div class="progress-bar-container">
            <div class="progress" style="height: 1.5rem; border-radius: 0.75rem;">
              <div 
                class="progress-bar progress-bar-striped"
                :class="[progressBarClass, { 'progress-bar-animated': progressState.isActive }]"
                role="progressbar"
                :style="{ width: progressPercent + '%' }" 
                :aria-valuenow="progressPercent" 
                aria-valuemin="0" 
                aria-valuemax="100"
              >
                <span class="progress-text">{{ Math.round(progressPercent) }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Step Progress -->
        <div v-if="progressState.processingSteps.length > 0" class="steps-progress">
          <div class="steps-header">
            <h6><i class="bi bi-list-task me-2"></i>Processing Steps</h6>
          </div>
          <div class="steps-list">
            <div 
              v-for="(step, index) in progressState.processingSteps" 
              :key="index"
              class="step-item"
              :class="{
                'active': step.step === progressState.currentStep,
                'completed': step.completed,
                'pending': !step.completed && step.step !== progressState.currentStep
              }"
            >
              <div class="step-icon">
                <i v-if="step.completed" class="bi bi-check-circle-fill"></i>
                <i v-else-if="step.step === progressState.currentStep" class="bi bi-arrow-right-circle-fill"></i>
                <i v-else class="bi bi-circle"></i>
              </div>
              <div class="step-content">
                <span class="step-name">{{ step.step }}</span>
                <span v-if="step.estimated_time" class="step-time">
                  (~{{ step.estimated_time }}s)
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Rate Limit Info -->
        <div v-if="progressState.rateLimitInfo" class="rate-limit-info">
          <div class="alert alert-info">
            <i class="bi bi-info-circle me-2"></i>
            <strong>Rate Limit:</strong> 
            {{ progressState.rateLimitInfo.remaining || 0 }} requests remaining
            <span v-if="progressState.rateLimitInfo.reset_time">
              (resets in {{ formatTime(progressState.rateLimitInfo.reset_time) }})
            </span>
          </div>
        </div>
      </div>

      <!-- Error Actions -->
      <div v-if="progressState.processingError" class="error-actions">
        <button 
          v-if="progressState.canRetry"
          @click="handleRetry"
          class="btn btn-primary me-2"
        >
          <i class="bi bi-arrow-clockwise me-1"></i>
          Retry Analysis
        </button>
        <button @click="handleReset" class="btn btn-outline-secondary">
          <i class="bi bi-x-circle me-1"></i>
          Clear Error
        </button>
      </div>

      <!-- Completion Actions -->
      <div v-if="progressState.hasResults && !progressState.isActive" class="completion-actions">
        <div class="alert alert-success">
          <i class="bi bi-check-circle-fill me-2"></i>
          <strong>Analysis Complete!</strong> Your results are ready.
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';
import { useUnifiedProgress } from '@/stores/progressStore';

export default {
  name: 'UnifiedProgress',
  emits: ['retry', 'reset', 'complete'],
  setup(props, { emit }) {
    const {
      progressState,
      elapsedTime,
      remainingTime,
      progressPercent,
      progressBarClass,
      shouldShowProgress,
      formatTime,
      retryProgress,
      resetProgress
    } = useUnifiedProgress();

    const getUploadTypeLabel = () => {
      switch (progressState.uploadType) {
        case 'file': return 'Document';
        case 'url': return 'URL Content';
        case 'text': return 'Text';
        default: return 'Content';
      }
    };

    const handleRetry = () => {
      const success = retryProgress();
      if (success) {
        emit('retry', {
          uploadType: progressState.uploadType,
          uploadData: progressState.uploadData
        });
      }
    };

    const handleReset = () => {
      resetProgress();
      emit('reset');
    };

    return {
      progressState,
      elapsedTime,
      remainingTime,
      progressPercent,
      progressBarClass,
      shouldShowProgress,
      formatTime,
      getUploadTypeLabel,
      handleRetry,
      handleReset
    };
  }
};
</script>

<style scoped>
.unified-progress-container {
  margin: 2rem 0;
}

.progress-card {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
  overflow: hidden;
  transition: all 0.3s ease;
}

.progress-card.error-state {
  border-color: #dc3545;
  box-shadow: 0 4px 6px rgba(220, 53, 69, 0.2);
}

.progress-header {
  display: flex;
  align-items: center;
  padding: 1.5rem;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 1px solid #dee2e6;
}

.progress-icon {
  margin-right: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
}

.loading-icon .spinner-border {
  width: 2.5rem;
  height: 2.5rem;
}

.success-icon i {
  font-size: 2.5rem;
  color: #28a745;
}

.error-icon i {
  font-size: 2.5rem;
  color: #dc3545;
}

.progress-title-section {
  flex: 1;
}

.progress-title {
  margin: 0 0 0.25rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #495057;
}

.progress-subtitle {
  margin: 0;
  color: #6c757d;
  font-size: 0.95rem;
}

.progress-content {
  padding: 1.5rem;
}

.progress-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.stat-item i {
  font-size: 1rem;
}

.stat-label {
  color: #6c757d;
  font-weight: 500;
}

.stat-value {
  color: #495057;
  font-weight: 600;
}

.main-progress-section {
  margin-bottom: 1.5rem;
}

.progress-bar-container {
  position: relative;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-weight: 600;
  font-size: 0.85rem;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.steps-progress {
  margin-bottom: 1.5rem;
}

.steps-header h6 {
  margin: 0 0 1rem 0;
  color: #495057;
  font-weight: 600;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
}

.step-item.active {
  background-color: rgba(0, 123, 255, 0.1);
  border: 1px solid rgba(0, 123, 255, 0.2);
}

.step-item.completed {
  background-color: rgba(40, 167, 69, 0.1);
  border: 1px solid rgba(40, 167, 69, 0.2);
}

.step-item.pending {
  background-color: rgba(108, 117, 125, 0.05);
  border: 1px solid rgba(108, 117, 125, 0.1);
}

.step-icon i {
  font-size: 1.1rem;
}

.step-item.active .step-icon i {
  color: #007bff;
}

.step-item.completed .step-icon i {
  color: #28a745;
}

.step-item.pending .step-icon i {
  color: #6c757d;
}

.step-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.step-name {
  font-weight: 500;
  color: #495057;
}

.step-time {
  font-size: 0.8rem;
  color: #6c757d;
}

.rate-limit-info {
  margin-bottom: 1rem;
}

.error-actions,
.completion-actions {
  padding: 1.5rem;
  background-color: #f8f9fa;
  border-top: 1px solid #dee2e6;
}

.error-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .progress-header {
    flex-direction: column;
    text-align: center;
    gap: 1rem;
  }
  
  .progress-stats {
    flex-direction: column;
    gap: 1rem;
  }
  
  .error-actions {
    flex-direction: column;
  }
  
  .error-actions .btn {
    width: 100%;
  }
}
</style>
