import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

// Get base URL from environment variables
// For production, use relative path to work with any domain
const baseURL = import.meta.env.VITE_API_BASE_URL || '/casestrainer/api';

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

// Add request interceptor to set specific timeouts and headers for different endpoints
api.interceptors.request.use(config => {
  // Set default headers if not already set
  if (!config.headers) {
    config.headers = {};
  }
  
  // Set Content-Type header for JSON requests
  if (!(config.data instanceof FormData) && !config.headers['Content-Type']) {
    config.headers['Content-Type'] = 'application/json';
  }
  
  // Set longer timeout for URL analysis
  if (config.url === '/analyze' && config.data && config.data.type === 'url') {
    config.timeout = 300000; // 5 minutes for URL analysis
    config.retryCount = 0;
    config.maxRetries = 3;
  } else if (config.url === '/analyze' && config.data instanceof FormData) {
    // Set longer timeout for file uploads (PDF processing can take time)
    config.timeout = 600000; // 10 minutes for file uploads
    config.retryCount = 0;
    config.maxRetries = 1;
    // Remove Content-Type header for FormData to let the browser set it with the correct boundary
    delete config.headers['Content-Type'];
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
    // Add API key to headers - REQUIRED environment variable
    const apiKey = import.meta.env.VITE_COURTLISTENER_API_KEY;
    if (!apiKey) {
      console.error('❌ VITE_COURTLISTENER_API_KEY environment variable is required but not set');
      throw new Error('CourtListener API key not configured. Please set VITE_COURTLISTENER_API_KEY environment variable.');
    }
    config.headers['X-API-Key'] = apiKey;
    
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
const MAX_POLLING_TIME = 1200000; // 20 minutes (increased for file processing)
const MAX_RETRIES = 3;

// Add request tracking
const activeRequests = new Map();

// Helper function to poll for results
async function pollForResults(requestId, clientRequestId = null, startTime = Date.now()) {
  if (Date.now() - startTime > MAX_POLLING_TIME) {
    throw new Error('Request timed out after 10 minutes');
  }
  
  try {
    // Log the polling attempt
    console.log('Polling for results:', {
      taskId: requestId,
      clientRequestId: clientRequestId,
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
    
    // Handle nested response structure
    const responseData = response.data.result || response.data;
    const status = responseData.status || responseData.state;
    const result = responseData.result || responseData;
    const message = responseData.message || responseData.detail || '';
    
    // Log the response
    console.log('Status check response:', {
      taskId: requestId,
      clientRequestId,
      status: response.status,
      statusMessage: status,
      message,
      hasCitations: !!result.citations,
      citationsCount: result.citations?.length,
      hasClusters: !!result.clusters,
      clustersCount: result.clusters?.length,
      responseStructure: response.data.result ? 'nested' : 'flat',
      elapsed: Date.now() - startTime,
      responseKeys: Object.keys(responseData)
    });
    
    // Handle 404 - task not found or not ready
    if (response.status === 404) {
      console.log('Task not found or not ready yet, retrying...', {
        taskId: requestId,
        clientRequestId,
        elapsed: Date.now() - startTime,
        endpoint: `/task_status/${requestId}`
      });
      
      // If we've been waiting a while, the task might have been lost
      if (Date.now() - startTime > 30000) { // 30 seconds
        console.warn('Task not found after 30 seconds, it may have been lost', {
          taskId: requestId,
          clientRequestId,
          elapsed: Date.now() - startTime
        });
        throw new Error('Task not found or lost. Please try again.');
      }
      
      await new Promise(resolve => setTimeout(resolve, POLLING_INTERVAL));
      return pollForResults(requestId, clientRequestId, startTime);
    }
    
    // Check for completion - CRITICAL: Check status first, then data presence
    // Empty arrays are falsy, so check for array existence explicitly
    const hasCitations = Array.isArray(result.citations);
    const hasClusters = Array.isArray(result.clusters);
    const isComplete = status === 'completed' || status === 'finished' || hasCitations || hasClusters;
    
    if (isComplete) {
      console.log('✅ Task completed successfully:', {
        taskId: requestId,
        clientRequestId,
        status,
        elapsed: Date.now() - startTime,
        citationsCount: result.citations?.length || 0,
        clustersCount: result.clusters?.length || 0,
        hasError: !!result.error
      });
      
      // Return completed result - stop polling
      return { 
        ...result,
        status: 'completed',
        requestId: clientRequestId,
        message: message || 'Analysis completed successfully'
      };
    } else if (status === 'failed' || status === 'error' || responseData.error) {
      const errorMessage = responseData.error?.message ||
        responseData.error ||
        responseData.message ||
        'Request failed';

      console.error('Task failed:', {
        taskId: requestId,
        clientRequestId,
        error: errorMessage,
        status,
        elapsed: Date.now() - startTime,
        responseData: responseData,
        stack: responseData.stack || responseData.error?.stack
      });

      // Create a more detailed error object
      const error = new Error(errorMessage);
      error.response = response;
      error.taskId = requestId;
      error.status = status;
      error.elapsed = Date.now() - startTime;

      throw error;

    } else if (status === 'processing' || status === 'queued' || status === 'pending' || status === 'started') {
      // Log processing status for debugging
      const progressInfo = {
        taskId: requestId,
        clientRequestId,
        status,
        progress: responseData.progress,
        message: responseData.message || message,
        queuePosition: responseData.queue_position,
        estimatedWaitTime: responseData.estimated_wait_time,
        citationsCount: result.citations?.length || 0,
        clustersCount: result.clusters?.length || 0,
        elapsed: Date.now() - startTime
      };

      console.log('Processing status:', progressInfo);

      // If we've been processing for too long, consider it a timeout
      if (Date.now() - startTime > 300000) { // 5 minutes
        const timeoutError = new Error('Analysis timed out after 5 minutes');
        timeoutError.code = 'ETIMEDOUT';
        timeoutError.taskId = requestId;
        throw timeoutError;
      }

      // Continue polling with increasing delay
      const elapsed = Date.now() - startTime;
      const delay = Math.min(POLLING_INTERVAL * (1 + Math.floor(elapsed / 60000)), 10000); // Max 10s delay

      console.log(`🔄 POLLING: Status=${status}, Elapsed=${Math.round(elapsed / 1000)}s, Next check in ${delay}ms`);

      await new Promise(resolve => setTimeout(resolve, delay));
      return pollForResults(requestId, clientRequestId, startTime);

    } else {
      // Unknown status, log and continue polling with backoff
      const elapsed = Date.now() - startTime;
      const backoffTime = Math.min(POLLING_INTERVAL * 2, 15000); // Max 15s backoff

      console.warn('Unknown status, continuing to poll:', {
        taskId: requestId,
        clientRequestId,
        status,
        responseData: responseData,
        elapsed,
        nextCheckIn: backoffTime
      });

      // If we've been in an unknown state for too long, fail
      if (elapsed > 300000) { // 5 minutes
        const error = new Error('Analysis stuck in unknown state');
        error.code = 'EUNKNOWNSTATE';
        error.taskId = requestId;
        error.elapsed = elapsed;
        throw error;
      }

      await new Promise(resolve => setTimeout(resolve, backoffTime));
      return pollForResults(requestId, clientRequestId, startTime);
    }
  } catch (error) {
    // Enhanced error handling with detailed logging
    if (error.response) {
      if (error.response.status === 404) {
        console.log('Status endpoint not found, retrying...', {
          taskId: requestId,
          clientRequestId: clientRequestId,
          elapsed: Date.now() - startTime,
          endpoint: `/task_status/${requestId}`,
          baseURL,
          response: error.response.data
        });
        await new Promise(resolve => setTimeout(resolve, POLLING_INTERVAL));
        return pollForResults(requestId, clientRequestId, startTime);
      } else {
        console.error('Status check failed:', {
          taskId: requestId,
          clientRequestId: clientRequestId,
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
        clientRequestId: clientRequestId,
        message: error.message,
        endpoint: `/task_status/${requestId}`,
        baseURL
      });
      throw new Error('No response received from server');
    } else {
      console.error('Error checking status:', {
        taskId: requestId,
        clientRequestId: clientRequestId,
        message: error.message,
        endpoint: `/task_status/${requestId}`,
        baseURL
      });
      throw error;
    }
  }
}

// Test data detection function
const isTestData = (data) => {
    if (!data) return false;
    
    // Check if it's a text request with test data
    if (data.text) {
        const text = data.text.toLowerCase();
        const testPatterns = [
            'smith v. jones',
            '123 f.3d 456',
            '999 u.s. 999',
            'test citation',
            'sample citation',
            'fake citation'
        ];
        
        return testPatterns.some(pattern => text.includes(pattern));
    }
    
    // Check if it's a URL request with test URLs
    if (data.url) {
        return isTestUrl(data.url);
    }
    
    return false;
};

// URL validation function to detect test and problematic URLs
const isTestUrl = (url) => {
    if (!url || typeof url !== 'string') return false;
    
    const urlLower = url.toLowerCase();
    
    // Special exception for Washington court URLs - never block these
    if (urlLower.includes('courts.wa.gov')) {
        console.log('Washington court URL detected - allowing access:', url);
        return false;
    }
    
    // Test URL patterns
    const testUrlPatterns = [
        'example.com',
        'test.com',
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '::1',
        'test.local',
        'dev.local',
        'staging.local',
        'mock.com',
        'fake.com',
        'dummy.com',
        'sample.com'
    ];
    
    // Check for test URL patterns
    for (const pattern of testUrlPatterns) {
        if (urlLower.includes(pattern)) {
            console.warn(`Test URL detected: ${url} (pattern: ${pattern})`);
            return true;
        }
    }
    
    // Check for local development URLs
    if (urlLower.includes('localhost') || urlLower.includes('127.0.0.1')) {
        console.warn(`Local URL detected: ${url}`);
        return true;
    }
    
    // Check for potentially problematic URLs
    const problematicPatterns = [
        'file://',
        'ftp://',
        'mailto:',
        'tel:',
        'javascript:',
        'data:',
        'chrome://',
        'about:',
        'moz-extension://'
    ];
    
    for (const pattern of problematicPatterns) {
        if (urlLower.startsWith(pattern)) {
            console.warn(`Problematic URL protocol detected: ${url} (protocol: ${pattern})`);
            return true;
        }
    }
    
    return false;
};

// URL validation function for general use
const validateUrl = (url) => {
    if (!url || typeof url !== 'string') {
        throw new Error('URL must be a non-empty string');
    }
    
    if (url.length > 2048) {
        throw new Error('URL is too long (maximum 2048 characters)');
    }
    
    try {
        const urlObj = new URL(url);
        
        // Check protocol
        if (urlObj.protocol !== 'http:' && urlObj.protocol !== 'https:') {
            throw new Error('Only HTTP and HTTPS URLs are supported');
        }
        
        // Check for test URLs (temporarily disabled for debugging)
        if (isTestUrl(url)) {
            console.warn('Test URL detected but allowing for debugging:', url);
            // throw new Error('Test or local URLs are not allowed');
        }
        
        return true;
    } catch (error) {
        if (error.message.includes('Only HTTP and HTTPS') || error.message.includes('Test or local URLs')) {
            throw error;
        }
        throw new Error('Invalid URL format');
    }
};

// Update the analyze function to use the consolidated /analyze endpoint
export const analyze = async (requestData, requestId = null) => {
    // NUCLEAR OPTION: Global route check to prevent HomeView from calling analyze on EnhancedValidator page
    const currentPath = window.location.pathname;
    const isEnhancedValidatorPage = currentPath.includes('enhanced-validator');
    
    console.log('=== ANALYZE FUNCTION CALLED ===');
    console.log('🔍 Current path:', currentPath);
    console.log('🔍 Is EnhancedValidator page:', isEnhancedValidatorPage);
    console.log('Request data:', requestData);
    console.log('Request ID:', requestId);
    console.log('Request data type:', typeof requestData);
    console.log('Is FormData:', requestData instanceof FormData);
    
    // NUCLEAR BLOCK: If on EnhancedValidator page and this is a file upload, block HomeView calls
    if (isEnhancedValidatorPage && requestData instanceof FormData) {
        console.log('🔍 NUCLEAR BLOCK: analyze function blocked on EnhancedValidator page for file uploads!');
        console.log('🔍 NUCLEAR BLOCK: analyze function blocked on EnhancedValidator page! Only EnhancedValidator should handle file uploads!');
        throw new Error('File uploads are blocked on EnhancedValidator page. Only EnhancedValidator should handle file uploads.');
    }
    
    // DEBUG: Alert when analyze function is called
    let typeInfo = 'unknown';
    if (requestData instanceof FormData) {
      typeInfo = requestData.has('type') ? requestData.get('type') : 'missing';
    } else {
      typeInfo = requestData.type || 'unknown';
    }
    
    // Get stack trace to see where analyze is called from
    const stackTrace = new Error().stack;
    console.log('🔍 ANALYZE FUNCTION CALLED FROM:', stackTrace);
    
    // Show stack trace in alert to see where it's called from
    const stackLines = stackTrace.split('\n').slice(1, 4).join('\n'); // Get first 3 lines of stack
    console.log('🔍 ANALYZE FUNCTION CALLED! Type: ' + typeInfo + ' | IsFormData: ' + (requestData instanceof FormData) + '\n\nStack:\n' + stackLines);
    
    // Check for test data and reject it (only for text and URL inputs, not file uploads)
    // TEMPORARILY DISABLED for debugging - re-enable after testing
    /*
    if (!(requestData instanceof FormData) && isTestData(requestData)) {
        // Special exception for Washington court URLs
        if (requestData.url && requestData.url.includes('courts.wa.gov')) {
            console.log('Washington court URL detected - allowing despite test data check');
        } else {
            console.error('Test data detected and rejected:', requestData);
            throw new Error('Test data detected. Please provide actual document content.');
        }
    }
    */
    console.log('Test data validation temporarily disabled for debugging');
    
    // Validate URL if present
    if (requestData.url) {
        try {
            validateUrl(requestData.url);
        } catch (error) {
            console.error('URL validation failed:', error.message);
            throw new Error(`URL validation failed: ${error.message}`);
        }
    }
    
    // Set appropriate timeout based on input type
    let timeout;
    if (requestData.type === 'url') {
        timeout = 300000; // 5 minutes for URLs
    } else if (requestData instanceof FormData) {
        timeout = 600000; // 10 minutes for file uploads (PDF processing)
    } else {
        timeout = 120000; // 2 minutes for text input
    }
    
    console.log('Timeout set to:', timeout);
    
    try {
        // Log the analyze request
        console.log('Starting analysis:', {
            type: requestData.type,
            requestId: requestId,
            isFormData: requestData instanceof FormData,
            baseURL,
            endpoint: '/analyze'
        });
        
        // If it's FormData, log its contents
        if (requestData instanceof FormData) {
            console.log('FormData contents:');
            for (let [key, value] of requestData.entries()) {
                if (value instanceof File) {
                    console.log(`- ${key}: File(${value.name}, ${value.size} bytes, ${value.type})`);
                } else {
                    console.log(`- ${key}: ${value}`);
                }
            }
        }

        // If requestData is FormData (file upload), don't set Content-Type header
        // Otherwise, use application/json for other requests
        const headers = requestData instanceof FormData ? {} : {
            'Content-Type': 'application/json'
        };
        
        console.log('Request headers:', headers);
        console.log('Making API call to:', `${baseURL}/analyze`);
        
        const response = await api.post('/analyze', requestData, {
            timeout,
            headers,
            validateStatus: function (status) {
                console.log('Response status received:', status);
                return status < 500; // Accept any status less than 500
            }
        });
        
        // Log the analyze response
        console.log('Analysis response received:');
        console.log('- Status:', response.status);
        console.log('- Status text:', response.statusText);
        console.log('- Headers:', response.headers);
        console.log('- Data:', response.data);
        
        // Log the actual response data structure
        console.log('Response data details:', {
            hasCitations: !!response.data.citations,
            citationsLength: response.data.citations ? response.data.citations.length : 0,
            hasValidationResults: !!response.data.validation_results,
            validationResultsLength: response.data.validation_results ? response.data.validation_results.length : 0,
            hasError: !!response.data.error,
            error: response.data.error,
            status: response.data.status,
            message: response.data.message,
            hasTaskId: !!response.data.task_id,
            taskId: response.data.task_id
        });
        
        // Extract status and task ID from response
        const responseData = response.data.result || response.data;
        const status = responseData.status || responseData.state;
        const taskId = responseData.task_id || responseData.request_id || responseData.job_id;
        const message = responseData.message || responseData.detail;
        
        console.log('Processing response:', {
            status,
            taskId,
            message,
            hasResult: !!responseData.result,
            hasCitations: !!responseData.citations,
            hasClusters: !!responseData.clusters
        });
        
        // If we have a processing status with a task ID, start polling
        if ((status === 'processing' || status === 'queued' || status === 'started') && taskId) {
            console.log('Starting polling for task:', {
                taskId,
                requestId: requestId,
                status,
                message
            });
            
            try {
                const polledResults = await pollForResults(taskId, requestId);
                console.log('Polling completed with results:', {
                    hasCitations: !!polledResults.citations,
                    citationsCount: polledResults.citations?.length,
                    hasClusters: !!polledResults.clusters,
                    clustersCount: polledResults.clusters?.length
                });
                return { ...polledResults, requestId: requestId };
            } catch (error) {
                console.error('Error during polling:', error);
                throw error;
            }
        }
        
        console.log('Returning response data:', response.data);
        return { ...response.data, requestId: requestId };
    } catch (error) {
        console.error('=== ANALYZE FUNCTION ERROR ===');
        console.error('Error in analyze request:', {
            error,
            requestId: requestId,
            type: requestData.type,
            isFormData: requestData instanceof FormData,
            baseURL,
            endpoint: '/analyze'
        });
        console.error('Error details:', {
            message: error.message,
            code: error.code,
            response: error.response,
            request: error.request
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
