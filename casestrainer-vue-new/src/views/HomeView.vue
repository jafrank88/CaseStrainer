<template>
  <div class="home">
    <div class="background-pattern"></div>
    
    <!-- Main Content Section -->
    <div class="container">
      <div class="main-content-wrapper">
        <!-- Main Input Area -->
        <div class="main-input-area">
          <div class="hero-content">
            <div class="hero-text">
              <h1 class="hero-title">
                <i class="bi bi-shield-check me-3"></i>
                Legal Citation Verification
              </h1>
              <p class="hero-subtitle">
                Upload legal documents, paste text, or provide URLs to automatically extract and verify citations against authoritative legal databases.
              </p>
            </div>

            <!-- Experimental Use Banner -->
            <div class="experimental-banner">
              <i class="bi bi-flask me-2"></i>
              <strong>Experimental Use:</strong> This tool is for research and educational purposes. Always verify results independently.
            </div>
          </div>

          <div class="input-container">
            <!-- Input Method Selection -->
            <div class="input-methods">
              <div 
                :class="['input-method-card', { active: activeTab === 'paste' }]"
                @click="activeTab = 'paste'"
              >
                <div class="method-icon">
                  <i class="bi bi-clipboard-text"></i>
                </div>
                <div class="method-content">
                  <h4>Paste Text</h4>
                  <p>Copy and paste legal text directly</p>
                </div>
                <div v-if="activeTab === 'paste'" class="active-indicator">
                  <i class="bi bi-check"></i>
                </div>
              </div>

              <div 
                :class="['input-method-card', { active: activeTab === 'file' }]"
                @click="activeTab = 'file'"
              >
                <div class="method-icon">
                  <i class="bi bi-file-earmark-text"></i>
                </div>
                <div class="method-content">
                  <h4>Upload File</h4>
                  <p>Upload PDF, DOC, DOCX, or TXT files</p>
                </div>
                <div v-if="activeTab === 'file'" class="active-indicator">
                  <i class="bi bi-check"></i>
                </div>
              </div>

              <div 
                :class="['input-method-card', { active: activeTab === 'url' }]"
                @click="activeTab = 'url'"
              >
                <div class="method-icon">
                  <i class="bi bi-link-45deg"></i>
                </div>
                <div class="method-content">
                  <h4>URL Input</h4>
                  <p>Provide a URL to analyze online content</p>
                </div>
                <div v-if="activeTab === 'url'" class="active-indicator">
                  <i class="bi bi-check"></i>
                </div>
              </div>
            </div>

            <!-- Input Content Area -->
            <div class="input-content-area">
              <!-- Text Input Tab -->
              <div v-if="activeTab === 'paste'" class="input-tab-content">
                <div class="form-group">
                  <label class="form-label">
                    <i class="bi bi-clipboard-text me-2"></i>
                    Legal Text Content
                  </label>
                  <textarea 
                    v-model="textContent"
                    class="form-control input-field"
                    rows="8"
                    placeholder="Paste your legal text here... (minimum 10 characters)"
                    @input="validateInput"
                  ></textarea>
                  
                  <!-- Input Quality Indicators -->
                  <div v-if="textContent" class="input-quality-indicators">
                    <div class="quality-item">
                      <span class="quality-label">Words:</span>
                      <span class="quality-value">{{ wordCount }}</span>
                    </div>
                    <div class="quality-item">
                      <span class="quality-label">Est. Citations:</span>
                      <span class="quality-value">{{ estimatedCitations }}</span>
                    </div>
                    <div class="quality-item">
                      <span class="quality-label">Years:</span>
                      <span class="quality-value">{{ yearCount }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- File Input Tab -->
              <div v-if="activeTab === 'file'" class="input-tab-content">
                <div class="form-group">
                  <label class="form-label">
                    <i class="bi bi-file-earmark-text me-2"></i>
                    Document File
                  </label>
                  <div 
                    :class="['file-drop-zone', { 'drag-over': isDragOver }]"
                    @drop="onFileDrop"
                    @dragover.prevent="isDragOver = true"
                    @dragleave.prevent="isDragOver = false"
                    @click="triggerFileInput"
                  >
                    <div class="file-drop-content">
                      <i class="bi bi-cloud-upload file-drop-icon"></i>
                      <p class="file-drop-text">
                        <strong>Click to select</strong> or drag and drop your file here
                      </p>
                      <p class="file-drop-hint">
                        Supported formats: PDF, DOC, DOCX, TXT (max 50MB)
                      </p>
                    </div>
                    <input 
                      ref="fileInput"
                      type="file" 
                      class="file-input-hidden"
                      accept=".pdf,.doc,.docx,.txt"
                      @change="onFileChange"
                    />
                  </div>
                  
                  <!-- Selected File Display -->
                  <div v-if="selectedFile" class="selected-file">
                    <div class="file-info">
                      <i class="bi bi-file-earmark-text me-2"></i>
                      <span class="file-name">{{ selectedFile.name }}</span>
                      <span class="file-size">({{ formatFileSize(selectedFile.size) }})</span>
                    </div>
                    <button @click="clearFile" class="btn btn-sm btn-outline-danger">
                      <i class="bi bi-x"></i>
                    </button>
                  </div>
                  
                  <div v-if="fileError" class="text-danger mt-2">
                    <i class="bi bi-exclamation-triangle me-1"></i>
                    {{ fileError }}
                  </div>
                </div>
              </div>

              <!-- URL Input Tab -->
              <div v-if="activeTab === 'url'" class="input-tab-content">
                <div class="form-group">
                  <label class="form-label">
                    <i class="bi bi-link-45deg me-2"></i>
                    Document URL
                  </label>
                  <input 
                    v-model="urlContent"
                    type="url" 
                    class="form-control input-field"
                    placeholder="https://example.com/legal-document"
                    @input="validateInput"
                  />
                  
                  <div v-if="urlError" class="text-danger mt-2">
                    <i class="bi bi-exclamation-triangle me-1"></i>
                    {{ urlError }}
                  </div>
                  <div v-else-if="urlContent && !urlError" class="form-text mt-2">
                    <i class="bi bi-info-circle me-1"></i>
                    We'll fetch and analyze the document from the provided URL
                  </div>
                </div>
              </div>
            </div>

            <!-- Analyze Button -->
            <div class="analyze-button-container">
              <button 
                :class="['btn', 'analyze-btn', { 'disabled': !canAnalyze || isAnalyzing }]"
                :disabled="!canAnalyze || isAnalyzing" 
                @click="analyzeContent"
              >
                <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2" role="status"></span>
                <i v-else class="bi bi-search me-2"></i>
                <span>{{ isAnalyzing ? 'Analyzing...' : 'Analyze Content' }}</span>
              </button>
            </div>

            <!-- Progress Bar (shown during analysis) -->
            <div v-if="isAnalyzing" class="progress-section">
              <div class="progress-info mb-3">
                <div class="progress-stats">
                  <span class="stat">
                    <i class="bi bi-list-ol text-primary"></i>
                    {{ progressCurrent }} of {{ progressTotal }} citations
                  </span>
                  <span class="stat">
                    <i class="bi bi-clock text-primary"></i>
                    {{ formatTime(elapsedTime) }} elapsed
                  </span>
                </div>
              </div>
              
              <div class="progress-container">
                <div class="progress" style="height: 1.5rem; border-radius: 0.75rem;">
                  <div 
                    class="progress-bar progress-bar-striped progress-bar-animated" 
                    :class="progressBarClass" 
                    role="progressbar"
                    :style="{ width: progressPercent + '%' }" 
                    :aria-valuenow="progressPercent" 
                    aria-valuemin="0" 
                    aria-valuemax="100"
                  >
                    <span class="progress-text">{{ progressPercent }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Inputs Sidebar -->
        <div class="recent-inputs-sidebar-container">
          <RecentInputs @load-input="loadRecentInput" />
        </div>
      </div>
    </div>

    <!-- Features Section -->
    <div class="container">
      <div class="features-section">
        <div class="text-center mb-4">
          <h2 class="text-white mb-3">Powerful Citation Analysis Features</h2>
          <p class="text-white opacity-75">Everything you need for comprehensive legal citation verification</p>
        </div>
        
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">
              <i class="bi bi-search"></i>
            </div>
            <h4 class="feature-title">Smart Detection</h4>
            <p class="feature-description">Automatically identifies and extracts citations from complex legal documents using advanced pattern recognition.</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <i class="bi bi-shield-check"></i>
            </div>
            <h4 class="feature-title">Accuracy Verification</h4>
            <p class="feature-description">Cross-references citations against authoritative legal databases to ensure accuracy and validity.</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <i class="bi bi-lightning"></i>
            </div>
            <h4 class="feature-title">Instant Analysis</h4>
            <p class="feature-description">Get comprehensive results in seconds with detailed breakdowns of citation quality and completeness.</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <i class="bi bi-file-earmark-text"></i>
            </div>
            <h4 class="feature-title">Multiple Formats</h4>
            <p class="feature-description">Supports PDF, Word documents, plain text, and direct URL analysis for maximum flexibility.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { analyze } from '@/api/api';
import RecentInputs from '@/components/RecentInputs.vue';
import { useRecentInputs } from '@/composables/useRecentInputs';

const router = useRouter();
const activeTab = ref('paste');
const textContent = ref('');
const urlContent = ref('');
const selectedFile = ref(null);
const isAnalyzing = ref(false);
const isDragOver = ref(false);
const fileError = ref('');
const urlError = ref('');

// Progress tracking
const progressCurrent = ref(0);
const progressTotal = ref(0);
const elapsedTime = ref(0);
const progressTimer = ref(null);
const startTime = ref(null);

// Recent Inputs
const { addRecentInput } = useRecentInputs();

// Load input from URL parameters (for recent input navigation)
onMounted(() => {
  const route = useRoute();
  if (route.query.tab) {
    activeTab.value = route.query.tab;
    
    if (route.query.text) {
      textContent.value = route.query.text;
    }
    
    if (route.query.url) {
      urlContent.value = route.query.url;
    }
  }
});

// Input Quality Computed Properties
const wordCount = computed(() => {
  if (!textContent.value) return 0;
  return textContent.value.trim().split(/\s+/).length;
});

const estimatedCitations = computed(() => {
  if (!textContent.value) return 0;
  const citationPatterns = [
    /\d+\s+[Uu]\.?[Ss]\.?\s+\d+/g,
    /\d+\s+[Ff]\.?\d*\s+\d+/g,
    /\d+\s+[Ss]\.?\s+\d+/g,
    /\d+\s+[Aa]pp\.?\s+\d+/g,
    /\d+\s+[A-Z][a-z]*\.?\s*(?:2d|3d)?\s+\d+/g
  ];
  let count = 0;
  citationPatterns.forEach(pattern => {
    const matches = textContent.value.match(pattern);
    if (matches) count += matches.length;
  });
  return Math.max(count, Math.floor(wordCount.value / 100));
});

const yearCount = computed(() => {
  if (!textContent.value) return 0;
  const yearMatches = textContent.value.match(/\b(19|20)\d{2}\b/g);
  return yearMatches ? new Set(yearMatches).size : 0;
});

// Remove Quality Score label and badge
// Remove computed property and class for qualityScore and qualityScoreClass

const canAnalyze = computed(() => {
  switch (activeTab.value) {
    case 'paste':
      return textContent.value.trim().length >= 10;
    case 'file':
      return selectedFile.value !== null;
    case 'url':
      return urlContent.value.trim() !== '' && !urlError.value;
    default:
      return false;
  }
});

// Progress bar computed properties
const progressPercent = computed(() => {
  if (!progressTotal.value) return 0;
  return Math.min(100, Math.round((progressCurrent.value / progressTotal.value) * 100));
});

const progressBarClass = computed(() => {
  if (progressPercent.value >= 80) return 'bg-success';
  if (progressPercent.value >= 50) return 'bg-info';
  if (progressPercent.value >= 30) return 'bg-warning';
  return 'bg-danger';
});

// Methods
const validateInput = () => {
  fileError.value = '';
  urlError.value = '';

  if (activeTab.value === 'url' && urlContent.value.trim()) {
    try {
      new URL(urlContent.value);
    } catch {
      urlError.value = 'Please enter a valid URL';
    }
  }
};

const loadRecentInput = (input) => {
  activeTab.value = input.tab;
  switch (input.tab) {
    case 'paste':
      textContent.value = input.text || '';
      break;
    case 'url':
      urlContent.value = input.url || '';
      break;
  }
  validateInput();
};

const onFileChange = (event) => {
  const file = event.target.files[0];
  if (file) {
    handleFile(file);
  }
};

const onFileDrop = (event) => {
  event.preventDefault();
  isDragOver.value = false;
  const file = event.dataTransfer.files[0];
  if (file) {
    handleFile(file);
  }
};

const handleFile = (file) => {
  fileError.value = '';

  const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
  if (!allowedTypes.includes(file.type)) {
    fileError.value = 'Please select a valid file type (PDF, DOC, DOCX, or TXT)';
    return;
  }

  if (file.size > 50 * 1024 * 1024) {
    fileError.value = 'File size must be less than 50MB';
    return;
  }

  selectedFile.value = file;
};

const fileInput = ref(null);

const triggerFileInput = () => {
  if (!isAnalyzing.value && fileInput.value) {
    fileInput.value.click();
  }
};

const clearFile = () => {
  selectedFile.value = null;
  fileError.value = '';
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatTime = (seconds) => {
  if (!seconds || seconds < 0) return '0s';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  } else {
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }
};

const startProgressTracking = () => {
  startTime.value = Date.now();
  progressCurrent.value = 0;
  progressTotal.value = estimatedCitations.value || 10; // Use estimated citations or default to 10
  
  // Start elapsed time tracking
  progressTimer.value = setInterval(() => {
    elapsedTime.value = Math.floor((Date.now() - startTime.value) / 1000);
  }, 1000);
  
  // Simulate progress for better UX
  const progressInterval = setInterval(() => {
    if (progressCurrent.value < progressTotal.value && isAnalyzing.value) {
      progressCurrent.value++;
    } else {
      clearInterval(progressInterval);
    }
  }, 2000); // Update every 2 seconds
};

const stopProgressTracking = () => {
  if (progressTimer.value) {
    clearInterval(progressTimer.value);
    progressTimer.value = null;
  }
  startTime.value = null;
  elapsedTime.value = 0;
  progressCurrent.value = 0;
  progressTotal.value = 0;
};

const analyzeContent = async () => {
  if (!canAnalyze.value || isAnalyzing.value) return;

  isAnalyzing.value = true;
  startProgressTracking();

  try {
    const inputData = {
      tab: activeTab.value,
      text: textContent.value,
      url: urlContent.value,
      fileName: selectedFile.value ? selectedFile.value.name : null,
      timestamp: new Date().toISOString()
    };
    
    if (activeTab.value !== 'file') {
      addRecentInput(inputData);
      localStorage.setItem('lastCitationInput', JSON.stringify(inputData));
    } else {
      addRecentInput(inputData);
    }

    let response;
    
    if (activeTab.value === 'url' && urlContent.value.trim()) {
      router.push({ 
        path: '/enhanced-validator', 
        query: { 
          tab: activeTab.value,
          url: urlContent.value.trim()
        }
      });
      return;
    }
    
    switch (activeTab.value) {
      case 'paste':
        if (textContent.value.trim()) {
          response = await analyze({
            text: textContent.value.trim(),
            type: 'text'
          });
        }
        break;
        
      case 'file':
        if (selectedFile.value) {
          const formData = new FormData();
          formData.append('file', selectedFile.value);
          formData.append('type', 'file');
          response = await analyze(formData);
        }
        break;
    }

    if (response && response.task_id) {
      router.push({
        name: 'EnhancedValidator',
        query: { task_id: response.task_id }
      });
      return;
    }

    if (response) {
      router.push({ 
        path: '/enhanced-validator', 
        query: { 
          tab: activeTab.value,
          ...(activeTab.value === 'paste' && textContent.value.trim() ? { text: textContent.value.trim() } : {})
        },
        state: { 
          results: response 
        }
      });
    }
  } catch (error) {
    console.error('Analysis error:', error);
    
    let errorMessage = 'An error occurred during analysis. Please try again.';
    
    if (error.response) {
      switch (error.response.status) {
        case 400:
          errorMessage = error.response.data?.message || 'Invalid input. Please check your data and try again.';
          break;
        case 413:
          errorMessage = 'File too large. Please use a smaller file.';
          break;
        case 429:
          errorMessage = 'Too many requests. Please wait a moment and try again.';
          break;
        case 500:
          errorMessage = 'Server error. Please try again later.';
          break;
        default:
          errorMessage = error.response.data?.message || `Server error (${error.response.status}). Please try again.`;
      }
    } else if (error.code === 'ECONNABORTED') {
      errorMessage = 'Request timed out. Please try again.';
    } else if (error.code === 'NETWORK_ERROR') {
      errorMessage = 'Network error. Please check your connection and try again.';
    }
    
    alert(errorMessage);
  } finally {
    isAnalyzing.value = false;
    stopProgressTracking();
  }
};
</script>

<style scoped>
:root {
  --primary-color: #4b2e83;
  --primary-light: #6a4c93;
  --primary-dark: #3a1f5e;
  --secondary-color: #f8f9fa;
  --accent-color: #ff6b35;
  --success-color: #4caf50;
  --warning-color: #ff9800;
  --error-color: #f44336;
  --text-primary: #212529;
  --text-secondary: #6c757d;
  --border-color: #e9ecef;
  --shadow-light: 0 2px 12px 0 rgba(60, 72, 88, 0.08);
  --shadow-medium: 0 4px 24px 0 rgba(60, 72, 88, 0.12);
}

/* Main Layout */
.main-content-wrapper {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 0;
}

.main-input-area {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: var(--shadow-medium);
  border: 1px solid rgba(75, 46, 131, 0.1);
}

.recent-inputs-sidebar-container {
  align-self: start;
  position: sticky;
  top: 2rem;
}

/* Hero Content */
.hero-content {
  text-align: center;
  margin-bottom: 2rem;
}

.hero-text {
  margin-bottom: 1.5rem;
}

.hero-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--primary-color);
  margin-bottom: 1rem;
  line-height: 1.2;
}

