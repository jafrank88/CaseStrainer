<template>
  <div class="processing-progress">
    <!-- Overall Progress -->
    <div class="progress-section">
      <h3>Overall Progress</h3>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${totalProgress}%` }"></div>
      </div>
      <div class="time-info">
        <span>Elapsed: {{ formatTime(elapsedTime) }}</span>
        <span>Remaining: {{ formatTime(remainingTime) }}</span>
        <span v-if="timeout" class="timeout-info" :class="{ 'warning': isTimeoutWarning }">
          Timeout: {{ formatTime(timeout - elapsedTime) }}
        </span>
      </div>
    </div>

    <!-- Citation Processing -->
    <div v-if="citationInfo" class="citation-section">
      <h3>Citation Processing</h3>
      <div class="citation-stats">
        <div class="stat">
          <span class="label">Total Citations:</span>
          <span class="value">{{ citationInfo.total }}</span>
        </div>
        <div class="stat">
          <span class="label">Unique Citations:</span>
          <span class="value">{{ citationInfo.unique }}</span>
        </div>
        <div class="stat">
          <span class="label">Processed:</span>
          <span class="value">{{ citationInfo.processed }}</span>
        </div>
        <div class="stat" v-if="citationInfo.unique">
          <span class="label">Processing Rate:</span>
          <span class="value">{{ formatProcessingRate(citationInfo) }}</span>
        </div>
      </div>
      <div class="rate-limit-info" v-if="rateLimitInfo">
        <div class="stat">
          <span class="label">API Rate Limit:</span>
          <span class="value">{{ rateLimitInfo.remaining }}/{{ rateLimitInfo.limit }}</span>
        </div>
        <div class="stat" v-if="rateLimitInfo.resetTime">
          <span class="label">Reset in:</span>
          <span class="value">{{ formatTime(rateLimitInfo.resetTime - Date.now()/1000) }}</span>
        </div>
      </div>
    </div>

    <!-- Current Step -->
    <div class="current-step" v-if="currentStep">
      <h3>Current Step</h3>
      <div class="step-info">
        <span class="step-name">{{ currentStep }}</span>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${currentStepProgress}%` }"></div>
        </div>
        <div class="time-info">
          <span>Elapsed: {{ formatTime(currentStepElapsed) }}</span>
          <span>Remaining: {{ formatTime(currentStepRemaining) }}</span>
        </div>
      </div>
    </div>

    <!-- Processing Steps -->
    <div class="steps-section">
      <h3>Processing Steps</h3>
      <div class="steps-list">
        <div v-for="step in processingSteps" 
             :key="step.step" 
             :class="['step', getStepClass(step)]">
          <div class="step-header">
            <span class="step-name">{{ step.step }}</span>
            <span class="step-status">{{ getStepStatus(step) }}</span>
          </div>
          <div class="progress-bar" v-if="step.progress !== undefined">
            <div class="progress-fill" :style="{ width: `${step.progress}%` }"></div>
          </div>
          <div class="time-info" v-if="step.estimated_time">
            <span>Estimated: {{ formatTime(step.estimated_time) }}</span>
            <span v-if="step.actual_time">Actual: {{ formatTime(step.actual_time) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Information -->
    <div v-if="error" class="error-section">
      <div class="error-message">
        <i class="fas fa-exclamation-circle"></i>
        {{ error }}
      </div>
      <button v-if="canRetry" @click="$emit('retry')" class="retry-button">
        Retry Processing
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProcessingProgress',
  props: {
    elapsedTime: {
      type: Number,
      required: true
    },
    remainingTime: {
      type: Number,
      required: true
    },
    totalProgress: {
      type: Number,
      required: true
    },
    currentStep: {
      type: String,
      default: ''
    },
    currentStepProgress: {
      type: Number,
      default: 0
    },
    processingSteps: {
      type: Array,
      default: () => []
    },
    actualTimes: {
      type: Object,
      default: () => ({})
    },
    citationInfo: {
      type: Object,
      default: null
    },
    rateLimitInfo: {
      type: Object,
      default: null
    },
    error: {
      type: String,
      default: ''
    },
    canRetry: {
      type: Boolean,
      default: false
    },
    timeout: {
      type: Number,
      default: null
    }
  },
  computed: {
    currentStepElapsed() {
      const step = this.processingSteps.find(s => s.step === this.currentStep)
      return step ? (Date.now()/1000 - step.start_time) : 0
    },
    currentStepRemaining() {
      const step = this.processingSteps.find(s => s.step === this.currentStep)
      if (!step || !step.estimated_time) return 0
      return Math.max(0, step.estimated_time - this.currentStepElapsed)
    },
    isTimeoutWarning() {
      if (!this.timeout) return false
      const timeRemaining = this.timeout - this.elapsedTime
      return timeRemaining < 60 // Show warning when less than 1 minute remaining
    }
  },
  methods: {
    formatTime(seconds) {
      if (seconds < 0) return '0s'
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = Math.round(seconds % 60)
      if (minutes > 0) {
        return `${minutes}m ${remainingSeconds}s`
      }
      return `${remainingSeconds}s`
    },
    getStepClass(step) {
      if (step.progress === 100) return 'completed'
      if (step.step === this.currentStep) return 'current'
      if (step.progress > 0) return 'in-progress'
      return 'pending'
    },
    getStepStatus(step) {
      if (step.progress === 100) return 'Completed'
      if (step.step === this.currentStep) return 'In Progress'
      if (step.progress > 0) return `${step.progress}%`
      return 'Pending'
    },
    formatProcessingRate(citationInfo) {
      if (!citationInfo.processed || !this.elapsedTime) return '0/min'
      const rate = (citationInfo.processed / this.elapsedTime) * 60
      return `${Math.round(rate)}/min`
    }
  }
}
</script>

<style scoped>
.processing-progress {
  padding: 1rem;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.progress-section,
.citation-section,
.current-step,
.steps-section {
  margin-bottom: 1.5rem;
}

h3 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.progress-bar {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
  margin: 0.5rem 0;
}

.progress-fill {
  height: 100%;
  background: #42b983;
  transition: width 0.3s ease;
}

.time-info {
  display: flex;
  justify-content: space-between;
  color: #666;
  font-size: 0.9rem;
}

.citation-stats,
.rate-limit-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin: 0.5rem 0;
}

.stat {
  display: flex;
  flex-direction: column;
}

.label {
  color: #666;
  font-size: 0.9rem;
}

.value {
  font-weight: 500;
  color: #2c3e50;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.step {
  padding: 0.75rem;
  border-radius: 4px;
  background: #f8f9fa;
}

.step.completed {
  background: #e8f5e9;
}

.step.current {
  background: #e3f2fd;
}

.step.in-progress {
  background: #fff3e0;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.step-name {
  font-weight: 500;
}

.step-status {
  font-size: 0.9rem;
  color: #666;
}

.error-section {
  margin-top: 1rem;
  padding: 1rem;
  background: #ffebee;
  border-radius: 4px;
}

.error-message {
  color: #c62828;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.retry-button {
  margin-top: 0.5rem;
  padding: 0.5rem 1rem;
  background: #c62828;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.retry-button:hover {
  background: #b71c1c;
}

.timeout-info {
  color: #666;
  font-size: 0.9rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background: #f8f9fa;
}

.timeout-info.warning {
  color: #856404;
  background: #fff3cd;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}
</style> 