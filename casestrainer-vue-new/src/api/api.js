import axios from 'axios';

// Get base URL from environment variables
const baseURL = import.meta.env.DEV 
  ? ''  // Use empty base URL in development to let Vite handle the proxy
  : (import.meta.env.VITE_API_BASE_URL || '');  // Use absolute URL in production

// Create axios instance with base URL
const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  withCredentials: true, // Important for cookies/sessions if using them
  timeout: 30000, // 30 second timeout
});

// Log API configuration in development
if (import.meta.env.DEV) {
  console.log('API Configuration:', {
    baseURL,
    environment: import.meta.env.MODE,
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL,
    enhancedEndpoint: '/casestrainer/api/enhanced/analyze'
  });
}

// Request interceptor for API requests
api.interceptors.request.use(
  (config) => {
    // Add API key to headers
    config.headers['X-API-Key'] = import.meta.env.VITE_COURTLISTENER_API_KEY || '***REDACTED_COURTLISTENER_KEY***';
    
    // Log request details in development
    if (import.meta.env.DEV) {
      console.log('API Request:', {
        method: config.method,
        url: config.url,
        baseURL: config.baseURL,
        headers: config.headers
      });
    }
    
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    // Log successful responses in development
    if (import.meta.env.DEV) {
      console.log('API Response:', {
        status: response.status,
        url: response.config.url,
        data: response.data
      });
    }
    return response;
  },
  (error) => {
    // Enhanced error logging
    if (error.response) {
      console.error('API Error Response:', {
        status: error.response.status,
        url: error.config?.url,
        data: error.response.data,
        headers: error.response.headers
      });
    } else if (error.request) {
      console.error('API Request Error (No Response):', {
        url: error.config?.url,
        message: error.message
      });
    } else {
      console.error('API Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;
