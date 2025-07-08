<template>
  <div class="home">
    <div class="background-pattern"></div>
    
    <!-- Hero Section -->
    <div class="hero-section">
      <div class="container">
        <h1 class="hero-title fade-in">Citation Verifier</h1>
        <p class="hero-subtitle fade-in">Advanced legal citation analysis and verification powered by AI</p>
      </div>
    </div>

    <!-- Main Application Card -->
    <div class="container">
      <div class="main-card slide-up">
        <div class="card-header">
          <h2 class="card-title">Analyze Your Legal Documents</h2>
          <p class="card-subtitle">Upload text, files, or URLs for comprehensive citation verification</p>
        </div>
        
        <div class="card-body">
          <!-- Tab Navigation -->
          <div class="tab-navigation">
            <div class="d-flex">
              <button 
                class="tab-btn" 
                :class="{ active: activeTab === 'paste' }"
                @click="activeTab = 'paste'"
                :disabled="isAnalyzing"
              >
                <i class="bi bi-clipboard-text"></i>
                <span>Paste Text</span>
              </button>
              <button 
                class="tab-btn" 
                :class="{ active: activeTab === 'file' }"
                @click="activeTab = 'file'"
                :disabled="isAnalyzing"
              >
                <i class="bi bi-upload"></i>
                <span>Upload File</span>
              </button>
              <button 
                class="tab-btn" 
                :class="{ active: activeTab === 'url' }"
                @click="activeTab = 'url'"
                :disabled="isAnalyzing"
              >
                <i class="bi bi-link-45deg"></i>
                <span>URL Analysis</span>
              </button>
            </div>
          </div>

          <!-- Tab Content -->
          <div class="tab-content">
            <!-- Paste Text Tab -->
            <div v-if="activeTab === 'paste'" class="tab-pane active">
              <div class="mb-4">
                <label for="textInput" class="form-label">
                  <i class="bi bi-file-text me-2"></i>
                  Paste your legal text here
                </label>
                <textarea 
                  id="textInput"
                  v-model="textContent"
                  class="form-control"
                  rows="8"
                  placeholder="Paste legal text, citations, or document content here for analysis..."
                  :disabled="isAnalyzing"
                  @input="validateInput"
                ></textarea>
              </div>
              
              <!-- Quality Indicator -->
              <div v-if="textContent.trim().length >= 10" class="quality-indicator">
                <div class="quality-header">
                  <h6 class="mb-0">
                    <i class="bi bi-graph-up me-2"></i>
                    Content Analysis
                  </h6>
                  <span class="quality-score" :class="qualityScoreClass">{{ qualityScore }}%</span>
                </div>
                <div class="quality-bar">
                  <div 
                    class="quality-fill" 
                    :class="qualityScoreClass"
                    :style="{ width: qualityScore + '%' }"
                  ></div>
                </div>
                <div class="quality-stats">
                  <div class="stat-item">
                    <div class="stat-value">{{ wordCount.toLocaleString() }}</div>
                    <div class="stat-label">Words</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">{{ estimatedCitations }}</div>
                    <div class="stat-label">Citations</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">{{ yearCount }}</div>
                    <div class="stat-label">Years</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- File Upload Tab -->
            <div v-if="activeTab === 'file'" class="tab-pane">
              <div class="mb-4">
                <label class="form-label">
                  <i class="bi bi-cloud-upload me-2"></i>
                  Upload a document
                </label>
                <div 
                  :class="['drop-zone', { 
                    'has-file': selectedFile, 
                    'dragover': isDragOver,
                    'error': fileError
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
                  <div v-if="!selectedFile" class="drop-zone-content">
                    <i class="bi bi-cloud-upload drop-zone-icon"></i>
                    <h5>Drop your file here or click to browse</h5>
                    <p class="text-muted mb-0">Supports: PDF, DOC, DOCX, TXT (max 50MB)</p>
                  </div>
                  <div v-else class="file-info">
                    <i class="bi bi-file-earmark-text text-success" style="font-size: 2rem;"></i>
                    <div class="file-details">
                      <div class="file-name">{{ selectedFile.name }}</div>
                      <div class="file-size">{{ formatFileSize(selectedFile.size) }}</div>
                    </div>
                    <button 
                      v-if="!isAnalyzing"
                      @click.stop="clearFile" 
                      class="btn btn-sm btn-outline-danger"
                    >
                      <i class="bi bi-x"></i>
                    </button>
                  </div>
                </div>
                <div v-if="fileError" class="text-danger mt-2">
                  <i class="bi bi-exclamation-triangle me-1"></i>
                  {{ fileError }}
                </div>
              </div>
            </div>

            <!-- URL Tab -->
            <div v-if="activeTab === 'url'" class="tab-pane">
              <div class="mb-4">
                <label for="urlInput" class="form-label">
                  <i class="bi bi-link-45deg me-2"></i>
                  Enter URL to analyze
                </label>
                <input 
                  id="urlInput"
                  v-model="urlContent"
                  type="url" 
                  class="form-control"
                  placeholder="https://example.com/document.pdf"
                  :disabled="isAnalyzing"
                  @input="validateInput"
                  :class="{ 'is-invalid': urlError }"
                />
                <div v-if="urlError" class="invalid-feedback">
                  {{ urlError }}
                </div>
                <div v-else-if="urlContent && !urlError" class="form-text mt-2">
                  <i class="bi bi-info-circle me-1"></i>
                  We'll fetch and analyze the document from the provided URL
                </div>
              </div>
            </div>
          </div>

          <!-- Recent Inputs Section -->
          <RecentInputs @load-input="loadRecentInput" />
          
          <!-- Analyze Button -->
          <div class="d-grid">
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