.hero-subtitle {
  font-size: 1.1rem;
  color: var(--text-secondary);
  line-height: 1.6;
  max-width: 600px;
  margin: 0 auto;
}

.experimental-banner {
  background: linear-gradient(135deg, #fff3cd, #ffeaa7);
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: #856404;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

/* Input Container */
.input-container {
  max-width: 800px;
  margin: 0 auto;
}

/* Input Methods */
.input-methods {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
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
}

.input-method-card:hover:not(.disabled) {
  border-color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(75, 46, 131, 0.15);
}

.input-method-card.active {
  border-color: var(--primary-color);
  background: #f8f9ff;
}

.input-method-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.method-icon {
  font-size: 2rem;
  color: var(--primary-color);
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
  color: var(--text-primary);
}

.method-content p {
  margin: 0;
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.3;
}

.active-indicator {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: var(--primary-color);
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
}

/* Input Content Area */
.input-content-area {
  margin-bottom: 2rem;
}

.input-tab-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  font-size: 1rem;
}

.input-field {
  border: 2px solid #e9ecef;
  border-radius: 8px;
  padding: 0.75rem;
  font-size: 1rem;
  transition: all 0.2s ease;
  background: white;
}

.input-field:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(75, 46, 131, 0.1);
  outline: none;
}

