<template>
  <div class="file-upload">
    <div class="card">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">Upload Document</h5>
      </div>
      <div class="card-body">
        <div class="mb-3">
          <label for="fileUpload" class="form-label">Select a file to analyze for citations</label>
          <input 
            type="file" 
            id="fileUpload" 
            class="form-control" 
            @change="handleFileChange"
            accept=".pdf,.docx,.txt,.rtf,.doc,.html,.htm"
            :disabled="isAnalyzing"
          >
          <div class="form-text">Supported formats: PDF, DOCX, TXT, RTF, DOC, HTML</div>
        </div>
        <div v-if="file" class="mb-3">
          <div class="alert alert-info">
            <strong>Selected file:</strong> {{ file.name }} ({{ formatFileSize(file.size) }})
          </div>
        </div>
        <button 
          class="btn btn-primary" 
          @click="emitAnalyze"
          :disabled="!file || isAnalyzing"
        >
          <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
          {{ isAnalyzing ? 'Analyzing...' : 'Analyze Document' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';

export default {
  name: 'FileUpload',
  emits: ['analyze'],
  props: {
    isAnalyzing: {
      type: Boolean,
      default: false
    }
  },
  setup(props, { emit }) {
    const file = ref(null);
    const handleFileChange = (event) => {
      const selectedFile = event.target.files[0];
      file.value = selectedFile || null;
    };
    const formatFileSize = (bytes) => {
      if (!bytes) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };
    const emitAnalyze = () => {
      if (!file.value) return;
      emit('analyze', { file: file.value });
    };
    return {
      file,
      handleFileChange,
      formatFileSize,
      emitAnalyze
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

@media (max-width: 768px) {
  .card {
    margin-bottom: 1rem;
  }
  .btn {
    width: 100%;
    margin-top: 0.5rem;
  }
  .form-control {
    font-size: 16px;
  }
}
</style>
