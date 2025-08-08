<template>
  <div class="modern-file-upload">
    <div class="upload-card">
      <div class="upload-header">
        <div class="header-icon">
          <i class="bi bi-cloud-upload"></i>
        </div>
        <h3 class="header-title">Upload Document</h3>
        <p class="header-subtitle">Drag & drop or click to select your legal document</p>
      </div>
      
      <div class="upload-body">
        <!-- Hidden file input -->
        <input 
          ref="fileInput"
          type="file" 
          id="fileUpload" 
          class="file-input" 
          @change="handleFileChange"
          accept=".pdf,.docx,.txt,.rtf,.md,.html,.htm,.xml,.xhtml"
          :disabled="isAnalyzing"
        />
        
        <!-- Drop Zone -->
        <div 
          :class="['drop-zone', { 
            'has-file': file, 
            'dragover': isDragOver,
            'analyzing': isAnalyzing,
            'error': fileError
          }]"
          @drop="onFileDrop"
          @dragover.prevent="onDragOver"
          @dragleave.prevent="onDragLeave"
          @click="triggerFileInput"
        >
          <!-- Empty State -->
          <div v-if="!file" class="drop-zone-empty">
            <div class="upload-icon">
              <i class="bi bi-cloud-upload"></i>
            </div>
            <h4 class="upload-title">
              {{ isDragOver ? 'Drop your file here' : 'Click to browse or drag & drop' }}
            </h4>
            <p class="upload-subtitle">
              Supports: PDF, DOCX, TXT, RTF, MD, HTML, XML
            </p>
            <div class="upload-limit">
              <i class="bi bi-info-circle me-1"></i>
              Maximum file size: 50MB
            </div>
          </div>
          
          <!-- File Selected State -->
          <div v-else class="file-preview">
            <div class="file-icon">
              <i :class="getFileIcon(file.name)"></i>
            </div>
            <div class="file-details">
              <h5 class="file-name">{{ file.name }}</h5>
              <p class="file-size">{{ formatFileSize(file.size) }}</p>
              <div class="file-type">{{ getFileType(file.name) }}</div>
            </div>
            <button 
              v-if="!isAnalyzing"
              @click.stop="clearFile" 
              class="remove-btn remove-btn-purple"
              title="Remove file"
              aria-label="Remove file"
            >
              <i class="bi bi-x-lg"></i> Remove
            </button>
          </div>
        </div>
        
        <!-- Error Message -->
        <div v-if="fileError" class="error-message">
          <i class="bi bi-exclamation-triangle me-2"></i>
          {{ fileError }}
        </div>
        
        <!-- File Analysis Info -->
        <div v-if="file && !fileError" class="file-analysis-info">
          <div class="analysis-stats">
            <div class="stat-item">
              <i class="bi bi-file-earmark-text"></i>
              <span>{{ getFileType(file.name) }}</span>
            </div>
            <div class="stat-item">
              <i class="bi bi-hdd"></i>
              <span>{{ formatFileSize(file.size) }}</span>
            </div>
            <div class="stat-item">
              <i class="bi bi-calendar3"></i>
              <span>{{ formatDate(file.lastModified) }}</span>
            </div>
          </div>
        </div>
        
        <!-- Analyze Button -->
        <div class="upload-actions">
          <button 
            :class="['analyze-btn', { 'disabled': !file || isAnalyzing || fileError }]"
            @click="emitAnalyze"
            :disabled="!file || isAnalyzing || fileError"
          >
            <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2"></span>
            <i v-else class="bi bi-search me-2"></i>
            {{ isAnalyzing ? 'Analyzing Document...' : 'Analyze Document' }}
          </button>
          
          <div v-if="file && !isAnalyzing" class="secondary-actions">
            <button 
              @click="clearFile" 
              class="btn btn-outline-secondary btn-sm"
            >
              <i class="bi bi-arrow-clockwise me-1"></i>
              Choose Different File
            </button>
          </div>
        </div>
        
        <!-- Analysis Progress -->
        <div v-if="isAnalyzing" class="analysis-progress">
          <div class="progress-info">
            <div class="progress-text">
              <i class="bi bi-gear-fill spinning me-2"></i>
              Processing your document...
            </div>
            <div class="progress-steps">
              <span class="step active">Reading file</span>
              <span class="step active">Extracting text</span>
              <span class="step">Finding citations</span>
              <span class="step">Validating results</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';

