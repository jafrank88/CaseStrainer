<template>
  <div class="file-upload">
    <div class="card">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">Upload Document</h5>
      </div>
      <div class="card-body">
        <div v-if="error" class="alert alert-danger">
          <strong>Error:</strong> {{ error }}
        </div>
        
        <div class="mb-3">
          <label for="fileUpload" class="form-label">Select a file to analyze for citations</label>
          <input 
            type="file" 
            id="fileUpload" 
            class="form-control" 
            @change="handleFileChange"
            accept=".pdf,.docx,.txt,.rtf,.doc,.html,.htm"
          >
          <div class="form-text">Supported formats: PDF, DOCX, TXT, RTF, DOC, HTML</div>
        </div>
        
        <div v-if="file" class="mb-3">
          <div class="alert alert-info">
            <strong>Selected file:</strong> {{ file.name }} ({{ formatFileSize(file.size) }})
          </div>
        </div>
        
        <div v-if="uploadProgress > 0 && uploadProgress < 100" class="mb-3">
          <div class="progress">
            <div 
              class="progress-bar progress-bar-striped progress-bar-animated" 
              role="progressbar" 
              :style="{ width: uploadProgress + '%' }"
              :aria-valuenow="uploadProgress" 
              aria-valuemin="0" 
              aria-valuemax="100"
            >
              {{ uploadProgress }}%
            </div>
          </div>
        </div>
        
        <button 
          class="btn btn-primary" 
          @click="uploadFile" 
          :disabled="!file || isUploading"
        >
          <span v-if="isUploading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
          {{ isUploading ? 'Analyzing...' : 'Analyze Document' }}
        </button>
        
        <div v-if="results" class="mt-4">
          <h5>Analysis Results</h5>
          <div :class="['alert', getAlertClass(results.valid)]">
            <p><strong>Status:</strong> {{ results.valid ? 'Valid' : 'Invalid' }}</p>
            <p v-if="results.message">{{ results.message }}</p>
            
            <div v-if="results.citations && results.citations.length > 0">
              <h6>Found {{ results.citations.length }} citations:</h6>
              <ul class="list-group mt-2">
                <li 
                  v-for="(citation, index) in results.citations" 
                  :key="index"
                  class="list-group-item d-flex justify-content-between align-items-center"
                >
                  {{ citation.text }}
                  <span 
                    class="badge rounded-pill" 
                    :class="citation.valid ? 'bg-success' : 'bg-danger'"
                  >
                    {{ citation.valid ? 'Valid' : 'Invalid' }}
                  </span>
                </li>
              </ul>
            </div>
            
            <div v-if="results.metadata" class="mt-3">
              <h6>Document Metadata:</h6>
              <pre>{{ JSON.stringify(results.metadata, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';

export default {
  name: 'FileUpload',
  emits: ['results', 'error'],
  setup(props, { emit }) {
    const file = ref(null);
    const isUploading = ref(false);
    const uploadProgress = ref(0);
    const error = ref(null);
    const results = ref(null);
    
    // Base path for API requests
    const basePath = import.meta.env.VITE_API_BASE_URL || '';
    
    const handleFileChange = (event) => {
      if (event.target.files.length > 0) {
        file.value = event.target.files[0];
        error.value = null;
        results.value = null;
      }
    };
    
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };
    
    const uploadFile = async () => {
      if (!file.value) {
        error.value = 'Please select a file to upload';
        return;
      }
      
      // Check file size (max 10MB)
      const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
      if (file.value.size > MAX_FILE_SIZE) {
        error.value = `File is too large. Maximum size is ${formatFileSize(MAX_FILE_SIZE)}.`;
        return;
      }
      
      isUploading.value = true;
      uploadProgress.value = 0;
      error.value = null;
      results.value = null;
      
      try {
        console.log('Preparing to upload file:', file.value.name);
        
        // Create FormData for file upload
        const formData = new FormData();
        
        // Append the file with the correct field name and filename
        formData.append('file', file.value, file.value.name);
        formData.append('citation', 'document_analysis');
        formData.append('extract_citations', 'true');
        formData.append('validate_citations', 'true');
        
        // Get file extension
        const fileExt = file.value.name.split('.').pop().toLowerCase();
        
        // Add options as JSON string
        const options = {
          is_binary: true,
          file_type: file.value.type || `application/${fileExt}`,
          file_ext: fileExt,
          filename: file.value.name
        };
        
        console.log('File options:', options);
        formData.append('options', JSON.stringify(options));
        
        // Log form data contents for debugging
        for (let [key, value] of formData.entries()) {
          console.log(key, value);
        }
        
        // Import and use the API utility
        const api = (await import('@/api/api')).default;
        
        console.log('Sending request to enhanced validator endpoint');
        
        // Send the request with form data to the correct endpoint
        const response = await api.post('/analyze-document', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              uploadProgress.value = Math.min(percentCompleted, 90); // Cap at 90% until complete
            }
          },
        });
        
        console.log('Upload successful, response:', response);
        
        uploadProgress.value = 100;
        
        // Log the raw response for debugging
        console.log('Raw API Response:', response.data);
        
        // Handle the response data
        const responseData = response.data || {};
        let transformedResults = {
          valid: false,
          message: 'No results found',
          citations: [],
          metadata: {}
        };
        
        try {
          // Extract citations from the response (check both root and results.citations)
          const results = responseData.results || {};
          const citations = results.citations || responseData.citations || [];
          const totalCitations = results.total || responseData.total || 0;
          const verifiedCitations = results.verified || responseData.verified || 0;
          const message = results.message || `Found ${totalCitations} citations (${verifiedCitations} verified)`;
          
          // Transform the results
          transformedResults = {
            valid: results.valid || verifiedCitations > 0,
            message: message,
            citations: citations.map(citation => ({
              text: citation.text || 'Unknown citation',
              valid: citation.verified || false,
              source: citation.source || 'unknown',
              correction: citation.correction || '',
              url: citation.url || '',
              case_name: citation.case_name || '',
              confidence: citation.confidence || 0,
              name_match: citation.name_match || false
            })),
            metadata: {
              analysis_id: responseData.analysis_id || (results.metadata && results.metadata.analysis_id) || '',
              file_name: file?.value?.name || (results.metadata && results.metadata.file_name) || '',
              statistics: (results.metadata && results.metadata.statistics) || responseData.statistics || {}
            }
          };
        } catch (transformError) {
          console.error('Error transforming response:', transformError);
          throw new Error('Failed to process server response');
        }
        
        // Update the component state
        results.value = transformedResults;
        emit('results', transformedResults);
      } catch (err) {
        console.error('File upload error:', err);
        
        // Create a properly formatted error object
        const errorObj = {
          message: 'Failed to analyze document',
          details: null,
          status: 500
        };

        if (err.response) {
          // Handle HTTP errors (4xx, 5xx)
          errorObj.status = err.response.status;
          if (err.response.data) {
            if (typeof err.response.data === 'string' && err.response.data.includes('Error:')) {
              errorObj.message = err.response.data;
            } else if (err.response.status === 413) {
              errorObj.message = 'File is too large. Please upload a smaller file.';
            } else if (err.response.status === 415) {
              errorObj.message = 'Unsupported file type. Please upload a supported document format.';
            } else if (err.response.status === 400) {
              errorObj.message = 'Invalid request. Please check the file and try again.';
            } else if (err.response.data.message) {
              errorObj.message = err.response.data.message;
            }
            errorObj.details = err.response.data;
          }
        } else if (err.request) {
          // The request was made but no response was received
          errorObj.message = 'No response from server. Please check your connection and try again.';
        } else if (err.message) {
          // Something happened in setting up the request
          errorObj.message = `Request error: ${err.message}`;
        }
        
        error.value = errorObj.message;
        emit('error', errorObj);  // Emit the full error object
      } finally {
        isUploading.value = false;
      }
    };
    
    const getAlertClass = (isValid) => {
      return {
        'alert-success': isValid === true,
        'alert-danger': isValid === false,
        'alert-info': isValid === null || isValid === undefined
      };
    };
    
    return {
      file,
      isUploading,
      uploadProgress,
      error,
      results,
      handleFileChange,
      uploadFile,
      formatFileSize,
      getAlertClass
    };
  }
};
</script>

