<template>
  <div class="home">
    <div class="background-pattern"></div>
    <div class="background-pattern"></div>
    
    <!-- Main Content Section -->
    <div class="container">
      <div class="main-content-wrapper">
        <!-- Main Input Area - Hidden when results are shown -->
        <div v-if="!analysisResults && !analysisError" class="main-input-area">
          <div class="hero-content">
            <div class="hero-text">
              <h1 class="hero-title">
                <i class="bi bi-shield-check me-3"></i>
                U.S. Case Citation Verification
              </h1>
              <p class="hero-subtitle">
                Upload legal documents, paste text, or provide URLs to automatically extract and verify U.S. case citations against authoritative legal databases.
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
                  <p>Upload PDF, DOCX, TXT, RTF, MD, HTML, or XML files</p>
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
                  <div class="d-flex justify-content-between align-items-center mb-2">
                    <label class="form-label mb-0">
                      <i class="bi bi-clipboard-text me-2"></i>
                      Legal Text Content
                    </label>
                    <div v-if="textContent" class="text-muted small">
                      {{ textContent.length.toLocaleString() }} characters
                    </div>
                  </div>
                  
                  <div class="position-relative">
                    <textarea 
                      v-model="textContent"
                      class="form-control input-field"
                      :class="{ 'is-valid': textContent && textContent.trim().length >= 10, 'is-invalid': textContent && textContent.trim().length < 10 }"
                      rows="8"
                      placeholder="Paste your legal text here..."
                      @input="validateInput"
                      @keydown.enter.ctrl.exact.prevent="canAnalyze ? analyzeContent() : null"
                      spellcheck="false"
                      style="resize: vertical; min-height: 200px;"
                    ></textarea>
                    
                    <!-- Clear button (only shown when there's content) -->
                    <button 
                      v-if="textContent"
                      @click="textContent = ''; validateInput()"
                      class="btn btn-sm btn-outline-secondary position-absolute"
                      style="top: 0.5rem; right: 0.5rem; z-index: 10;"
                      title="Clear text"
                      type="button"
                    >
                      <i class="bi bi-x-lg"></i>
                    </button>
                  </div>
                  
                  <!-- Input Quality Indicators -->
                  <div v-if="textContent" class="input-quality-indicators mt-3">
                    <div class="d-flex flex-wrap gap-3">
                      <div class="quality-item">
                        <span class="quality-label"><i class="bi bi-fonts me-1"></i>Words:</span>
                        <span class="quality-value">{{ wordCount }}</span>
                      </div>
                      <div class="quality-item">
                        <span class="quality-label"><i class="bi bi-quote me-1"></i>Est. Citations:</span>
                        <span class="quality-value">{{ estimatedCitations }}</span>
                      </div>
                      <div class="quality-item">
                        <span class="quality-label"><i class="bi bi-calendar3 me-1"></i>Years:</span>
                        <span class="quality-value">{{ yearCount }}</span>
                      </div>
                    </div>
                    
                    <!-- Text validation feedback -->
                    <div v-if="textContent" class="mt-3">
                      <div v-if="textContent.trim().length < 10" class="alert alert-warning py-2 mb-0">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        Please enter at least 10 characters for meaningful analysis
                      </div>

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
                  <div class="file-upload-container">
                    <input 
                      type="file" 
                      id="fileInput"
                      ref="fileInput"
                      class="d-none"
                      accept=".pdf,.doc,.docx,.txt,.rtf"
                      @change="handleFileSelect"
                    />
                    
                    <div 
                      class="file-dropzone rounded-3 border-2 border-dashed p-5 text-center position-relative" 
                      :class="{ 
                        'border-danger': fileError, 
                        'border-success': selectedFile && !fileError,
                        'border-primary': !selectedFile && !fileError,
                        'bg-light': !dragOver,
                        'bg-light bg-opacity-75': dragOver
                      }"
                      @click="$refs.fileInput.click()"
                      @dragover.prevent="dragOver = true"
                      @dragleave="dragOver = false"
                      @drop.prevent="handleDrop"
                      style="cursor: pointer; transition: all 0.3s ease;"
                    >
                      <!-- Drag & Drop Overlay -->
                      <div 
                        v-if="dragOver"
                        class="position-absolute top-0 start-0 w-100 h-100 d-flex flex-column align-items-center justify-content-center bg-primary bg-opacity-10 rounded-3"
                        style="z-index: 5;"
                      >
                        <i class="bi bi-cloud-arrow-up fs-1 text-primary"></i>
                        <p class="mt-2 mb-0 text-primary fw-bold">Drop file to upload</p>
                      </div>
                      
                      <div class="file-dropzone-content">
                        <i class="bi bi-upload fs-1 text-muted mb-3"></i>
                        <h5 class="mb-2">Drag & drop your file here</h5>
                        <p class="text-muted mb-0">or click to browse files</p>
                        <p class="text-muted small mt-2">Supports: PDF, DOC, DOCX, TXT, RTF</p>
                        
                        <div v-if="selectedFile" class="selected-file mt-3">
                          <div class="d-flex align-items-center justify-content-center">
                            <i class="bi bi-file-earmark-text me-2"></i>
                            <span class="text-truncate" style="max-width: 200px;">{{ selectedFile.name }}</span>
                            <span class="ms-2 text-muted">({{ formatFileSize(selectedFile.size) }})</span>
                            <button 
                              type="button" 
                              class="btn-close ms-2" 
                              @click.stop="clearFile"
                              aria-label="Remove file"
                            ></button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- File validation feedback -->
                  <div v-if="fileError" class="alert alert-danger d-flex align-items-center mt-3 py-2">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    <div>{{ fileError }}</div>
                  </div>
                  
                  <div v-else-if="selectedFile" class="alert alert-success d-flex align-items-center mt-3 py-2">
                    <i class="bi bi-check-circle-fill me-2"></i>
                    <div>
                      <strong>Ready for analysis</strong>
                      <div class="small">Click "Analyze Content" to process your document</div>
                    </div>
                  </div>
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
                  <div class="input-group">
                    <span class="input-group-text"><i class="bi bi-link-45deg"></i></span>
                    <input 
                      v-model.trim="urlContent"
                      type="url" 
                      class="form-control input-field"
                      placeholder="https://example.com/legal-document"
                      @input="validateInput"
                      :class="{ 'is-invalid': urlError }"
                      autocomplete="off"
                      spellcheck="false"
                      @keyup.enter="canAnalyze ? analyzeContent() : null"
                    />
                  </div>
                  
                  <div v-if="urlError" class="invalid-feedback d-flex align-items-center mt-1">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    <span>{{ urlError }}</span>
                  </div>
                  
                  <div v-else-if="urlContent && !urlError" class="valid-feedback d-flex align-items-center mt-1">
                    <i class="bi bi-check-circle-fill text-success me-2"></i>
                    <span>Valid URL - ready to analyze</span>
                  </div>
                  
                  <div v-else class="form-text mt-2">
                    <i class="bi bi-info-circle me-1"></i>
                    Enter a valid URL to a legal document (PDF, DOCX, HTML, etc.)
                  </div>
                </div>
                
                <!-- URL Analysis Preview (optional) -->
                <div v-if="urlContent && !urlError" class="url-preview mt-3 p-3 bg-light rounded">
                  <h6 class="mb-2"><i class="bi bi-link-45deg me-2"></i>Preview:</h6>
                  <div class="d-flex align-items-center">
                    <div class="flex-grow-1 text-truncate">
                      <a :href="urlContent" target="_blank" class="text-primary text-decoration-none">
                        {{ urlContent }}
                      </a>
                    </div>
                    <button 
                      @click="urlContent = ''; urlError = ''" 
                      class="btn btn-sm btn-outline-secondary ms-2"
                      title="Clear URL"
                    >
                      <i class="bi bi-x"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Analyze Button -->
            <div class="analyze-button-container mt-4">
              <div class="d-flex flex-column align-items-center">
                <button 
                  :class="[
                    'btn', 
                    'analyze-btn', 
                    'position-relative',
                    'overflow-hidden',
                    { 
                      'btn-primary': canAnalyze && !isAnalyzing,
                      'btn-secondary': !canAnalyze,
                      'btn-success': isAnalyzing,
                      'pe-none': !canAnalyze
                    }
                  ]"
                  :disabled="!canAnalyze || isAnalyzing"
                  @click="analyzeContent"
                  :title="getAnalyzeButtonTooltip"
                  style="min-width: 200px; transition: all 0.3s ease;"
                >
                  <!-- Animated background effect -->
                  <div 
                    v-if="isAnalyzing"
                    class="position-absolute top-0 start-0 h-100 bg-white bg-opacity-25"
                    :style="{ 
                      width: '0%',
                      animation: 'progressBar 2s linear infinite',
                      'animation-play-state': isAnalyzing ? 'running' : 'paused'
                    }"
                  ></div>
                  
                  <!-- Button content -->
                  <div class="position-relative d-flex align-items-center justify-content-center">
                    <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2" role="status"></span>
                    <i v-else class="bi bi-search me-2"></i>
                    <span class="fw-medium">
                      {{ getAnalyzeButtonText }}
                    </span>
                  </div>
                </button>
                
                <!-- Status message -->
                <div 
                  v-if="!isAnalyzing"
                  class="mt-2 text-center"
                  :class="{ 
                    'text-muted': !canAnalyze, 
                    'text-success': canAnalyze 
                  }"
                  style="font-size: 0.9em;"
                >
                  <template v-if="!canAnalyze">
                    <div v-if="activeTab === 'paste' && (!textContent || textContent.trim().length < 10)" class="d-flex align-items-center justify-content-center">
                      <i class="bi bi-info-circle me-2"></i>
                      <span>Enter at least 10 characters to analyze</span>
                    </div>
                    <div v-else-if="activeTab === 'file' && !selectedFile" class="d-flex align-items-center justify-content-center">
                      <i class="bi bi-upload me-2"></i>
                      <span>Upload a document to analyze</span>
                    </div>
                    <div v-else-if="activeTab === 'url' && !urlContent" class="d-flex align-items-center justify-content-center">
                      <i class="bi bi-link-45deg me-2"></i>
                      <span>Enter a URL to analyze</span>
                    </div>
                    <div v-else-if="urlError" class="text-danger d-flex align-items-center justify-content-center">
                      <i class="bi bi-exclamation-triangle-fill me-2"></i>
                      <span>{{ urlError }}</span>
                    </div>
                    <div v-else-if="fileError" class="text-danger d-flex align-items-center justify-content-center">
                      <i class="bi bi-exclamation-triangle-fill me-2"></i>
                      <span>{{ fileError }}</span>
                    </div>
                  </template>
                  <template v-else>
                    <div class="d-flex align-items-center justify-content-center">
                      <i class="bi bi-check-circle-fill text-success me-2"></i>
                      <span>Ready to analyze</span>
                      <span class="ms-2 text-muted">
                        <template v-if="activeTab === 'paste'">(or press Ctrl+Enter)</template>
                        <template v-else-if="activeTab === 'url'">(or press Enter in URL field)</template>
                      </span>
                    </div>
                  </template>
                </div>
                
                <!-- Debug info - can be removed in production -->
                <div v-if="false" class="debug-info mt-3 p-2 bg-light rounded" style="font-size: 0.8em; color: #666; max-width: 100%; overflow-x: auto;">
                  <div><strong>Debug Info</strong></div>
                  <div class="d-flex flex-wrap gap-4">
                    <div>Active Tab: <span class="badge bg-secondary">{{ activeTab }}</span></div>
                    <div>Has Text: <span class="badge" :class="{ 'bg-success': textContent, 'bg-secondary': !textContent }">{{ !!textContent }}</span></div>
                    <div>Has File: <span class="badge" :class="{ 'bg-success': selectedFile, 'bg-secondary': !selectedFile }">{{ !!selectedFile }}</span></div>
                    <div>Has URL: <span class="badge" :class="{ 'bg-success': urlContent, 'bg-secondary': !urlContent }">{{ !!urlContent }}</span></div>
                    <div>Can Analyze: <span class="badge" :class="{ 'bg-success': canAnalyze, 'bg-secondary': !canAnalyze }">{{ canAnalyze }}</span></div>
                    <div>Is Analyzing: <span class="badge" :class="{ 'bg-info': isAnalyzing, 'bg-secondary': !isAnalyzing }">{{ isAnalyzing }}</span></div>
                  </div>
                </div>
              </div>
              
              <style>
                @keyframes progressBar {
                  0% { width: 0%; left: 0; right: auto; }
                  50% { width: 100%; left: 0; right: auto; }
                  51% { left: auto; right: 0; }
                  100% { width: 0%; left: auto; right: 0; }
                }
                
                .analyze-btn {
                  transition: all 0.3s ease, transform 0.1s ease;
                  transform-origin: center;
                }
                
                .analyze-btn:not(:disabled):hover {
                  transform: translateY(-2px);
                  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                }
                
                .analyze-btn:not(:disabled):active {
                  transform: translateY(0);
                  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                
                .analyze-btn:disabled {
                  opacity: 0.7;
                  cursor: not-allowed;
                }
              </style>
            </div>

            <!-- Enhanced Progress Bar (shown during analysis) -->
            <div v-if="isAnalyzing || globalProgress.progressState.isActive" class="progress-section">
              <!-- Status Messages -->
              <div class="progress-status mb-3">
                <div class="status-main">
                  <i class="bi bi-gear-fill text-primary me-2 rotating"></i>
                  <strong>{{ globalProgress.progressState.currentStep || 'Processing...' }}</strong>
                </div>
              </div>

              <div class="progress-info mb-3">
                <div class="progress-stats">
                  <span class="stat">
                    <i class="bi bi-clock text-primary"></i>
                    {{ globalProgress.formatTime(globalProgress.elapsedTime) }} elapsed
                  </span>
                  <span v-if="globalProgress.remainingTime > 0" class="stat">
                    <i class="bi bi-hourglass-split text-info"></i>
                    ~{{ globalProgress.formatTime(globalProgress.remainingTime) }} remaining
                  </span>
                </div>
              </div>
              
              <div class="progress-container">
                <div class="progress" style="height: 1.5rem; border-radius: 0.75rem;">
                  <div 
                    class="progress-bar progress-bar-striped progress-bar-animated" 
                    :class="globalProgress.progressBarClass" 
                    role="progressbar"
                    :style="{ width: globalProgress.progressPercent + '%' }" 
                    :aria-valuenow="globalProgress.progressPercent" 
                    aria-valuemin="0" 
                    aria-valuemax="100"
                  >
                    <span class="progress-text">{{ Math.round(globalProgress.progressPercent) }}%</span>
                  </div>
                </div>
              </div>

              <!-- Processing Phase Indicator -->
              <div class="processing-phases mt-3">
                <div class="phase-indicators">
                  <div :class="['phase-indicator', { active: globalProgress.progressState.currentStep?.includes('extract') || globalProgress.progressPercent > 0 }]">
                    <i class="bi bi-file-text"></i>
                    <span>Extract</span>
                  </div>
                  <div :class="['phase-indicator', { active: globalProgress.progressState.currentStep?.includes('analyz') || globalProgress.progressPercent > 25 }]">
                    <i class="bi bi-search"></i>
                    <span>Analyze</span>
                  </div>
                  <div :class="['phase-indicator', { active: globalProgress.progressState.currentStep?.includes('name') || globalProgress.progressPercent > 50 }]">
                    <i class="bi bi-person-badge"></i>
                    <span>Extract Names</span>
                  </div>
                  <div :class="['phase-indicator', { active: globalProgress.progressState.currentStep?.includes('verif') || globalProgress.progressPercent > 75 }]">
                    <i class="bi bi-shield-check"></i>
                    <span>Verify</span>
                  </div>
                  <div :class="['phase-indicator', { active: globalProgress.progressState.currentStep?.includes('cluster') || globalProgress.progressPercent > 90 }]">
                    <i class="bi bi-collection"></i>
                    <span>Cluster</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Inputs Sidebar - Temporarily Hidden -->
        <!-- <div class="recent-inputs-sidebar-container">
          <RecentInputs @load-input="loadRecentInput" />
        </div> -->

        <!-- Async Task Progress Section -->
        <AsyncTaskProgress
          v-if="asyncTaskProgress && !analysisResults && !analysisError"
          :task-id="asyncTaskProgress.taskId"
          :initial-status="asyncTaskProgress.status"
          :initial-message="asyncTaskProgress.message"
          @cancel="handleCancelAsyncTask"
          @complete="handleAsyncTaskComplete"
          @error="handleAsyncTaskError"
        />

        <!-- Results Section - Replaces input area when results are available -->
        <div v-if="analysisResults || analysisError" class="results-replacement-area">
          <div class="results-header">
            <h2 class="results-title">
              <i class="bi bi-shield-check me-2"></i>
              Citation Analysis Results
            </h2>
            <button 
              @click="handleNewAnalysis" 
              class="btn btn-primary new-analysis-btn"
            >
              <i class="bi bi-plus-circle me-2"></i>
              New Analysis
            </button>
          </div>
          
          <CitationResults
            :results="analysisResults"
            :error="analysisError"
            @new-analysis="handleNewAnalysis"
            @copy-results="handleCopyResults"
            @download-results="handleDownloadResults"
          />
        </div>
      </div>
    </div>

</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import api, { analyze } from '@/api/api';
import { globalProgress } from '@/stores/progressStore';
import CitationResults from '@/components/CitationResults.vue';
import AsyncTaskProgress from '@/components/AsyncTaskProgress.vue';
import pollingService from '@/services/pollingService';
// import RecentInputs from '@/components/RecentInputs.vue'; // Temporarily hidden
// import { useRecentInputs } from '@/composables/useRecentInputs'; // Temporarily hidden

const router = useRouter();
const route = useRoute();
const activeTab = ref('paste');
const textContent = ref('');
const urlContent = ref('');
const selectedFile = ref(null);
const fileError = ref('');
const urlError = ref('');
const isAnalyzing = ref(false);
const isDragOver = ref(false);
const dragOver = ref(false);
const analysisResults = ref(null);
const analysisError = ref('');

// Async task state
const activeAsyncTask = ref(null);
const asyncTaskProgress = ref(null);

// Progress tracking state is now handled by the global store

// Watch for tab changes to clear results
watch(activeTab, () => {
  // Clear previous results when switching tabs
  analysisResults.value = null;
  analysisError.value = '';
  
  // Stop any active async task polling when switching tabs
  if (activeAsyncTask.value) {
    pollingService.stopPolling(activeAsyncTask.value);
    activeAsyncTask.value = null;
    asyncTaskProgress.value = null;
    isAnalyzing.value = false;
  }
  
  console.log('Tab changed - results cleared and async tasks stopped');
});

// Initialize with URL parameters if present
onMounted(() => {
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

// Cleanup on component unmount
onUnmounted(() => {
  // Stop all active polling
  if (activeAsyncTask.value) {
    pollingService.stopPolling(activeAsyncTask.value);
  }
  pollingService.stopAllPolling();
  console.log('HomeView unmounted - all polling stopped');
});

// Input Quality Computed Properties
const isFormValid = computed(() => {
  if (!textContent.value) return 0;
  return textContent.value.trim().split(/\s+/).length;
});

const wordCount = computed(() => {
  if (!textContent.value) return 0;
  return textContent.value.trim().split(/\s+/).length;
});

// Analyze button text based on state
const getAnalyzeButtonText = computed(() => {
  if (isAnalyzing.value) return 'Analyzing...';
  return 'Analyze Content';
});

// Analyze button tooltip text
const getAnalyzeButtonTooltip = computed(() => {
  if (isAnalyzing.value) return 'Analysis in progress...';
  
  if (!canAnalyze.value) {
    if (activeTab.value === 'paste' && !textContent.value) {
      return 'Enter text to analyze';
    } else if (activeTab.value === 'file' && !selectedFile.value) {
      return 'Please select a valid file to analyze';
    } else if (activeTab.value === 'url' && (!urlContent.value || urlError.value)) {
      return urlError.value || 'Please enter a valid URL to analyze';
    }
    return 'Please provide valid input to analyze';
  }
  
  // Return appropriate tooltip based on active tab
  switch (activeTab.value) {
    case 'paste':
      return `Analyze ${wordCount.value} words of text`;
    case 'file':
      return `Analyze ${selectedFile.value?.name || 'selected file'}`;
    case 'url':
      return `Analyze content from ${urlContent.value}`;
    default:
      return 'Analyze content';
  }
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
  console.log('🔍 Checking canAnalyze for tab:', activeTab.value);
  
  switch (activeTab.value) {
    case 'paste':
      // Only check that there is some text, length validation happens in analyzeContent
      const hasText = textContent.value.trim() !== '';
      console.log('📝 Text input present:', hasText);
      return hasText;
      
    case 'file':
      const hasFile = selectedFile.value !== null && !fileError.value;
      console.log('📂 File selected:', hasFile, selectedFile.value);
      return hasFile;
      
    case 'url':
      const urlValid = urlContent.value.trim() !== '' && !urlError.value;
      console.log('🌐 URL valid:', urlValid, 'URL:', urlContent.value, 'Error:', urlError.value);
      return urlValid;
      
    default:
      console.log('❌ No active tab or invalid tab');
      return false;
  }
});

// Progress properties are now handled by the global progress store

// Check if we're on the EnhancedValidator page
    const isOnEnhancedValidatorPage = computed(() => {
      const currentPath = router.currentRoute.value.path;
      const fullPath = window.location.pathname;
      return currentPath === '/' || fullPath.includes('/casestrainer/') || fullPath.includes('/casestrainer');
    });

// Utility Methods
const getFileExtension = (filename) => {
  return filename.split('.').pop().toLowerCase();
};

const formatFileDate = (timestamp) => {
  const date = new Date(timestamp);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// File Handling Methods
const handleFileSelect = (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  // Validate file type
  const validTypes = ['application/pdf', 'application/msword', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain', 'application/rtf'];
  
  if (!validTypes.includes(file.type) && !file.name.match(/\.(pdf|doc|docx|txt|rtf)$/i)) {
    fileError.value = 'Invalid file type. Please upload a PDF, DOC, DOCX, TXT, or RTF file.';
    return;
  }
  
  // Validate file size (20MB max)
  const maxSize = 20 * 1024 * 1024; // 20MB
  if (file.size > maxSize) {
    fileError.value = 'File is too large. Maximum size is 20MB.';
    return;
  }
  
  selectedFile.value = file;
  fileError.value = '';
  
  // Update active tab to ensure consistency
  activeTab.value = 'file';
  
  // Log for debugging
  console.log('File selected:', file.name, formatFileSize(file.size));
};

const handleDrop = (event) => {
  dragOver.value = false;
  const file = event.dataTransfer.files[0];
  if (!file) return;
  
  // Create a synthetic event for handleFileSelect
  const syntheticEvent = { target: { files: [file] } };
  handleFileSelect(syntheticEvent);
};

const removeFile = () => {
  selectedFile.value = null;
  fileError.value = '';
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

// Input Validation
const validateInput = () => {
  // Clear previous errors
  fileError.value = '';
  
  // Only validate URL if we're on the URL tab
  if (activeTab.value === 'url' && urlContent.value.trim()) {
    try {
      // Basic URL validation
      const url = new URL(urlContent.value);
      
      // Ensure URL has a protocol (http or https)
      if (!url.protocol.match(/^https?:$/)) {
        throw new Error('Invalid protocol');
      }
      
      // Additional validation can be added here (e.g., allowed domains)
      
      // Clear any previous errors if URL is valid
      urlError.value = '';
      console.log('✅ Valid URL:', urlContent.value);
    } catch (error) {
      urlError.value = 'Please enter a valid URL starting with http:// or https://';
      console.log('❌ Invalid URL:', urlContent.value, error);
    }
  } else if (activeTab.value === 'url' && !urlContent.value.trim()) {
    // Clear error when URL is empty
    urlError.value = '';
  }
  
  // For file tab, ensure any file errors are cleared when switching away
  if (activeTab.value !== 'file') {
    fileError.value = '';
  }
};

// const loadRecentInput = (input) => {
//   activeTab.value = input.tab;
//   switch (input.tab) {
//     case 'paste':
//       textContent.value = input.text || '';
//       break;
//     case 'url':
//       urlContent.value = input.url || '';
//       break;
//   }
//   validateInput();
// };

const onFileChange = (event) => {
  // NUCLEAR OPTION: Completely disable file handling if we're on EnhancedValidator page
  const currentPath = router.currentRoute.value.path;
  const fullPath = window.location.pathname;
  const isEnhancedValidatorPage = currentPath === '/enhanced-validator' || fullPath.includes('enhanced-validator');
  
  console.log('🔍 HomeView onFileChange called!');
  console.log('🔍 Router path:', currentPath);
  console.log('🔍 Full URL path:', fullPath);
  console.log('🔍 Is EnhancedValidator page:', isEnhancedValidatorPage);
  
  // NUCLEAR BLOCK: Prevent ANY file handling if on EnhancedValidator page
  if (isEnhancedValidatorPage) {
    console.log('🔍 NUCLEAR BLOCK: HomeView file handling completely disabled!');
    console.log('🔍 NUCLEAR BLOCK: HomeView file handling completely disabled on EnhancedValidator page!');
    // Clear the file input to prevent any further processing
    if (event.target) {
      event.target.value = '';
    }
    selectedFile.value = null;
    return;
  }
  
  console.log('🔍 Proceeding with HomeView file handling');
  const file = event.target.files[0];
  if (file) {
    handleFile(file);
  } else {
    // Handle case where file selection was cancelled
    selectedFile.value = null;
    fileError.value = '';
  }
};

const onFileDrop = (event) => {
  event.preventDefault();
  isDragOver.value = false;
  
  // NUCLEAR BLOCK: Prevent ANY file handling if on EnhancedValidator page
  const currentPath = router.currentRoute.value.path;
  const fullPath = window.location.pathname;
  const isEnhancedValidatorPage = currentPath === '/enhanced-validator' || fullPath.includes('enhanced-validator');
  if (isEnhancedValidatorPage) {
    console.log('🔍 NUCLEAR BLOCK: File drop disabled on EnhancedValidator page!');
    return;
  }
  
  const file = event.dataTransfer.files[0];
  if (file) {
    handleFile(file);
  }
};

const handleFile = (file) => {
  fileError.value = '';
  selectedFile.value = null; // Reset selected file first

  // Define allowed MIME types and file extensions
  const allowedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/rtf',
    'text/rtf',
    'text/html',
    'application/xhtml+xml',
    'application/xml',
    'text/xml'
  ];
  
  const allowedExtensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.md', '.html', '.htm', '.xml', '.xhtml'];
  const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
  
  // Check file type and extension
  if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
    fileError.value = 'Please select a valid file type (PDF, DOCX, TXT, RTF, MD, HTML, or XML)';
    return;
  }

  // Check file size (50MB limit)
  if (file.size > 50 * 1024 * 1024) {
    fileError.value = 'File size must be less than 50MB';
    return;
  }

  // If we get here, the file is valid
  selectedFile.value = file;
  console.log('✅ File selected and validated:', file.name);
};

const fileInput = ref(null);

const triggerFileInput = () => {
  // NUCLEAR BLOCK: Completely disable file input trigger on EnhancedValidator page
  if (isOnEnhancedValidatorPage.value) {
    console.log('🔍 NUCLEAR BLOCK: File input trigger disabled on EnhancedValidator page!');
    console.log('🔍 NUCLEAR BLOCK: File input trigger disabled on EnhancedValidator page!');
    return;
  }
  
  if (!isAnalyzing.value && fileInput.value) {
    fileInput.value.click();
  }
};

const clearFile = () => {
  if (fileInput.value) {
    fileInput.value.value = '';
  }
  selectedFile.value = null;
  fileError.value = '';
  
  // Clear previous results when changing input
  analysisResults.value = null;
  analysisError.value = '';
  
  console.log('🗑️ File selection cleared');
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// formatTime is now available from the global progress store

// Progress tracking methods are now handled by the global progress store

const analyzeContent = async () => {
  // Show debug popup
      // Debug alert removed for cleaner interface
  
  if (!canAnalyze.value || isAnalyzing.value) {
    return;
  }
  
  // Add text length validation here instead of in canAnalyze
  if (activeTab.value === 'paste' && textContent.value.trim().length < 5) {
    return;
  }
  
  isAnalyzing.value = true;
  
  try {
    let requestData;
    
    // Prepare request data based on active tab
    if (activeTab.value === 'file' && selectedFile.value) {
      // For file uploads, use FormData
      requestData = new FormData();
      requestData.append('file', selectedFile.value);
      requestData.append('type', 'file');
    } else if (activeTab.value === 'url' && urlContent.value) {
      // For URL analysis, use JSON data
      requestData = {
        type: 'url',
        url: urlContent.value.trim()
      };
    } else if (activeTab.value === 'paste' && textContent.value) {
      // For text analysis, use JSON data
      requestData = {
        type: 'text',
        text: textContent.value.trim()
      };
    } else {
      throw new Error('Invalid input configuration');
    }
    
    // Start progress tracking AFTER we have requestData
    try {
      globalProgress.startProgress(activeTab.value, requestData, 30); // 30 seconds estimated
      
      // Set up processing steps for text analysis
      if (activeTab.value === 'text') {
        globalProgress.setSteps([
          { step: 'Initializing...', estimated_time: 2 },
          { step: 'Extracting citations...', estimated_time: 8 },
          { step: 'Verifying citations...', estimated_time: 15 },
          { step: 'Clustering citations...', estimated_time: 5 }
        ]);
        
        // Update to first step immediately
        globalProgress.updateProgress({ 
          step: 'Initializing...', 
          progress: 5,
          total_progress: 5 
        });
      }
    } catch (error) {
      throw error;
    }
    
    // Debug alert removed for cleaner interface
    
    // Use the analyze function from the API
    // Debug alerts removed for cleaner interface
    
    const response = await analyze(requestData);
    // Debug alert removed for cleaner interface
    
    // Response details logged to console for debugging

    console.log('Response analysis:');
    console.log('- Has response:', !!response);
    console.log('- Has task_id:', response?.task_id);
    console.log('- Has citations:', !!response?.citations);
    console.log('- Citations count:', response?.citations?.length || 0);
    console.log('- Success:', response?.success);

    // Check if we have immediate results vs. async task
    if (response && response.status === 'completed' && response.result) {
      console.log('🎉 IMMEDIATE RESULTS RECEIVED! Citations:', response.result?.citations?.length || 0);
      
      // Update progress to show completion
      globalProgress.updateProgress({ 
        step: 'Clustering citations...', 
        progress: 90,
        total_progress: 90 
      });
      
      // Store results in the format expected by CitationResults component
      // Map citation_objects to citations for component compatibility
      const mappedClusters = (response.result.clusters || []).map(cluster => ({
        ...cluster,
        citations: cluster.citation_objects || cluster.citations || []
      }));
      
      analysisResults.value = {
        clusters: mappedClusters,
        citations: response.result.citations || [],
        message: response.message,
        metadata: response.metadata,
        success: response.success,
        total_citations: response.result.citations?.length || 0
      };
      analysisError.value = '';
      
      // Complete progress tracking
      globalProgress.completeProgress(analysisResults.value);
      
      console.log('Results stored for display:', {
        citations: response.result?.citations?.length || 0,
        clusters: response.result?.clusters?.length || 0,
        message: response.message,
        reformattedData: analysisResults.value
      });
      
      return; // Don't navigate, show results on current page
    }
    
    // Handle async task with task_id
    if (response && response.task_id) {
      console.log('🔄 Async task started with task_id:', response.task_id);
      
      // Set up async task progress tracking
      activeAsyncTask.value = response.task_id;
      asyncTaskProgress.value = {
        taskId: response.task_id,
        status: 'queued',
        message: response.message || 'Task queued and waiting to be processed'
      };
      
      // Update progress to show queued status
      globalProgress.updateProgress({ 
        step: 'Task queued...', 
        progress: 20,
        total_progress: 20 
      });
      
      // Start polling for task status
      pollingService.startPolling(
        response.task_id,
        // Progress callback
        (progressData) => {
          console.log('📊 Task progress:', progressData);
          
          // Update global progress based on task status
          if (progressData.status === 'queued') {
            globalProgress.updateProgress({ 
              step: 'Task queued...', 
              progress: 20,
              total_progress: 20 
            });
          } else if (progressData.status === 'processing') {
            globalProgress.updateProgress({ 
              step: 'Processing citations...', 
              progress: 50,
              total_progress: 50 
            });
          } else if (progressData.status === 'verifying') {
            globalProgress.updateProgress({ 
              step: 'Verifying citations...', 
              progress: 75,
              total_progress: 75 
            });
          }
          
          if (asyncTaskProgress.value) {
            asyncTaskProgress.value.status = progressData.status;
            asyncTaskProgress.value.message = progressData.message;
          }
        },
        // Complete callback
        (result) => {
          console.log('✅ Task completed:', result);
          
          // Format the result data for CitationResults component
          if (result.result) {
            const mappedClusters = (result.result.clusters || []).map(cluster => ({
              ...cluster,
              citations: cluster.citation_objects || cluster.citations || []
            }));
            
            analysisResults.value = {
              clusters: mappedClusters,
              citations: result.result.citations || [],
              message: result.message || 'Analysis completed successfully',
              metadata: result.metadata || {},
              success: true,
              total_citations: result.result.citations?.length || 0
            };
          } else {
            analysisResults.value = {
              clusters: [],
              citations: [],
              message: 'Analysis completed but no results found',
              metadata: {},
              success: false,
              total_citations: 0
            };
          }
          
          // Clear async task state
          activeAsyncTask.value = null;
          asyncTaskProgress.value = null;
          
          // Complete progress tracking
          globalProgress.completeProgress(analysisResults.value);
          
          console.log('Async task results stored:', analysisResults.value);
        },
        // Error callback
        (errorMessage) => {
          console.error('❌ Task failed:', errorMessage);
          
          analysisError.value = `Task failed: ${errorMessage}`;
          
          // Clear async task state
          activeAsyncTask.value = null;
          asyncTaskProgress.value = null;
          
          // Complete progress tracking
          globalProgress.completeProgress(null);
        }
      );
      
      return; // Don't navigate, show progress on current page
    } else if (response) {
      console.log('Response received but no task_id or immediate results - storing for display');
      // Format response data for CitationResults component
      if (response.result) {
        // Map citation_objects to citations for component compatibility
        const mappedClusters = (response.result.clusters || []).map(cluster => ({
          ...cluster,
          citations: cluster.citation_objects || cluster.citations || []
        }));
        
        analysisResults.value = {
          clusters: mappedClusters,
          citations: response.result.citations || [],
          message: response.message,
          metadata: response.metadata,
          success: response.success,
          total_citations: response.result.citations?.length || 0
        };
      } else {
        analysisResults.value = response;
      }
      analysisError.value = '';
      
      // Complete progress tracking
      globalProgress.completeProgress(analysisResults.value);
    } else {
      console.log('No response received');
      analysisError.value = 'No response received from server';
    }
  } catch (error) {
    console.error('=== ANALYSIS ERROR ===');
    console.error('Error details:', error);
    console.error('Error response:', error.response);
    console.error('Error message:', error.message);
    
    analysisResults.value = null;
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
    
    console.error('Final error message:', errorMessage);
    console.error(errorMessage);
    
    // Store error for display
    analysisError.value = errorMessage;
    
    // Set error in global progress store
    globalProgress.setError(errorMessage);
  } finally {
    console.log('=== ANALYSIS COMPLETED ===');
    isAnalyzing.value = false;
    
    // Complete progress tracking if not already completed
    if (globalProgress.progressState.isActive) {
      globalProgress.completeProgress();
    }
  }
};

// Handler functions for CitationResults component
const handleNewAnalysis = () => {
  // Clear previous results and reset form
  analysisResults.value = null;
  analysisError.value = '';
  textContent.value = '';
  urlContent.value = '';
  selectedFile.value = null;
  fileError.value = '';
  urlError.value = '';
  
  // Stop any active async task polling
  if (activeAsyncTask.value) {
    pollingService.stopPolling(activeAsyncTask.value);
    activeAsyncTask.value = null;
    asyncTaskProgress.value = null;
    isAnalyzing.value = false;
  }
  
  // Focus on text input
  activeTab.value = 'paste';
  
  console.log('New analysis initiated - form reset and async tasks stopped');
};

const handleCopyResults = () => {
  // This will be handled by the CitationResults component
  console.log('Copy results requested');
};

const handleDownloadResults = () => {
  // This will be handled by the CitationResults component
  console.log('Download results requested');
};

// Async task handler methods
const handleCancelAsyncTask = (taskId) => {
  console.log('Cancelling async task:', taskId);
  
  // Stop polling for this task
  pollingService.stopPolling(taskId);
  
  // Clear async task state
  activeAsyncTask.value = null;
  asyncTaskProgress.value = null;
  
  // Reset analysis state
  isAnalyzing.value = false;
  
  // Complete progress tracking
  globalProgress.completeProgress(null);
  
  console.log('Async task cancelled and state cleared');
};

const handleAsyncTaskComplete = (result) => {
  console.log('Async task completed via component event:', result);
  
  // The result should already be stored in analysisResults.value
  // from the polling service callback, but let's ensure it's there
  if (!analysisResults.value && result) {
    // Format the result data for CitationResults component
    if (result.result) {
      const mappedClusters = (result.result.clusters || []).map(cluster => ({
        ...cluster,
        citations: cluster.citation_objects || cluster.citations || []
      }));
      
      analysisResults.value = {
        clusters: mappedClusters,
        citations: result.result.citations || [],
        message: result.message || 'Analysis completed successfully',
        metadata: result.metadata || {},
        success: true,
        total_citations: result.result.citations?.length || 0
      };
    }
  }
  
  // Clear async task state
  activeAsyncTask.value = null;
  asyncTaskProgress.value = null;
  
  console.log('Async task completion handled');
};

const handleAsyncTaskError = (errorMessage) => {
  console.error('Async task error via component event:', errorMessage);
  
  // Set error message
  analysisError.value = `Task failed: ${errorMessage}`;
  
  // Clear async task state
  activeAsyncTask.value = null;
  asyncTaskProgress.value = null;
  
  // Reset analysis state
  isAnalyzing.value = false;
  
  // Complete progress tracking
  globalProgress.completeProgress(null);
  
  console.log('Async task error handled');
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
  display: block;
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
  max-width: 1000px;
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

.file-dropzone {
  border: 2px dashed #0d6efd;
  transition: all 0.3s ease;
}

.file-dropzone:hover {
  background-color: #f8f9fa;
  transform: translateY(-1px);
}

.file-dropzone.border-success {
  border-color: #198754;
}

.file-dropzone.border-danger {
  border-color: #dc3545;
  background-color: #fff8f8;
}

.file-icon-cover {
  position: absolute;
  bottom: -5px;
  right: -5px;
  background: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.hover-lift {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.hover-lift:hover {
  transform: translateY(-3px);
  box-shadow: 0 0.5rem 1.5rem rgba(0, 0, 0, 0.1) !important;
}

.icon-shape {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-shape i {
  font-size: 1.75rem;
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
  border-radius: 1.5rem;
  padding: 1.5rem;
  margin: 1.5rem auto;
  max-width: 1200px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.feature-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 1rem;
  padding: 1rem;
  text-align: center;
  box-shadow: var(--shadow-light);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-medium);
}

.feature-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 0.75rem auto;
  color: white;
  font-size: 1.25rem;
}

.feature-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.feature-description {
  color: var(--text-secondary);
  line-height: 1.4;
  font-size: 0.85rem;
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

/* Results Replacement Area Styles */
.results-replacement-area {
  margin-top: 2rem;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  border: 1px solid #dee2e6;
}

.results-title {
  margin: 0;
  color: #2c3e50;
  font-size: 1.5rem;
  font-weight: 600;
}

.new-analysis-btn {
  background: linear-gradient(45deg, #007bff, #0056b3);
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
}

.new-analysis-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
  background: linear-gradient(45deg, #0056b3, #004085);
}

/* Mobile responsive for results header */
@media (max-width: 768px) {
  .results-header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .results-title {
    font-size: 1.25rem;
  }
  
  .new-analysis-btn {
    width: 100%;
    padding: 1rem;
  }
}
</style>
