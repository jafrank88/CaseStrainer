import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

// Get base URL from environment variables
const baseURL = import.meta.env.DEV 
  ? '/casestrainer/api'  // Use relative path in development
  : (import.meta.env.VITE_API_BASE_URL || '/casestrainer/api');  // Use configured URL in production

// Create axios instance with default config
const api = axios.create({
  baseURL,
  timeout: 120000, // 2 minutes default timeout
  // Remove default Content-Type header to let browser set it for FormData
});

// Log API configuration in development
if (import.meta.env.DEV) {
  console.log('API Configuration:', {
    baseURL,
    environment: import.meta.env.MODE,
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL,
    fullUrl: `${baseURL}/analyze`
  });
}

// Add request interceptor to set specific timeouts for different endpoints
api.interceptors.request.use(config => {
  // Set longer timeout for URL analysis
  if (config.url === '/analyze' && config.data && config.data.type === 'url') {
    config.timeout = 300000; // 5 minutes for URL analysis
    config.retryCount = 0;
    config.maxRetries = 3;
  } else {
    config.timeout = 120000; // 2 minutes for other endpoints
    config.retryCount = 0;
    config.maxRetries = 1;
  }
  return config;
});

// Add response interceptor for retry logic
api.interceptors.response.use(
  response => response,
  async error => {
    const config = error.config;
    
    // Only retry on timeout or network errors
    if (!config || !config.retryCount || 
      config.retryCount >= config.maxRetries || 
      !(error.code === 'ECONNABORTED' || error.message.includes('timeout') || error.message.includes('Network Error'))) {
      return Promise.reject(error);
    }

    // Increment retry count
    config.retryCount += 1;
    
    // Calculate delay with exponential backoff
    const delay = Math.min(1000 * Math.pow(2, config.retryCount), 30000);
    
    // Log retry attempt
    console.log(`Retrying request to ${config.url} (attempt ${config.retryCount}/${config.maxRetries}) after ${delay}ms delay`);
    
    // Wait before retrying
    await new Promise(resolve => setTimeout(resolve, delay));
    
    // Retry the request
    return api(config);
  }
);

