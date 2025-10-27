<template>
  <transition name="fade">
    <div v-if="isProcessing" class="simple-progress-container">
      <div class="progress-card">
        <!-- Header with Icon -->
        <div class="progress-header">
          <div class="icon-wrapper">
            <div v-if="isComplete" class="success-icon">
              <i class="bi bi-check-circle-fill"></i>
            </div>
            <div v-else-if="hasError" class="error-icon">
              <i class="bi bi-exclamation-triangle-fill"></i>
            </div>
            <div v-else class="loading-spinner">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
            </div>
          </div>
          
          <div class="header-content">
            <h4 class="title">
              <span v-if="isComplete">Processing Complete</span>
              <span v-else-if="hasError">Processing Failed</span>
              <span v-else>Processing Content</span>
            </h4>
            <p class="subtitle">{{ currentMessage }}</p>
          </div>
        </div>

        <!-- Main Progress Bar -->
        <div v-if="!hasError" class="progress-section">
          <div class="progress-bar-wrapper">
            <div class="progress" style="height: 32px; border-radius: 8px; overflow: hidden;">
              <div 
                class="progress-bar progress-bar-striped"
                :class="{ 
                  'progress-bar-animated': isActive,
                  'bg-success': isComplete,
                  'bg-primary': !isComplete
                }"
                role="progressbar"
                :style="{ width: displayPercent + '%', transition: 'width 0.5s ease-in-out' }" 
                :aria-valuenow="displayPercent" 
                aria-valuemin="0" 
                aria-valuemax="100"
              >
                <span class="progress-label fw-bold">{{ displayPercent }}%</span>
              </div>
            </div>
          </div>

          <!-- Processing Stats -->
          <div class="stats-row">
            <div class="stat-item">
              <i class="bi bi-clock me-1"></i>
              <span>{{ elapsedTimeFormatted }}</span>
            </div>
            <div v-if="processingMode" class="stat-item">
              <i class="bi bi-cpu me-1"></i>
              <span class="text-capitalize">{{ processingMode }} Mode</span>
            </div>
            <div v-if="pollCount > 0" class="stat-item text-muted">
              <small>Updates: {{ pollCount }}</small>
            </div>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="hasError && !isComplete" class="error-section">
          <div class="alert alert-danger mb-0">
            <i class="bi bi-exclamation-triangle-fill me-2"></i>
            {{ errorMessage }}
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { globalProgress } from '@/stores/progressStore'

const props = defineProps({
  componentId: {
    type: String,
    default: 'default'
  }
})

// Reactive state
const currentPercent = ref(0)
const displayPercent = ref(0)
const currentMessage = ref('Initializing...')
const elapsedTime = ref(0)
const pollCount = ref(0)
const processingMode = ref('')
const hasError = ref(false)
const errorMessage = ref('')
const isComplete = ref(false)

// Timers
let elapsedTimer = null
let smoothProgressTimer = null

// Computed
const isProcessing = computed(() => {
  return globalProgress.progressState.isActive || 
         globalProgress.progressState.hasResults ||
         hasError.value
})

const isActive = computed(() => {
  return globalProgress.progressState.isActive && !isComplete.value && !hasError.value
})

const elapsedTimeFormatted = computed(() => {
  const seconds = Math.floor(elapsedTime.value / 1000)
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  
  if (mins > 0) {
    return `${mins}m ${secs}s`
  }
  return `${secs}s`
})

// Smooth progress animation
const animateProgress = (targetPercent) => {
  const startPercent = displayPercent.value
  const diff = targetPercent - startPercent
  
  if (Math.abs(diff) < 1) {
    displayPercent.value = targetPercent
    return
  }
  
  // Animate over 500ms
  const steps = 10
  const increment = diff / steps
  let currentStep = 0
  
  if (smoothProgressTimer) {
    clearInterval(smoothProgressTimer)
  }
  
  smoothProgressTimer = setInterval(() => {
    currentStep++
    if (currentStep >= steps) {
      displayPercent.value = targetPercent
      clearInterval(smoothProgressTimer)
      smoothProgressTimer = null
    } else {
      displayPercent.value = Math.round(startPercent + (increment * currentStep))
    }
  }, 50)
}

// Watch for progress updates
watch(
  () => globalProgress.progressState,
  (newState) => {
    // Update current percent
    const newPercent = Math.min(100, Math.max(0, 
      newState.totalProgress || 
      newState.progressPercent || 
      0
    ))
    
    if (newPercent !== currentPercent.value) {
      currentPercent.value = newPercent
      animateProgress(newPercent)
      pollCount.value++
    }
    
    // Update message
    if (newState.currentStep) {
      currentMessage.value = newState.currentStep
    }
    
    // Check for completion - ONLY when results are actually available
    // Don't mark complete just because progress hits 100% - backend may still be working
    if (newState.hasResults && newState.resultData) {
      isComplete.value = true
      displayPercent.value = 100
      currentMessage.value = 'Processing completed successfully'
      
      // Hide after 2 seconds
      setTimeout(() => {
        if (elapsedTimer) {
          clearInterval(elapsedTimer)
          elapsedTimer = null
        }
      }, 2000)
    } else if (newPercent >= 100 && !isComplete.value) {
      // Progress reached 100% but no results yet - keep showing "Processing..."
      currentMessage.value = 'Finalizing results...'
    }
    
    // Check for errors
    if (newState.processingError) {
      hasError.value = true
      errorMessage.value = newState.processingError
      displayPercent.value = 0
      
      if (elapsedTimer) {
        clearInterval(elapsedTimer)
        elapsedTimer = null
      }
    }
  },
  { deep: true, immediate: true }
)

// Start elapsed time counter
onMounted(() => {
  const startTime = Date.now()
  
  elapsedTimer = setInterval(() => {
    elapsedTime.value = Date.now() - startTime
  }, 100)
  
  // Detect processing mode
  const metadata = globalProgress.progressState.metadata || {}
  processingMode.value = metadata.processing_mode || ''
})

onUnmounted(() => {
  if (elapsedTimer) {
    clearInterval(elapsedTimer)
  }
  if (smoothProgressTimer) {
    clearInterval(smoothProgressTimer)
  }
})
</script>

<style scoped>
.simple-progress-container {
  margin: 2rem 0;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.progress-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  padding: 2rem;
  border: 1px solid #e5e7eb;
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.icon-wrapper {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #f8f9fa;
}

.loading-spinner .spinner-border {
  width: 2rem;
  height: 2rem;
}

.success-icon {
  font-size: 2rem;
  color: #28a745;
}

.error-icon {
  font-size: 2rem;
  color: #dc3545;
}

.header-content {
  flex: 1;
  min-width: 0;
}

.title {
  margin: 0 0 0.25rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.subtitle {
  margin: 0;
  font-size: 0.95rem;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.progress-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.progress-bar-wrapper {
  position: relative;
}

.progress {
  background-color: #e5e7eb;
}

.progress-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  transition: width 0.5s ease-in-out;
}

.progress-label {
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  font-size: 1rem;
}

.stats-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-top: 0.5rem;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.stat-item i {
  font-size: 1rem;
}

.error-section {
  margin-top: 1rem;
}

.alert {
  border-radius: 8px;
}

/* Responsive */
@media (max-width: 640px) {
  .progress-card {
    padding: 1.5rem;
  }
  
  .progress-header {
    gap: 1rem;
  }
  
  .icon-wrapper {
    width: 48px;
    height: 48px;
  }
  
  .title {
    font-size: 1.1rem;
  }
  
  .subtitle {
    font-size: 0.875rem;
  }
  
  .stats-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
