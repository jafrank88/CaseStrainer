import { ref, computed } from 'vue';

// Global loading state
const isLoading = ref(false);
const loadingMessage = ref('Loading...');

/**
 * Composable for managing loading state across the application
 * @returns {Object} Loading state utilities
 */
export function useLoadingState() {
  /**
   * Set loading state
   * @param {boolean} value - Whether loading is active
   * @param {string} [message='Loading...'] - Loading message to display
   */
  const setLoading = (value, message = 'Loading...') => {
    isLoading.value = value;
    if (message) {
      loadingMessage.value = message;
    }
  };

  /**
   * Show loading with optional message
   * @param {string} [message] - Optional loading message
   */
  const showLoading = (message) => {
    setLoading(true, message);
  };

  /**
   * Hide loading
   */
  const hideLoading = () => {
    setLoading(false);
  };

  /**
   * Toggle loading state
   * @param {string} [message] - Optional loading message when toggling on
   */
  const toggleLoading = (message) => {
    setLoading(!isLoading.value, message);
  };

  return {
    // State
    isLoading: computed(() => isLoading.value),
    loadingMessage: computed(() => loadingMessage.value),
    
    // Actions
    setLoading,
    showLoading,
    hideLoading,
    toggleLoading
  };
}

// Export the loading state for direct access if needed
export const globalLoading = {
  get isLoading() {
    return isLoading.value;
  },
  get message() {
    return loadingMessage.value;
  },
  set message(value) {
    loadingMessage.value = value;
  }
};