export default {
  name: 'ModernFileUpload',
  emits: ['analyze'],
  props: {
    isAnalyzing: {
      type: Boolean,
      default: false
    }
  },
  setup(props, { emit }) {
    const file = ref(null);
    const fileInput = ref(null);
    const isDragOver = ref(false);
    const fileError = ref('');
    
    // File handling methods
    const handleFileChange = (event) => {
      const selectedFile = event.target.files[0];
      if (selectedFile) {
        validateAndSetFile(selectedFile);
      }
    };
    
    const onFileDrop = (event) => {
      event.preventDefault();
      isDragOver.value = false;
      
      const droppedFile = event.dataTransfer.files[0];
      if (droppedFile) {
        validateAndSetFile(droppedFile);
      }
    };
    
    const onDragOver = (event) => {
      event.preventDefault();
      isDragOver.value = true;
    };
    
    const onDragLeave = (event) => {
      event.preventDefault();
      isDragOver.value = false;
    };
    
    const validateAndSetFile = (selectedFile) => {
      fileError.value = '';
      
      // Validate file type
      const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'application/rtf',
        'text/html',
        'text/htm'
      ];
      
      const allowedExtensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.html', '.htm'];
      const fileExtension = selectedFile.name.toLowerCase().substring(selectedFile.name.lastIndexOf('.'));
      
      if (!allowedTypes.includes(selectedFile.type) && !allowedExtensions.includes(fileExtension)) {
        fileError.value = 'Please select a valid file type (PDF, DOCX, TXT, RTF, MD, HTML, or XML)';
        return;
      }
      
      // Validate file size (100MB)
      if (selectedFile.size > 100 * 1024 * 1024) {
        fileError.value = 'File size must be less than 100MB';
        return;
      }
      
      file.value = selectedFile;
    };
    
    const triggerFileInput = () => {
      if (!props.isAnalyzing && fileInput.value) {
        fileInput.value.click();
      }
    };
    
    const clearFile = () => {
      file.value = null;
      fileError.value = '';
      if (fileInput.value) {
        fileInput.value.value = '';
      }
    };
    
    // Utility methods
    const formatFileSize = (bytes) => {
      if (!bytes) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };
    
    const formatDate = (timestamp) => {
      if (!timestamp) return 'Unknown';
      return new Date(timestamp).toLocaleDateString();
    };
    
    const getFileIcon = (fileName) => {
      const extension = fileName.toLowerCase().substring(fileName.lastIndexOf('.'));
      const iconMap = {
        '.pdf': 'bi bi-file-earmark-pdf text-danger',
        '.doc': 'bi bi-file-earmark-word text-primary',
        '.docx': 'bi bi-file-earmark-word text-primary',
        '.txt': 'bi bi-file-earmark-text text-secondary',
        '.rtf': 'bi bi-file-earmark-richtext text-info',
        '.html': 'bi bi-file-earmark-code text-warning',
        '.htm': 'bi bi-file-earmark-code text-warning'
      };
      return iconMap[extension] || 'bi bi-file-earmark text-muted';
    };
    
    const getFileType = (fileName) => {
      const extension = fileName.toLowerCase().substring(fileName.lastIndexOf('.'));
      const typeMap = {
        '.pdf': 'PDF Document',
        '.doc': 'Word Document',
        '.docx': 'Word Document',
        '.txt': 'Text File',
        '.rtf': 'Rich Text Format',
        '.html': 'HTML Document',
        '.htm': 'HTML Document'
      };
      return typeMap[extension] || 'Document';
    };
    
    const emitAnalyze = async () => {
      if (!file.value || fileError.value) return;
      
      console.log('🔍 FileUpload: Starting text extraction process');
      
      try {
        // Step 1: Extract text from the file
        let extractedText = '';
        
        if (file.value.type === 'text/plain' || file.value.name.endsWith('.txt')) {
          // For text files, read directly
          extractedText = await file.value.text();
        } else if (file.value.type === 'application/pdf' || file.value.name.endsWith('.pdf')) {
          // For PDFs, we'll need to send to backend for extraction
          console.log('🔍 FileUpload: PDF detected, sending to backend for text extraction');
          const formData = new FormData();
          formData.append('file', file.value);
          formData.append('type', 'file');
          formData.append('fileName', file.value.name);
          formData.append('fileSize', file.value.size.toString());
          formData.append('extractText', 'true');
          
          emit('analyze', formData);
          return;
        } else {
          // For other file types, try to read as text
          try {
            extractedText = await file.value.text();
          } catch (error) {
            console.error('🔍 FileUpload: Error reading file as text:', error);
            // Fallback to original file upload
            const formData = new FormData();
            formData.append('file', file.value);
            formData.append('type', 'file');
            formData.append('fileName', file.value.name);
            formData.append('fileSize', file.value.size.toString());
            emit('analyze', formData);
            return;
          }
        }
        
        console.log('🔍 FileUpload: Text extracted successfully, length:', extractedText.length);
        
        // Step 2: Pass extracted text to text processing
        const textData = {
          text: extractedText,
          type: 'text',
          source: 'file',
          fileName: file.value.name,
          fileSize: file.value.size
        };
        
        console.log('🔍 FileUpload: Emitting text data for processing');
        emit('analyze', textData);
        
      } catch (error) {
        console.error('🔍 FileUpload: Error in text extraction:', error);
        // Fallback to original file upload
        const formData = new FormData();
        formData.append('file', file.value);
        formData.append('type', 'file');
        formData.append('fileName', file.value.name);
        formData.append('fileSize', file.value.size.toString());
        emit('analyze', formData);
      }
    };
    
    return {
      file,
      fileInput,
      isDragOver,
      fileError,
      handleFileChange,
      onFileDrop,
      onDragOver,
      onDragLeave,
      triggerFileInput,
      clearFile,
      formatFileSize,
      formatDate,
      getFileIcon,
      getFileType,
      emitAnalyze
    };
  }
};
</script>

