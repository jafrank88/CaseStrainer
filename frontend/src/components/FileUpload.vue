<template>
  <div class="file-upload">
    <!-- File Selection Area -->
    <div v-if="!isProcessing" class="upload-container">
      <div 
        class="file-drop-zone"
        :class="{ 
          'dragover': isDragOver, 
          'has-file': selectedFile,
          'error': !!errorMessage 
        }"
        @drop="handleDrop"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
        @click="triggerFileSelect"
      >
        <input
          ref="fileInput"
          type="file"
          @change="handleFileSelect"
          :accept="acceptedTypes"
          class="file-input"
          :disabled="disabled"
        />
        
        <div v-if="!selectedFile" class="drop-zone-content">
          <i class="fas fa-cloud-upload-alt upload-icon"></i>
          <h3 class="drop-zone-title">Choose a file or drag it here</h3>
          <p class="file-types">Supported: {{ supportedFormats }}</p>
          <div class="drop-zone-hint">
            <i class="fas fa-info-circle"></i>
            Maximum file size: {{ maxFileSizeMB }}MB
          </div>
        </div>

        <div v-else class="file-info">
          <i class="fas fa-file file-icon" :class="getFileIconClass(selectedFile)"></i>
          <div class="file-details">
            <strong>{{ selectedFile.name }}</strong>
            <div class="file-meta">
              {{ formatFileSize(selectedFile.size) }} • {{ getFileType(selectedFile) }}
            </div>
          </div>
          <button 
            @click.stop="clearFile" 
            class="clear-file-btn"
            :disabled="disabled"
            title="Remove file"
          >
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>

      <!-- Upload Button -->
      <button 
        v-if="selectedFile"
        @click="uploadFile" 
        :disabled="!selectedFile || isProcessing || disabled" 
        class="upload-button"
      >
        <i class="fas fa-upload"></i>
        {{ uploadButtonText }}
      </button>
    </div>

    <!-- Processing State -->
    <div v-else class="processing-container">
      <div class="progress-container">
        <div class="progress-bar-bg">
          <div 
            class="progress-bar" 
            :class="{ 'processing': isProcessing && uploadProgress >= 100 }"
            :style="{ width: Math.min(uploadProgress, 100) + '%' }"
          ></div>
        </div>
        <div class="progress-text">
          <span v-if="uploadProgress < 100">
            <i class="fas fa-upload"></i>
            Uploading... {{ Math.round(uploadProgress) }}%
          </span>
          <span v-else>
            <i class="fas fa-cog fa-spin"></i>
            Processing... {{ Math.round(processingProgress) }}%
          </span>
        </div>
      </div>
      
      <div v-if="statusMessage" class="status-message">
        <i class="fas fa-info-circle"></i>
        {{ statusMessage }}
      </div>

      <!-- Cancel Button -->
      <button 
        @click="cancelUpload" 
        class="cancel-button"
        :disabled="!canCancel"
      >
        <i class="fas fa-times"></i>
        Cancel
      </button>
    </div>

    <!-- Error Message -->
    <div v-if="errorMessage" class="error-message">
      <i class="fas fa-exclamation-triangle"></i>
      {{ errorMessage }}
      <button @click="clearError" class="error-dismiss">
        <i class="fas fa-times"></i>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useFileUpload } from '@/composables/useFileUpload';

// Props with defaults
interface FileUploadProps {
  modelValue: File[] | null;
  multiple?: boolean;
  maxFiles?: number;
  maxFileSize?: number;
  acceptedTypes?: string;
}

const props = withDefaults(defineProps<FileUploadProps>(), {
  disabled: false,
  maxFileSize: 10 * 1024 * 1024, // 10MB
  maxFiles: 5,
  multiple: false,
  acceptedTypes: '.pdf,.doc,.docx,.txt',
  modelValue: null
});

// Emits
interface FileUploadEmits {
  (e: 'update:modelValue', files: File[] | null): void;
  (e: 'upload', files: File[]): Promise<void>;
  (e: 'error', error: Error): void;
  (e: 'progress', progress: number): void;
  (e: 'complete', result: any): void;
}

const emit = defineEmits<FileUploadEmits>();

// ... rest of the code remains the same ...
// Refs for template reactivity
const isProcessing = ref(false);
const uploadProgress = ref(0);
const processingProgress = ref(0);
const errorMessage = ref<string | null>(null);
const statusMessage = ref('Drag & drop a file here or click to browse');
const selectedFile = ref<File | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const isDragging = ref(false);

// Computed properties
const canCancel = computed(() => {
  return isProcessing.value && uploadProgress.value < 100;
});

const maxFileSizeMB = computed(() => (props.maxFileSize / (1024 * 1024)).toFixed(2));

