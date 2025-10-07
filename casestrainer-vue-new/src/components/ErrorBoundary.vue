<template>
  <div class="error-boundary">
    <slot v-if="!hasError" />
    <div v-else class="error-fallback">
      <div class="error-icon">
        <i class="bi bi-exclamation-triangle-fill text-danger"></i>
      </div>
      <h3 class="error-title">Oops! Something went wrong</h3>
      <p class="error-message">
        We're sorry, but an unexpected error occurred. This has been reported to our team.
      </p>

      <div class="error-actions">
        <button @click="handleRetry" class="btn btn-primary">
          <i class="bi bi-arrow-clockwise me-2"></i>
          Try Again
        </button>
        <button @click="handleReload" class="btn btn-outline-secondary ms-2">
          <i class="bi bi-house-door me-2"></i>
          Go Home
        </button>
      </div>

      <details v-if="showDetails" class="error-details mt-3">
        <summary class="error-details-toggle">Technical Details</summary>
        <pre class="error-stack">{{ error.stack }}</pre>
      </details>

      <button
        v-if="!showDetails"
        @click="showDetails = true"
        class="btn btn-link btn-sm mt-2 p-0"
      >
        Show technical details
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue';
import { useRouter } from 'vue-router';
import logger from '@/utils/logger';

const router = useRouter();
const hasError = ref(false);
const error = ref(null);
const showDetails = ref(false);

const handleRetry = () => {
  hasError.value = false;
  error.value = null;
  showDetails.value = false;
};

const handleReload = () => {
  window.location.href = '/';
};

const capturedError = onErrorCaptured((err, instance, info) => {
  hasError.value = true;
  error.value = err;

  // Log the error
  logger.error('Error boundary caught error:', {
    error: err,
    component: instance?.$?.type?.name || 'Unknown component',
    info,
    stack: err.stack,
    url: window.location.href,
    userAgent: navigator.userAgent
  });

  // In production, you might want to send this to an error reporting service
  if (import.meta.env.PROD) {
    // Example: send to error reporting service
    // reportError(err, { component: instance?.$?.type?.name, info });
  }

  // Prevent the error from propagating further
  return false;
});
</script>

<style scoped>
.error-boundary {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-fallback {
  text-align: center;
  padding: 2rem;
  max-width: 500px;
  margin: 0 auto;
}

.error-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.7;
}

.error-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary, #212529);
  margin-bottom: 1rem;
}

.error-message {
  color: var(--text-secondary, #6c757d);
  margin-bottom: 2rem;
  line-height: 1.5;
}

.error-actions {
  margin-bottom: 1rem;
}

.error-details {
  text-align: left;
  border: 1px solid #e9ecef;
  border-radius: 0.375rem;
  padding: 1rem;
  background: #f8f9fa;
}

.error-details-toggle {
  cursor: pointer;
  font-weight: 600;
  color: var(--text-primary, #212529);
  margin-bottom: 0.5rem;
}

.error-stack {
  background: #f1f3f4;
  padding: 1rem;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  color: #dc3545;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.btn-link {
  text-decoration: none;
}

.btn-link:hover {
  text-decoration: underline;
}
</style>