<style scoped>
.file-upload {
  width: 100%;
}

.progress {
  height: 25px;
  margin-bottom: 1rem;
  overflow: hidden;
  background-color: #e9ecef;
  border-radius: 0.25rem;
}

.progress-bar {
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
  color: #fff;
  text-align: center;
  white-space: nowrap;
  background-color: #0d6efd;
  transition: width 0.6s ease;
}

.progress-bar-striped {
  background-image: linear-gradient(45deg, rgba(255, 255, 255, 0.15) 25%, transparent 25%, transparent 50%, rgba(255, 255, 255, 0.15) 50%, rgba(255, 255, 255, 0.15) 75%, transparent 75%, transparent);
  background-size: 1rem 1rem;
}

@keyframes progress-bar-stripes {
  0% { background-position-x: 1rem; }
}

.progress-bar-animated {
  animation: progress-bar-stripes 1s linear infinite;
}

.badge {
  display: inline-block;
  padding: 0.35em 0.65em;
  font-size: 0.75em;
  font-weight: 700;
  line-height: 1;
  color: #fff;
  text-align: center;
  white-space: nowrap;
  vertical-align: baseline;
  border-radius: 0.25rem;
}

.bg-success {
  background-color: #198754 !important;
}

.bg-danger {
  background-color: #dc3545 !important;
}

.rounded-pill {
  border-radius: 50rem !important;
}

.d-flex {
  display: flex !important;
}

.justify-content-between {
  justify-content: space-between !important;
}

.align-items-center {
  align-items: center !important;
}

.mt-2 {
  margin-top: 0.5rem !important;
}

.mt-3 {
  margin-top: 1rem !important;
}

.mt-4 {
  margin-top: 1.5rem !important;
}

.mb-0 {
  margin-bottom: 0 !important;
}

.mb-3 {
  margin-bottom: 1rem !important;
}

.mr-2 {
  margin-right: 0.5rem !important;
}

.text-muted {
  color: #6c757d !important;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .card {
    margin-bottom: 1rem;
  }
  
  .btn {
    width: 100%;
    margin-bottom: 0.5rem;
  }
  
  .form-control {
    font-size: 16px; /* Prevent zoom on mobile */
  }
}
</style>
