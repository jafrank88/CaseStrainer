import { ref, onUnmounted } from 'vue';
import { globalProgress } from '@/stores/progressStore';

/**
 * Composable for making API calls with loading and error states
 * @param {Object} options - Options for the API call
 * @param {string} [options.loadingMessage] - Loading message to show during the request
 * @param {boolean} [options.showLoading=true] - Whether to show loading state
 * @param {Function} [options.onSuccess] - Callback for successful response
 * @param {Function} [options.onError] - Callback for error response
 * @param {Function} [options.onFinally] - Callback after request completes (success or error)
 * @returns {Object} API call utilities
 */
export function useApi(options = {}) {
  const {
    loadingMessage = 'Loading...',
    showLoading = true,
    onSuccess,
    onError,
    onFinally,
  } = options;
  
  const data = ref(null);
  const error = ref(null);
  const isLoading = ref(false);
  const status = ref(null);
  let controller = null;
  
  // Track active requests for cleanup
  const activeRequests = new Set();
  
  // Cleanup on component unmount
  onUnmounted(() => {
    if (controller) {
      controller.abort();
    }
  });
  
  /**
   * Execute an API call
   * @param {Function} apiCall - Function that returns a promise (usually an axios call)
   * @param {Object} callOptions - Options for this specific call
   * @returns {Promise} The API call promise
   */
  async function execute(apiCall, callOptions = {}) {
    const {
      message = loadingMessage,
      showLoader = showLoading,
      signal,
      ...requestConfig
    } = { ...options, ...callOptions };
    
    // Reset state
    error.value = null;
    status.value = null;
    data.value = null;
    
    // Start loading
    if (options.showLoading !== false) {
      globalProgress.startProgress('api', {
        text: options.loadingMessage || 'Processing request...'
      });
    }
    
    isLoading.value = true;
    
    // Create abort controller for this request
    if (typeof AbortController !== 'undefined') {
      controller = new AbortController();
      requestConfig.signal = signal || controller.signal;
    }
    
    try {
      const response = await apiCall({
        ...requestConfig,
        signal: requestConfig.signal,
      });
      
      data.value = response.data || response;
      status.value = response.status || 200;
      
      if (onSuccess) {
        onSuccess(response);
      }
      
      return response;
    } catch (err) {
      error.value = err;
      status.value = err.response?.status || 0;
      
      if (onError) {
        onError(err);
      }
      
      // Re-throw the error so the calling code can handle it if needed
      throw err;
    } finally {
      isLoading.value = false;
      
      // Update progress
      if (options.showLoading !== false) {
        // Progress updates are handled by the global progress store
        // globalProgress.updateProgress(progress);
      }
      
      if (onFinally) {
        onFinally();
      }
      
      controller = null;
    }
  }
  
  /**
   * Cancel the current request
   */
  function cancel() {
    if (controller) {
      controller.abort();
      controller = null;
    }
    
    if (loader) {
      loader.remove();
      loader = null;
    }
    
    isLoading.value = false;
  }
  
  return {
    execute,
    cancel,
    data,
    error,
    isLoading,
    status,
  };
}

/**
 * Composable for making GET requests
 * @param {string} url - API endpoint URL
 * @param {Object} options - Options for the API call
 * @returns {Object} API call utilities
 */
export function useGet(url, options = {}) {
  const { execute, ...rest } = useApi(options);
  
  async function get(params = {}, config = {}) {
    return execute(api => api.get(url, { params, ...config }));
  }
  
  return {
    get,
    ...rest,
  };
}

/**
 * Composable for making POST requests
 * @param {string} url - API endpoint URL
 * @param {Object} options - Options for the API call
 * @returns {Object} API call utilities
 */
export function usePost(url, options = {}) {
  const { execute, ...rest } = useApi(options);
  
  async function post(data = {}, config = {}) {
    return execute(api => api.post(url, data, config));
  }
  
  return {
    post,
    ...rest,
  };
}

/**
 * Composable for making PUT requests
 * @param {string} url - API endpoint URL
 * @param {Object} options - Options for the API call
 * @returns {Object} API call utilities
 */
export function usePut(url, options = {}) {
  const { execute, ...rest } = useApi(options);
  
  async function put(data = {}, config = {}) {
    return execute(api => api.put(url, data, config));
  }
  
  return {
    put,
    ...rest,
  };
}

/**
 * Composable for making DELETE requests
 * @param {string} url - API endpoint URL
 * @param {Object} options - Options for the API call
 * @returns {Object} API call utilities
 */
export function useDelete(url, options = {}) {
  const { execute, ...rest } = useApi(options);
  
  async function del(config = {}) {
    return execute(api => api.delete(url, config));
  }
  
  return {
    delete: del,
    ...rest,
  };
}
