<template>
  <div class="home">
    <!-- Main Content -->
      <div class="container">
      <div class="modern-card shadow-sm mt-5">
        <div class="card-body p-5">
          <!-- Title -->
          <h2 class="mb-5 text-center modern-title">Citation Verifier</h2>
          <!-- HMR TEST: This comment should trigger hot reload -->

          <!-- Tab Navigation -->
          <div class="mb-5">
            <div class="btn-group w-100 modern-tab-group" role="group">
              <button 
                type="button" 
                class="btn modern-tab-btn"
                :class="activeTab === 'paste' ? 'active' : ''"
                @click="activeTab = 'paste'"
                :disabled="isAnalyzing"
              >
                <i class="bi bi-clipboard-text me-2"></i>
                Paste Text
              </button>
              <button 
                type="button" 
                class="btn modern-tab-btn"
                :class="activeTab === 'file' ? 'active' : ''"
                @click="activeTab = 'file'"
                :disabled="isAnalyzing"
              >
                <i class="bi bi-upload me-2"></i>
                File Upload
              </button>
            <button 
                type="button" 
                class="btn modern-tab-btn"
                :class="activeTab === 'url' ? 'active' : ''"
                @click="activeTab = 'url'"
                :disabled="isAnalyzing"
              >
                <i class="bi bi-link-45deg me-2"></i>
                URL Upload
            </button>
            </div>
          </div>

          <!-- Tab Content -->
          <div class="modern-tab-content">
            <!-- Paste Text Tab -->
            <div v-if="activeTab === 'paste'" class="my-tab-pane">
              <div class="form-group mb-4">
                <label for="textInput" class="form-label">Paste your text here</label>
                <textarea 
                  id="textInput"
                  v-model="textContent"
                  class="form-control modern-input"
                  rows="8"
                  placeholder="Paste legal text, citations, or document content here..."
                  :disabled="isAnalyzing"
                  @input="validateInput"
                ></textarea>
              </div>
            </div>

            <!-- File Upload Tab -->
            <div v-if="activeTab === 'file'" class="my-tab-pane">
              <div class="form-group mb-4">
                <label class="form-label">Upload a document</label>
                <div 
                  :class="['file-drop-zone modern-drop-zone', { 
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
                    id="fileInput"
                    type="file" 
                    @change="onFileChange" 
                    :disabled="isAnalyzing"
                    accept=".pdf,.doc,.docx,.txt"
                    style="display: none;"
                  />
                  <div v-if="!selectedFile" class="drop-zone-content">
                    <i class="bi bi-cloud-upload fs-1 text-muted mb-3"></i>
                    <p class="mb-2">Click to browse or drag & drop</p>
                    <p class="text-muted small">Supports: PDF, DOC, DOCX, TXT (max 50MB)</p>
                  </div>
                  <div v-else class="file-info">
                    <i class="bi bi-file-earmark-text fs-3 text-primary me-3"></i>
                    <div class="file-details">
                      <strong>{{ selectedFile.name }}</strong>
                      <span class="text-muted">{{ formatFileSize(selectedFile.size) }}</span>
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

            <!-- URL Upload Tab -->
            <div v-if="activeTab === 'url'" class="my-tab-pane">
              <div class="form-group mb-4">
                <label for="urlInput" class="form-label">Enter URL to analyze</label>
                <input 
                  id="urlInput"
                  v-model="urlContent"
                  type="url" 
                  class="form-control modern-input"
                  placeholder="https://example.com/document.pdf"
                  :disabled="isAnalyzing"
                  @input="validateInput"
                  :class="{ 'is-invalid': urlError }"
                />
                <div v-if="urlError" class="invalid-feedback">
                  {{ urlError }}
                </div>
                <div v-else-if="urlContent && !urlError" class="form-text mt-1">
                  Will analyze: {{ urlContent }}
                </div>
              </div>
            </div>
          </div>
          
          <!-- Recent Inputs Section -->
          <RecentInputs @load-input="loadRecentInput" />
          
          <!-- Analyze Button -->
          <div class="mt-5">
            <button 
              :class="['btn', 'btn-primary', 'btn-lg', 'w-100', { 'disabled': !canAnalyze || isAnalyzing }]"
              :disabled="!canAnalyze || isAnalyzing" 
              @click="analyzeContent"
            >
              <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2" role="status"></span>
              <i v-else class="bi bi-search me-2"></i>
              {{ isAnalyzing ? 'Analyzing...' : 'Analyze Content' }}
            </button>
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
  // Simple heuristic: look for patterns like "v.", "U.S.", "F.", "S.", etc.
  const citationPatterns = [
    /\d+\s+[Uu]\.?[Ss]\.?\s+\d+/g,
    /\d+\s+[Ff]\.?\d*\s+\d+/g,
    /\d+\s+[Ss]\.?\s+\d+/g,
    /\d+\s+[Aa]pp\.?\s+\d+/g
  ];
  let count = 0;
  citationPatterns.forEach(pattern => {
    const matches = textContent.value.match(pattern);
    if (matches) count += matches.length;
  });
  return Math.max(count, Math.floor(wordCount.value / 100)); // Fallback estimate
});

