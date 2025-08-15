<template>
  <div class="async-task-progress" v-if="isVisible">
    <div class="progress-header">
      <h3>Processing Task</h3>
      <div class="task-info">
        <span class="task-id">ID: {{ taskId }}</span>
        <span class="status-badge" :class="statusClass">{{ status }}</span>
      </div>
    </div>

    <div class="progress-content">
      <!-- Progress Bar -->
      <div class="progress-bar-container">
        <div class="progress-bar" :style="{ width: progressWidth + '%' }"></div>
        <div class="progress-text">{{ progressText }}</div>
      </div>

      <!-- Status Message -->
      <div class="status-message">
        <i class="status-icon" :class="statusIconClass"></i>
        <span>{{ message }}</span>
      </div>

      <!-- Polling Info -->
      <div class="polling-info" v-if="showPollingInfo">
        <small>
          Polling: {{ pollCount }} attempts | 
          Elapsed: {{ elapsedTime }}
        </small>
      </div>

      <!-- Cancel Button -->
      <div class="actions" v-if="canCancel">
        <button @click="cancelTask" class="btn btn-secondary btn-sm">
          Cancel Task
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue';

export default {
  name: 'AsyncTaskProgress',
  props: {
    taskId: {
      type: String,
      required: true
    },
    initialStatus: {
      type: String,
      default: 'queued'
    },
    initialMessage: {
      type: String,
      default: 'Task queued and waiting to be processed'
    },
    canCancel: {
      type: Boolean,
      default: true
    }
  },
  emits: ['cancel', 'complete', 'error'],
  setup(props, { emit }) {
    const status = ref(props.initialStatus);
    const message = ref(props.initialMessage);
    const pollCount = ref(0);
    const startTime = ref(Date.now());
    const isVisible = ref(true);

    // Computed properties
    const statusClass = computed(() => {
      switch (status.value) {
        case 'completed': return 'status-success';
        case 'failed': return 'status-error';
        case 'processing': return 'status-processing';
        case 'queued': return 'status-queued';
        case 'error': return 'status-error';
        default: return 'status-unknown';
      }
    });

    const statusIconClass = computed(() => {
      switch (status.value) {
        case 'completed': return 'fas fa-check-circle';
        case 'failed': return 'fas fa-exclamation-circle';
        case 'processing': return 'fas fa-spinner fa-spin';
        case 'queued': return 'fas fa-clock';
        case 'error': return 'fas fa-exclamation-triangle';
        default: return 'fas fa-question-circle';
      }
    });

    const progressWidth = computed(() => {
      switch (status.value) {
        case 'queued': return 10;
        case 'processing': return 50;
        case 'completed': return 100;
        case 'failed': return 100;
        case 'error': return 100;
        default: return 25;
      }
    });

    const progressText = computed(() => {
      switch (status.value) {
        case 'queued': return 'Queued';
        case 'processing': return 'Processing...';
        case 'completed': return 'Completed';
        case 'failed': return 'Failed';
        case 'error': return 'Error';
        default: return 'Unknown';
      }
    });

    const showPollingInfo = computed(() => {
      return status.value === 'processing' || status.value === 'queued';
    });

    const elapsedTime = computed(() => {
      const elapsed = Date.now() - startTime.value;
      const seconds = Math.floor(elapsed / 1000);
      const minutes = Math.floor(seconds / 60);
      
      if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
      }
      return `${seconds}s`;
    });

    // Methods
    const updateStatus = (newStatus, newMessage, newPollCount = null) => {
      status.value = newStatus;
      message.value = newMessage;
      if (newPollCount !== null) {
        pollCount.value = newPollCount;
      }
    };

    const cancelTask = () => {
      emit('cancel', props.taskId);
    };

    const complete = (result) => {
      updateStatus('completed', 'Task completed successfully!');
      setTimeout(() => {
        emit('complete', result);
        isVisible.value = false;
      }, 1000);
    };

    const error = (errorMessage) => {
      updateStatus('failed', `Task failed: ${errorMessage}`);
      setTimeout(() => {
        emit('error', errorMessage);
        isVisible.value = false;
      }, 3000);
    };

    const progress = (progressData) => {
      updateStatus(
        progressData.status, 
        progressData.message, 
        progressData.pollCount
      );
    };

    // Expose methods to parent
    const expose = {
      updateStatus,
      progress,
      complete,
      error
    };

    // Lifecycle
    onMounted(() => {
      // Component is ready
    });

    onUnmounted(() => {
      // Cleanup if needed
    });

    return {
      status,
      message,
      pollCount,
      isVisible,
      statusClass,
      statusIconClass,
      progressWidth,
      progressText,
      showPollingInfo,
      elapsedTime,
      cancelTask,
      ...expose
    };
  }
};
</script>

<style scoped>
.async-task-progress {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 24px;
  margin: 20px 0;
  border: 1px solid #e1e5e9;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.progress-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.25rem;
  font-weight: 600;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-id {
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  color: #6c757d;
  background: #f8f9fa;
  padding: 4px 8px;
  border-radius: 4px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-success {
  background: #d4edda;
  color: #155724;
}

.status-error {
  background: #f8d7da;
  color: #721c24;
}

.status-processing {
  background: #cce5ff;
  color: #004085;
}

.status-queued {
  background: #fff3cd;
  color: #856404;
}

.status-unknown {
  background: #e2e3e5;
  color: #383d41;
}

.progress-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.progress-bar-container {
  position: relative;
  height: 24px;
  background: #e9ecef;
  border-radius: 12px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #007bff, #0056b3);
  border-radius: 12px;
  transition: width 0.3s ease;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.status-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #007bff;
}

.status-icon {
  font-size: 1.25rem;
  color: #007bff;
}

.polling-info {
  text-align: center;
  color: #6c757d;
  font-size: 0.875rem;
}

.actions {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 0.8rem;
}

/* Animation for processing state */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.status-processing .progress-bar {
  animation: pulse 2s infinite;
}

/* Responsive design */
@media (max-width: 768px) {
  .progress-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .task-info {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
