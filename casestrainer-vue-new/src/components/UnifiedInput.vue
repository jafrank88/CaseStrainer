<template>
  <div class="unified-input">
    <!-- Top Row: File Upload and URL Upload -->
    <div class="input-methods-top">
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
    </div>

    <!-- Input Area for File and URL -->
    <div class="input-area-top" v-if="inputMode === 'file' || inputMode === 'url'">
      <!-- File Input -->
      <div v-if="inputMode === 'file'" class="file-input">
        <label>Upload a document</label>
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
            type="file" 
            @change="onFileChange" 
            :disabled="isAnalyzing"
            accept=".pdf,.doc,.docx,.txt"
            style="display: none;"
          />
          <div v-if="!file" class="drop-zone-content">
            <div class="upload-icon">📁</div>
            <p>Click to browse or drag & drop</p>
            <p class="file-types">Supports: PDF, DOC, DOCX, TXT (max 50MB)</p>
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
            >
              ✕
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
        <label>Enter URL to analyze</label>
        <input 
          v-model="url" 
          type="url" 
          placeholder="https://example.com/document.pdf"
          :disabled="isAnalyzing"
          @input="handleInputChange"
          :class="{ 'error': hasErrors && isDirty.url }"
        />
        <div class="input-footer">
          <span class="url-preview" v-if="url && !hasErrors">Will analyze: {{ url }}</span>
          <span v-else-if="url && hasErrors" class="url-error">Invalid URL format</span>
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

    <!-- Bottom Row: Quick Citation and Paste Text -->
    <div class="input-methods-bottom">
      <div 
        :class="['input-method-card', { active: inputMode === 'quick', disabled: isAnalyzing }]"
        @click="!isAnalyzing && (inputMode = 'quick', onModeChange())"
      >
        <div class="method-icon">{{ methodIcons.quick }}</div>
        <div class="method-content">
          <h4>{{ modeLabels.quick }}</h4>
          <p>{{ modeDescriptions.quick }}</p>
        </div>
        <div v-if="inputMode === 'quick'" class="active-indicator">✓</div>
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

    <!-- Analyze Button -->
    <div class="analyze-section">
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

    <!-- Input Area for Quick Citation and Text -->
    <div class="input-area-bottom" v-if="inputMode === 'text' || inputMode === 'quick'">
      <!-- Text Input -->
      <div v-if="inputMode === 'text'" class="text-input">
        <label>Paste your text here</label>
        <textarea 
          v-model="text" 
          placeholder="Paste legal text, citations, or document content here..."
          :disabled="isAnalyzing"
          rows="6"
          @input="handleInputChange"
          :class="{ 'error': hasErrors && isDirty.text }"
        ></textarea>
        <div class="input-footer">
          <span class="char-count" :class="{ 'error': text.length > VALIDATION_RULES.text.maxLength }">
            {{ text.length }} / {{ VALIDATION_RULES.text.maxLength }} characters
          </span>
          <span v-if="text.length < VALIDATION_RULES.text.minLength && isDirty.text" class="min-length-hint">
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

      <!-- Quick Citation Input -->
      <div v-else-if="inputMode === 'quick'" class="quick-citation-input-area">
        <label>Enter a single citation</label>
        <input
          v-model="quickCitation"
          type="text"
          placeholder="Enter citation..."
          :disabled="isAnalyzing"
          @keyup.enter="emitAnalyze"
          class="quick-citation-input"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  isAnalyzing: { type: Boolean, default: false }
});

const emit = defineEmits(['analyze']);

