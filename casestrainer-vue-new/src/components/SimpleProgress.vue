<template>
  <transition name="fade">
    <div
      v-if="isProcessing"
      class="simple-progress-container"
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <div class="progress-card">

        <!-- Queue Position Banner (shown while job waits in Redis queue) -->
        <div v-if="queueInfo" class="queue-banner">
          <div class="queue-banner-icon">
            <i class="bi bi-hourglass-split" aria-hidden="true"></i>
          </div>
          <div class="queue-banner-body">
            <strong>Your brief is in the queue.</strong>
            <span v-if="queueInfo.position >= 0">
              Position <strong>{{ queueInfo.position + 1 }}</strong>
              <span v-if="queueInfo.queueTotal"> of {{ queueInfo.queueTotal }}</span>
            </span>
            <span v-if="queueInfo.estimatedWaitHuman" class="queue-eta">
              — estimated wait: <strong>{{ queueInfo.estimatedWaitHuman }}</strong>
            </span>
          </div>
        </div>

        <!-- Main Progress Bar -->
        <div v-if="!hasError" class="progress-section">
          <div class="progress-center-text">
            <p class="subtitle centered-message">{{ currentMessage }}</p>
          </div>
          <div class="processing-indicator" v-if="isActive">
            <i class="bi bi-arrow-repeat spinning me-1" aria-hidden="true"></i>
            <span>Still processing</span>
            <span class="dot-sep">•</span>
            <span>{{ elapsedTimeFormatted }} elapsed</span>
            <span class="dot-sep">•</span>
            <span>{{ pollCount }} updates</span>
          </div>
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

        </div>

        <!-- Error Message -->
        <div v-if="hasError && !isComplete" class="error-section">
          <div class="alert alert-danger mb-0">
            <i class="bi bi-exclamation-triangle-fill me-2" aria-hidden="true"></i>
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
const hasError = ref(false)
const errorMessage = ref('')
const isComplete = ref(false)

// Computed for timeout state
const isTimeout = computed(() => {
  return globalProgress.progressState.isTimeout || false
})

// Queue position info from store
const queueInfo = computed(() => globalProgress.progressState.queueInfo || null)

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

// Track when analysis actually starts
let timerStartTime = null

// Watch for progress updates - use deep watch to detect nested changes
watch(
  () => globalProgress.progressState,
  (newState) => {
    // CRITICAL FIX: Only start timer when analysis actually begins (isActive becomes true)
    if (newState.isActive && !timerStartTime) {
      timerStartTime = Date.now()
      elapsedTime.value = 0
      pollCount.value = 0 // Reset poll count for new analysis
      
      // Start elapsed time counter when analysis begins
      if (elapsedTimer) {
        clearInterval(elapsedTimer)
      }
      elapsedTimer = setInterval(() => {
        if (timerStartTime) {
          elapsedTime.value = Date.now() - timerStartTime
        }
      }, 100)
    }
    
    // CRITICAL FIX: Only reset timer if startTime actually changed AND it's a different analysis
    // Don't reset if startTime is just being updated with the same value
    // Convert startTime to milliseconds if it's in seconds (backend sends seconds)
    const stateStartTime = newState.startTime ? (newState.startTime < 10000000000 ? newState.startTime * 1000 : newState.startTime) : null
    const localStartTimeMs = timerStartTime
    if (newState.isActive && timerStartTime && stateStartTime && Math.abs(stateStartTime - localStartTimeMs) > 5000) {
      // New analysis started - reset timer (only if startTime differs by more than 5 seconds)
      timerStartTime = Date.now()
      elapsedTime.value = 0
      pollCount.value = 0
    }
    
    // Stop timer when analysis completes or errors
    if (!newState.isActive && timerStartTime) {
      if (elapsedTimer) {
        clearInterval(elapsedTimer)
        elapsedTimer = null
      }
      timerStartTime = null
    }
    
    // Update current percent
    const newPercent = Math.min(100, Math.max(0, 
      newState.totalProgress || 
      newState.progressPercent || 
      0
    ))
    
    // CRITICAL FIX: Use pollCount from progressState if available, otherwise increment local counter
    // This ensures the counter increments even if the watcher doesn't fire due to unchanged values
    if (newState.pollCount !== undefined && newState.pollCount !== null) {
      pollCount.value = newState.pollCount
    } else {
      pollCount.value++
    }
    
    if (newPercent !== currentPercent.value) {
      currentPercent.value = newPercent
      animateProgress(newPercent)
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
        timerStartTime = null
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
      timerStartTime = null
    }
    
  },
  { deep: true, immediate: true }
)

// Initialize component (don't start timer here)
onMounted(() => {
  // Don't start timer on mount - wait for isActive to become true
  // Timer will start when analyze button is clicked and progress becomes active
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
  background: var(--card-bg, #fff);
  border-radius: 16px;
  box-shadow: 0 4px 24px var(--ui-card-shadow, rgba(0, 0, 0, 0.08));
  padding: 2rem;
  border: 1px solid var(--border, #e5e7eb);
  color: var(--foreground, inherit);
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
  background: var(--ui-surface-2, #f8f9fa);
}

.loading-spinner i {
  font-size: 2rem;
}

.success-icon {
  font-size: 2rem;
  color: var(--success, #28a745);
}

.error-icon {
  font-size: 2rem;
  color: var(--danger, #dc3545);
}

.header-content {
  flex: 1;
  min-width: 0;
}

.title {
  margin: 0 0 0.25rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--foreground, #1f2937);
}

.subtitle {
  margin: 0;
  font-size: 0.95rem;
  color: var(--ui-text-secondary, #6b7280);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.progress-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.progress-center-text {
  text-align: center;
}

.centered-message {
  white-space: normal;
  overflow: visible;
  text-overflow: unset;
}

.progress-bar-wrapper {
  position: relative;
}

.processing-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: var(--ui-text-muted, #4b5563);
}

.spinning {
  display: inline-block;
  animation: progress-spin 1s linear infinite;
}

.dot-sep {
  color: var(--ui-text-muted, #9ca3af);
}

@keyframes progress-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.progress {
  background-color: var(--border, #e5e7eb);
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

.centered-stats {
  justify-content: center;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: var(--ui-text-secondary, #6b7280);
}

.stat-item i {
  font-size: 1rem;
}

.queue-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  margin-bottom: 1.25rem;
  background: #fff8e1;
  border: 1px solid #ffe082;
  border-left: 4px solid #f9a825;
  border-radius: 8px;
  font-size: 0.925rem;
  color: #5d4037;
  line-height: 1.5;
}

.queue-banner-icon {
  font-size: 1.25rem;
  color: #f9a825;
  flex-shrink: 0;
  padding-top: 0.1rem;
}

.queue-banner-body {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 0.5rem;
  align-items: center;
}

.queue-eta {
  color: #795548;
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
