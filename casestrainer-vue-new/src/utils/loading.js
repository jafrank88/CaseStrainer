import { ref, readonly } from 'vue';

// Global loading state
const isLoading = ref(false);
const loadingMessage = ref('');
const loadingProgress = ref(0);
const loadingErrors = ref([]);

// Track all active loading states
const activeLoaders = new Set();

/**
 * Creates a loading state with automatic cleanup
 * @param {string} id - Unique identifier for this loading state
 * @param {Object} options - Loading options
 * @param {string} [options.message] - Loading message
 * @param {number} [options.progress] - Initial progress (0-100)
 * @returns {Object} Loading state controller
 */
function createLoader(id, { message = 'Loading...', progress = 0 } = {}) {
  if (activeLoaders.has(id)) {
    console.warn(`Loader with id "${id}" already exists`);
  }
  
  activeLoaders.add(id);
  isLoading.value = true;
  loadingMessage.value = message;
  loadingProgress.value = progress;
  
  return {
    /**
     * Update the loading state
     * @param {Object} update - Update object
     * @param {string} [update.message] - New loading message
     * @param {number} [update.progress] - New progress value (0-100)
     */
    update({ message, progress }) {
      if (message !== undefined) loadingMessage.value = message;
      if (progress !== undefined) loadingProgress.value = Math.max(0, Math.min(100, progress));
    },
    
    /**
     * Complete the loading state
     */
    complete() {
      loadingProgress.value = 100;
      this.remove();
    },
    
    /**
     * Report an error
     * @param {Error|string} error - Error object or message
     */
    error(error) {
      const errorObj = typeof error === 'string' ? new Error(error) : error;
      loadingErrors.value = [...loadingErrors.value, errorObj];
      this.remove();
    },
    
    /**
     * Remove this loader
     */
    remove() {
      activeLoaders.delete(id);
      if (activeLoaders.size === 0) {
        resetLoadingState();
      } else {
        // If other loaders are still active, update to the most recent one
        const lastLoader = Array.from(activeLoaders).pop();
        // In a real app, you might want to restore the previous loader's state
        loadingMessage.value = lastLoader || 'Loading...';
      }
    },
  };
}

/**
 * Reset all loading states
 */
function resetLoadingState() {
  isLoading.value = false;
  loadingMessage.value = '';
  loadingProgress.value = 0;
  activeLoaders.clear();
}

/**
 * Clear all errors
 */
function clearErrors() {
  loadingErrors.value = [];
}

/**
 * Get a readonly version of the loading state
 */
function useLoadingState() {
  return {
    isLoading: readonly(isLoading),
    message: readonly(loadingMessage),
    progress: readonly(loadingProgress),
    errors: readonly(loadingErrors),
    hasErrors: loadingErrors.value.length > 0,
  };
}

export {
  createLoader,
  useLoadingState,
  resetLoadingState,
  clearErrors,
};