const modes = ['text', 'url', 'file', 'quick'];
const modeLabels = { 
  text: 'Paste Text', 
  url: 'URL', 
  file: 'Upload File',
  quick: 'Quick Citation'
};
const modeDescriptions = {
  text: 'Paste legal text or citations directly',
  url: 'Analyze content from a web URL',
  file: 'Upload a document for analysis',
  quick: 'Enter a single citation and analyze instantly'
};
const methodIcons = {
  text: '📝',
  url: '🔗',
  file: '📁',
  quick: '🔎'
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
const quickCitation = ref('');

// Validation state
const validationErrors = ref({});
const isDirty = ref({ text: false, url: false, file: false, quick: false });
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
  } else if (inputMode.value === 'quick') {
    result = quickCitation.value.trim().length > 0;
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
    emit('analyze', { file: file.value, type: 'file' });
  } else if (inputMode.value === 'quick') {
    emit('analyze', { text: quickCitation.value.trim(), type: 'text', quick: true });
    quickCitation.value = '';
  }
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
  isDirty.value = { text: false, url: false, file: false, quick: false };
  showValidationWarning.value = false;
  validateCurrentInput();
  console.log('[onModeChange] inputMode:', inputMode.value, 'file:', file.value, 'url:', url.value, 'hasErrors:', hasErrors.value, 'currentErrors:', currentErrors.value);
}
</script>

<style scoped>
.unified-input {
  max-width: 800px;
  margin: 0 auto;
}

.input-methods-top {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.input-methods-bottom {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  flex-wrap: wrap;
}

.input-method-card {
  background: white;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
  min-width: 200px;
  max-width: 300px;
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
  font-size: 2rem;
  flex-shrink: 0;
}

.method-content {
  flex: 1;
  min-width: 0;
}

.method-content h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.method-content p {
  margin: 0;
  font-size: 0.9rem;
  color: #6c757d;
  line-height: 1.3;
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

.input-area-top {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  animation: slideDown 0.3s ease-out;
}

.input-area-bottom {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  margin-top: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  animation: slideDown 0.3s ease-out;
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

.input-area label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #495057;
}

.text-input textarea,
.url-input input {
  width: 100%;
  padding: 1rem;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.text-input textarea:focus,
.url-input input:focus {
  outline: none;
  border-color: #007bff;
}

.text-input textarea.error,
.url-input input.error {
  border-color: #dc3545;
  background-color: #fff5f5;
}

.text-input textarea {
  resize: vertical;
  min-height: 120px;
}

.input-footer {
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: #6c757d;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.char-count.error {
  color: #dc3545;
  font-weight: 600;
}

.min-length-hint {
  color: #856404;
  background: #fff3cd;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.url-error {
  color: #dc3545;
  font-weight: 600;
}

.file-drop-zone {
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.file-drop-zone:hover:not(.disabled) {
  border-color: #007bff;
  background: #f8f9ff;
}

.file-drop-zone.dragover {
  border-color: #007bff;
  background: #f8f9ff;
}

.file-drop-zone.has-file {
  border-style: solid;
  border-color: #28a745;
  background: #f8fff9;
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
}

.file-types {
  font-size: 0.8rem;
  margin-top: 0.5rem;
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
}

.analyze-btn {
  background: #007bff;
  color: white;
  border: none;
  border-radius: 12px;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.analyze-btn:hover:not(.disabled) {
  background: #0056b3;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

.analyze-btn.disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
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
  .input-methods-top,
  .input-methods-bottom {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .input-method-card {
    min-width: auto;
    max-width: none;
    padding: 1rem;
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
  
  .input-area-top,
  .input-area-bottom {
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    margin-top: 1.5rem;
  }
  
  .analyze-btn {
    padding: 0.875rem 1.5rem;
    font-size: 1rem;
  }
}

@media (max-width: 480px) {
  .unified-input {
    max-width: 100%;
    padding: 0 1rem;
  }
  
  .input-method-card {
    padding: 0.875rem;
  }
  
  .method-icon {
    font-size: 1.25rem;
  }
  
  .input-area-top,
  .input-area-bottom {
    padding: 1rem;
  }
  
  .text-input textarea,
  .url-input input {
    padding: 0.75rem;
    font-size: 0.9rem;
  }
}
</style> 