const qualityScore = computed(() => {
  if (!textContent.value) return 0;
  
  let score = 0;
  score += Math.min(30, (textContent.value.length / 1000) * 10);
  score += Math.min(25, (wordCount.value / 50) * 5);
  const citationDensity = estimatedCitations.value / Math.max(1, wordCount.value / 100);
  score += Math.min(25, citationDensity * 10);
  score += Math.min(20, yearCount.value * 4);
  
  return Math.round(score);
});

const qualityScoreClass = computed(() => {
  if (qualityScore.value >= 80) return 'bg-success';
  if (qualityScore.value >= 60) return 'bg-primary';
  if (qualityScore.value >= 40) return 'bg-warning';
  return 'bg-danger';
});

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

const triggerFileInput = () => {
  if (!isAnalyzing.value) {
    const fileInputElement = document.getElementById('fileInput');
    if (fileInputElement) {
      fileInputElement.click();
    }
  }
};

const clearFile = () => {
  selectedFile.value = null;
  fileError.value = '';
  if (document.getElementById('fileInput')) {
    document.getElementById('fileInput').value = '';
  }
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const analyzeContent = async () => {
  if (!canAnalyze.value || isAnalyzing.value) return;

  isAnalyzing.value = true;

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
  }
};
</script>

<style scoped>
:root {
  --primary-color: #1976d2;
  --primary-light: #42a5f5;
  --primary-dark: #1565c0;
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
  --shadow-heavy: 0 8px 32px 0 rgba(60, 72, 88, 0.16);
}

* {
  box-sizing: border-box;
}

.home {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  margin: 0;
  overflow-x: hidden;
}

.background-pattern {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0.1;
  pointer-events: none;
  background-image: 
    radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.2) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 40% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
}

.hero-section {
  padding: 3rem 0 2rem 0;
  text-align: center;
  color: white;
  position: relative;
  z-index: 1;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  margin-bottom: 1rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  line-height: 1.2;
}

.hero-subtitle {
  font-size: 1.4rem;
  font-weight: 300;
  margin-bottom: 2rem;
  opacity: 0.9;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.main-card {
  max-width: 800px;
  margin: 0 auto 4rem auto;
  border-radius: 2rem;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  box-shadow: var(--shadow-heavy);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
  position: relative;
  z-index: 2;
}

.card-header {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  color: white;
  padding: 2rem;
  text-align: center;
  border: none;
}

.card-title {
  font-size: 2.2rem;
  font-weight: 700;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card-subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  margin-top: 0.5rem;
}

.card-body {
  padding: 3rem;
}

.tab-navigation {
  background: var(--secondary-color);
  border-radius: 1.5rem;
  padding: 0.75rem;
  margin-bottom: 2.5rem;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.06);
}

.tab-btn {
  flex: 1;
  padding: 1rem 1.5rem;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-weight: 600;
  border-radius: 1rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 1rem;
  position: relative;
}

.tab-btn.active {
  background: white;
  color: var(--primary-color);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.tab-btn:hover:not(.active) {
  background: rgba(255, 255, 255, 0.7);
  color: var(--text-primary);
}

.tab-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.tab-content {
  background: #f8fafe;
  border-radius: 1.5rem;
  padding: 2.5rem;
  margin-bottom: 2rem;
  border: 1px solid #e3f2fd;
  position: relative;
  overflow: hidden;
}

.tab-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--primary-color), var(--primary-light));
}

.form-control {
  border-radius: 1rem;
  border: 2px solid var(--border-color);
  padding: 1rem 1.25rem;
  font-size: 1.05rem;
  transition: all 0.3s ease;
  background: white;
}

.form-control:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 0.2rem rgba(25, 118, 210, 0.15);
  background: white;
}

.form-label {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
  font-size: 1.05rem;
}

.drop-zone {
  border: 3px dashed var(--border-color);
  border-radius: 1.5rem;
  padding: 3rem 2rem;
  text-align: center;
  background: white;
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
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
}

.drop-zone.has-file {
  border-color: var(--success-color);
  background: rgba(76, 175, 80, 0.05);
}

.drop-zone.error {
  border-color: var(--error-color);
  background: rgba(244, 67, 54, 0.05);
}

.drop-zone-icon {
  font-size: 3rem;
  color: var(--text-secondary);
  margin-bottom: 1rem;
  transition: all 0.3s ease;
}

.drop-zone:hover .drop-zone-icon {
  color: var(--primary-color);
  transform: translateY(-4px);
}

.file-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  background: white;
  padding: 1.5rem;
  border-radius: 1rem;
  box-shadow: var(--shadow-light);
  border: 2px solid var(--success-color);
}

.file-details {
  text-align: left;
}

.file-name {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.file-size {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.analyze-btn {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  border: none;
  border-radius: 1.5rem;
  padding: 1.25rem 2.5rem;
  font-size: 1.2rem;
  font-weight: 600;
  color: white;
  box-shadow: 0 6px 20px rgba(25, 118, 210, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
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
  transition: left 0.6s;
}

.analyze-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(25, 118, 210, 0.4);
}

.analyze-btn:hover::before {
  left: 100%;
}

.analyze-btn:disabled {
  background: var(--text-secondary);
  box-shadow: none;
  transform: none;
}

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
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.stat-item {
  text-align: center;
  padding: 0.75rem;
  background: var(--secondary-color);
  border-radius: 0.75rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary-color);
}

.stat-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-subtitle {
    font-size: 1.2rem;
  }
  
  .card-body {
    padding: 2rem;
  }
  
  .tab-content {
    padding: 2rem;
  }
  
  .features-section {
    margin: 2rem 1rem;
    padding: 2rem;
  }
  
  .main-card {
    margin: 0 1rem 2rem 1rem;
  }
}

.fade-in {
  animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slide-up {
  animation: slideUp 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