const supportedFormats = computed((): string => {
  return props.acceptedTypes
    .split(',')
    .map((ext: string): string => ext.replace('.', '').toUpperCase())
    .join(', ');
});

// Composable
const {
  isProcessing: isProcessingComposable,
  uploadProgress: uploadProgressComposable,
  processingProgress: processingProgressComposable,
  errorMessage: errorMessageComposable,
  statusMessage: statusMessageComposable,
  uploadFile: uploadWithProgress,
  cancelUpload: cancelFileUpload,
  cleanupProcessing
} = useFileUpload();

// Sync refs with composable
watch(isProcessingComposable, (val) => {
  isProcessing.value = val;
});

watch(uploadProgressComposable, (val) => {
  uploadProgress.value = val;
  emit('update:progress', val);
});

watch(processingProgressComposable, (val) => {
  processingProgress.value = val;
});

watch(errorMessageComposable, (val) => {
  errorMessage.value = val;
  emit('update:error', val);
});

watch(statusMessageComposable, (val) => {
  statusMessage.value = val;
  emit('update:status', val);
});

// File validation
const validateFile = (file: File): string | null => {
  // Check file type
  if (props.acceptedTypes) {
    const allowedTypes = props.acceptedTypes.split(',').map(t => t.trim().toLowerCase());
    const fileExt = file.name.split('.').pop()?.toLowerCase() || '';
    const fileType = file.type.toLowerCase();
    
    const isTypeAllowed = allowedTypes.some(type => {
      // Handle both extensions (e.g., '.pdf') and MIME types (e.g., 'application/pdf')
      return fileExt === type.replace('.', '') || fileType.includes(type.replace('*', ''));
    });

    if (!isTypeAllowed) {
      return `File type not allowed. Allowed types: ${props.acceptedTypes}`;
    }
  }

  // Check file size
  if (file.size > props.maxFileSize) {
    return `File is too large. Maximum size is ${maxFileSizeMB.value}MB`;
  }

  return null;
};

// Event handlers
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const files = target.files;
  
  if (files && files.length > 0) {
    selectFile(files[0]);
  }
};

const handleDrop = (event: DragEvent) => {
  event.preventDefault();
  event.stopPropagation();
  isDragging.value = false;

  if (props.disabled) return;

  const files = event.dataTransfer?.files;
  if (files && files.length > 0) {
    selectFile(files[0]);
  }
};

const handleDragOver = (event: DragEvent) => {
  event.preventDefault();
  event.stopPropagation();
  if (!props.disabled) {
    isDragging.value = true;
  }
};

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault();
  event.stopPropagation();
  isDragging.value = false;
};

const selectFile = (file: File) => {
  const validationError = validateFile(file);
  
  if (validationError) {
    errorMessage.value = validationError;
    return;
  }

  selectedFile.value = file;
  clearError();
  emit('file-selected', file);
};

const triggerFileSelect = () => {
  if (!props.disabled && fileInput.value) {
    fileInput.value.click();
  }
};

const clearFile = () => {
  selectedFile.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
  clearError();
  emit('file-cleared');
};

const clearError = () => {
  errorMessage.value = '';
};

const cancelUpload = () => {
  cancelFileUpload();
  clearFile();
};

// Upload function
const uploadFile = async () => {
  if (!selectedFile.value) {
    errorMessage.value = "Please select a file first";
    return;
  }

  try {
    const formData = new FormData();
    formData.append('file', selectedFile.value);
    
    const fileOptions = {
      convert_pdf_to_md: true,
      is_binary: true,
      file_type: selectedFile.value.type,
      file_ext: selectedFile.value.name.split('.').pop()?.toLowerCase()
    };
    
    formData.append('options', JSON.stringify(fileOptions));
    
    const result = await uploadWithProgress(formData);
    
    if (result) {
      emit('upload-success', result);
      // Clear file after successful upload
      clearFile();
    }
  } catch (error) {
    emit('upload-error', {
      message: errorMessage.value || 'An error occurred during upload',
      error: error
    });
  }
};