/* File Drop Zone */
.file-drop-zone {
  border: 3px dashed #e9ecef;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  background: white;
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
}

.file-drop-zone:hover {
  border-color: var(--primary-color);
  background: rgba(75, 46, 131, 0.02);
}

.file-drop-zone.drag-over {
  border-color: var(--primary-color);
  background: rgba(75, 46, 131, 0.05);
  transform: scale(1.02);
}

.file-drop-content {
  pointer-events: none;
}

.file-drop-icon {
  font-size: 3rem;
  color: var(--primary-color);
  margin-bottom: 1rem;
  display: block;
}

.file-drop-text {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.file-drop-hint {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0;
}

.file-input-hidden {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

/* Selected File */
.selected-file {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.file-name {
  font-weight: 600;
  color: var(--text-primary);
}

.file-size {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

/* Input Quality Indicators */
.input-quality-indicators {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.quality-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.quality-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.quality-value {
  font-weight: 600;
  color: var(--text-primary);
}

/* Analyze Button */
.analyze-button-container {
  text-align: center;
  margin-top: 2rem;
}

/* Progress Bar Styles */
.progress-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #e9ecef;
}

.progress-info {
  margin-bottom: 1.5rem;
}

.progress-stats {
  display: flex;
  justify-content: space-around;
  gap: 1rem;
  flex-wrap: wrap;
}

.stat {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
}

.progress-container {
  margin: 1.5rem 0;
}

.progress {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid rgba(0, 123, 255, 0.2);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
}

.progress-bar {
  background: linear-gradient(90deg, #007bff, #0056b3);
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.3);
  position: relative;
  overflow: hidden;
}

.progress-text {
  font-weight: 600;
  font-size: 0.9rem;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.analyze-btn {
  background: linear-gradient(90deg, #4b2e83 60%, #6a4c93 100%);
  border: none;
  color: white;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 12px;
  transition: all 0.3s ease;
  min-width: 200px;
  box-shadow: 0 4px 12px rgba(75, 46, 131, 0.3);
}

.analyze-btn:hover:not(.disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(75, 46, 131, 0.4);
}

.analyze-btn:active {
  transform: translateY(0);
}

.analyze-btn.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Features Section */
.features-section {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2rem;
  padding: 3rem;
  margin: 3rem auto;
  max-width: 1200px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

.feature-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 1.5rem;
  padding: 2rem;
  text-align: center;
  box-shadow: var(--shadow-light);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-medium);
}

.feature-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem auto;
  color: white;
  font-size: 2rem;
}

.feature-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.feature-description {
  color: var(--text-secondary);
  line-height: 1.6;
}

.quality-indicator {
  background: white;
  border-radius: 1.5rem;
  padding: 1.5rem;
  margin-bottom: 2rem;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-light);
}

.quality-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.quality-bar {
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.quality-fill {
  height: 100%;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 4px;
}

.quality-stats {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.2rem;
  flex-wrap: wrap;
  justify-content: center;
}

.stat-item {
  background: #f7f5fa;
  border-radius: 0.65rem;
  box-shadow: 0 1.5px 6px rgba(75, 46, 131, 0.06);
  border: 1.2px solid #e3e0f3;
  min-width: 90px;
  min-height: 54px;
  padding: 0.5rem 0.3rem 0.3rem 0.3rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.stat-value {
  font-size: 1.15rem;
  font-weight: 700;
  color: #4b2e83;
  margin-bottom: 0.05rem;
}

.stat-label {
  font-size: 0.78rem;
  color: #6c757d;
  margin-top: 0.05rem;
}

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .main-content-wrapper {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .recent-inputs-sidebar-container {
    position: static;
    order: -1;
  }
}

@media (max-width: 768px) {
  .main-input-area {
    padding: 1.5rem;
  }
  
  .hero-title {
    font-size: 2rem;
  }
  
  .hero-subtitle {
    font-size: 1rem;
  }
  
  .input-methods {
    grid-template-columns: 1fr;
  }
  
  .input-method-card {
    padding: 1rem;
  }
  
  .method-icon {
    font-size: 1.5rem;
  }
  
  .input-quality-indicators {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .quality-item {
    justify-content: space-between;
  }
}

@media (max-width: 480px) {
  .main-input-area {
    padding: 1rem;
  }
  
  .hero-title {
    font-size: 1.8rem;
  }
  
  .file-drop-zone {
    padding: 1.5rem;
  }
  
  .file-drop-icon {
    font-size: 2rem;
  }
}
</style>
