import { createApp } from 'vue';
import axios from 'axios';
import { createPinia } from 'pinia';
import { createLoader } from '@/utils/loading';
import './style.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import App from './App.vue';
import router from './router';
import AppErrorHandler from '@/components/AppErrorHandler.vue';

// Configure axios defaults
axios.defaults.withCredentials = true;
axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL || '/casestrainer/api';
axios.defaults.timeout = 30000; // 30 seconds

// Global error handler
const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    
    if (status === 401) {
      // Handle unauthorized (e.g., redirect to login)
      console.warn('Unauthorized access - redirecting to login');
      // router.push('/login');
    } else if (status === 403) {
      // Handle forbidden
      console.error('Forbidden access');
    } else if (status >= 500) {
      // Server error
      console.error('Server error:', data);
    }
    
    return Promise.reject({
      message: data?.message || `Request failed with status ${status}`,
      status,
      data,
      isApiError: true,
    });
  } else if (error.request) {
    // No response received
    return Promise.reject({
      message: 'No response received from server. Please check your connection.',
      isNetworkError: true,
    });
  }
  
  // Other errors
  return Promise.reject({
    message: error.message || 'An unknown error occurred',
    isUnknownError: true,
  });
};

// Add a request interceptor
axios.interceptors.request.use(
  (config) => {
    // Add auth token if available
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    
    // Add request timestamp for tracking
    config.metadata = { startTime: new Date() };
    
    // Show loading indicator for non-background requests
    if (!config._silent) {
      const message = config.loadingMessage || 'Loading...';
      window.activeLoader = createLoader(`request_${Date.now()}`, { message });
    }
    
    return config;
  },
  (error) => {
    // Clean up loading indicator on request error
    if (window.activeLoader) {
      window.activeLoader.remove();
      window.activeLoader = null;
    }
    return Promise.reject(error);
  }
);

// Add a response interceptor
axios.interceptors.response.use(
  (response) => {
    // Clean up loading indicator
    if (window.activeLoader) {
      window.activeLoader.complete();
      window.activeLoader = null;
    }
    
    // Log request timing
    if (response.config.metadata?.startTime) {
      const duration = new Date() - response.config.metadata.startTime;
      console.debug(`API Request: ${response.config.url} completed in ${duration}ms`);
    }
    
    return response;
  },
  async (error) => {
    // Clean up loading indicator on error
    if (window.activeLoader) {
      window.activeLoader.error();
      window.activeLoader = null;
    }
    
    return handleApiError(error);
  }
);

// Create the app
const app = createApp(App);

// Add global error handler component
app.component('AppErrorHandler', AppErrorHandler);

// Add global error handler
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue error:', { err, vm, info });
  // You could also log this to an error tracking service
};

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  event.preventDefault();
});

// Handle global errors
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error || event.message);
  // You could also show a user-friendly error message
});

// Create Pinia instance
const pinia = createPinia();

// Use plugins
app.use(pinia);
app.use(router);

// Make axios available globally (for legacy code)
app.config.globalProperties.$http = axios;

// Mount the app
app.mount('#app');

// Export the app instance for testing
if (import.meta.env.DEV) {
  window.app = app;
}
