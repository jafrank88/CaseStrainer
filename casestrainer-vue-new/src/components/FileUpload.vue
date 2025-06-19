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
          :disabled="!file || isAnalyzing"
        >
          <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
          {{ isAnalyzing ? 'Analyzing...' : 'Analyze Document' }}
        </button>
        
        <div v-if="false" class="mt-4">
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
                  {{ citation.citation }}
                  <span 
                    class="badge rounded-pill" 
                    :class="getStatusBadgeClass(citation)"
                  >
                    {{ getStatusText(citation) }}
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
import { ref, onMounted, onUnmounted } from 'vue';
import { useAnalysisService } from '@/services/analysisService';

export default {
  name: 'FileUpload',
  emits: ['results', 'error', 'loading', 'progress'],
  setup(props, { emit }) {
    const file = ref(null);
    const isAnalyzing = ref(false);
    const error = ref(null);
    const results = ref(null);
    const uploadProgress = ref(0);
    const taskProgress = ref(null);
    
    const {
      analyzeContent,
      cleanup,
      validators,
      textUtils
    } = useAnalysisService();
    
    const handleFileChange = (event) => {
      const selectedFile = event.target.files[0];
      if (!selectedFile) return;
      
      try {
        validators.validateFile(selectedFile);
        file.value = selectedFile;
        error.value = null;
      } catch (err) {
        error.value = err.message;
        file.value = null;
        event.target.value = ''; // Reset file input
      }
    };
    
    const uploadFile = async () => {
      if (!file.value) {
        error.value = 'Please select a file to analyze';
        return;
      }
      
      try {
        // Validate file again before upload
        validators.validateFile(file.value);
        
        isAnalyzing.value = true;
        error.value = null;
        results.value = null;
        uploadProgress.value = 0;
        emit('loading', true);
        
        try {
          // Create FormData with additional metadata
          const fd = new FormData();
          fd.append("file", file.value);
          fd.append("type", "file");
          fd.append("options", JSON.stringify({
            extract_citations: true,
            validate_citations: true,
            preserve_formatting: true,
            extract_metadata: true,
            source_name: file.value.name,
            source_type: "file"
          }));
          
          // Log upload start
          console.log('Starting file upload:', {
            fileName: file.value.name,
            fileSize: file.value.size,
            fileType: file.value.type
          });
          
          // Pass the FormData to analyzeContent
          const processedResults = await analyzeContent(
            fd,
            'file',
            {
              onUploadProgress: (progressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 95) / progressEvent.total);
                uploadProgress.value = percentCompleted;
                console.log('Upload progress:', percentCompleted + '%');
              },
              onProgress: (progressData) => {
                taskProgress.value = progressData;
                emit('progress', progressData);
                console.log('Task progress:', progressData);
                
                // Update upload progress to 100% once processing starts
                if (progressData.progress > 0) {
                  uploadProgress.value = 100;
                }
              }
            }
          );
          
          // Log successful upload
          console.log('File upload completed:', {
            taskId: processedResults.task_id,
            status: processedResults.status,
            message: processedResults.message
          });
          
          uploadProgress.value = 100;
          results.value = processedResults;
          emit('results', processedResults);
          
        } catch (err) {
          console.error('File upload error:', {
            error: err,
            message: err.message,
            response: err.response?.data
          });
          
          // Enhanced error handling
          if (err.response) {
            if (err.response.status === 413) {
              error.value = 'File is too large. Please try a smaller file.';
            } else if (err.response.status === 415) {
              error.value = 'Unsupported file type. Please upload a PDF, Word document, or text file.';
            } else if (err.response.status === 429) {
              error.value = 'Too many requests. Please wait a moment before trying again.';
            } else {
              error.value = err.response.data?.message || `Upload failed: ${err.response.status} ${err.response.statusText}`;
            }
          } else if (err.code === 'ECONNABORTED') {
            error.value = 'Upload timed out. Please try again.';
          } else {
            error.value = err.message || 'An error occurred during file upload.';
          }
          
          emit('error', error.value);
        }
        
      } catch (err) {
        error.value = err.message;
        emit('error', { message: err.message, status: 400 });
      } finally {
        isAnalyzing.value = false;
        emit('loading', false);
      }
    };
    
    onUnmounted(() => {
      cleanup();
    });
    
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };
    
    const getAlertClass = (isValid) => {
      return {
        'alert-success': isValid === true,
        'alert-danger': isValid === false,
        'alert-info': isValid === null || isValid === undefined
      };
    };
    
    const getStatusBadgeClass = (citation) => {
      if (citation.valid || citation.verified || citation.data?.valid || citation.data?.found || citation.exists) {
        return 'bg-success';
      } else if (isValidCitationFormat(citation)) {
        return 'bg-warning text-dark';
      }
      return 'bg-danger';
    };
    
    const getStatusText = (citation) => {
      if (citation.valid || citation.verified || citation.data?.valid || citation.data?.found || citation.exists) {
        return 'Verified';
      } else if (isValidCitationFormat(citation)) {
        return 'Valid but Not Verified';
      }
      return 'Invalid';
    };
    
    const isValidCitationFormat = (citation) => {
      const citationText = citation.citation || citation.text || citation.citation_text || 'Unknown Citation';
      
      // Check if it's clearly invalid (like "Filed", "Page", etc.)
      const invalidPatterns = [
        /^filed\s+\d+$/i,
        /^page\s+\d+$/i,
        /^docket\s+\d+$/i,
        /^\d+\s+filed\s+\d+$/i,
        /^\d+\s+page\s+\d+$/i,
        /^\d+\s+docket\s+\d+$/i
      ];
      
      for (const pattern of invalidPatterns) {
        if (pattern.test(citationText)) {
          return false;
        }
      }
      
      // Check if it looks like a valid legal citation format
      const validPatterns = [
        /\d+\s+[A-Z]\.\s*\d+/i,  // e.g., "534 F.3d 1290"
        /\d+\s+[A-Z]{2,}\.\s*\d+/i,  // e.g., "123 Wash. 456"
        /\d+\s+WL\s+\d+/i,  // Westlaw citations
        /\d+\s+U\.S\.\s+\d+/i,  // Supreme Court
        /\d+\s+S\.\s*Ct\.\s+\d+/i,  // Supreme Court
        /\d+\s+[A-Z]\.\s*App\.\s*\d+/i,  // Appellate courts
      ];
      
      for (const pattern of validPatterns) {
        if (pattern.test(citationText)) {
          return true;
        }
      }
      
      return false;
    };
    
    return {
      file,
      isAnalyzing,
      error,
      results,
      uploadProgress,
      taskProgress,
      handleFileChange,
      uploadFile,
      formatFileSize,
      getAlertClass,
      getStatusBadgeClass,
      getStatusText,
      isValidCitationFormat
    };
  }
};
</script>

<style scoped>
.file-upload {
  width: 100%;
}

.form-control:disabled {
  background-color: #e9ecef;
  cursor: not-allowed;
}

.progress {
  height: 0.5rem;
  margin-top: 0.5rem;
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
    margin-top: 0.5rem;
  }
  
  .form-control {
    font-size: 16px; /* Prevent zoom on mobile */
  }
}
</style>
