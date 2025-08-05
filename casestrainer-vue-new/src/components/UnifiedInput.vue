<template>
  <div class="unified-input">
         <!-- Single Row: File Upload, URL, and Paste Text -->
     <div class="input-methods-single">
       <div 
         :class="['input-method-card', { active: inputMode === 'file', disabled: isAnalyzing }]"
         @click="!isAnalyzing && (inputMode = 'file', onModeChange())"
       >
         <div class="method-icon">{{ methodIcons.file }}</div>
         <div class="method-content">
           <h4>{{ modeLabels.file }}</h4>
           <p>{{ modeDescriptions.file }}</p>
         </div>
         <div v-if="inputMode === 'file'" class="active-indicator">✓</div>
       </div>
 
       <div 
         :class="['input-method-card', { active: inputMode === 'url', disabled: isAnalyzing }]"
         @click="!isAnalyzing && (inputMode = 'url', onModeChange())"
       >
         <div class="method-icon">{{ methodIcons.url }}</div>
         <div class="method-content">
           <h4>{{ modeLabels.url }}</h4>
           <p>{{ modeDescriptions.url }}</p>
         </div>
         <div v-if="inputMode === 'url'" class="active-indicator">✓</div>
       </div>
 
       <div 
         :class="['input-method-card', { active: inputMode === 'text', disabled: isAnalyzing }]"
         @click="!isAnalyzing && (inputMode = 'text', onModeChange())"
       >
         <div class="method-icon">{{ methodIcons.text }}</div>
         <div class="method-content">
           <h4>{{ modeLabels.text }}</h4>
           <p>{{ modeDescriptions.text }}</p>
         </div>
         <div v-if="inputMode === 'text'" class="active-indicator">✓</div>
       </div>
     </div>
 
     <!-- Input Area for File, URL, and Text -->
     <div class="input-area-single" v-if="inputMode === 'file' || inputMode === 'url' || inputMode === 'text'">
      <!-- File Input -->
      <div v-if="inputMode === 'file'" class="file-input">
        <label class="input-label">
          <i class="bi bi-file-earmark-arrow-up me-2"></i>
          Upload a document
        </label>
        <div 
          :class="['file-drop-zone', { 
            'has-file': file, 
            'dragover': isDragOver,
            'error': hasErrors && isDirty.file 
          }]"
          @drop="onFileDrop"
          @dragover.prevent="isDragOver = true"
          @dragleave.prevent="isDragOver = false"
          @click="triggerFileInput"
        >
          <input 
            ref="fileInput"
            id="fileInput"
            type="file" 
            @change="onFileChange" 
            :disabled="isAnalyzing"
            accept=".pdf,.doc,.docx,.txt"
            style="display: none;"
          />
          <div v-if="!file" class="drop-zone-content">
            <div class="upload-icon">📁</div>
            <h5 class="drop-zone-title">Click to browse or drag & drop</h5>
            <p class="file-types">Supports: PDF, DOC, DOCX, TXT (max 50MB)</p>
            <div class="drop-zone-hint">
              <i class="bi bi-arrow-up-circle"></i>
              <span>Drop your file here</span>
            </div>
          </div>
          <div v-else class="file-info">
            <div class="file-icon">📄</div>
            <div class="file-details">
              <strong>{{ file.name }}</strong>
              <span>{{ formatFileSize(file.size) }}</span>
            </div>
            <button 
              v-if="!isAnalyzing"
              @click.stop="clearFile" 
              class="clear-file-btn"
              title="Remove file"
            >
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
        </div>
        <!-- Validation Errors -->
        <div v-if="hasErrors && isDirty.file" class="validation-errors">
          <div v-for="error in currentErrors" :key="error" class="error-message">
            <span class="error-icon">⚠️</span>
            {{ error }}
          </div>
        </div>
      </div>

      <!-- URL Input -->
      <div v-else-if="inputMode === 'url'" class="url-input">
        <label class="input-label">
          <i class="bi bi-link-45deg me-2"></i>
          Enter URL to analyze
        </label>
        <div class="url-input-container">
          <div class="input-wrapper">
            <div class="input-icon">
              <i class="bi bi-globe"></i>
            </div>
            <input 
              v-model="url" 
              type="url" 
              placeholder="https://example.com/document.pdf"
              :disabled="isAnalyzing"
              @input="handleInputChange"
              :class="{ 'error': hasErrors && isDirty.url }"
              class="url-input-field"
            />
            <div v-if="url && !hasErrors" class="input-status valid">
              <i class="bi bi-check-circle-fill"></i>
            </div>
            <div v-else-if="url && hasErrors" class="input-status invalid">
              <i class="bi bi-x-circle-fill"></i>
            </div>
          </div>
        </div>
        <div class="input-footer">
          <span class="url-preview" v-if="url && !hasErrors">
            <i class="bi bi-eye me-1"></i>
            Will analyze: {{ url }}
          </span>
          <span v-else-if="url && hasErrors" class="url-error">
            <i class="bi bi-exclamation-triangle me-1"></i>
            Invalid URL format
          </span>
          <span v-else class="url-hint">
            <i class="bi bi-info-circle me-1"></i>
            Enter a valid URL to analyze web content
          </span>
        </div>
        <!-- Validation Errors -->
        <div v-if="hasErrors && isDirty.url" class="validation-errors">
          <div v-for="error in currentErrors" :key="error" class="error-message">
            <span class="error-icon">⚠️</span>
            {{ error }}
          </div>
        </div>
             </div>
     </div>
 
     <!-- Recent Inputs Section - Temporarily Hidden -->
     <!-- <RecentInputs @load-input="loadRecentInput" /> -->
     
     <!-- Input Area for Text (moved from bottom) -->
     <div class="input-area-single" v-if="inputMode === 'text'">
      <!-- Text Input -->
      <div v-if="inputMode === 'text'" class="text-input">
        <label class="input-label">
          <i class="bi bi-text-paragraph me-2"></i>
          Paste your text here
        </label>
        <div class="textarea-container">
          <textarea 
            v-model="text" 
            placeholder="Paste legal text, citations, or document content here..."
            :disabled="isAnalyzing"
            rows="8"
            @input="handleInputChange"
            :class="{ 'error': hasErrors && isDirty.text }"
            class="text-input-field"
          ></textarea>
          <div class="textarea-overlay" v-if="!text">
            <i class="bi bi-clipboard"></i>
            <span>Paste your content here</span>
          </div>
        </div>
        <div class="input-footer">
          <span class="char-count" :class="{ 'error': text.length > VALIDATION_RULES.text.maxLength }">
            <i class="bi bi-type me-1"></i>
            {{ text.length }} / {{ VALIDATION_RULES.text.maxLength }} characters
          </span>
          <span v-if="text.length < VALIDATION_RULES.text.minLength && isDirty.text" class="min-length-hint">
            <i class="bi bi-exclamation-circle me-1"></i>
            Minimum {{ VALIDATION_RULES.text.minLength }} characters required
          </span>
        </div>
        <!-- Validation Errors -->
        <div v-if="hasErrors && isDirty.text" class="validation-errors">
          <div v-for="error in currentErrors" :key="error" class="error-message">
            <span class="error-icon">⚠️</span>
            {{ error }}
          </div>
        </div>
             </div>
     </div>
   </div>
   
   <!-- Analyze Button - Outside input areas so it appears for all input types -->
   <div class="analyze-section" v-if="inputMode === 'file' || inputMode === 'url' || inputMode === 'text'">
     <button 
       :class="['analyze-btn', { disabled: !canAnalyze || isAnalyzing }]"
       :disabled="!canAnalyze || isAnalyzing" 
       @click="emitAnalyze"
     >
       <span v-if="isAnalyzing" class="analyzing-spinner"></span>
       <span v-else class="analyze-icon">🔍</span>
       {{ isAnalyzing ? 'Analyzing...' : 'Analyze Content' }}
     </button>
     <!-- Validation Summary -->
     <div v-if="showValidationWarning && hasErrors" class="validation-summary">
       <p>Please fix the errors above before analyzing</p>
     </div>
 </div>
 </template>