// Utility functions
const formatFileSize = (bytes: number): string => {
  if (!bytes) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

const getFileType = (file: File): string => {
  const ext = file.name.split('.').pop()?.toLowerCase();
  return ext ? ext.toUpperCase() : 'Unknown';
};

const getFileIconClass = (file: File): string => {
  const type = getFileType(file).toLowerCase();
  const iconMap: Record<string, string> = {
    'pdf': 'fa-file-pdf',
    'doc': 'fa-file-word',
    'docx': 'fa-file-word',
    'xls': 'fa-file-excel',
    'xlsx': 'fa-file-excel',
    'ppt': 'fa-file-powerpoint',
    'pptx': 'fa-file-powerpoint',
    'txt': 'fa-file-alt',
    'zip': 'fa-file-archive',
    'rar': 'fa-file-archive',
    '7z': 'fa-file-archive',
    'jpg': 'fa-file-image',
    'jpeg': 'fa-file-image',
    'png': 'fa-file-image',
    'gif': 'fa-file-image',
    'bmp': 'fa-file-image',
    'csv': 'fa-file-csv',
    'json': 'fa-file-code',
    'js': 'fa-file-code',
    'ts': 'fa-file-code',
    'html': 'fa-file-code',
    'css': 'fa-file-code',
    'md': 'fa-file-alt',
    'rtf': 'fa-file-alt'
  };
  
  return iconMap[type] || 'fa-file';
};

// Lifecycle
onMounted(() => {
  // Prevent default drag behaviors on the window
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    document.addEventListener(eventName, preventDefaults, false);
  });
});

onUnmounted(() => {
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    document.removeEventListener(eventName, preventDefaults, false);
  });
  cleanupProcessing();
});

const preventDefaults = (e: Event) => {
  e.preventDefault();
  e.stopPropagation();
};

// Expose methods for parent component
defineExpose({
  clearFile,
  clearError,
  triggerFileSelect,
  selectedFile: readonly(selectedFile)
});
</script>

<style scoped>
.file-upload {
  width: 100%;
  max-width: 100%;
}

.upload-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.file-input {
  display: none;
}

.file-drop-zone {
  border: 3px dashed #dee2e6;
  border-radius: 16px;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafbfc;
  position: relative;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-drop-zone:hover:not(.error) {
  border-color: #4dabf7;
  background: #f8f9ff;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(77, 171, 247, 0.15);
}

.file-drop-zone.dragover {
  border-color: #4dabf7;
  background: #f8f9ff;
  transform: scale(1.02);
  box-shadow: 0 12px 30px rgba(77, 171, 247, 0.2);
}

.file-drop-zone.has-file {
  border-style: solid;
  border-color: #28a745;
  background: #f8fff9;
  padding: 2rem;
}

.file-drop-zone.error {
  border-color: #dc3545;
  background: #fff5f5;
}

.drop-zone-content {
  color: #6c757d;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.7;
  color: #4dabf7;
}

.drop-zone-title {
  margin: 0 0 1rem 0;
  font-weight: 600;
  color: #495057;
  font-size: 1.25rem;
}

.file-types {
  font-size: 0.9rem;
  margin: 1rem 0;
  color: #6c757d;
  background: rgba(77, 171, 247, 0.1);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  display: inline-block;
}

.drop-zone-hint {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(77, 171, 247, 0.1);
  border-radius: 8px;
  color: #4dabf7;
  font-weight: 500;
  font-size: 0.9rem;
}

.drop-zone-hint i {
  margin-right: 0.5rem;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  text-align: left;
  width: 100%;
}

.file-icon {
  font-size: 2.5rem;
  color: #28a745;
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-details strong {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 1.1rem;
  color: #343a40;
  word-break: break-all;
}

.file-meta {
  color: #6c757d;
  font-size: 0.9rem;
}

.clear-file-btn {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.clear-file-btn:hover:not(:disabled) {
  background: #c82333;
  transform: scale(1.1);
}

.upload-button {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
}

.upload-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #20c997 0%, #17a2b8 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
}

.upload-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.processing-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 2rem;
  background: #f8f9fa;
  border-radius: 12px;
  text-align: center;
}

.progress-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.progress-bar-bg {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #4dabf7, #28a745);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-bar.processing {
  background: linear-gradient(90deg, #ffc107, #fd7e14);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.progress-text {
  font-weight: 600;
  color: #495057;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.status-message {
  color: #6c757d;
  font-style: italic;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.cancel-button {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  align-self: center;
}

.cancel-button:hover:not(:disabled) {
  background: #c82333;
  transform: translateY(-1px);
}

.cancel-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #f5c6cb;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
}

.error-dismiss {
  background: none;
  border: none;
  color: #721c24;
  cursor: pointer;
  padding: 0.25rem;
  margin-left: auto;
  border-radius: 4px;
  transition: background 0.2s ease;
}

.error-dismiss:hover {
  background: rgba(114, 28, 36, 0.1);
}

/* Responsive Design */
@media (max-width: 768px) {
  .file-drop-zone {
    padding: 2rem 1rem;
    min-height: 150px;
  }
  
  .upload-icon {
    font-size: 2rem;
  }
  
  .drop-zone-title {
    font-size: 1.1rem;
  }
  
  .file-info {
    flex-direction: column;
    text-align: center;
    gap: 0.75rem;
  }
  
  .upload-button {
    padding: 0.875rem 1.5rem;
    font-size: 1rem;
  }
}
</style>