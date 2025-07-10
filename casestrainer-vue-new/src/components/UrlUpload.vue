<template>
  <div class="modern-url-upload">
    <div class="upload-card">
      <div class="upload-header">
        <div class="header-icon">
          <i class="bi bi-link-45deg"></i>
        </div>
        <h3 class="header-title">Analyze Web Content</h3>
        <p class="header-subtitle">Enter a URL to fetch and analyze legal documents from the web</p>
      </div>
      
      <div class="upload-body">
        <!-- URL Input Section -->
        <div class="url-input-section">
          <label for="urlInput" class="form-label">
            <i class="bi bi-globe me-2"></i>
            Website URL
          </label>
          
          <div class="url-input-container">
            <div class="input-wrapper">
              <div class="input-icon">
                <i class="bi bi-link-45deg"></i>
              </div>
              <input
                type="url"
                id="urlInput"
                class="url-input"
                v-model="url"
                placeholder="https://example.com/legal-document"
                :disabled="isAnalyzing"
                @keyup.enter="emitAnalyze"
                @input="validateUrl"
                :class="{
                  'valid': isValidUrl && url.length > 0,
                  'invalid': !isValidUrl && url.length > 0,
                  'analyzing': isAnalyzing
                }"
              />
              <div v-if="isValidUrl && url.length > 0" class="input-status valid">
                <i class="bi bi-check-circle-fill"></i>
              </div>
              <div v-else-if="!isValidUrl && url.length > 0" class="input-status invalid">
                <i class="bi bi-x-circle-fill"></i>
              </div>
            </div>
          </div>
          
          <!-- URL Validation Messages -->
          <div class="validation-messages">
            <div v-if="validationMessage" :class="['validation-message', validationMessageType]">
              <i :class="validationMessageIcon"></i>
              {{ validationMessage }}
            </div>
            <div v-else class="form-help">
              <i class="bi bi-info-circle me-1"></i>
              Supported: PDF, HTML pages, legal databases, court websites
            </div>
          </div>
        </div>
        
        <!-- URL Preview Section -->
        <div v-if="urlPreview" class="url-preview-section">
          <h6 class="preview-title">
            <i class="bi bi-eye me-2"></i>
            URL Preview
          </h6>
          <div class="url-preview">
            <div class="preview-icon">
              <i :class="getUrlIcon(urlPreview.protocol)"></i>
            </div>
            <div class="preview-details">
              <div class="preview-domain">{{ urlPreview.hostname }}</div>
              <div class="preview-path">{{ urlPreview.pathname }}</div>
              <div class="preview-protocol">{{ urlPreview.protocol.replace(':', '') }}</div>
            </div>
            <div class="preview-security">
              <span :class="['security-badge', urlPreview.protocol === 'https:' ? 'secure' : 'insecure']">
                <i :class="urlPreview.protocol === 'https:' ? 'bi bi-shield-fill-check' : 'bi bi-shield-fill-exclamation'"></i>
                {{ urlPreview.protocol === 'https:' ? 'Secure' : 'Not Secure' }}
              </span>
            </div>
          </div>
        </div>
        
        <!-- Quick URL Examples -->
        <div class="url-examples-section">
          <h6 class="examples-title">
            <i class="bi bi-lightbulb me-2"></i>
            Quick Examples
          </h6>
          <div class="url-examples">
            <button 
              v-for="example in urlExamples" 
              :key="example.url"
              @click="setExampleUrl(example.url)"
              class="example-btn"
              :disabled="isAnalyzing"
            >
              <i :class="example.icon"></i>
              <span>{{ example.label }}</span>
            </button>
          </div>
        </div>
        
        <!-- Analysis Options -->
        <div v-if="isValidUrl && url.length > 0" class="analysis-options-section">
          <h6 class="options-title">
            <i class="bi bi-gear me-2"></i>
            Analysis Options
          </h6>
          <div class="options-grid">
            <label class="option-item">
              <input type="checkbox" v-model="options.includeSubpages" :disabled="isAnalyzing">
              <div class="option-content">
                <div class="option-icon">
                  <i class="bi bi-collection"></i>
                </div>
                <div class="option-text">
                  <div class="option-title">Include Subpages</div>
                  <div class="option-description">Analyze linked documents</div>
                </div>
              </div>
            </label>
            
            <label class="option-item">
              <input type="checkbox" v-model="options.followRedirects" :disabled="isAnalyzing">
              <div class="option-content">
                <div class="option-icon">
                  <i class="bi bi-arrow-repeat"></i>
                </div>
                <div class="option-text">
                  <div class="option-title">Follow Redirects</div>
                  <div class="option-description">Handle URL redirections</div>
                </div>
              </div>
            </label>
            
            <label class="option-item">
              <input type="checkbox" v-model="options.deepScan" :disabled="isAnalyzing">
              <div class="option-content">
                <div class="option-icon">
                  <i class="bi bi-search"></i>
                </div>
                <div class="option-text">
                  <div class="option-title">Deep Scan</div>
                  <div class="option-description">Comprehensive citation search</div>
                </div>
              </div>
            </label>
          </div>
        </div>
        
        <!-- Analyze Button -->
        <div class="analyze-section">
          <button 
            :class="['analyze-btn', { 'disabled': !isValidUrl || isAnalyzing || url.length === 0 }]"
            @click="emitAnalyze"
            :disabled="!isValidUrl || isAnalyzing || url.length === 0"
          >
            <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2"></span>
            <i v-else class="bi bi-search me-2"></i>
            {{ getAnalyzeButtonText() }}
          </button>
          
          <div v-if="isValidUrl && url.length > 0 && !isAnalyzing" class="analyze-info">
            <div class="info-grid">
              <div class="info-item">
                <i class="bi bi-clock"></i>
                <span>~30-60 seconds</span>
              </div>
              <div class="info-item">
                <i class="bi bi-download"></i>
                <span>Fetches content</span>
              </div>
              <div class="info-item">
                <i class="bi bi-shield-check"></i>
                <span>Secure analysis</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Analysis Progress -->
        <div v-if="isAnalyzing" class="analysis-progress">
          <div class="progress-header">
            <h6 class="progress-title">
              <i class="bi bi-gear-fill spinning me-2"></i>
              Analyzing URL Content
            </h6>
            <div class="progress-url">{{ getDisplayUrl(url) }}</div>
          </div>
          
          <div class="progress-steps">
            <div class="step" :class="{ active: progressStep >= 1 }">
              <i class="bi bi-download"></i>
              <span>Fetching</span>
            </div>
            <div class="step" :class="{ active: progressStep >= 2 }">
              <i class="bi bi-file-text"></i>
              <span>Parsing</span>
            </div>
            <div class="step" :class="{ active: progressStep >= 3 }">
              <i class="bi bi-search"></i>
              <span>Analyzing</span>
            </div>
            <div class="step" :class="{ active: progressStep >= 4 }">
              <i class="bi bi-check-circle"></i>
              <span>Complete</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue';

