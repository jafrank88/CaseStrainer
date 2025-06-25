import { createApp } from 'vue';
import axios from 'axios';
import { createPinia } from 'pinia';
import { createLoader } from '@/utils/loading';
import './style.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import App from './App.vue';
import router from './router';
import AppErrorHandler from '@/components/AppErrorHandler.vue';

// Configure axios defaults
axios.defaults.withCredentials = true;
axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL || '/casestrainer/api';
axios.defaults.timeout = 30000;

// Simplified error handler
const handleApiError = (error) => {
  if (error.response) {
    const { status, data } = error.response;
    return Promise.reject({
      message: data?.message || `Request failed with status ${status}`,
      status,
      data,
      isApiError: true,
    });
  } else if (error.request) {
    return Promise.reject({
      message: 'No response received from server. Please check your connection.',
      isNetworkError: true,
    });
  }
  
  return Promise.reject({
    message: error.message || 'An unknown error occurred',
    isUnknownError: true,
  });
};

// Request interceptor
axios.interceptors.request.use(
  (config) => {
    config.metadata = { startTime: Date.now() };
    
    if (!config._silent) {
      const message = config.loadingMessage || 'Loading...';
      window.activeLoader = createLoader(`request_${Date.now()}`, { message });
    }
    
    return config;
  },
  (error) => {
    if (window.activeLoader) {
      window.activeLoader.remove();
      window.activeLoader = null;
    }
    return Promise.reject(error);
  }
);

// Response interceptor
axios.interceptors.response.use(
  (response) => {
    if (window.activeLoader) {
      window.activeLoader.complete();
      window.activeLoader = null;
    }
    
    if (response.config.metadata?.startTime) {
      const duration = Date.now() - response.config.metadata.startTime;
      console.debug(`API Request: ${response.config.url} completed in ${duration}ms`);
    }
    
    return response;
  },
  async (error) => {
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

// Simplified global error handler
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue error:', { err, vm, info });
};

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  event.preventDefault();
});

// Create Pinia instance
const pinia = createPinia();

// Use plugins
app.use(pinia);
app.use(router);

// Make axios available globally
app.config.globalProperties.$http = axios;

// Mount the app
app.mount('#app');

// Export the app instance for testing in development
if (import.meta.env.DEV) {
  window.app = app;
}
