import axios from 'axios';

// Determine the base URL based on environment
const isProduction = import.meta.env.PROD;
const baseURL = isProduction ? '' : 'http://localhost:5000/casestrainer/api';

// Create an axios instance with default config
const api = axios.create({
  baseURL,
  timeout: 60000, // 60 seconds
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest'
  },
  withCredentials: true
});

// Add a request interceptor to log requests (for debugging)
api.interceptors.request.use(
  config => {
    // Remove /casestrainer/api prefix from URL if it's already in baseURL
    if (!isProduction && config.url.startsWith('/casestrainer/api')) {
      config.url = config.url.replace('/casestrainer/api', '');
    }
    console.log('API Request:', config.method.toUpperCase(), config.url);
    return config;
  },
  error => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle errors
api.interceptors.response.use(
  response => {
    return response;
  },
  error => {
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      console.error('API Error Response:', {
        status: error.response.status,
        statusText: error.response.statusText,
        data: error.response.data,
        headers: error.response.headers
      });
    } else if (error.request) {
      // The request was made but no response was received
      console.error('API No Response:', error.request);
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('API Request Setup Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// API methods
export default {
  analyzeText(text) {
    return api.post('/enhanced/analyze', { text });
  },
  
  // Add other API methods here as needed
  
  // Health check
  checkHealth() {
    return api.get('/health');
  }
};