<script setup>
import { ref, computed } from 'vue';
// import RecentInputs from './RecentInputs.vue'; // Temporarily hidden

const props = defineProps({
  isAnalyzing: { type: Boolean, default: false }
});

const emit = defineEmits(['analyze']);

 const modes = ['text', 'url', 'file'];
 const modeLabels = { 
   text: 'Paste Text', 
   url: 'URL', 
   file: 'Upload File'
 };
 const modeDescriptions = {
   text: 'Paste legal text or citations directly',
   url: 'Analyze content from a web URL',
   file: 'Upload a document for analysis'
 };
 const methodIcons = {
   text: '📝',
   url: '🔗',
   file: '📁'
 };

// Validation constants
const VALIDATION_RULES = {
  text: {
    minLength: 10,
    maxLength: 50000,
    minLengthMessage: 'Text must be at least 10 characters long',
    maxLengthMessage: 'Text is too long. Maximum 50,000 characters allowed.'
  },
  url: {
    maxLength: 2048,
    maxLengthMessage: 'URL is too long. Maximum 2,048 characters allowed.'
  },
  file: {
    maxSize: 50 * 1024 * 1024, // 50MB
    allowedTypes: ['.pdf', '.doc', '.docx', '.txt'],
    maxSizeMessage: 'File is too large. Maximum 50MB allowed.',
    typeMessage: 'Invalid file type. Please upload PDF, DOC, DOCX, or TXT files.'
  }
};

