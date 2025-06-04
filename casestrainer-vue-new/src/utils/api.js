import axios from 'axios';

// Default configuration
const DEFAULT_RETRY_ATTEMPTS = 3;
const DEFAULT_RETRY_DELAY = 1000; // 1 second
const DEFAULT_TIMEOUT = 30000; // 30 seconds

// Track active requests
const activeRequests = new Set();

// Create axios instance with default config
const api = axios.create({
  timeout: DEFAULT_TIMEOUT,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add request to active requests
    const requestId = `${config.method?.toUpperCase()}:${config.url}`;
    activeRequests.add(requestId);
    
    // Add auth token if available
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    
    // Add timestamp for request timing
    config.metadata = { startTime: new Date() };
    
    return config;
  },
  (error) => {
    return Promise.reject(createApiError('Request failed to be sent', error));
  }
);

// Response interceptor with retry logic
api.interceptors.response.use(
  (response) => {
    // Remove from active requests
    const requestId = `${response.config.method?.toUpperCase()}:${response.config.url}`;
    activeRequests.delete(requestId);
    
    // Log successful request timing
    const endTime = new Date();
    const duration = endTime - (response.config.metadata?.startTime || endTime);
    console.debug(`API Request: ${requestId} completed in ${duration}ms`);
    
    return response.data;
  },
  async (error) => {
    const originalRequest = error.config;
    const requestId = `${originalRequest.method?.toUpperCase()}:${originalRequest.url}`;
    
    // Clean up active requests on error
    activeRequests.delete(requestId);
    
    // Create enhanced error object
    const apiError = createApiError(
      error.response?.data?.message || 'An unexpected error occurred',
      error,
      {
        status: error.response?.status,
        url: originalRequest.url,
        method: originalRequest.method,
      }
    );
    
    // Handle retry logic for network errors or 5xx responses
    const shouldRetry = !error.response || (error.response.status >= 500 && error.response.status < 600);
    const retryCount = originalRequest._retryCount || 0;
    const maxRetries = originalRequest._maxRetries ?? DEFAULT_RETRY_ATTEMPTS;
    
    if (shouldRetry && retryCount < maxRetries) {
      // Calculate delay with exponential backoff
      const delay = (originalRequest._retryDelay ?? DEFAULT_RETRY_DELAY) * Math.pow(2, retryCount);
      
      console.warn(`Retrying request (${retryCount + 1}/${maxRetries}) to ${originalRequest.url} in ${delay}ms`);
      
      // Return a promise that resolves after the delay and retries the request
      return new Promise((resolve) => {
        setTimeout(() => {
          originalRequest._retryCount = retryCount + 1;
          originalRequest._retryDelay = delay;
          resolve(api(originalRequest));
        }, delay);
      });
    }
    
    // Log error details in development
    if (import.meta.env.DEV) {
      console.error('API Error:', {
        message: apiError.message,
        status: apiError.status,
        url: originalRequest.url,
        method: originalRequest.method,
        response: error.response?.data,
      });
    }
    
    return Promise.reject(apiError);
  }
);

// Helper function to create consistent error objects
function createApiError(message, error, details = {}) {
  const apiError = new Error(message);
  
  // Copy error properties
  if (error) {
    Object.getOwnPropertyNames(error).forEach((key) => {
      apiError[key] = error[key];
    });
  }
  
  // Add additional details
  Object.entries(details).forEach(([key, value]) => {
    apiError[key] = value;
  });
  
  // Add custom properties
  apiError.isApiError = true;
  apiError.timestamp = new Date().toISOString();
  
  return apiError;
}

// Add utility methods to the API instance
api.cancelAllRequests = (reason = 'User cancelled all requests') => {
  // This would be implemented if using axios CancelToken
  console.warn('Cancelling all active requests:', activeRequests.size);
  // Reset active requests
  activeRequests.clear();
};

// Add a method to check if there are active requests
api.hasActiveRequests = () => activeRequests.size > 0;

export default api;