<style scoped>
:root {
  --primary-color: #1976d2;
  --primary-light: #42a5f5;
  --success-color: #4caf50;
  --error-color: #f44336;
  --warning-color: #ff9800;
  --text-primary: #212529;
  --text-secondary: #6c757d;
  --border-color: #e9ecef;
  --background-light: #f8f9fa;
  --shadow-light: 0 2px 12px 0 rgba(60, 72, 88, 0.08);
  --shadow-medium: 0 4px 24px 0 rgba(60, 72, 88, 0.12);
}

.modern-file-upload {
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
}

.upload-card {
  background: white;
  border-radius: 2rem;
  box-shadow: var(--shadow-medium);
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s ease;
}

.upload-header {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  color: white;
  padding: 2rem;
  text-align: center;
  position: relative;
}

.upload-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Cpath d='m36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E") repeat;
  opacity: 0.1;
}

.header-icon {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem auto;
  font-size: 2.5rem;
  position: relative;
  z-index: 1;
}

.header-title {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  position: relative;
  z-index: 1;
}

.header-subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  margin: 0;
  position: relative;
  z-index: 1;
}

.upload-body {
  padding: 2.5rem;
}

.file-input {
  display: none;
}

.drop-zone {
  border: 3px dashed var(--border-color);
  border-radius: 1.5rem;
  padding: 3rem 2rem;
  text-align: center;
  background: var(--background-light);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  margin-bottom: 2rem;
}

.drop-zone::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(25, 118, 210, 0.1), transparent);
  transition: left 0.6s;
}

.drop-zone:hover::before {
  left: 100%;
}

.drop-zone.dragover {
  border-color: var(--primary-color);
  background: rgba(25, 118, 210, 0.05);
  transform: scale(1.02);
  box-shadow: 0 8px 25px rgba(25, 118, 210, 0.2);
}

.drop-zone.has-file {
  border-color: var(--success-color);
  background: rgba(76, 175, 80, 0.05);
  border-style: solid;
}

.drop-zone.analyzing {
  pointer-events: none;
  opacity: 0.7;
}