const inputMode = ref('text');
const text = ref('');
const url = ref('');
 const file = ref(null);
 const isDragOver = ref(false);
 const fileInput = ref(null);

// Validation state
const validationErrors = ref({});
 const isDirty = ref({ text: false, url: false, file: false });
const showValidationWarning = ref(false);

// Validation functions
function validateText(text) {
  const errors = [];
  const rules = VALIDATION_RULES.text;
  
  if (!text.trim()) {
    errors.push('Text is required');
  } else if (text.length < rules.minLength) {
    errors.push(rules.minLengthMessage);
  } else if (text.length > rules.maxLength) {
    errors.push(rules.maxLengthMessage);
  }
  
  // Check for non-printable characters
  if (/[\x00-\x08\x0B\x0C\x0E-\x1F]/.test(text)) {
    errors.push('Text contains invalid characters. Please remove any special characters.');
  }
  
  return errors;
}

function validateUrl(url) {
  const errors = [];
  const rules = VALIDATION_RULES.url;
  if (!url.trim()) {
    errors.push('URL is required');
  } else if (url.length > rules.maxLength) {
    errors.push(rules.maxLengthMessage);
  } else {
    // Only require http(s) and a dot
    if (!/^https?:\/\//.test(url)) {
      errors.push('URL must start with http:// or https://');
    } else if (!/\./.test(url)) {
      errors.push('URL must contain a dot');
    }
  }
  return errors;
}

function validateFile(file) {
  const errors = [];
  const rules = VALIDATION_RULES.file;
  
  if (!file) {
    errors.push('Please select a file');
  } else {
    if (file.size > rules.maxSize) {
      errors.push(rules.maxSizeMessage);
    }
    
    if (file.size === 0) {
      errors.push('File is empty');
    }
    
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    if (!rules.allowedTypes.includes(extension)) {
      errors.push(rules.typeMessage);
    }
  }
  
  return errors;
}

// Real-time validation
function validateCurrentInput() {
  const errors = {};
  
  if (inputMode.value === 'text') {
    errors.text = validateText(text.value);
  } else if (inputMode.value === 'url') {
    errors.url = validateUrl(url.value);
  } else if (inputMode.value === 'file') {
    errors.file = validateFile(file.value);
  }
  
  validationErrors.value = errors;
}