const yearCount = computed(() => {
  if (!textContent.value) return 0;
  const yearMatches = textContent.value.match(/\b(19|20)\d{2}\b/g);
  return yearMatches ? new Set(yearMatches).size : 0;
});

const qualityScore = computed(() => {
  if (!textContent.value) return 0;
  
  let score = 0;
  
  // Length score (0-30 points)
  const lengthScore = Math.min(30, (textContent.value.length / 1000) * 10);
  score += lengthScore;
  
  // Word count score (0-25 points)
  const wordScore = Math.min(25, (wordCount.value / 50) * 5);
  score += wordScore;
  
  // Citation density score (0-25 points)
  const citationDensity = estimatedCitations.value / Math.max(1, wordCount.value / 100);
  const citationScore = Math.min(25, citationDensity * 10);
  score += citationScore;
  
  // Year diversity score (0-20 points)
  const yearScore = Math.min(20, yearCount.value * 4);
  score += yearScore;
  
  return Math.round(score);
});

const qualityScoreClass = computed(() => {
  if (qualityScore.value >= 80) return 'excellent';
  if (qualityScore.value >= 60) return 'good';
  if (qualityScore.value >= 40) return 'fair';
  return 'poor';
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
  // Reset errors
  fileError.value = '';
  urlError.value = '';

  // Validate URL
  if (activeTab.value === 'url' && urlContent.value.trim()) {
    try {
      new URL(urlContent.value);
    } catch {
      urlError.value = 'Please enter a valid URL';
    }
  }

  // Validate text length
  if (activeTab.value === 'paste' && textContent.value.length > 50000) {
    // Text is too long, but we'll show the character count in red
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
    case 'file':
      // For files, we can't restore the actual file, but we can show the filename
      // and prompt user to re-upload if needed
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
  // Reset error
  fileError.value = '';

  // Validate file type
  const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
  if (!allowedTypes.includes(file.type)) {
    fileError.value = 'Please select a valid file type (PDF, DOC, DOCX, or TXT)';
    return;
  }

  // Validate file size (50MB)
  if (file.size > 50 * 1024 * 1024) {
    fileError.value = 'File size must be less than 50MB';
    return;
  }

  selectedFile.value = file;
};

const triggerFileInput = () => {
  if (!isAnalyzing.value) {
    // Use Vue ref instead of getElementById
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
    // Prepare input data for persistence
    const inputData = {
      tab: activeTab.value,
      text: textContent.value,
      url: urlContent.value,
      fileName: selectedFile.value ? selectedFile.value.name : null,
      timestamp: new Date().toISOString()
    };
    
    // Save to recent inputs (but don't save file uploads to localStorage since they can't be restored)
    if (activeTab.value !== 'file') {
      addRecentInput(inputData);
      
      // Save to localStorage for results page (only for text and URL inputs)
      localStorage.setItem('lastCitationInput', JSON.stringify(inputData));
    } else {
      // For file uploads, only save to recent inputs but not to localStorage
      addRecentInput(inputData);
    }

    let response;
    
    // Send to backend based on input type
    switch (activeTab.value) {
      case 'paste':
        if (textContent.value.trim()) {
          response = await analyze({
            text: textContent.value.trim(),
            type: 'text'
          });
        }
        break;
        
      case 'url':
        if (urlContent.value.trim()) {
          response = await analyze({
            url: urlContent.value.trim(),
            type: 'url'
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

    if (response) {
      // The analyze function handles both sync and async responses
      // If it's an async response, it will have already polled for results
      // So we can always navigate to the results page with the results
      router.push({ 
        path: '/enhanced-validator', 
        query: { 
          tab: activeTab.value,
          ...(activeTab.value === 'paste' && textContent.value.trim() ? { text: textContent.value.trim() } : {}),
          ...(activeTab.value === 'url' && urlContent.value.trim() ? { url: urlContent.value.trim() } : {})
        },
        state: { 
          results: response 
        }
      });
    }
  } catch (error) {
    console.error('Analysis error:', error);
    
    // Handle specific error types
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
    
    // Show error to user (you might want to add a toast notification system)
    alert(errorMessage);
  } finally {
    isAnalyzing.value = false;
  }
};
</script>

<style scoped>
.modern-card {
  max-width: 650px;
  margin: 0 auto;
  border-radius: 2rem;
  box-shadow: 0 4px 32px 0 rgba(60, 72, 88, 0.08);
  border: 1px solid #e9ecef;
  background: #fff;
}

.card-body {
  border-radius: 2rem;
  padding-left: 2.5rem !important;
  padding-right: 2.5rem !important;
}

.modern-title {
  font-size: 2.2rem;
  font-weight: 700;
  color: #1976d2;
  letter-spacing: 0.01em;
}

.modern-tab-group {
  border-radius: 2rem;
  overflow: hidden;
  gap: 0.5rem;
}

.modern-tab-btn {
  border-radius: 2rem !important;
  margin: 0 0.25rem;
  font-weight: 500;
  font-size: 1.08rem;
  padding: 0.75rem 1.5rem;
  background: #f8f9fa;
  color: #1976d2;
  border: 1px solid #e3e6ea;
  transition: background 0.2s, color 0.2s;
}
.modern-tab-btn.active,
.modern-tab-btn:active {
  background: #1976d2 !important;
  color: #fff !important;
  border-color: #1976d2 !important;
}
.modern-tab-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.modern-tab-content {
  background: #f7fafd;
  border-radius: 1.25rem;
  padding: 2.5rem 2rem 2rem 2rem;
  margin-bottom: 2rem;
  min-height: 220px;
  box-shadow: 0 2px 12px 0 rgba(60, 72, 88, 0.04);
}

.my-tab-pane {
  min-height: 120px;
}

.modern-input {
  border-radius: 1rem;
  padding: 0.75rem 1.25rem;
  font-size: 1.08rem;
}

.modern-drop-zone {
  border-radius: 1.25rem;
  padding: 2.5rem 1.5rem;
  background: #f8f9fa;
  border: 2px dashed #dee2e6;
  transition: all 0.2s;
}
.modern-drop-zone.has-file {
  border-color: #198754;
  background: #f0f9f0;
}
.modern-drop-zone.dragover {
  border-color: #1976d2;
  background: #e3f2fd;
}
.modern-drop-zone.error {
  border-color: #dc3545;
  background: #fef2f2;
}

.file-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.file-details {
  flex: 1;
  margin-left: 1rem;
}

.file-details strong {
  display: block;
  margin-bottom: 0.25rem;
}

@media (max-width: 768px) {
  .modern-card {
    padding: 0.5rem;
  }
  .card-body {
    padding-left: 0.5rem !important;
    padding-right: 0.5rem !important;
  }
  .modern-tab-content {
    padding: 1.25rem 0.5rem 1rem 0.5rem;
  }
}

.input-quality-indicator {
  background: #f8f9fa;
  border-radius: 1rem;
  padding: 1rem;
  border: 1px solid #e9ecef;
}

.quality-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.quality-label {
  font-weight: 500;
  color: #6c757d;
}

.quality-score {
  font-weight: 600;
  font-size: 1.1rem;
}

.quality-score.excellent { color: #198754; }
.quality-score.good { color: #0d6efd; }
.quality-score.fair { color: #ffc107; }
.quality-score.poor { color: #dc3545; }

.quality-bar {
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.quality-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.quality-fill.excellent { background: #198754; }
.quality-fill.good { background: #0d6efd; }
.quality-fill.fair { background: #ffc107; }
.quality-fill.poor { background: #dc3545; }

.quality-details {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.quality-item {
  font-size: 0.9rem;
  color: #6c757d;
  display: flex;
  align-items: center;
}

.recent-inputs {
  max-height: 300px;
  overflow-y: auto;
}

.recent-input-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  border: 1px solid #e9ecef;
  border-radius: 0.75rem;
  margin-bottom: 0.5rem;
  background: #f8f9fa;
  cursor: pointer;
  transition: all 0.2s;
}

.recent-input-item:hover {
  background: #e9ecef;
  border-color: #dee2e6;
}

.recent-input-content {
  flex: 1;
  min-width: 0;
}

.recent-input-title {
  font-weight: 500;
  color: #495057;
  margin-bottom: 0.25rem;
}

.recent-input-preview {
  font-size: 0.9rem;
  color: #6c757d;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.processing-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.processing-content {
  text-align: center;
}

.progress-container {
  margin-top: 1rem;
}

.progress {
  height: 8px;
  background-color: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background-color: #1976d2;
  transition: width 0.3s ease;
}

.progress-text {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: #6c757d;
}
</style>
