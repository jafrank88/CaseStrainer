import { ref } from 'vue';

// Constants
export const CONSTANTS = {
  MAX_TEXT_LENGTH: 1000000, // 1MB of text
  MIN_TEXT_LENGTH: 10,
  MAX_URL_LENGTH: 2048,
  PROCESSING_TIMEOUT: 300000, // 5 minutes
  URL_FETCH_TIMEOUT: 30000, // 30 seconds
  ALLOWED_PROTOCOLS: ['http:', 'https:'],
  VALID_FILE_TYPES: {
    'application/pdf': ['.pdf'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'text/plain': ['.txt'],
    'text/rtf': ['.rtf']
  },
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
  CONTENT_TYPES: {
    PDF: 'application/pdf',
    HTML: 'text/html',
    TEXT: 'text/plain',
    DOCX: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    DOC: 'application/msword',
    RTF: 'text/rtf'
  },
  PDF_EXTENSIONS: ['.pdf'],
};

// Validation utilities
export const validators = {
  validateText(text) {
    if (!text || typeof text !== 'string') {
      throw new Error('No text provided');
    }
    
    if (text.length > CONSTANTS.MAX_TEXT_LENGTH) {
      throw new Error(`Text is too long. Maximum length is ${CONSTANTS.MAX_TEXT_LENGTH} characters.`);
    }
    
    if (text.length < CONSTANTS.MIN_TEXT_LENGTH) {
      throw new Error(`Text is too short. Minimum length is ${CONSTANTS.MIN_TEXT_LENGTH} characters.`);
    }
    
    // Check for non-printable characters
    if (/[\x00-\x08\x0B\x0C\x0E-\x1F]/.test(text)) {
      throw new Error('Text contains invalid characters. Please remove any special characters and try again.');
    }
    
    return true;
  },
  
  validateUrl(urlString) {
    if (!urlString || typeof urlString !== 'string') {
      throw new Error('No URL provided');
    }
    
    if (urlString.length > CONSTANTS.MAX_URL_LENGTH) {
      throw new Error(`URL is too long. Maximum length is ${CONSTANTS.MAX_URL_LENGTH} characters.`);
    }
    
    try {
      const urlObj = new URL(urlString);
      
      if (!CONSTANTS.ALLOWED_PROTOCOLS.includes(urlObj.protocol)) {
        throw new Error('Only HTTP and HTTPS URLs are supported.');
      }
      
      return true;
    } catch (err) {
      if (err instanceof TypeError) {
        throw new Error('Invalid URL format. Please enter a valid URL.');
      }
      throw err;
    }
  },
  
  validateFile(file) {
    if (!file) {
      throw new Error('No file selected');
    }
    
    if (file.size > CONSTANTS.MAX_FILE_SIZE) {
      throw new Error(`File is too large. Maximum size is ${CONSTANTS.MAX_FILE_SIZE / (1024 * 1024)}MB.`);
    }
    
    if (file.size === 0) {
      throw new Error('File is empty');
    }
    
    const fileType = CONSTANTS.VALID_FILE_TYPES[file.type];
    if (!fileType) {
      throw new Error('Invalid file type. Please upload a PDF, Word document, or text file.');
    }
    
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    if (!fileType.includes(extension)) {
      throw new Error(`Invalid file extension. Allowed extensions for ${file.type} are: ${fileType.join(', ')}`);
    }
    
    return true;
  }
};

// Text processing utilities
export const textUtils = {
  cleanText(text) {
    return text
      .replace(/\r\n/g, '\n') // Normalize line endings
      .replace(/\t/g, '    ') // Replace tabs with spaces
      .replace(/[ \t]+/g, ' ') // Replace multiple spaces/tabs with single space
      .replace(/\n{3,}/g, '\n\n') // Replace multiple newlines with double newline
      .trim();
  },
  
  sanitizeFileName(name) {
    return name
      .replace(/[^a-zA-Z0-9.-]/g, '_') // Replace special chars with underscore
      .replace(/_+/g, '_') // Replace multiple underscores with single
      .replace(/^_+|_+$/g, ''); // Remove leading/trailing underscores
  }
};

// Error handling utilities
export const errorUtils = {
  createErrorObject(err) {
    const errorObj = {
      message: 'An error occurred during analysis',
      details: null,
      status: 500,
      code: err.code
    };

    if (err.code === 'ECONNABORTED') {
      errorObj.message = 'Request timed out. Please try again.';
    } else if (err.response) {
      errorObj.status = err.response.status;
      if (err.response.data) {
        switch (err.response.status) {
          case 400:
            errorObj.message = err.response.data.message || 'Invalid input. Please check your input and try again.';
            break;
          case 401:
            errorObj.message = 'Authentication required. Please log in and try again.';
            break;
          case 403:
            errorObj.message = 'Access denied. The resource might be restricted.';
            break;
          case 404:
            errorObj.message = 'Resource not found. Please check the input and try again.';
            break;
          case 429:
            errorObj.message = 'Too many requests. Please try again later.';
            break;
          case 500:
            errorObj.message = 'Server error. Please try again later.';
            break;
          default:
            errorObj.message = err.response.data.message || 'An error occurred while processing the request.';
        }
        errorObj.details = err.response.data;
      }
    } else if (err.request) {
      errorObj.message = 'No response from server. Please check your connection and try again.';
    } else {
      errorObj.message = `Request error: ${err.message}`;
    }
    
    return errorObj;
  }
};

// Citation processing utilities
export const citationUtils = {
  processCitations(citationsRaw) {
    // The backend now returns the correct structure, so just return as-is
    return citationsRaw;
  }
};

// Main analysis service
export const useAnalysisService = () => {
  const api = ref(null);
  const processingTimeout = ref(null);
  
  const initApi = async () => {
    if (!api.value) {
      api.value = (await import('@/api/api')).default;
    }
    return api.value;
  };
  
  const analyzeContent = async (content, type, options = {}) => {
    const startTime = Date.now();
    const currentApi = await initApi();
    
    // Set processing timeout
    processingTimeout.value = setTimeout(() => {
      throw new Error('Processing timed out. The content might be too large or the server might be slow to respond.');
    }, CONSTANTS.PROCESSING_TIMEOUT);
    
    try {
      // For URLs, check if it's a PDF
      let enhancedOptions = {
        extract_citations: true,
        validate_citations: true,
        ...options
      };
      
      if (type === 'url' && content.url) {
        const url = content.url.toLowerCase();
        const isPdfUrl = CONSTANTS.PDF_EXTENSIONS.some(ext => url.endsWith(ext));
        
        if (isPdfUrl) {
          enhancedOptions = {
            ...enhancedOptions,
            content_type: CONSTANTS.CONTENT_TYPES.PDF,
            pdf_options: {
              extract_metadata: true,
              extract_images: false,
              extract_tables: false,
              preserve_formatting: true
            }
          };
        }
      }
      
      let response;
      
      // Smart endpoint selection: use enhanced endpoint for text input, standard for files
      if (content instanceof File || content instanceof Blob) {
         // File uploads: use standard endpoint (enhanced doesn't support files)
         const fd = new FormData();
         fd.append("file", content);
         fd.append("type", "file");
         if (options && Object.keys(options).length > 0) {
           fd.append("options", JSON.stringify(options));
         }
         console.log('[ANALYSIS] Using standard /analyze endpoint for file upload');
         response = await currentApi.post('/analyze', fd, { timeout: CONSTANTS.PROCESSING_TIMEOUT, headers: {} });
      } else if (content instanceof FormData) {
         // Form data: use standard endpoint
         if (!content.has('type')) content.append('type', type);
         if (options && Object.keys(options).length > 0 && !content.has('options')) {
           content.append('options', JSON.stringify(options));
         }
         console.log('[ANALYSIS] Using standard /analyze endpoint for form data');
         response = await currentApi.post('/analyze', content, { timeout: CONSTANTS.PROCESSING_TIMEOUT, headers: {} });
      } else {
         // Text input: try enhanced endpoint first, fallback to standard if needed
         const isTextInput = type === 'text' || (content && content.text);
         
         if (isTextInput) {
           try {
             console.log('[ANALYSIS] Using enhanced /analyze_enhanced endpoint for text input');
             response = await currentApi.post('/analyze_enhanced', { ...content, type, options: enhancedOptions }, { timeout: CONSTANTS.PROCESSING_TIMEOUT });
           } catch (enhancedError) {
             console.warn('[ANALYSIS] Enhanced endpoint failed, falling back to standard:', enhancedError.message);
             console.log('[ANALYSIS] Using fallback standard /analyze endpoint');
             response = await currentApi.post('/analyze', { ...content, type, options: enhancedOptions }, { timeout: CONSTANTS.PROCESSING_TIMEOUT });
           }
         } else {
           // Non-text input (URLs, etc.): use standard endpoint
           console.log('[ANALYSIS] Using standard /analyze endpoint for non-text input');
           response = await currentApi.post('/analyze', { ...content, type, options: enhancedOptions }, { timeout: CONSTANTS.PROCESSING_TIMEOUT });
         }
      }
      
      // Clear timeout on success
      if (processingTimeout.value) clearTimeout(processingTimeout.value);
      
      const responseData = response.data || {};
      
      // Check if we got a task_id and need to poll for results
      if (responseData.task_id && (responseData.status === 'processing' || responseData.status === 'queued')) {
        console.log('Task started, polling for results:', responseData.task_id);
        
        // Poll for results
        let attempts = 0;
        const maxAttempts = 60; // 60 attempts * 2 seconds = 120 seconds max wait time
        let taskProgress = null;
        
        while (attempts < maxAttempts) {
          // Wait 2 seconds between polls
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          // Poll for results
          const pollResponse = await currentApi.get(`/casestrainer/api/analyze/progress/${responseData.task_id}`);
          
          if (pollResponse.data && pollResponse.data.status === 'completed') {
            console.log('Task completed, returning results');
            const completedData = pollResponse.data;
            const processedCitations = completedData.citations || [];
            const status = processedCitations.some(c => c.data?.valid || c.data?.found) ? 'Valid' : 'Invalid';
            
            return {
              ...completedData,
              citations: processedCitations,
              validation_results: processedCitations,
              status,
              taskProgress: {
                ...completedData,
                progress: 100,
                status: 'completed'
              },
              metadata: {
                ...completedData.metadata,
                processing_time: Date.now() - startTime,
                content_type: completedData.content_type || (type === 'url' && content.url?.toLowerCase().endsWith('.pdf') ? CONSTANTS.CONTENT_TYPES.PDF : undefined),
                content_length: completedData.content_length
              }
            };
          } else if (pollResponse.data && pollResponse.data.status === 'failed') {
            throw new Error(pollResponse.data.error || 'Task failed');
          } else if (pollResponse.data && (pollResponse.data.status === 'processing' || pollResponse.data.status === 'queued')) {
            // Task is still processing, capture progress info
            const progress = pollResponse.data.progress || 0;
            const statusMessage = pollResponse.data.status_message || 'Processing...';
            const currentStep = pollResponse.data.current_step || 'Processing';
            const estimatedTimeRemaining = pollResponse.data.estimated_time_remaining;
            
            taskProgress = {
              ...pollResponse.data,
              task_id: responseData.task_id,
              attempts: attempts + 1,
              max_attempts: maxAttempts,
              progress,
              status_message: statusMessage,
              current_step: currentStep,
              estimated_time_remaining: estimatedTimeRemaining
            };
            
            // Emit progress update if callback provided
            if (options.onProgress && typeof options.onProgress === 'function') {
              options.onProgress(taskProgress);
            }
            
            // Log progress for debugging
            console.log(`Task ${responseData.task_id} progress: ${progress}% - ${statusMessage}`);
            
            attempts++;
            continue;
          }
          
          attempts++;
        }
        
        // If we get here, the task timed out
        throw new Error('Task timed out');
      }
      
      // If no task_id or immediate response, process as before
      const processedCitations = responseData.citations || responseData.validation_results || [];
      const status = processedCitations.some(c => c.data?.valid || c.data?.found) ? 'Valid' : 'Invalid';
      
      return {
        ...responseData,
        citations: processedCitations,
        validation_results: processedCitations,
        status,
        metadata: {
          ...responseData.metadata,
          processing_time: Date.now() - startTime,
          content_type: responseData.content_type || (type === 'url' && content.url?.toLowerCase().endsWith('.pdf') ? CONSTANTS.CONTENT_TYPES.PDF : undefined),
          content_length: responseData.content_length
        }
      };
      
    } catch (err) {
      if (processingTimeout.value) clearTimeout(processingTimeout.value);
      
      // Enhance error message for PDF URLs
      if (type === 'url' && content.url?.toLowerCase().endsWith('.pdf')) {
        if (err.code === 'ECONNABORTED') {
          err.message = 'PDF download timed out. The file might be too large or the server might be slow to respond.';
        } else if (err.response?.status === 404) {
          err.message = 'PDF file not found. Please check if the URL is correct and the file is accessible.';
        } else if (err.response?.status === 403) {
          err.message = 'Access to the PDF file is restricted. The file might require authentication.';
        }
      }
      
      throw errorUtils.createErrorObject(err);
    }
  };
  
  const cleanup = () => {
    if (processingTimeout.value) {
      clearTimeout(processingTimeout.value);
      processingTimeout.value = null;
    }
  };
  
  return {
    analyzeContent,
    cleanup,
    CONSTANTS,
    validators,
    textUtils,
    errorUtils,
    citationUtils
  };
}; 