// Watch for changes and validate
function handleInputChange() {
  isDirty.value[inputMode.value] = true;
  showValidationWarning.value = false;
  validateCurrentInput();
  console.log('[handleInputChange] mode:', inputMode.value, 'file:', file.value, 'url:', url.value, 'hasErrors:', hasErrors.value, 'currentErrors:', currentErrors.value);
}

// Computed properties
const currentErrors = computed(() => {
  return validationErrors.value[inputMode.value] || [];
});

const hasErrors = computed(() => {
  return currentErrors.value.length > 0;
});

const canAnalyze = computed(() => {
  let result = false;
  if (props.isAnalyzing) return false;
  if (inputMode.value === 'text') {
    result = text.value.length >= VALIDATION_RULES.text.minLength && text.value.length <= VALIDATION_RULES.text.maxLength;
  } else if (inputMode.value === 'url') {
    // TEMP: Only require a value for debugging
    result = url.value.length > 0;
  } else if (inputMode.value === 'file') {
    // TEMP: Only require a file for debugging
    result = !!file.value;
  }
  
  console.log('[canAnalyze] mode:', inputMode.value, 'result:', result, 'file:', file.value, 'url:', url.value, 'hasErrors:', hasErrors.value, 'currentErrors:', currentErrors.value);
  return result;
});

// Event handlers
function onFileChange(e) {
  e.preventDefault();
  e.stopPropagation();
  file.value = e.target.files[0] || null;
  isDragOver.value = false;
  handleInputChange();
}

function onFileDrop(e) {
  e.preventDefault();
  e.stopPropagation();
  const droppedFile = e.dataTransfer.files[0];
  if (droppedFile) {
    file.value = droppedFile;
    handleInputChange();
  }
  isDragOver.value = false;
}

function triggerFileInput() {
  if (!props.isAnalyzing) {
    fileInput.value?.click();
  }
}

function clearFile() {
  file.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
  handleInputChange();
}

function emitAnalyze() {
  if (!canAnalyze.value) {
    showValidationWarning.value = true;
    return;
  }
  showValidationWarning.value = false;
  if (inputMode.value === 'text') {
    emit('analyze', { text: text.value, type: 'text' });
  } else if (inputMode.value === 'url') {
    emit('analyze', { url: url.value, type: 'url' });
  } else if (inputMode.value === 'file') {
    // Always send FormData with 'type' and optional 'options'
    const formData = new FormData();
    formData.append('file', file.value);
    formData.append('type', 'file');
    // If you have options, add them here (example: analysis options)
    // formData.append('options', JSON.stringify(options));
    emit('analyze', formData);
  }
}

function loadRecentInput(input) {
  // Update the input mode and values based on the recent input
  inputMode.value = input.tab;
  
  switch (input.tab) {
    case 'text':
      text.value = input.text || '';
      break;
    case 'url':
      url.value = input.url || '';
      break;
    case 'file':
      // For files, we can't restore the actual file, but we can show a message
      console.log('File input selected:', input.fileName);
      break;
  }
  
  // Trigger validation
  validateCurrentInput();
}