.drop-zone.error {
  border-color: var(--error-color);
  background: rgba(244, 67, 54, 0.05);
}

.drop-zone-empty {
  padding: 1rem;
}

.upload-icon {
  font-size: 4rem;
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
  transition: all 0.3s ease;
}

.drop-zone:hover .upload-icon {
  color: var(--primary-color);
  transform: translateY(-8px);
}

.upload-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
}

.upload-subtitle {
  color: var(--text-secondary);
  margin-bottom: 1rem;
  font-size: 1rem;
}

.upload-limit {
  color: var(--text-secondary);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-preview {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  background: white;
  padding: 1.5rem;
  border-radius: 1rem;
  box-shadow: var(--shadow-light);
  position: relative;
}

.file-icon {
  font-size: 3rem;
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  text-align: left;
  min-width: 0;
}

.file-name {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
  word-break: break-all;
}

.file-size {
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
  font-size: 0.95rem;
}

.file-type {
  color: var(--primary-color);
  font-size: 0.9rem;
  font-weight: 500;
}

.remove-btn {
  background: var(--error-color);
  color: white;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.remove-btn:hover {
  background: #d32f2f;
  transform: scale(1.1);
}

.error-message {
  background: rgba(244, 67, 54, 0.1);
  color: var(--error-color);
  padding: 1rem;
  border-radius: 0.75rem;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  font-weight: 500;
}

.file-analysis-info {
  background: var(--background-light);
  border-radius: 1rem;
  padding: 1.5rem;
  margin-bottom: 2rem;
  border: 1px solid var(--border-color);
}

.analysis-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.stat-item i {
  color: var(--primary-color);
}

.upload-actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.analyze-btn {
  background: #1976d2;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 14px 36px;
  font-size: 1.1rem;
  font-weight: bold;
  cursor: pointer;
  margin-top: 24px;
  box-shadow: 0 2px 12px rgba(25, 118, 210, 0.12);
  transition: background 0.2s, box-shadow 0.2s;
  display: block;
  width: 100%;
  max-width: 340px;
  margin-left: auto;
  margin-right: auto;
}
.analyze-btn:hover:not(:disabled),
.analyze-btn:focus:not(:disabled) {
  background: #1565c0;
  box-shadow: 0 4px 16px rgba(25, 118, 210, 0.18);
}
.analyze-btn:disabled {
  background: #bdbdbd;
  cursor: not-allowed;
  opacity: 0.7;
}

.secondary-actions {
  display: flex;
  justify-content: center;
}

.analysis-progress {
  background: var(--background-light);
  border-radius: 1rem;
  padding: 2rem;
  text-align: center;
  border: 1px solid var(--border-color);
}

.progress-text {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--primary-color);
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.progress-steps {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.step {
  flex: 1;
  padding: 0.5rem;
  background: white;
  border-radius: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  min-width: 100px;
}

.step.active {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

/* Purple remove button style for file */
.remove-btn-purple {
  background: #a259e6 !important;
  color: #fff !important;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  padding: 0.25rem 0.75rem;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 0.4em;
  transition: background 0.2s;
}
.remove-btn-purple:hover, .remove-btn-purple:focus {
  background: #7c3aed !important;
  color: #fff !important;
}

@media (max-width: 768px) {
  .upload-card {
    margin: 0 1rem;
    border-radius: 1.5rem;
  }
  
  .upload-header {
    padding: 1.5rem;
  }
  
  .upload-body {
    padding: 1.5rem;
  }
  
  .drop-zone {
    padding: 2rem 1rem;
  }
  
  .file-preview {
    flex-direction: column;
    text-align: center;
    gap: 1rem;
  }
  
  .analysis-stats {
    grid-template-columns: 1fr;
  }
  
  .progress-steps {
    flex-direction: column;
  }
  
  .step {
    min-width: auto;
  }
}

@media (max-width: 480px) {
  .header-title {
    font-size: 1.5rem;
  }
  
  .header-subtitle {
    font-size: 1rem;
  }
  
  .upload-icon {
    font-size: 3rem;
  }
  
  .upload-title {
    font-size: 1.1rem;
  }
}
</style>