// Request interceptor for API requests
api.interceptors.request.use(
  (config) => {
    // Add API key to headers
    config.headers['X-API-Key'] = import.meta.env.VITE_COURTLISTENER_API_KEY || '***REDACTED_COURTLISTENER_KEY***';
    
    // Only set Content-Type for non-FormData requests
    if (!(config.data instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json';
    }
    
    // Log request details in development
    if (import.meta.env.DEV) {
      console.log('API Request:', {
        method: config.method,
        url: config.url,
        baseURL: config.baseURL,
        headers: config.headers,
        dataType: config.data instanceof FormData ? 'FormData' : 'JSON'
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

// Add response interceptor for better error handling
api.interceptors.response.use(
  response => response,
  error => {
    if (error.config && error.config.url === '/analyze' && error.config.data && error.config.data.type === 'url') {
      // Handle URL-specific errors
      if (error.response) {
        switch (error.response.status) {
          case 400:
            error.message = 'Invalid URL or content type not supported';
            break;
          case 404:
            error.message = 'URL not found or content not accessible';
            break;
          case 429:
            error.message = 'Too many requests. Please try again in a few minutes';
            break;
          case 502:
            error.message = 'Failed to fetch URL content. The server may be temporarily unavailable';
            break;
          case 504:
            error.message = 'Request timed out while fetching URL content';
            break;
          default:
            error.message = `Error fetching URL: ${error.response.status} ${error.response.statusText}`;
        }
      } else if (error.code === 'ECONNABORTED') {
        error.message = 'Request timed out while fetching URL content';
      } else if (error.code === 'ECONNREFUSED') {
        error.message = 'Could not connect to the server';
      } else if (error.code === 'ENOTFOUND') {
        error.message = 'URL not found or domain does not exist';
      }
    }
    return Promise.reject(error);
  }
);

// Add polling configuration
const POLLING_INTERVAL = 2000; // 2 seconds
const MAX_POLLING_TIME = 600000; // 10 minutes
const MAX_RETRIES = 3;

// Add request tracking
const activeRequests = new Map();

// Helper function to poll for results
async function pollForResults(requestId, startTime = Date.now()) {
  if (Date.now() - startTime > MAX_POLLING_TIME) {
    throw new Error('Request timed out after 10 minutes');
  }
  
  try {
    // Log the polling attempt
    console.log('Polling for results:', {
      taskId: requestId,
      endpoint: `/task_status/${requestId}`,
      elapsed: Date.now() - startTime,
      baseURL
    });

    // Use the correct endpoint structure with explicit baseURL
    const response = await api.get(`/task_status/${requestId}`, {
      timeout: 30000, // 30 second timeout for status checks
      validateStatus: function (status) {
        return status < 500; // Accept any status less than 500
      }
    });
    
    // Log the response
    console.log('Status check response:', {
      taskId: requestId,
      status: response.status,
      data: response.data,
      headers: response.headers
    });
    
    // Add more detailed status handling
    if (response.status === 404) {
      // If we get a 404, the task might not be ready yet
      console.log('Task not ready yet, retrying...', {
        taskId: requestId,
        elapsed: Date.now() - startTime,
        endpoint: `/task_status/${requestId}`
      });
      await new Promise(resolve => setTimeout(resolve, POLLING_INTERVAL));
      return pollForResults(requestId, startTime);
    }
    
    if (response.data.status === 'completed') {
      console.log('Task completed:', {
        taskId: requestId,
        elapsed: Date.now() - startTime,
        citations: response.data.citations?.length || 0
      });
      return response.data;
    } else if (response.data.status === 'failed') {
      console.error('Task failed:', {
        taskId: requestId,
        error: response.data.error,
        elapsed: Date.now() - startTime
      });
      throw new Error(response.data.error || 'Request failed');
    } else if (response.data.status === 'processing' || response.data.status === 'queued' || response.data.status === 'pending') {
      // Log processing status for debugging
      console.log('Processing status:', {
        taskId: requestId,
        status: response.data.status,
        progress: response.data.progress,
        message: response.data.message,
        queuePosition: response.data.queue_position,
        estimatedWaitTime: response.data.estimated_wait_time,
        citations: response.data.citations?.length || 0
      });
      
      // Continue polling
      await new Promise(resolve => setTimeout(resolve, POLLING_INTERVAL));
      return pollForResults(requestId, startTime);
    } else {
      // Handle unknown status
      console.warn('Unknown status received:', {
        taskId: requestId,
        status: response.data.status,
        data: response.data
      });
      await new Promise(resolve => setTimeout(resolve, POLLING_INTERVAL));
      return pollForResults(requestId, startTime);
    }
  } catch (error) {
    // Enhanced error handling with detailed logging
    if (error.response) {
      if (error.response.status === 404) {
        console.log('Status endpoint not found, retrying...', {
          taskId: requestId,
          elapsed: Date.now() - startTime,
          endpoint: `/task_status/${requestId}`,
          baseURL,
          response: error.response.data
        });
        await new Promise(resolve => setTimeout(resolve, POLLING_INTERVAL));
        return pollForResults(requestId, startTime);
      } else {
        console.error('Status check failed:', {
          taskId: requestId,
          status: error.response.status,
          data: error.response.data,
          headers: error.response.headers,
          endpoint: `/task_status/${requestId}`,
          baseURL
        });
        throw new Error(`Status check failed: ${error.response.status} ${error.response.statusText}`);
      }
    } else if (error.request) {
      console.error('No response received for status check:', {
        taskId: requestId,
        message: error.message,
        endpoint: `/task_status/${requestId}`,
        baseURL
      });
      throw new Error('No response received from server');
    } else {
      console.error('Error checking status:', {
        taskId: requestId,
        message: error.message,
        endpoint: `/task_status/${requestId}`,
        baseURL
      });
      throw error;
    }
  }
}

// Update the analyze function to use the consolidated /analyze endpoint
export const analyze = async (requestData) => {
    // Set appropriate timeout based on input type
    const timeout = requestData.type === 'url' ? 300000 : 120000; // 5 minutes for URLs, 2 minutes for others
    
    try {
        // Log the analyze request
        console.log('Starting analysis:', {
            type: requestData.type,
            isFormData: requestData instanceof FormData,
            baseURL,
            endpoint: '/analyze'
        });

        // If requestData is FormData (file upload), don't set Content-Type header
        // Otherwise, use application/json for other requests
        const headers = requestData instanceof FormData ? {} : {
            'Content-Type': 'application/json'
        };
        
        const response = await api.post('/analyze', requestData, {
            timeout,
            headers,
            validateStatus: function (status) {
                return status < 500; // Accept any status less than 500
            }
        });
        
        // Log the analyze response
        console.log('Analysis response:', {
            status: response.status,
            data: response.data,
            headers: response.headers
        });
        
        // If we get a 202 Accepted, start polling
        if (response.status === 202 && response.data.task_id) {
            console.log('Starting polling for task:', {
                taskId: response.data.task_id,
                status: response.data.status,
                message: response.data.message
            });
            return await pollForResults(response.data.task_id);
        }
        
        return response.data;
    } catch (error) {
        console.error('Error in analyze request:', {
            error,
            type: requestData.type,
            isFormData: requestData instanceof FormData,
            baseURL,
            endpoint: '/analyze'
        });
        throw error;
    }
};

// Add function to cancel active requests
export function cancelRequest(requestId) {
  if (activeRequests.has(requestId)) {
    activeRequests.delete(requestId);
    return api.post(`/analyze/cancel/${requestId}`);
  }
  return Promise.resolve();
}

// Add function to get request status
export function getRequestStatus(requestId) {
  return activeRequests.get(requestId) || null;
}

// Add function to get all active requests
export function getActiveRequests() {
  return Array.from(activeRequests.entries()).map(([id, data]) => ({
    id,
    ...data
  }));
}

export default api;