export default {
  name: 'ModernUrlUpload',
  emits: ['analyze'],
  props: {
    isAnalyzing: {
      type: Boolean,
      default: false
    }
  },
  setup(props, { emit }) {
    const url = ref('');
    const validationMessage = ref('');
    const validationMessageType = ref('');
    const progressStep = ref(1);
    
    // Analysis options
    const options = ref({
      includeSubpages: false,
      followRedirects: true,
      deepScan: false
    });
    
    // URL examples
    const urlExamples = ref([
      {
        label: 'Court Opinion',
        url: 'https://www.courts.wa.gov/opinions/',
        icon: 'bi bi-bank'
      },
      {
        label: 'Legal Database',
        url: 'https://scholar.google.com/scholar',
        icon: 'bi bi-journal-text'
      },
      {
        label: 'PDF Document',
        url: 'https://example.com/document.pdf',
        icon: 'bi bi-file-pdf'
      }
    ]);
    
    // Computed properties
    const isValidUrl = computed(() => {
      if (!url.value) return false;
      try {
        const urlObj = new URL(url.value);
        return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
      } catch {
        return false;
      }
    });
    
    const urlPreview = computed(() => {
      if (!isValidUrl.value) return null;
      try {
        return new URL(url.value);
      } catch {
        return null;
      }
    });
    
    const validationMessageIcon = computed(() => {
      const iconMap = {
        'success': 'bi bi-check-circle-fill',
        'error': 'bi bi-x-circle-fill',
        'warning': 'bi bi-exclamation-triangle-fill',
        'info': 'bi bi-info-circle-fill'
      };
      return iconMap[validationMessageType.value] || 'bi bi-info-circle';
    });
    
    // Methods
    const validateUrl = () => {
      if (!url.value) {
        validationMessage.value = '';
        return;
      }
      
      if (url.value.length < 8) {
        validationMessage.value = 'URL is too short';
        validationMessageType.value = 'error';
        return;
      }
      
      try {
        const urlObj = new URL(url.value);
        
        if (urlObj.protocol !== 'http:' && urlObj.protocol !== 'https:') {
          validationMessage.value = 'Only HTTP and HTTPS URLs are supported';
          validationMessageType.value = 'error';
          return;
        }
        
        if (urlObj.hostname === 'localhost' || urlObj.hostname === '127.0.0.1') {
          validationMessage.value = 'Local URLs cannot be analyzed';
          validationMessageType.value = 'warning';
          return;
        }
        
        if (urlObj.protocol === 'http:') {
          validationMessage.value = 'HTTP URLs are less secure than HTTPS';
          validationMessageType.value = 'warning';
        } else {
          validationMessage.value = 'Valid HTTPS URL ready for analysis';
          validationMessageType.value = 'success';
        }
        
      } catch {
        validationMessage.value = 'Please enter a valid URL';
        validationMessageType.value = 'error';
      }
    };
    
    const getUrlIcon = (protocol) => {
      const iconMap = {
        'https:': 'bi bi-shield-fill-check text-success',
        'http:': 'bi bi-shield-fill-exclamation text-warning'
      };
      return iconMap[protocol] || 'bi bi-globe text-muted';
    };
    
    const setExampleUrl = (exampleUrl) => {
      url.value = exampleUrl;
      validateUrl();
    };
    
    const getDisplayUrl = (fullUrl) => {
      try {
        const urlObj = new URL(fullUrl);
        return urlObj.hostname + (urlObj.pathname !== '/' ? urlObj.pathname : '');
      } catch {
        return fullUrl;
      }
    };
    
    const getAnalyzeButtonText = () => {
      if (isAnalyzing.value) return 'Analyzing URL...';
      if (!url.value) return 'Enter URL to Analyze';
      if (!isValidUrl.value) return 'Invalid URL';
      return 'Analyze URL Content';
    };
    
    const emitAnalyze = () => {
      if (!isValidUrl.value || isAnalyzing.value) return;
      
      const analysisData = {
        url: url.value,
        options: options.value,
        type: 'url'
      };
      
      emit('analyze', analysisData);
    };
    
    // Simulate progress steps when analyzing
    watch(() => props.isAnalyzing, (newVal) => {
      if (newVal) {
        progressStep.value = 1;
        const interval = setInterval(() => {
          if (progressStep.value < 4 && props.isAnalyzing) {
            progressStep.value++;
          } else {
            clearInterval(interval);
          }
        }, 1500);
      }
    });
    
    // Watch URL changes
    watch(url, validateUrl);
    
    return {
      url,
      options,
      urlExamples,
      isValidUrl,
      urlPreview,
      validationMessage,
      validationMessageType,
      validationMessageIcon,
      progressStep,
      validateUrl,
      getUrlIcon,
      setExampleUrl,
      getDisplayUrl,
      getAnalyzeButtonText,
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

.modern-url-upload {
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
  background: url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Cpath d='M20 20c0-5.5-4.5-10-10-10s-10 4.5-10 10 4.5 10 10 10 10-4.5 10-10zm10 0c0-5.5-4.5-10-10-10s-10 4.5-10 10 4.5 10 10 10 10-4.5 10-10z'/%3E%3C/g%3E%3C/svg%3E") repeat;
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

.url-input-section {
  margin-bottom: 2rem;
}

.form-label {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
  font-size: 1.05rem;
  display: flex;
  align-items: center;
}

.url-input-container {
  margin-bottom: 1rem;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 1rem;
  z-index: 2;
  color: var(--text-secondary);
  font-size: 1.2rem;
}

.url-input {
  width: 100%;
  padding: 1rem 1rem 1rem 3rem;
  border: 2px solid var(--border-color);
  border-radius: 1rem;
  font-size: 1.05rem;
  transition: all 0.3s ease;
  background: white;
  color: var(--text-primary);
}

.url-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 0.2rem rgba(25, 118, 210, 0.15);
}

.url-input.valid {
  border-color: var(--success-color);
  padding-right: 3rem;
}

.url-input.invalid {
  border-color: var(--error-color);
  padding-right: 3rem;
}

.url-input.analyzing {
  background: var(--background-light);
  pointer-events: none;
}

.input-status {
  position: absolute;
  right: 1rem;
  font-size: 1.2rem;
}

.input-status.valid {
  color: var(--success-color);
}

.input-status.invalid {
  color: var(--error-color);
}

.validation-messages {
  min-height: 1.5rem;
}

.validation-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
}

.validation-message.success {
  color: var(--success-color);
}

.validation-message.error {
  color: var(--error-color);
}

.validation-message.warning {
  color: var(--warning-color);
}

.validation-message.info {
  color: var(--primary-color);
}

.form-help {
  color: var(--text-secondary);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
}

.url-preview-section {
  background: var(--background-light);
  border-radius: 1rem;
  padding: 1.5rem;
  margin-bottom: 2rem;
  border: 1px solid var(--border-color);
}

.preview-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
}

.url-preview {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: white;
  padding: 1rem;
  border-radius: 0.75rem;
  border: 1px solid var(--border-color);
}

.preview-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.preview-details {
  flex: 1;
  min-width: 0;
}

.preview-domain {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.preview-path {
  color: var(--text-secondary);
  font-size: 0.9rem;
  word-break: break-all;
  margin-bottom: 0.25rem;
}

.preview-protocol {
  font-size: 0.8rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.security-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.8rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.security-badge.secure {
  background: rgba(76, 175, 80, 0.1);
  color: var(--success-color);
}

.security-badge.insecure {
  background: rgba(255, 152, 0, 0.1);
  color: var(--warning-color);
}

.url-examples-section {
  margin-bottom: 2rem;
}

.examples-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
}

.url-examples {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.75rem;
}

.example-btn {
  padding: 0.75rem;
  border: 2px solid var(--border-color);
  border-radius: 0.75rem;
  background: white;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
}

.example-btn:hover:not(:disabled) {
  border-color: var(--primary-color);
  background: rgba(25, 118, 210, 0.05);
  transform: translateY(-2px);
}

.example-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.analysis-options-section {
  background: var(--background-light);
  border-radius: 1rem;
  padding: 1.5rem;
  margin-bottom: 2rem;
  border: 1px solid var(--border-color);
}

.options-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: white;
  border-radius: 0.75rem;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.3s ease;
}

.option-item:hover {
  border-color: var(--primary-color);
}

.option-item input[type="checkbox"] {
  width: 1.2rem;
  height: 1.2rem;
  margin: 0;
}

.option-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.option-icon {
  color: var(--primary-color);
  font-size: 1.2rem;
}

.option-text {
  flex: 1;
}

.option-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.option-description {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.analyze-section {
  margin-bottom: 2rem;
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

.analyze-info {
  background: var(--background-light);
  border-radius: 0.75rem;
  padding: 1rem;
  border: 1px solid var(--border-color);
}

.info-grid {
  display: flex;
  justify-content: space-around;
  gap: 1rem;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.info-item i {
  color: var(--primary-color);
}

.analysis-progress {
  background: var(--background-light);
  border-radius: 1rem;
  padding: 2rem;
  border: 1px solid var(--border-color);
  text-align: center;
}

.progress-header {
  margin-bottom: 2rem;
}

.progress-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--primary-color);
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-url {
  color: var(--text-secondary);
  font-size: 0.9rem;
  word-break: break-all;
}

.progress-steps {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.step {
  flex: 1;
  padding: 1rem 0.5rem;
  background: white;
  border-radius: 0.75rem;
  border: 2px solid var(--border-color);
  color: var(--text-secondary);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  font-weight: 500;
}

.step.active {
  border-color: var(--primary-color);
  background: var(--primary-color);
  color: white;
  transform: scale(1.05);
}

.step i {
  font-size: 1.2rem;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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
  
  .url-examples {
    grid-template-columns: 1fr;
  }
  
  .options-grid {
    grid-template-columns: 1fr;
  }
  
  .info-grid {
    flex-direction: column;
    text-align: center;
  }
  
  .progress-steps {
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .step {
    min-width: calc(50% - 0.25rem);
  }
}

@media (max-width: 480px) {
  .header-title {
    font-size: 1.5rem;
  }
  
  .header-subtitle {
    font-size: 1rem;
  }
  
  .url-input {
    font-size: 16px; /* Prevent zoom on mobile */
  }
  
  .step {
    min-width: calc(100% - 0.5rem);
    margin-bottom: 0.5rem;
  }
  
  .preview-details {
    font-size: 0.9rem;
  }
  
  .option-item {
    padding: 0.75rem;
  }
  
  .analyze-btn {
    padding: 1rem 1.5rem;
    font-size: 1rem;
  }
}

/* Additional animations and interactions */
.url-input-container {
  position: relative;
}

.url-input-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 1rem;
  padding: 2px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.url-input:focus + .url-input-container::before {
  opacity: 1;
}

/* Smooth transitions for all interactive elements */
* {
  transition: color 0.2s ease, background-color 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

/* Loading states */
.analyzing .url-input {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* Focus styles for accessibility */
.example-btn:focus,
.option-item:focus,
.analyze-btn:focus {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

/* Enhanced hover effects */
.url-preview:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-light);
}

.option-item:has(input:checked) {
  border-color: var(--primary-color);
  background: rgba(25, 118, 210, 0.05);
}

/* Progress animation */
.step.active {
  animation: stepActivate 0.3s ease-out;
}

@keyframes stepActivate {
  0% {
    transform: scale(1);
    opacity: 0.5;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1.05);
    opacity: 1;
  }
}
</style>