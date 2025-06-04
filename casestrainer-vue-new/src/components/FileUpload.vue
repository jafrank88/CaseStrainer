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
      
      isUploading.value = true;
      uploadProgress.value = 0;
      error.value = null;
      results.value = null;
      
      const formData = new FormData();
      formData.append('file', file.value);
      
      try {
        // Import and use the API utility
        const api = (await import('@/utils/api')).default;
        
        // For file uploads, we need to use axios directly but with our configured instance
        const response = await api.post('/analyze-document', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              uploadProgress.value = Math.min(percentCompleted, 90); // Cap at 90% until complete
            }
          },
        });
        
        uploadProgress.value = 100;
        results.value = response;
        emit('results', results.value);
      } catch (err) {
        console.error('File upload error:', err);
        error.value = err.response?.data?.message || 'Failed to analyze document';
        emit('error', error.value);
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