function formatFileSize(bytes) {
  if (!bytes) return '0 Bytes';
  const k = 1024, sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Watch for mode changes to reset validation and force validation
function onModeChange() {
  validationErrors.value = {};
  isDirty.value = { text: false, url: false, file: false };
  showValidationWarning.value = false;
  validateCurrentInput();
  console.log('[onModeChange] inputMode:', inputMode.value, 'file:', file.value, 'url:', url.value, 'hasErrors:', hasErrors.value, 'currentErrors:', currentErrors.value);
}
</script>

<style scoped>
.unified-input {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

 .input-methods-single {
   display: flex;
   gap: 0.75rem;
   margin-bottom: 1.5rem;
   flex-wrap: wrap;
   width: 100%;
 }

.input-method-card {
  background: white;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  min-width: 140px;
  max-width: none;
}

.input-method-card:hover:not(.disabled) {
  border-color: #007bff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.15);
}

.input-method-card.active {
  border-color: #007bff;
  background: #f8f9ff;
}

.input-method-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.method-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.method-content {
  flex: 1;
  min-width: 0;
}

.method-content h4 {
  margin: 0 0 0.2rem 0;
  font-size: 0.9rem;
  font-weight: 600;
}

.method-content p {
  margin: 0;
  font-size: 0.75rem;
  color: #6c757d;
  line-height: 1.1;
}

.active-indicator {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: #007bff;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
}

 .input-area-single {
   background: white;
   border-radius: 12px;
   padding: 1.5rem;
   margin-bottom: 1.5rem;
   box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
   animation: slideDown 0.3s ease-out;
   width: 100%;
 }

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.input-label {
  display: block;
  margin-bottom: 1rem;
  font-weight: 600;
  color: #495057;
  font-size: 1.1rem;
}

.input-label i {
  color: #007bff;
}

/* URL Input Styling */
.url-input-container {
  position: relative;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  background: white;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  transition: all 0.2s ease;
  overflow: hidden;
}

.input-wrapper:focus-within {
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.input-wrapper.error {
  border-color: #dc3545;
  background-color: #fff5f5;
}

.input-icon {
  padding: 0 1rem;
  color: #6c757d;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.url-input-field,
.quick-citation-input {
  flex: 1;
  padding: 1rem;
  border: none;
  outline: none;
  font-size: 1rem;
  background: transparent;
}

.url-input-field:focus,
.quick-citation-input:focus {
  outline: none;
}

.input-status {
  padding: 0 1rem;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.input-status.valid {
  color: #28a745;
}

.input-status.invalid {
  color: #dc3545;
}

/* Text Input Styling */
.textarea-container {
  position: relative;
}

.text-input-field {
  width: 100%;
  padding: 1.25rem;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.2s ease;
  resize: vertical;
  min-height: 180px;
  background: white;
}

.text-input-field:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.text-input-field.error {
  border-color: #dc3545;
  background-color: #fff5f5;
}

.textarea-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #6c757d;
  text-align: center;
  pointer-events: none;
  z-index: 1;
}

.textarea-overlay i {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  display: block;
}

/* Quick Input Container */
.quick-input-container {
  position: relative;
}

.input-footer {
  margin-top: 1rem;
  font-size: 0.9rem;
  color: #6c757d;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #007bff;
}

.url-preview {
  color: #28a745;
  font-weight: 500;
}

.url-error {
  color: #dc3545;
  font-weight: 600;
}

.url-hint,
.citation-hint {
  color: #6c757d;
  font-style: italic;
}

.char-count {
  color: #6c757d;
  font-weight: 500;
}

.char-count.error {
  color: #dc3545;
  font-weight: 600;
}

.min-length-hint {
  color: #856404;
  background: #fff3cd;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-size: 0.85rem;
  border-left: 3px solid #ffc107;
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
  overflow: hidden;
}

.file-drop-zone:hover:not(.disabled) {
  border-color: #007bff;
  background: #f8f9ff;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 123, 255, 0.15);
}

.file-drop-zone.dragover {
  border-color: #007bff;
  background: #f8f9ff;
  transform: scale(1.02);
  box-shadow: 0 12px 30px rgba(0, 123, 255, 0.2);
}

.file-drop-zone.has-file {
  border-style: solid;
  border-color: #28a745;
  background: #f8fff9;
  box-shadow: 0 4px 15px rgba(40, 167, 69, 0.15);
}

.file-drop-zone.error {
  border-color: #dc3545;
  background: #fff5f5;
}

.drop-zone-content {
  color: #6c757d;
}

.drop-zone-title {
  margin: 0.75rem 0 0.4rem 0;
  font-weight: 600;
  color: #495057;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 0.75rem;
  opacity: 0.7;
}

.file-types {
  font-size: 0.85rem;
  margin: 0.75rem 0;
  color: #6c757d;
  background: rgba(0, 123, 255, 0.1);
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  display: inline-block;
}

.drop-zone-hint {
  margin-top: 0.75rem;
  padding: 0.6rem 0.8rem;
  background: rgba(0, 123, 255, 0.1);
  border-radius: 8px;
  color: #007bff;
  font-weight: 500;
}

.drop-zone-hint i {
  margin-right: 0.5rem;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-icon {
  font-size: 2rem;
}

.file-details {
  flex: 1;
  text-align: left;
}

.file-details strong {
  display: block;
  margin-bottom: 0.25rem;
}

.clear-file-btn {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  cursor: pointer;
  font-size: 1rem;
}

.analyze-section {
  text-align: center;
  margin: 0.75rem 0 1.5rem 0;
  padding: 1.25rem;
  background: linear-gradient(135deg, #f8f9ff 0%, #e8f4fd 100%);
  border-radius: 16px;
  border: 2px solid #e3f2fd;
  width: 100%;
}

.analyze-btn {
  background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
  color: white;
  border: none;
  border-radius: 16px;
  padding: 1rem 2.5rem;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3);
  position: relative;
  overflow: hidden;
}

.analyze-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.analyze-btn:hover:not(.disabled)::before {
  left: 100%;
}

.analyze-btn:hover:not(.disabled) {
  background: linear-gradient(135deg, #0056b3 0%, #004085 100%);
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 123, 255, 0.4);
}

.analyze-btn:active:not(.disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3);
}

.analyze-btn.disabled {
  background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%);
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 2px 8px rgba(108, 117, 125, 0.2);
}

.analyze-btn.disabled::before {
  display: none;
}

.analyzing-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid transparent;
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.analyze-icon {
  font-size: 1.2rem;
}

.validation-errors {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 8px;
}

.error-message {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
  color: #721c24;
  font-size: 0.9rem;
}

.error-message:last-child {
  margin-bottom: 0;
}

.error-icon {
  margin-right: 0.5rem;
  font-size: 1rem;
}

.validation-summary {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  text-align: center;
}

.validation-summary p {
  margin: 0;
  color: #856404;
  font-weight: 600;
}

/* Prevent accidental PDF preview overlays */
embed, object, iframe {
  display: none !important;
}

 /* Responsive design */
   @media (max-width: 768px) {
    .input-methods-single {
      flex-direction: column;
      gap: 0.75rem;
      width: 100%;
    }
   
   .input-method-card {
     min-width: auto;
     max-width: none;
     padding: 1rem;
     width: 100%;
   }
  
  .method-icon {
    font-size: 1.5rem;
  }
  
  .method-content h4 {
    font-size: 1rem;
  }
  
  .method-content p {
    font-size: 0.8rem;
  }
  
           .input-area-single {
      padding: 1.5rem;
      margin-bottom: 1.5rem;
      width: 100%;
    }
   
   .analyze-section {
     padding: 1.5rem;
     margin: 1rem 0 1.5rem 0;
     width: 100%;
   }
  
  .analyze-btn {
    padding: 1rem 2rem;
    font-size: 1.1rem;
  }
  
  .file-drop-zone {
    padding: 2rem 1rem;
  }
  
  .upload-icon {
    font-size: 3rem;
  }
  
  .input-wrapper {
    flex-direction: column;
    align-items: stretch;
  }
  
  .input-icon {
    padding: 0.75rem;
    text-align: center;
    border-bottom: 1px solid #e9ecef;
  }
  
  .input-status {
    padding: 0.75rem;
    text-align: center;
    border-top: 1px solid #e9ecef;
  }
}

@media (max-width: 480px) {
  .unified-input {
    max-width: 100%;
    padding: 0 1rem;
    width: 100%;
  }
  
  .input-method-card {
    padding: 0.875rem;
    width: 100%;
  }
  
  .method-icon {
    font-size: 1.25rem;
  }
  
           .input-area-single {
      padding: 1rem;
      width: 100%;
    }
  
  .text-input-field,
  .url-input-field,
  .quick-citation-input {
    padding: 0.75rem;
    font-size: 0.9rem;
  }
  
  .analyze-btn {
    padding: 0.875rem 1.5rem;
    font-size: 1rem;
  }
  
  .input-footer {
    flex-direction: column;
    gap: 0.5rem;
    align-items: flex-start;
  }
}
</style> 