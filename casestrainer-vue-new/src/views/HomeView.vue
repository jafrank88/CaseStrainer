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
                <i class="bi bi-shield-check me-3" aria-hidden="true"></i>
                U.S. Case Citation Verification
              </h1>
              <p class="hero-subtitle">
                Extract and verify U.S. legal case citations from documents, text, or URLs against authoritative databases.
              </p>
              <div class="hero-badges">
                <span class="hero-badge"><i class="bi bi-lightning-charge-fill me-1" aria-hidden="true"></i>Fast Processing</span>
                <span class="hero-badge"><i class="bi bi-diagram-3-fill me-1" aria-hidden="true"></i>Clustered Results</span>
                <span class="hero-badge"><i class="bi bi-shield-lock-fill me-1" aria-hidden="true"></i>No Gen AI</span>
              </div>
            </div>

            <!-- Experimental Use Banner -->
            <div class="experimental-banner">
              <i class="bi bi-flask me-2" aria-hidden="true"></i>
              <strong>Research Tool:</strong> For educational and research purposes. Always verify results independently.
            </div>
          </div>

          <div class="input-container">
            <!-- Input Method Selection (tablist) -->
            <div class="input-methods" role="tablist" aria-label="Choose how to provide your document">
              <div 
                id="tab-home-paste"
                :class="['input-method-card', { active: activeTab === 'paste' }]"
                role="tab"
                :tabindex="activeTab === 'paste' ? 0 : -1"
                :aria-selected="activeTab === 'paste'"
                aria-controls="panel-home-paste"
                aria-label="Paste text: copy and paste legal text"
                @click="selectHomeTab('paste')"
                @keydown="onHomeTabKeydown"
              >
                <div class="method-icon">
                  <i class="bi bi-clipboard-text" aria-hidden="true"></i>
                </div>
                <div class="method-content">
                  <h4>Paste Text</h4>
                  <p>Copy and paste legal text</p>
                </div>
                <div v-if="activeTab === 'paste'" class="active-indicator" aria-hidden="true">
                  <i class="bi bi-check"></i>
                </div>
              </div>

              <div 
                id="tab-home-file"
                :class="['input-method-card', { active: activeTab === 'file' }]"
                role="tab"
                :tabindex="activeTab === 'file' ? 0 : -1"
                :aria-selected="activeTab === 'file'"
                aria-controls="panel-home-file"
                aria-label="Upload file: PDF, Word, text, and other formats"
                @click="selectHomeTab('file')"
                @keydown="onHomeTabKeydown"
              >
                <div class="method-icon">
                  <i class="bi bi-file-earmark-text" aria-hidden="true"></i>
                </div>
                <div class="method-content">
                  <h4>Upload File</h4>
                  <p>PDF, DOCX, TXT, RTF, MD, HTML, XML</p>
                </div>
                <div v-if="activeTab === 'file'" class="active-indicator" aria-hidden="true">
                  <i class="bi bi-check"></i>
                </div>
              </div>

              <div 
                id="tab-home-url"
                :class="['input-method-card', { active: activeTab === 'url' }]"
                role="tab"
                :tabindex="activeTab === 'url' ? 0 : -1"
                :aria-selected="activeTab === 'url'"
                aria-controls="panel-home-url"
                aria-label="URL input: analyze online content"
                @click="selectHomeTab('url')"
                @keydown="onHomeTabKeydown"
              >
                <div class="method-icon">
                  <i class="bi bi-link-45deg" aria-hidden="true"></i>
                </div>
                <div class="method-content">
                  <h4>URL Input</h4>
                  <p>Analyze online content</p>
                </div>
                <div v-if="activeTab === 'url'" class="active-indicator" aria-hidden="true">
                  <i class="bi bi-check"></i>
                </div>
              </div>
            </div>

            <!-- Input Content Area -->
            <div class="input-content-area panel-surface">
              <!-- Text Input Tab -->
              <div
                v-show="activeTab === 'paste'"
                id="panel-home-paste"
                class="input-tab-content"
                role="tabpanel"
                aria-labelledby="tab-home-paste"
                :hidden="activeTab !== 'paste'"
                :aria-hidden="activeTab !== 'paste'"
              >
                <div class="form-group">
                  <div class="d-flex justify-content-between align-items-center mb-2">
                    <label class="form-label mb-0" for="home-legal-text">
                      <i class="bi bi-clipboard-text me-2" aria-hidden="true"></i>
                      Legal Text
                    </label>
                    <div v-if="textContent" class="char-count-pill" aria-live="polite">
                      {{ textContent.length.toLocaleString() }} characters
                    </div>
                  </div>
                  
                  <div class="paste-field-wrap position-relative">
                    <textarea 
                      id="home-legal-text"
                      v-model="textContent"
                      class="form-control input-field textarea-legal"
                      :class="{ 'is-valid': textContent && textContent.trim().length >= 10, 'is-invalid': textContent && textContent.trim().length < 10 }"
                      rows="10"
                      placeholder="Paste your legal text here…"
                      aria-describedby="home-text-hint"
                      @input="validateInput"
                      @keydown.enter.ctrl.exact.prevent="canAnalyze ? analyzeContent() : null"
                      spellcheck="false"
                    ></textarea>
                    
                    <!-- Clear button (only shown when there's content) -->
                    <button 
                      v-if="textContent"
                      @click="textContent = ''; validateInput()"
                      class="btn btn-sm btn-outline-secondary textarea-clear-btn"
                      title="Clear text"
                      type="button"
                      aria-label="Clear legal text"
                    >
                      <i class="bi bi-x-lg" aria-hidden="true"></i>
                    </button>
                  </div>
                  <p id="home-text-hint" class="visually-hidden">Press Control and Enter to analyze when enough text is entered.</p>
                  
                  <p class="input-keyboard-hint">
                    <span class="input-keyboard-hint-label">Tip:</span>
                    <kbd>Ctrl</kbd><span class="kbd-plus">+</span><kbd>Enter</kbd>
                    <span class="input-keyboard-hint-rest">to analyze when ready</span>
                  </p>
                  
                  <!-- Input Quality Indicators -->
                  <div v-if="textContent" class="input-quality-indicators mt-3">
                    <div class="d-flex flex-wrap gap-3">
                      <div class="quality-item">
                        <span class="quality-label"><i class="bi bi-fonts me-1" aria-hidden="true"></i>Words:</span>
                        <span class="quality-value">{{ wordCount }}</span>
                      </div>
                      <div class="quality-item">
                        <span class="quality-label"><i class="bi bi-quote me-1" aria-hidden="true"></i>Est. Citations:</span>
                        <span class="quality-value">{{ estimatedCitations }}</span>
                      </div>
                      <div class="quality-item">
                        <span class="quality-label"><i class="bi bi-calendar3 me-1" aria-hidden="true"></i>Years:</span>
                        <span class="quality-value">{{ yearCount }}</span>
                      </div>
                    </div>
                    
                    <!-- Text validation feedback -->
                    <div v-if="textContent" class="mt-3">
                      <div v-if="textContent.trim().length < 10" class="alert alert-warning py-2 mb-0" role="status">
                        <i class="bi bi-exclamation-triangle-fill me-2" aria-hidden="true"></i>
                        Please enter at least 10 characters for meaningful analysis
                      </div>

                    </div>
                  </div>
                </div>
              </div>

              <!-- File Input Tab -->
              <div
                v-show="activeTab === 'file'"
                id="panel-home-file"
                class="input-tab-content"
                role="tabpanel"
                aria-labelledby="tab-home-file"
                :hidden="activeTab !== 'file'"
                :aria-hidden="activeTab !== 'file'"
              >
                <div class="form-group">
                  <label class="form-label" id="label-home-file">
                    <i class="bi bi-file-earmark-text me-2" aria-hidden="true"></i>
                    Document File
                  </label>
                  <div class="file-upload-container">
                    <input 
                      type="file" 
                      id="fileInput"
                      ref="fileInput"
                      class="d-none"
                      accept=".pdf,.doc,.docx,.txt,.rtf"
                      aria-labelledby="label-home-file"
                      @change="handleFileSelect"
                    />
                    
                    <div 
                      class="home-file-dropzone file-dropzone rounded-3 border-2 border-dashed p-5 text-center position-relative" 
                      :class="{ 
                        'border-danger': fileError, 
                        'border-success': selectedFile && !fileError,
                        'border-primary': !selectedFile && !fileError,
                        'home-file-dropzone--drag': dragOver
                      }"
                      role="button"
                      tabindex="0"
                      aria-label="Upload a document. Drop a file here or press Enter or Space to browse files."
                      @click="$refs.fileInput.click()"
                      @keydown.enter.prevent="$refs.fileInput.click()"
                      @keydown.space.prevent="$refs.fileInput.click()"
                      @dragover.prevent="dragOver = true"
                      @dragleave="dragOver = false"
                      @drop.prevent="handleDrop"
                    >
                      <!-- Drag & Drop Overlay -->
                      <div 
                        v-if="dragOver"
                        class="position-absolute top-0 start-0 w-100 h-100 d-flex flex-column align-items-center justify-content-center bg-primary bg-opacity-10 rounded-3"
                        style="z-index: 5;"
                      >
                        <i class="bi bi-cloud-arrow-up fs-1 text-primary" aria-hidden="true"></i>
                        <p class="mt-2 mb-0 text-primary fw-bold">Drop file to upload</p>
                      </div>
                      
                      <div class="file-dropzone-content">
                        <i class="bi bi-upload fs-1 text-muted mb-3" aria-hidden="true"></i>
                        <h5 class="mb-2">Drag & drop your file here</h5>
                        <p class="text-muted mb-0">or click to browse files</p>
                        <p class="text-muted small mt-2">Supports: PDF, DOC, DOCX, TXT, RTF</p>
                        
                        <div v-if="selectedFile" class="selected-file mt-3">
                          <div class="d-flex align-items-center justify-content-center">
                            <i class="bi bi-file-earmark-text me-2" aria-hidden="true"></i>
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
                  <div v-if="fileError" class="alert alert-danger d-flex align-items-center mt-3 py-2" role="alert">
                    <i class="bi bi-exclamation-triangle-fill me-2" aria-hidden="true"></i>
                    <div>{{ fileError }}</div>
                  </div>
                  
                  <div v-else-if="selectedFile && !isAnalyzing" class="alert alert-success d-flex align-items-center justify-content-center mt-3 py-2" role="status">
                    <i class="bi bi-check-circle-fill me-2" aria-hidden="true"></i>
                    <div class="text-center">
                      <strong>Ready for analysis</strong>
                      <div class="small">Click "Analyze Content" to process your document</div>
                    </div>
                  </div>
                  </div>
                </div>
                

              </div>

              <!-- URL Input Tab -->
              <div
                v-show="activeTab === 'url'"
                id="panel-home-url"
                class="input-tab-content"
                role="tabpanel"
                aria-labelledby="tab-home-url"
                :hidden="activeTab !== 'url'"
                :aria-hidden="activeTab !== 'url'"
              >
                <div class="form-group">
                  <label class="form-label" for="home-url-input">
                    <i class="bi bi-link-45deg me-2" aria-hidden="true"></i>
                    Document URL
                  </label>
                  <div class="input-group home-url-input-group">
                    <span class="input-group-text" aria-hidden="true"><i class="bi bi-link-45deg" aria-hidden="true"></i></span>
                    <input 
                      id="home-url-input"
                      v-model.trim="urlContent"
                      type="url" 
                      class="form-control input-field"
                      placeholder="https://example.com/legal-document"
                      :aria-describedby="urlAriaDescribedBy"
                      :aria-invalid="urlError ? 'true' : 'false'"
                      @input="validateInput"
                      :class="{ 'is-invalid': urlError }"
                      autocomplete="off"
                      spellcheck="false"
                      @keyup.enter="canAnalyze ? analyzeContent() : null"
                    />
                  </div>
                  
                  <div v-if="urlError" id="home-url-err" class="invalid-feedback d-flex align-items-center mt-1" role="alert">
                    <i class="bi bi-exclamation-triangle-fill me-2" aria-hidden="true"></i>
                    <span>{{ urlError }}</span>
                  </div>
                  
                  <div v-else-if="urlContent && !urlError && !isAnalyzing" id="home-url-ok" class="valid-feedback d-flex align-items-center mt-1" role="status">
                    <i class="bi bi-check-circle-fill text-success me-2" aria-hidden="true"></i>
                    <span>Valid URL - ready to analyze</span>
                  </div>
                  
                  <div v-else id="home-url-hint" class="form-text home-form-hint mt-2">
                    <i class="bi bi-info-circle me-1" aria-hidden="true"></i>
                    Enter a valid URL to a legal document (PDF, DOCX, HTML, etc.)
                  </div>
                </div>
                
                <!-- URL Analysis Preview (optional) -->
                <div v-if="urlContent && !urlError && !isAnalyzing" class="url-preview-card mt-3">
                  <h6 class="url-preview-card-title"><i class="bi bi-link-45deg me-2" aria-hidden="true"></i>Link preview</h6>
                  <div class="d-flex align-items-center gap-2">
                    <div class="flex-grow-1 text-truncate url-preview-card-link-wrap">
                      <a :href="urlContent" target="_blank" rel="noopener noreferrer" class="url-preview-card-link">
                        {{ urlContent }}<span class="visually-hidden"> (opens in new tab)</span>
                      </a>
                    </div>
                    <button 
                      @click="urlContent = ''; urlError = ''" 
                      class="btn btn-sm btn-outline-secondary flex-shrink-0"
                      title="Clear URL"
                      type="button"
                      aria-label="Clear URL"
                    >
                      <i class="bi bi-x" aria-hidden="true"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Analyze Button / Processing Content -->
            <div class="analyze-button-container mt-4">
              <!-- Show Processing Content when analyzing -->
              <SimpleProgress 
                v-if="isAnalyzing || globalProgress.progressState.isActive"
                component-id="home"
              />
              
              <!-- Show Analyze Button when not processing -->
              <div v-else class="d-flex flex-column align-items-center">
                <button 
                  :class="[
                    'btn', 
                    'analyze-btn', 
                    'position-relative',
                    'overflow-hidden',
                    { 
                      'btn-primary': canAnalyze && !isAnalyzing,
                      'btn-secondary': !canAnalyze && !isAnalyzing,
                      'btn-success': isAnalyzing,
                      'pe-none': !canAnalyze
                    }
                  ]"
                  :disabled="!canAnalyze || isAnalyzing"
                  @click="analyzeContent"
                  :title="getAnalyzeButtonTooltip"
                  :aria-label="getAnalyzeButtonTooltip"
                  :aria-busy="isAnalyzing ? 'true' : 'false'"
                  style="min-width: 200px; transition: all 0.3s ease;"
                >
                  <!-- Button content -->
                  <div class="d-flex align-items-center justify-content-center">
                    <span v-if="isAnalyzing" class="spinning-loader me-2" role="status" aria-hidden="true"></span>
                    <i v-else class="bi bi-search me-2" aria-hidden="true"></i>
                    <span class="fw-medium">
                      {{ getAnalyzeButtonText }}
                    </span>
                  </div>
                </button>
                
                <!-- Status message -->
                <div 
                  v-if="!isAnalyzing"
                  class="mt-3 analyze-status-line text-center"
                  role="status"
                  aria-live="polite"
                  :class="{ 
                    'analyze-status-line--muted': !canAnalyze, 
                    'analyze-status-line--ready': canAnalyze 
                  }"
                >
                  <template v-if="!canAnalyze">
                    <div v-if="activeTab === 'paste' && (!textContent || textContent.trim().length < 10)" class="d-flex align-items-center justify-content-center">
                      <i class="bi bi-info-circle me-2" aria-hidden="true"></i>
                      <span>Enter at least 10 characters to analyze</span>
                    </div>
                    <div v-else-if="activeTab === 'file' && !selectedFile" class="d-flex align-items-center justify-content-center">
                      <i class="bi bi-upload me-2" aria-hidden="true"></i>
                      <span>Upload a document to analyze</span>
                    </div>
                    <div v-else-if="activeTab === 'url' && !urlContent" class="d-flex align-items-center justify-content-center">
                      <i class="bi bi-link-45deg me-2" aria-hidden="true"></i>
                      <span>Enter a URL to analyze</span>
                    </div>
                    <div v-else-if="urlError" class="text-danger d-flex align-items-center justify-content-center">
                      <i class="bi bi-exclamation-triangle-fill me-2" aria-hidden="true"></i>
                      <span>{{ urlError }}</span>
                    </div>
                    <div v-else-if="fileError" class="text-danger d-flex align-items-center justify-content-center">
                      <i class="bi bi-exclamation-triangle-fill me-2" aria-hidden="true"></i>
                      <span>{{ fileError }}</span>
                    </div>
                  </template>
                  <template v-else>
                    <div class="d-flex align-items-center justify-content-center">
                      <i class="bi bi-check-circle-fill text-success me-2" aria-hidden="true"></i>
                      <span>Ready to analyze</span>
                      <span class="ms-2 text-muted">
                        <template v-if="activeTab === 'paste'">(or press Ctrl+Enter)</template>
                        <template v-else-if="activeTab === 'url'">(or press Enter in URL field)</template>
                      </span>
                    </div>
                  </template>
                </div>
              </div>
            </div>

            <!-- Static processing indicator removed - SimpleProgress now provides real-time updates -->
          </div>
        </div>

        <!-- Recent Inputs Sidebar - Temporarily Hidden -->
        <!-- <div class="recent-inputs-sidebar-container">
          <RecentInputs @load-input="loadRecentInput" />
        </div> -->

        <!-- Async Task Progress Section - DISABLED: Using globalProgress instead -->
        <!-- AsyncTaskProgress component shows static progress, globalProgress shows real-time updates -->
        <!--
        <AsyncTaskProgress
          v-if="asyncTaskProgress && !analysisResults && !analysisError"
          :task-id="asyncTaskProgress.taskId"
          :initial-status="asyncTaskProgress.status"
          :initial-message="asyncTaskProgress.message"
          @cancel="handleCancelAsyncTask"
          @complete="handleAsyncTaskComplete"
          @error="handleAsyncTaskError"
        />
        -->

        <!-- Real-time Progress Display - Moved to replace Analyze button when processing -->
        <!-- SimpleProgress now appears in place of Analyze button when processing starts -->

        <!-- Results Section - Replaces input area when results are available -->
        <div
          v-if="analysisResults || analysisError"
          class="results-replacement-area"
          role="region"
          aria-labelledby="home-results-heading"
        >
          <div class="results-header">
            <div class="results-heading">
              <h2 id="home-results-heading" class="results-title" tabindex="-1">
                <i class="bi bi-shield-check me-2" aria-hidden="true"></i>
                Citation Analysis Results
              </h2>
              <div class="results-meta">
                <span class="result-chip">
                  <i class="bi bi-journal-text me-1" aria-hidden="true"></i>
                  {{ resultClusterCount }} case mention{{ resultClusterCount === 1 ? '' : 's' }} detected
                </span>
                <span class="result-chip">
                  <i class="bi bi-link-45deg me-1" aria-hidden="true"></i>
                  {{ resultCitationCount }} citation mention{{ resultCitationCount === 1 ? '' : 's' }} detected
                </span>
                <span v-if="analysisError" class="result-chip chip-error">
                  <i class="bi bi-exclamation-triangle-fill me-1" aria-hidden="true"></i>
                  Partial/Error State
                </span>
              </div>
              <p class="results-meta-note" v-if="resultClusterCount > 0 || resultCitationCount > 0">
                Counts above are everything detected in the document. The case cards below merge duplicates and group related citations for easier review.
              </p>
            </div>
            <button 
              type="button"
              @click="handleNewAnalysis" 
              class="btn btn-primary new-analysis-btn"
              aria-label="Start a new analysis and return to the input form"
            >
              <i class="bi bi-plus-circle me-2" aria-hidden="true"></i>
              New Analysis
            </button>
          </div>
          
          <!-- HomeView Results Section -->
          

          
          <!-- CitationResults Component -->
          <!-- HARMONIZED: Pass top-level structure directly - both sync and async now have citations/clusters at top level -->
          <CitationResults
            :results="analysisResults"
            :error="analysisError"
            component-id="home"
            @new-analysis="handleNewAnalysis"
            @copy-results="handleCopyResults"
            @download-results="handleDownloadResults"
          />
          

        </div>
      </div>
    </div>

</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick, toRefs } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';
import api, { analyze } from '@/api/api';
import { globalProgress as globalProgressStore } from '@/stores/progressStore';
import CitationResults from '@/components/CitationResults.vue';
import AsyncTaskProgress from '@/components/AsyncTaskProgress.vue';
import SimpleProgress from '@/components/SimpleProgress.vue';
import pollingService from '@/services/pollingService';
import logger from '@/utils/logger';

// Use the progress store directly - it's already reactive
const globalProgress = globalProgressStore;
// import RecentInputs from '@/components/RecentInputs.vue'; // Temporarily hidden
// import { useRecentInputs } from '@/composables/useRecentInputs'; // Temporarily hidden

const router = useRouter();
const route = useRoute();
const HOME_TAB_ORDER = ['paste', 'file', 'url'];

function selectHomeTab(tab) {
  if (!HOME_TAB_ORDER.includes(tab)) return;
  activeTab.value = tab;
  nextTick(() => {
    document.getElementById(`tab-home-${tab}`)?.focus();
  });
}

function onHomeTabKeydown(e) {
  if (e.key === ' ' || e.key === 'Enter') {
    e.preventDefault();
    const id = e.currentTarget?.getAttribute?.('id');
    if (id === 'tab-home-paste') selectHomeTab('paste');
    else if (id === 'tab-home-file') selectHomeTab('file');
    else if (id === 'tab-home-url') selectHomeTab('url');
    return;
  }
  const i = HOME_TAB_ORDER.indexOf(activeTab.value);
  if (i < 0) return;
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
    e.preventDefault();
    selectHomeTab(HOME_TAB_ORDER[(i + 1) % HOME_TAB_ORDER.length]);
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    e.preventDefault();
    selectHomeTab(HOME_TAB_ORDER[(i - 1 + HOME_TAB_ORDER.length) % HOME_TAB_ORDER.length]);
  } else if (e.key === 'Home') {
    e.preventDefault();
    selectHomeTab(HOME_TAB_ORDER[0]);
  } else if (e.key === 'End') {
    e.preventDefault();
    selectHomeTab(HOME_TAB_ORDER[HOME_TAB_ORDER.length - 1]);
  }
}

const activeTab = ref('paste');
const textContent = ref('');
const urlContent = ref('');
const selectedFile = ref(null);
const fileError = ref('');
const urlError = ref('');
/** IDs of URL field helper messages (only one branch is visible at a time). */
const urlAriaDescribedBy = computed(() => {
  if (urlError.value) return 'home-url-err';
  if (urlContent.value && !urlError.value) return 'home-url-ok';
  return 'home-url-hint';
});
const isAnalyzing = ref(false);
// showProcessing removed - SimpleProgress component handles all progress display
const isDragOver = ref(false);
const dragOver = ref(false);
const analysisResults = ref(null);
const analysisError = ref('');
const progressCompletedDisplayCount = ref(0);
// Case count: use clusters when present; when backend returns 0 clusters we show one card per citation (fallback), so use citation count
const resultClusterCount = computed(() => {
  const c = analysisResults.value?.clusters?.length ?? 0;
  const n = analysisResults.value?.citations?.length ?? 0;
  return c > 0 ? c : n;
});
const resultCitationCount = computed(() => analysisResults.value?.citations?.length || 0);

// Async task state
const activeAsyncTask = ref(null);
const asyncTaskProgress = ref(null);
const isAsyncProcessing = ref(false); // Track if we're in async mode to prevent early spinner reset

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
    isAsyncProcessing.value = false;
    isAnalyzing.value = false;
  }
  
  console.log('Tab changed - results cleared and async tasks stopped');
  progressCompletedDisplayCount.value = 0;
});

const scrollToPageTop = async () => {
  await nextTick();
  try {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } catch (err) {
    window.scrollTo(0, 0);
  }
};

// When results or an error state appears, scroll to top and move focus to the results heading.
watch([analysisResults, analysisError], async ([res, err], [prevRes, prevErr]) => {
  const hasNow = !!(res || err);
  const hadBefore = !!(prevRes || prevErr);
  if (!hasNow) return;
  if (hasNow && hadBefore && res === prevRes && err === prevErr) return;
  await nextTick();
  await scrollToPageTop();
  await nextTick();
  document.getElementById('home-results-heading')?.focus({ preventScroll: true });
});

const normalizeProgressMessage = (rawStep, jobData) => {
  const text = (rawStep || '').toString().trim();
  if (!text) return 'Processing...';

  const isPdfRun =
    (globalProgressStore?.progressState?.uploadType === 'file') &&
    (globalProgressStore?.progressState?.uploadData?.name || '')
      .toString()
      .toLowerCase()
      .endsWith('.pdf');

  const withOcrHint = (base) => {
    if (!isPdfRun) return base;
    if (!base) return base;
    if (/\bocr\b/i.test(base)) return base;
    return `${base} (scanned/broken-text PDFs may require OCR and can take a few minutes)`;
  };

  // Make "queued" and early extraction phases more self-explanatory for PDFs.
  if (/queued for background processing/i.test(text) || /^task queued/i.test(text)) {
    return withOcrHint(text);
  }
  if (/extracting/i.test(text) && /pdf|text/i.test(text)) {
    return withOcrHint(text);
  }

  const m = text.match(/\b(\d+)\s+completed\b/i);
  if (!m) return text;

  const processed = Number(m[1]) || 0;
  const vs = jobData?.verification_status || {};
  const total = Number(vs.total_citations || jobData?.progress_data?.total_citations || 0) || 0;

  // Keep user-visible completion count monotonic even if backend phases reset counters.
  progressCompletedDisplayCount.value = Math.max(progressCompletedDisplayCount.value, processed);
  const shown = progressCompletedDisplayCount.value;

  if (shown > 0 && processed === 0 && (vs.state === 'running' || vs.state === 'verifying')) {
    return total > 0
      ? `Verifying citations... ${shown}/${total} completed (moving to next phase)`
      : `Verifying citations... ${shown} completed (moving to next phase)`;
  }

  return total > 0
    ? `Verifying citations... ${shown}/${total} completed`
    : `Verifying citations... ${shown} completed`;
};

// Initialize with URL parameters if present
onMounted(() => {
  // CRITICAL FIX: Reset any lingering progress state to prevent timer from starting on page load
  globalProgressStore.resetProgress();
  
  if (route.query.tab && HOME_TAB_ORDER.includes(String(route.query.tab))) {
    activeTab.value = String(route.query.tab);
    
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
  
  // Enhanced citation patterns that match our backend extraction logic
  const citationPatterns = [
    // Washington State patterns (most common)
    /\b\d+\s+Wn\.?\s*(?:2d|3d|App\.?)?\s+\d+\b/g,           // 123 Wn.2d 456, 123 Wn App 456
    /\b\d+\s+Wash\.?\s*(?:2d|3d|App\.?)?\s+\d+\b/g,          // 123 Wash.2d 456, 123 Wash App 456
    
    // Federal patterns
    /\b\d+\s+U\.?\s*S\.?\s+\d+\b/gi,                          // 123 US 456, 123 U.S. 456
    /\b\d+\s+F\.?\s*(?:2d|3d|Supp\.?|Supp\.?2d)?\s+\d+\b/gi, // 123 F.2d 456, 123 F.Supp. 456
    
    // State patterns (general)
    /\b\d+\s+[A-Z][a-z]+\.?\s*(?:2d|3d|App\.?)?\s+\d+\b/g,   // 123 Cal.2d 456, 123 Tex.App 456
    
    // Reporter patterns
    /\b\d+\s+P\.?\s*(?:2d|3d)?\s+\d+\b/g,                    // 123 P.2d 456, 123 P.3d 456
    /\b\d+\s+N\.?\s*W\.?\s*(?:2d|3d)?\s+\d+\b/g,             // 123 N.W.2d 456
    
    // Appellate patterns
    /\b\d+\s+[A-Z][a-z]*\.?\s*App\.?\s+\d+\b/g,              // 123 Wash.App 456
    
    // Supreme Court patterns
    /\b\d+\s+[A-Z][a-z]*\.?\s*(?:2d|3d)?\s+\d+\b/g           // 123 Wash.2d 456
  ];
  
  let count = 0;
  const uniqueMatches = new Set();
  
  citationPatterns.forEach(pattern => {
    const matches = textContent.value.match(pattern);
    if (matches) {
      matches.forEach(match => uniqueMatches.add(match.trim()));
    }
  });
  
  // Use the actual count of unique citations found
  return uniqueMatches.size;
});

const yearCount = computed(() => {
  if (!textContent.value) return 0;
  
  // Enhanced year detection that looks for years in legal citations and context
  const yearPatterns = [
    /\b(19|20)\d{2}\b/g,                    // Standard years: 2010, 2023
    /\(\s*(19|20)\d{2}\s*\)/g,              // Years in parentheses: (2010), (2023)
    /\b(19|20)\d{2}\s*[A-Z][a-z]*\b/g,     // Years followed by month: 2010 January
    /\b[A-Z][a-z]*\s+(19|20)\d{2}\b/g      // Month followed by year: January 2010
  ];
  
  const allYears = new Set();
  
  yearPatterns.forEach(pattern => {
    const matches = textContent.value.match(pattern);
    if (matches) {
      matches.forEach(match => {
        // Extract just the year from the match
        const yearMatch = match.match(/\b(19|20)\d{2}\b/);
        if (yearMatch) {
          allYears.add(yearMatch[0]);
        }
      });
    }
  });
  
  return allYears.size;
});

// Remove Quality Score label and badge
// Remove computed property and class for qualityScore and qualityScoreClass

const canAnalyze = computed(() => {
  console.log('Checking canAnalyze for tab:', activeTab.value);
  
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
      console.log('URL valid:', urlValid, 'URL:', urlContent.value, 'Error:', urlError.value);
      return urlValid;
      
    default:
      console.log('No active tab or invalid tab');
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
      console.log('Valid URL:', urlContent.value);
    } catch (error) {
      urlError.value = 'Please enter a valid URL starting with http:// or https://';
      console.log('Invalid URL:', urlContent.value, error);
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
  
  console.log('HomeView onFileChange called!');
  console.log('Router path:', currentPath);
  console.log('Full URL path:', fullPath);
  console.log('Is EnhancedValidator page:', isEnhancedValidatorPage);
  
  // NUCLEAR BLOCK: Prevent ANY file handling if on EnhancedValidator page
  if (isEnhancedValidatorPage) {
    console.log('NUCLEAR BLOCK: HomeView file handling completely disabled!');
    console.log('NUCLEAR BLOCK: HomeView file handling completely disabled on EnhancedValidator page!');
    // Clear the file input to prevent any further processing
    if (event.target) {
      event.target.value = '';
    }
    selectedFile.value = null;
    return;
  }
  
  console.log('Proceeding with HomeView file handling');
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
    console.log('NUCLEAR BLOCK: File drop disabled on EnhancedValidator page!');
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
  console.log('File selected and validated:', file.name);
};

const fileInput = ref(null);

const triggerFileInput = () => {
  // NUCLEAR BLOCK: Completely disable file input trigger on EnhancedValidator page
  if (isOnEnhancedValidatorPage.value) {
    console.log('NUCLEAR BLOCK: File input trigger disabled on EnhancedValidator page!');
    console.log('NUCLEAR BLOCK: File input trigger disabled on EnhancedValidator page!');
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
  
  console.log('File selection cleared');
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// formatTime is now available from the global progress store

// Enhanced async job polling function
const pollAsyncJob = async (jobId) => {
  console.log('Enhanced async job polling started for:', jobId);
  
  // CRITICAL FIX: Extended timeout for large documents
  // Base timeout: 10 minutes (120 attempts * 5 seconds)
  // For large documents with 100+ citations, allow up to 20 minutes (240 attempts)
  const baseMaxAttempts = 120; // 10 minutes
  const largeDocMaxAttempts = 240; // 20 minutes for documents with 100+ citations
  const maxAttempts = largeDocMaxAttempts; // Use extended timeout for all documents
  let attempts = 0;
  let consecutiveErrors = 0;
  const maxConsecutiveErrors = 10; // Increased from 3 to 10 - allow more resilience for network hiccups
  
  // Track stuck job detection
  let stuckDetection = {
    lastStep: null,
    lastProgress: null,
    lastCitationsProcessed: null,
    lastStepTime: Date.now(),
    stuckThreshold: 180000 // 3 minutes (increased from 2 minutes for large documents)
  };
  
  const poll = async () => {
    try {
      attempts++;
      console.log(`Polling attempt ${attempts}/${maxAttempts} for job ${jobId}`);
      console.log('FRONTEND FIX ACTIVE: Enhanced completion detection enabled');
      
      const statusResponse = await axios.get(`task_status/${jobId}?t=${Date.now()}`, {
        timeout: 30000, // 30 second timeout for status checks
        validateStatus: (status) => status < 500 // Don't throw on 404, 400, etc - only on 500+
      });
      const jobData = statusResponse.data;
      
      // Reset error counter on successful API call
      consecutiveErrors = 0;
      
      console.log('Job status:', jobData.status);
      console.log('DETAILED JOB DATA:', {
        status: jobData.status,
        is_finished: jobData.is_finished,
        is_failed: jobData.is_failed,
        citations_count: jobData.citations?.length || 0,
        has_citations: !!jobData.citations,
        message: jobData.message,
        task_id: jobData.task_id
      });
      
      // Check for completion - only trust explicit status (do not stop just because citations exist;
      // backend may return partial data while still processing)
      const isCompleted = jobData.status === 'completed' ||
                         jobData.status === 'finished' ||
                         jobData.is_finished === true;
      
      const isFailed = jobData.status === 'failed' || 
                      jobData.is_failed === true ||
                      jobData.error;
      
      if (isCompleted) {
        console.log('Async job completed successfully');
        console.log('Completion indicators:', {
          status: jobData.status,
          is_finished: jobData.is_finished,
          citations_count: jobData.citations?.length || 0,
          clusters_count: jobData.clusters?.length || 0
        });
        
        // Complete global progress
        globalProgress.completeProgress(jobData, 'home');
        
        return {
          citations: jobData.citations || [],
          clusters: jobData.clusters || [],
          cluster_sections: jobData.cluster_sections || {}
        };
      } else if (isFailed) {
        console.error('Async job failed:', jobData.error);
        globalProgress.setError(jobData.error || 'Async processing failed');
        throw new Error(jobData.error || 'Async processing failed');
      } else if (attempts >= maxAttempts) {
        console.error('Async job polling timeout');
        if (!globalProgress.progressState.hasResults) {
          globalProgress.setError('Processing timeout - please try again');
        }
        throw new Error('Processing timeout - please try again');
      } else {
        // Job still running, continue polling
        console.log('Job still running, continuing to poll...');

        // Queue position awareness: update store when job is waiting in queue
        if (jobData.status === 'queued') {
          globalProgress.setQueueInfo({
            position: jobData.position ?? -1,
            queueTotal: jobData.queue_total ?? null,
            estimatedWaitSeconds: jobData.estimated_wait_seconds ?? null,
            estimatedWaitHuman: jobData.estimated_wait_human ?? null,
            queuedSeconds: jobData.queued_seconds ?? null,
          });
        } else if (jobData.status === 'started' || jobData.status === 'processing') {
          // Job left the queue — clear the queue banner
          globalProgress.clearQueueInfo();
        }
        
        // STUCK JOB DETECTION: Check if job is stuck at same step
        // Better fallback chain for currentStep - check multiple sources
        const currentStep = jobData.current_step || 
                           jobData.progress_data?.current_message || 
                           jobData.message || 
                           jobData.progress_data?.message ||
                           jobData.current_message ||
                           jobData.verification_status?.current_message ||
                           jobData.status || 
                           'Initializing...'; // Use sensible default instead of 'Unknown'
        
        const currentProgress = jobData.progress || jobData.progress_data?.progress || jobData.progress_data?.overall_progress || 0;
        
        // Enhanced stuck detection: Check if progress AND citation counts are stuck
        const vs = jobData.verification_status || {};
        const citationsProcessed = vs.citations_processed || 0;
        const totalCitations = vs.total_citations || 0;
        const lastUpdated = vs.updated_at || 0;
        
        // Detect if progress is stuck (same values for multiple polls)
        const isProgressStuck = currentStep === stuckDetection.lastStep && 
                               currentProgress === stuckDetection.lastProgress &&
                               citationsProcessed === stuckDetection.lastCitationsProcessed;
        
        // Calculate time stuck
        const timeStuck = Date.now() - stuckDetection.lastStepTime;
        const isVerificationWait = /verifying citations/i.test(currentStep || '') && citationsProcessed === 0;
        
        // Only trigger stuck detection if we have meaningful progress data
        // Don't trigger if currentStep is still "Initializing..." (might be normal for large docs)
        if (currentStep !== 'Initializing...' && currentStep !== 'Unknown' && isProgressStuck) {
          const isPdfUpload =
            (globalProgress.progressState.uploadType === 'file') &&
            (globalProgress.progressState.uploadData?.name || '')
              .toString()
              .toLowerCase()
              .endsWith('.pdf');
          const isOcrLikelyStep = /ocr|extracting|pdf|text extraction/i.test(currentStep || '');
          // OCR/extraction can legitimately take longer without intermediate progress.
          const stuckThresholdMs = (isPdfUpload && isOcrLikelyStep) ? 8 * 60 * 1000 : 3 * 60 * 1000;
          if (timeStuck > stuckThresholdMs) {
            console.error(`Job appears stuck at "${currentStep}" for ${Math.round(timeStuck/1000)}s`);
            console.error('Job may be waiting in queue or encountered an issue');
            
            // More helpful error message
            if (currentProgress === 0 && citationsProcessed === 0) {
              const ocrHint = isPdfUpload ? ' If this is a scanned/broken-text PDF, OCR can take a few minutes.' : '';
              globalProgress.setError(`Processing appears to be queued. The job may be waiting behind other tasks.${ocrHint} Please wait a moment or try again later.`);
            } else if (citationsProcessed > 0 && citationsProcessed < totalCitations) {
              // Show progress-based message when citations are being processed
              const progressPct = totalCitations > 0 ? Math.round((citationsProcessed / totalCitations) * 100) : currentProgress;
              const ocrHint = (isPdfUpload && isOcrLikelyStep) ? ' OCR/extraction can take several minutes for scanned PDFs.' : '';
              globalProgress.setError(`Processing appears stuck at "${currentStep}" (${progressPct}% complete, ${citationsProcessed}/${totalCitations} citations).${ocrHint} The job may be processing a large document or encountering delays. Please wait or try again later.`);
            } else {
              const ocrHint = (isPdfUpload && isOcrLikelyStep) ? ' OCR/extraction can take several minutes for scanned PDFs.' : '';
              globalProgress.setError(`Processing appears stuck at "${currentStep}" (${Math.round(currentProgress)}% complete).${ocrHint} The job may be queued or processing a large document. Please wait or try again later.`);
            }
            throw new Error(`Job stuck at ${currentStep}`);
          }
        } else if (!isProgressStuck) {
          // Progress changed, reset stuck detection
          stuckDetection.lastStep = currentStep;
          stuckDetection.lastProgress = currentProgress;
          stuckDetection.lastCitationsProcessed = citationsProcessed;
          stuckDetection.lastStepTime = Date.now();
        }
        
        // Enhanced debugging and progress updates
        console.log('RAW BACKEND RESPONSE:', JSON.stringify(jobData, null, 2));
        
        // Update progress with detailed backend data
        // Check for progress in multiple formats: progress_data, progress_percent, verification_status
        const hasProgressData = jobData.progress !== undefined || 
                               jobData.current_step || 
                               jobData.progress_data ||
                               jobData.progress_percent !== undefined ||
                               jobData.verification_status?.progress_percent !== undefined ||
                               jobData.current_message ||
                               jobData.verification_status?.current_message;
        
        if (hasProgressData) {
          console.log('Updating progress from backend:', {
            progress: jobData.progress,
            progress_percent: jobData.progress_percent,
            current_step: jobData.current_step,
            current_message: jobData.current_message,
            progress_data: jobData.progress_data,
            verification_status: jobData.verification_status,
            hasProgressData: !!jobData.progress_data,
            hasVerificationStatus: !!jobData.verification_status,
            hasSteps: !!(jobData.progress_data && jobData.progress_data.steps)
          });
          
          // Use backend progress data if available - check multiple sources
          let progressPercent = jobData.progress || 
                               jobData.progress_percent ||
                               jobData.progress_data?.progress || 
                               jobData.progress_data?.overall_progress ||
                               jobData.verification_status?.progress_percent ||
                               0;
          
          let currentStep = jobData.current_step || 
                           jobData.current_message ||
                           jobData.progress_data?.current_message || 
                           jobData.message || 
                           jobData.progress_data?.message ||
                           jobData.verification_status?.current_message ||
                           jobData.status || 
                           'Initializing...'; // Better default
          currentStep = normalizeProgressMessage(currentStep, jobData);
          
          // If no explicit progress, try to calculate from steps
          if (!progressPercent && jobData.progress_data?.steps) {
            const completedSteps = jobData.progress_data.steps.filter(s => s.status === 'completed').length;
            const totalSteps = jobData.progress_data.steps.length;
            progressPercent = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;
            console.log('Calculated progress from steps:', progressPercent, `(${completedSteps}/${totalSteps})`);
          }
          
          // If still no progress but we have verification_status with citations info, estimate progress
          // OR if progress_percent seems stuck (same value for multiple polls), use citation counts for better estimate
          let estimatedTimeRemaining = null;
          if (jobData.verification_status) {
            const vs = jobData.verification_status;
            if (vs.total_citations > 0 && vs.citations_processed !== undefined) {
              // Calculate progress based on citation processing
              // 30% for extraction, 70% for verification
              const extractionProgress = Math.min(30, (vs.citations_processed / vs.total_citations) * 30);
              
              // If state is running/verifying, add verification progress
              let verificationProgress = 0;
              if (vs.state === 'running' || vs.state === 'verifying') {
                // Estimate verification progress based on citations processed
                verificationProgress = Math.min(70, (vs.citations_processed / vs.total_citations) * 70);
              }
              
              const calculatedProgress = extractionProgress + verificationProgress;
              
              // CRITICAL FIX: Calculate estimated time remaining based on citation processing rate
              // Only show estimate if we have processed at least 5 citations to avoid inaccurate early estimates
              if (vs.citations_processed >= 5 && vs.start_time) {
                const elapsedSeconds = (Date.now() / 1000) - vs.start_time;
                const citationsPerSecond = vs.citations_processed / elapsedSeconds;
                const remainingCitations = vs.total_citations - vs.citations_processed;
                if (citationsPerSecond > 0) {
                  const estimatedSecondsRemaining = remainingCitations / citationsPerSecond;
                  estimatedTimeRemaining = Math.ceil(estimatedSecondsRemaining);
                  // Cap at reasonable maximum (15 minutes) - more conservative than before
                  if (estimatedTimeRemaining > 900) {
                    estimatedTimeRemaining = null; // Don't show if estimate is too high
                  }
                  // Also cap minimum estimate - if less than 30 seconds, don't show
                  if (estimatedTimeRemaining < 30) {
                    estimatedTimeRemaining = null;
                  }
                }
              }
              
              // Use calculated progress if it's better than the provided progress_percent
              // OR if progress_percent is stuck at a low value (< 5%)
              if (!progressPercent || progressPercent < 5 || calculatedProgress > progressPercent) {
                progressPercent = Math.min(95, calculatedProgress); // Cap at 95% until complete
                const timeMsg = estimatedTimeRemaining ? ` (~${Math.ceil(estimatedTimeRemaining / 60)} min remaining)` : '';
                console.log(`Using calculated progress from verification_status: ${progressPercent}% (${vs.citations_processed}/${vs.total_citations} citations, state: ${vs.state}, extraction: ${extractionProgress.toFixed(1)}%, verification: ${verificationProgress.toFixed(1)}%)${timeMsg}`);
              } else {
                console.log(`Using backend progress_percent: ${progressPercent}% (calculated would be ${calculatedProgress.toFixed(1)}%)`);
              }
            }
          }

          // If verification has not moved for a while, make the wait reason explicit.
          if (isVerificationWait && timeStuck > 30000) {
            currentStep = 'Waiting on external citation source response...';
          }
          
          // Update progress message with time estimate if available
          if (estimatedTimeRemaining && currentStep) {
            const minutesRemaining = Math.ceil(estimatedTimeRemaining / 60);
            if (minutesRemaining > 0) {
              currentStep = `${currentStep} (est. ${minutesRemaining} min remaining)`;
            }
          }
          
          // Ensure progressPercent is a valid number (not NaN, null, or undefined)
          if (!progressPercent || isNaN(progressPercent) || progressPercent === 0) {
            progressPercent = Math.max(5, globalProgress.progressPercent || 5); // Minimum 5% to show activity
            console.log('Using minimum progress to show activity:', progressPercent);
          }
          
          // Final safety check - ensure it's a valid number
          progressPercent = Number(progressPercent) || 5;
          // Do not regress the visible bar when backend phases briefly report lower progress.
          progressPercent = Math.max(progressPercent, Number(globalProgress.progressPercent) || 0);
          
          // If no current step, try to find active step
          if (!currentStep && jobData.progress_data?.steps) {
            const activeStep = jobData.progress_data.steps.find(s => s.status === 'in_progress' || s.status === 'running');
            const lastCompletedStep = jobData.progress_data.steps.filter(s => s.status === 'completed').pop();
            currentStep = activeStep?.name || lastCompletedStep?.name || 'Processing...';
            console.log('Determined current step:', currentStep);
          }
          
          globalProgress.updateProgress({
            step: currentStep || 'Processing...',
            progress: progressPercent,
            total_progress: progressPercent
          });
          
          console.log('Updated global progress:', {
            step: currentStep,
            progress: progressPercent,
            globalProgressPercent: globalProgress.progressPercent
          });
          
          // Update individual step progress if available
          if (jobData.progress_data && jobData.progress_data.steps) {
            const steps = jobData.progress_data.steps.map(step => ({
              step: step.name,
              progress: step.progress || 0,
              status: step.status,
              message: step.message,
              completed: step.status === 'completed',
              startTime: step.start_time,
              endTime: step.end_time
            }));
            
            globalProgress.setSteps(steps);
            console.log('Updated processing steps:', {
              count: steps.length,
              steps: steps.map(s => `${s.step}: ${s.status} (${s.progress}%)`)
            });
          }
        } else {
          console.log('No progress data found in backend response');
          // Force a small progress increment to show activity
          const currentProgress = globalProgress.progressPercent;
          if (currentProgress < 95) {
            globalProgress.updateProgress({
              step: 'Processing...',
              progress: Math.min(currentProgress + 2, 95), // Small increment, max 95%
              total_progress: Math.min(currentProgress + 2, 95)
            });
            console.log('Incremented progress to show activity:', globalProgress.progressPercent);
          }
        }
        
        // Wait 2 seconds before next poll (reduced from 5 seconds for more responsive updates)
        await new Promise(resolve => setTimeout(resolve, 2000));
        return await poll(); // Recursive call
      }
    } catch (error) {
      // Check if this is a network error or a non-fatal HTTP error
      const isNetworkError = !error.response || error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK';
      const is404Error = error.response?.status === 404;
      const is500Error = error.response?.status >= 500;
      
      // Only count network errors and 500+ errors as consecutive errors
      // 404 errors might mean the task isn't registered yet, which is okay for async tasks
      if (isNetworkError || is500Error) {
        consecutiveErrors++;
      } else if (is404Error) {
        // 404 is not necessarily an error - task might not be registered yet
        // Only count it if we've been polling for a while (more than 10 attempts)
        if (attempts > 10) {
          consecutiveErrors++;
        }
        // Reset to 0 if we get a 404 early (task might not be registered yet)
        else {
          consecutiveErrors = Math.max(0, consecutiveErrors - 1);
        }
      }
      
      // Only log first error and every 5th error to reduce spam
      if (consecutiveErrors === 1 || consecutiveErrors % 5 === 0) {
        const errorType = isNetworkError ? 'Network' : is404Error ? 'Not Found (404)' : is500Error ? 'Server Error' : 'Unknown';
        console.error(`Error polling async job (${consecutiveErrors} consecutive errors, ${errorType}):`, error.message || error);
      }
      
      // Stop if too many consecutive errors
      if (consecutiveErrors >= maxConsecutiveErrors) {
        console.error(`Polling stopped after ${consecutiveErrors} consecutive errors`);
        // More helpful error message that doesn't suggest the job failed
        globalProgress.setError(`Temporarily unable to check job status (${consecutiveErrors} consecutive errors). The job may still be processing successfully. Please wait a moment and refresh the page to check status.`);
        throw new Error(`Polling failed after ${consecutiveErrors} consecutive errors`);
      }
      
      // Stop if max attempts reached
      if (attempts >= maxAttempts) {
        console.error('Async job polling timeout after', attempts, 'attempts');
        if (!globalProgress.progressState.hasResults) {
          globalProgress.setError('Processing timeout (5 minutes). The job may still be running. Please check back later.', true);
        }
        throw new Error('Processing timeout');
      }
      
      // Retry on error after delay with exponential backoff
      // Start with 2 seconds, increase up to 10 seconds
      const retryDelay = Math.min(2000 * Math.pow(1.5, consecutiveErrors - 1), 10000);
      console.log(`Retrying after ${retryDelay}ms delay (consecutive errors: ${consecutiveErrors})`);
      await new Promise(resolve => setTimeout(resolve, retryDelay));
      return await poll(); // Recursive call
    }
  };
  
  return await poll();
};

// Process immediate results after progress delay
const processImmediateResults = (response) => {
  // Store results in the format expected by CitationResults component
  // Map citation_objects to citations for component compatibility
  // FIXED: Look for clusters at top level (new structure) or fallback to result.clusters
  const clusters = response.clusters || response.result?.clusters || [];
  console.log('🔍 processImmediateResults - Raw clusters from response:', {
    hasClusters: !!response.clusters,
    clustersCount: clusters.length,
    firstCluster: clusters[0] ? Object.keys(clusters[0]) : null
  });
  
  // Ensure clusters have citations array - clusters from backend already have citations
  const mappedClusters = clusters.map(cluster => {
    // Clusters from backend already have citations array, just ensure it exists
    const clusterCitations = cluster.citation_objects || cluster.citations || [];
    console.log(`🔍 Cluster ${cluster.cluster_id}: ${clusterCitations.length} citations`);
    return {
      ...cluster,
      citations: clusterCitations  // Use existing citations array from cluster
    };
  });
  
  console.log('🔍 processImmediateResults - Mapped clusters:', {
    mappedCount: mappedClusters.length,
    clustersWithCitations: mappedClusters.filter(c => c.citations && c.citations.length > 0).length
  });

  // Extract and use progress data from backend response
  if (response.result && response.result.progress_data) {
    const progressData = response.result.progress_data;
    console.log('Backend progress data received:', progressData);

    // Update global progress with real backend data
    if (progressData.steps && progressData.steps.length > 0) {
      // Use real progress data from backend instead of time-based estimation
      globalProgress.progressState.totalProgress = progressData.progress || progressData.overall_progress || 0;
      globalProgress.progressState.currentStep = progressData.current_message || progressData.steps.find(s => s.status === 'in_progress')?.name || 'Processing...';

      // Set up processing steps from backend with real progress
      const backendSteps = progressData.steps.map(step => ({
        step: step.name,
        progress: step.progress || 0,
        status: step.status,
        message: step.message,
        estimated_time: 1, // Not used since we have real progress
        startTime: step.start_time,
        endTime: step.end_time,
        completed: step.status === 'completed'
      }));

      globalProgress.setSteps(backendSteps);

      // Override the time-based progress calculation with real data
      globalProgress.progressState.elapsedTime = progressData.elapsed_time || 0;
      globalProgress.progressState.startTime = progressData.start_time ? progressData.start_time * 1000 : Date.now(); // Convert to milliseconds

      console.log('Updated progress with real backend data:', {
        totalProgress: progressData.progress || progressData.overall_progress,
        currentStep: progressData.current_message || progressData.message,
        elapsedTime: progressData.elapsed_time,
        steps: backendSteps.length
      });

      // Update progress for each completed step
      progressData.steps.forEach(step => {
        if (step.status === 'completed') {
          globalProgress.updateProgress({
            step: step.name,
            progress: step.progress || 100,
            total_progress: step.progress || 100
          });
        }
      });
    }
  }

  // HARMONIZED: Ensure both sync and async paths use the same structure
  // The component expects: { citations: [...], clusters: [...] } at the top level
  analysisResults.value = {
    citations: response.citations || [],  // Top level for component
    clusters: mappedClusters,  // Top level for component (mapped clusters with citations array)
    cluster_sections: response.cluster_sections || {}, // Add cluster_sections
    result: {
      citations: response.citations || [],
      clusters: clusters  // Raw clusters for backward compatibility
    },
    message: response.message,
    metadata: response.metadata,
    success: response.success,
    total_citations: response.citations?.length || 0
  };
  analysisError.value = '';

  console.log('Results stored for display:', {
    citations: response.citations?.length || 0,  // FIXED: Use top level citations
    clusters: clusters?.length || 0,  // FIXED: Use extracted clusters
    mappedClusters: mappedClusters?.length || 0,
    message: response.message,
    hasResults: !!analysisResults.value
  });
  console.log('🔍 analysisResults.value structure:', {
    hasCitations: !!analysisResults.value.citations,
    citationsCount: analysisResults.value.citations?.length || 0,
    hasClusters: !!analysisResults.value.clusters,
    clustersCount: analysisResults.value.clusters?.length || 0,
    firstClusterId: analysisResults.value.clusters?.[0]?.cluster_id,
    firstClusterCitationsCount: analysisResults.value.clusters?.[0]?.citations?.length || 0
  });
  console.log('analysisResults.value =', analysisResults.value);
};

const analyzeContent = async () => {
  console.log('HOMEVIEW analyzeContent CALLED!');
  console.log('canAnalyze:', canAnalyze.value);
  console.log('isAnalyzing:', isAnalyzing.value);
  
  // Show debug popup
      // Debug alert removed for cleaner interface
  
  if (!canAnalyze.value || isAnalyzing.value) {
    console.log('Early return - canAnalyze:', canAnalyze.value, 'isAnalyzing:', isAnalyzing.value);
    return;
  }
  
  // Add text length validation here instead of in canAnalyze
  if (activeTab.value === 'paste' && textContent.value.trim().length < 5) {
    return;
  }
  
  isAnalyzing.value = true;
  progressCompletedDisplayCount.value = 0;
  // showProcessing removed - SimpleProgress component handles progress display
  console.log('isAnalyzing set to:', isAnalyzing.value);
  
  // Force Vue to recognize the change
  await nextTick();
  
  // Start progress immediately on click so spinner/progress bar show right away
  try {
    globalProgress.startProgress(activeTab.value, { kickoff: true }, 30); // 30 seconds estimated
    // Minimal initial state
    globalProgress.updateProgress({ 
      step: 'Initializing...', 
      total_progress: 5 
    });
    // Set initial metadata (will be refined after request starts)
    globalProgress.progressState.metadata = {
      processing_mode: 'async',
      input_type: activeTab.value
    };
  } catch (e) {
    console.warn('Progress init warning:', e);
  }
  
  try {
    let requestData;
    let pollingInterval = null; // declared here so both sync and async paths can clear it safely

    // Prepare request data based on active tab
    if (activeTab.value === 'file' && selectedFile.value) {
      // For file uploads, use FormData
      requestData = new FormData();
      requestData.append('file', selectedFile.value);
      requestData.append('type', 'file');
      requestData.append('force_mode', 'async');
      requestData.append('enable_verification', 'true'); // Explicitly enable verification
    } else if (activeTab.value === 'url' && urlContent.value) {
      // For URL analysis, use JSON data
      requestData = {
        type: 'url',
        url: urlContent.value.trim(),
        force_mode: 'async',
        enable_verification: true // Explicitly enable verification
      };
    } else if (activeTab.value === 'paste' && textContent.value) {
      // For text analysis, use JSON data
      requestData = {
        type: 'text',
        text: textContent.value.trim(),
        force_mode: 'async',
        enable_verification: true // Explicitly enable verification
      };
    } else {
      throw new Error('Invalid input configuration');
    }
    
    // Update progress metadata now that we have requestData (without restarting)
    try {
      // Ensure progress state is properly initialized before proceeding
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Set up processing steps for pasted text analysis
      if (activeTab.value === 'paste') {
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
    
    // Generate a client-side request_id that we can use for polling
    // This allows us to poll for progress even during long-running sync requests (30+ seconds)
    const clientRequestId = 'client-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    console.log('Generated client request_id:', clientRequestId);
    
    // Add the request_id to the request data
    if (requestData instanceof FormData) {
      requestData.append('client_request_id', clientRequestId);
    } else if (typeof requestData === 'object') {
      requestData.client_request_id = clientRequestId;
    }
    
    // Start the analyze request and await response
    // Progress callback updates the UI progress bar during polling
    console.log('Waiting for main API response...');
    const response = await analyze(requestData, clientRequestId, (progressData) => {
      // Update progress bar with polling data from api.js
      if (progressData && typeof progressData.progress === 'number') {
        globalProgress.updateProgress({
          step: progressData.message || 'Processing...',
          progress: progressData.progress,
          total_progress: progressData.progress
        });
      }
    });
    console.log('Main API response received!');
    // Handle error/timeout responses so user sees a message instead of no response
    if (response && response.success === false && response.error) {
      analysisError.value = response.error;
      isAnalyzing.value = false;
      globalProgress.completeProgress(null);
      return;
    }
    // Enhanced processing mode detection and async polling
    // FIX: Any response with task_id means the backend used async (queue); show "Async Mode" in UI
    if (response?.task_id) {
      globalProgress.progressState.metadata = {
        ...(globalProgress.progressState.metadata || {}),
        processing_mode: 'async'
      };
    }
    const processingMode = response?.metadata?.processing_mode;
    const jobId = response?.metadata?.job_id ?? response?.task_id;
    
    console.log('Enhanced Processing Analysis:');
    console.log('- Processing mode:', processingMode);
    console.log('- Job ID:', jobId);
    console.log('- Document size:', textContent.value?.length || 'unknown');
    console.log('- Response type:', typeof response);
    
    // Handle async processing with dedicated polling
    if (processingMode === 'queued' && jobId) {
      console.log('Large document detected - starting unified async polling');
      
      // Update metadata to indicate async mode
      globalProgress.progressState.metadata = {
        processing_mode: 'async',
        input_type: activeTab.value,
        job_id: jobId
      };
      
      // Initialize async task state similar to task_id path
      activeAsyncTask.value = jobId;
      asyncTaskProgress.value = { taskId: jobId, status: 'queued', message: 'Task queued and waiting to be processed' };
      isAsyncProcessing.value = true;
      
      // Start unified polling using the same progress callback used elsewhere
      pollingService.startPolling(
        jobId,
        async (progressData) => {
          console.log('Task progress:', progressData);
          // Prefer task_status progress/message; API may send progress or progress_percent
          const pct = progressData.progress ?? progressData.progress_percent;
          const msg = progressData.message ?? progressData.current_message;
          if (typeof pct === 'number' && pct >= 0) {
            globalProgress.updateProgress({ step: msg || 'Processing...', progress: pct, total_progress: pct });
            if (asyncTaskProgress.value) {
              asyncTaskProgress.value.status = progressData.status;
              asyncTaskProgress.value.message = msg;
            }
            return;
          }
          try {
            const progressResponse = await api.get(`/analyze/progress/${jobId}`);
            const pd = progressResponse.data?.progress_data || progressResponse.data?.progress || {};
            const fallbackPct = (pd.progress ?? pd.overall_progress ?? pd.total_progress ?? pd.progress_percent ?? 0);
            const fallbackMsg = pd.current_message || pd.message;
            if (fallbackPct !== undefined && fallbackPct > 0) {
              globalProgress.updateProgress({ step: fallbackMsg || 'Processing...', progress: fallbackPct, total_progress: fallbackPct });
              return;
            }
          } catch (e) {
            console.debug('Progress endpoint not available yet, using task status');
          }
          if (progressData.status === 'queued') {
            globalProgress.updateProgress({ step: 'Task queued...', progress: 20, total_progress: 20 });
          } else if (progressData.status === 'processing') {
            globalProgress.updateProgress({ step: msg || 'Processing citations...', progress: 50, total_progress: 50 });
          } else if (progressData.status === 'verifying') {
            globalProgress.updateProgress({ step: 'Verifying citations...', progress: 75, total_progress: 75 });
          }
          if (asyncTaskProgress.value) {
            asyncTaskProgress.value.status = progressData.status;
            asyncTaskProgress.value.message = progressData.message;
          }
        },
        (result) => {
          console.log('Task completed:', result);
          const citations = result.citations || [];
          const clusters = result.clusters || [];
          if (citations.length > 0 || clusters.length > 0) {
            // HARMONIZED: Ensure both sync and async paths use the same structure
            const mappedClusters = clusters.map(cluster => ({ ...cluster, citations: cluster.citation_objects || cluster.citations || [] }));
            analysisResults.value = {
              citations: citations,  // Top level for component
              clusters: mappedClusters,  // Top level for component (mapped clusters with citations array)
              cluster_sections: result.cluster_sections || {}, // Add cluster_sections
              result: {
                citations: citations,
                clusters: clusters  // Raw clusters for backward compatibility
              },
              message: result.message || 'Analysis completed successfully',
              metadata: result.metadata || {},
              success: true,
              total_citations: citations.length
            };
          } else {
            analysisResults.value = { clusters: [], citations: [], message: 'Analysis completed but no citations found', metadata: result.metadata || {}, success: result.success !== false, total_citations: 0 };
          }
          activeAsyncTask.value = null;
          asyncTaskProgress.value = null;
          isAsyncProcessing.value = false;
          isAnalyzing.value = false;
          globalProgress.completeProgress(analysisResults.value, 'home');
        },
        (errorMessage) => {
          console.error('Task failed:', errorMessage);
          analysisError.value = `Task failed: ${errorMessage}`;
          activeAsyncTask.value = null;
          asyncTaskProgress.value = null;
          isAsyncProcessing.value = false;
          isAnalyzing.value = false;
          globalProgress.completeProgress(null);
        }
      );
      return;
    }
    
    // Response details logged to console for debugging
    console.log('Response analysis:');
    console.log('- Has response:', !!response);
    console.log('- Has task_id:', response?.task_id);
    console.log('- Has citations:', !!response?.citations);
    console.log('- Citations count:', response?.citations?.length || 0);
    console.log('- Success:', response?.success);

    // Check if we have immediate results vs. async task
    // Sync response: top-level citations/clusters, no task_id. Async completion: status completed + result.
    const hasImmediateData = response && (
      (response.status === 'completed' && response.result) ||
      ((response.citations?.length > 0 || response.clusters?.length > 0) && !response.task_id)
    );
    if (hasImmediateData) {
      const citationCount = response.citations?.length ?? response.result?.citations?.length ?? 0;
      console.log('🎉 IMMEDIATE RESULTS RECEIVED! Citations:', citationCount);
      
      // CRITICAL: Stop polling immediately before processing results to prevent errors
      if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
        console.log('Stopped polling before processing results');
      }
      
      // Check if we have a task_id - if so, poll for progress even though task is complete
      // This shows the progress animation for sync tasks
      if (response.task_id || response.result?.task_id) {
        const taskId = response.task_id || response.result?.task_id;
        console.log('Sync task with task_id - polling for progress animation:', taskId);
        
        // Poll the progress endpoint to show progress animation
        try {
          const progressResponse = await api.get(`/analyze/progress/${taskId}`);
          const pd = progressResponse.data?.progress_data || progressResponse.data?.progress || {};
          const percent = (pd.progress ?? pd.overall_progress ?? pd.total_progress ?? pd.progress_percent ?? 0);
          const message = pd.current_message || pd.message;
          if (percent !== undefined) {
            console.log('Progress data retrieved:', { percent, message });
            globalProgress.updateProgress({
              step: message || 'Processing complete',
              progress: percent || 100,
              total_progress: percent || 100
            });
            await new Promise(resolve => setTimeout(resolve, 800));
          }
        } catch (error) {
          console.warn('Could not fetch progress data:', error);
        }
      }
      
      // For immediate results, ensure progress bar is visible for at least a moment
      // by delaying the completion slightly
      setTimeout(async () => {
        // Update progress to show completion
        globalProgress.updateProgress({ 
          step: 'Clustering citations...', 
          progress: 90,
          total_progress: 90 
        });
        
        // Small delay to show completion progress
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Process results after progress is shown
        console.log('📦 Calling processImmediateResults...');
        processImmediateResults(response);
        console.log('📦 processImmediateResults completed, analysisResults.value =', !!analysisResults.value);
        
        // Complete progress tracking with route scoping
        console.log('📦 Calling completeProgress with results:', analysisResults.value);
        globalProgress.completeProgress(analysisResults.value, 'home');
        console.log('📦 completeProgress called - results should now be visible');
      }, 100);

      // IMPORTANT: Prevent double-processing in the generic response handler below
      return;
    }
    
    // Handle async task with task_id
    // BUT: Check if api.js already polled and got results - if so, don't poll again
    // api.js sets status='completed' when polling finishes successfully
    // ALSO check if citations/clusters are present - if so, api.js already got results
    console.log('DEBUG: Checking hasCompletedResults:', {
      status: response.status,
      hasCitations: !!response.citations,
      citationsIsArray: Array.isArray(response.citations),
      citationsLength: response.citations?.length,
      hasClusters: !!response.clusters,
      clustersIsArray: Array.isArray(response.clusters),
      clustersLength: response.clusters?.length
    });
    
    // Only treat as final when backend explicitly says completed (do not use citations/clusters presence)
    const hasCompletedResults = response.status === 'completed' || response.is_finished === true;
    
    console.log('DEBUG: hasCompletedResults =', hasCompletedResults);
    
    if (response && response.task_id && !hasCompletedResults) {
      console.log('Async task started with task_id:', response.task_id);
      // Ensure UI shows "Async Mode" when we are polling for results
      globalProgress.progressState.metadata = {
        ...(globalProgress.progressState.metadata || {}),
        processing_mode: 'async'
      };

      // Always initialize progress state for async tasks
      // Don't reset if already initialized from startProgress
      if (!globalProgress.progressState.isActive || !globalProgress.progressState.startTime) {
        globalProgress.progressState.isActive = true;
        globalProgress.progressState.startTime = Date.now();
      const isPdf =
        (globalProgress.progressState.uploadType === 'file') &&
        (globalProgress.progressState.uploadData?.name || '')
          .toString()
          .toLowerCase()
          .endsWith('.pdf');
      globalProgress.progressState.estimatedTotalTime = isPdf ? 600 : 300; // PDFs can OCR: allow longer ETA
      }
      
      globalProgress.progressState.taskId = response.task_id;
      
      // Extract and use progress data from backend response for async tasks if available
      if (response.progress_data) {
        const progressData = response.progress_data;
        console.log('Backend progress data for async task:', progressData);
        
        // Update progress state with backend data (don't reset, just update)
        if (progressData.start_time) {
          globalProgress.progressState.startTime = progressData.start_time * 1000;
        }
        globalProgress.progressState.elapsedTime = progressData.elapsed_time || 0;
        globalProgress.progressState.currentStep = progressData.current_message || 'Initializing...';
        globalProgress.progressState.totalProgress = progressData.progress || progressData.overall_progress || 0;
        
        // Update global progress with real backend data for async tasks
        if (progressData.steps && progressData.steps.length > 0) {
          // Set up processing steps from backend with real progress
          const backendSteps = progressData.steps.map(step => ({
            step: step.name,
            progress: step.progress || 0,
            status: step.status,
            message: step.message,
            estimated_time: 50, // 50 seconds per step for async
            startTime: step.start_time,
            endTime: step.end_time,
            completed: step.status === 'completed'
          }));
          
          globalProgress.setSteps(backendSteps);
          
          console.log('Initialized async progress with backend data:', {
            totalProgress: progressData.progress || progressData.overall_progress,
            currentStep: progressData.current_message || progressData.message,
            elapsedTime: progressData.elapsed_time,
            startTime: globalProgress.progressState.startTime,
            isActive: globalProgress.progressState.isActive,
            steps: backendSteps.length
          });
        }
      }
      
      // Set up async task progress tracking
      activeAsyncTask.value = response.task_id;
      asyncTaskProgress.value = {
        taskId: response.task_id,
        status: 'queued',
      message:
        response.message ||
        ((globalProgress.progressState.uploadType === 'file' &&
          (globalProgress.progressState.uploadData?.name || '').toString().toLowerCase().endsWith('.pdf'))
          ? 'Task queued. Scanned/broken-text PDFs may require OCR and can take a few minutes.'
          : 'Task queued and waiting to be processed')
      };
      
      // Mark that we're in async processing mode to prevent early spinner reset
      isAsyncProcessing.value = true;
      
      // Only update progress if we don't have backend progress data
      if (!response.progress_data) {
        globalProgress.updateProgress({ 
          step: 'Task queued...', 
          progress: 20,
          total_progress: 20 
        });
      }
      
      // Start polling for task status AND progress
      pollingService.startPolling(
        response.task_id,
        // Progress callback
        async (progressData) => {
          console.log('Task progress:', progressData);
          
          // Also poll the progress endpoint for real progress data
          try {
            const progressResponse = await api.get(`/analyze/progress/${response.task_id}`);
            const pd = progressResponse.data?.progress_data || progressResponse.data?.progress || {};
            const pct = (pd.progress ?? pd.overall_progress ?? pd.total_progress ?? pd.progress_percent ?? 0);
            const msg = pd.current_message || pd.message;
            if (pct !== undefined) {
              console.log('Real async progress:', pct + '%', msg);
              
              // DON'T stop polling when reaching 100% - let it continue until task actually completes
              // The completion callback will handle final cleanup
              
              globalProgress.updateProgress({
                step: msg || 'Processing...',
                progress: pct || 0,
                total_progress: pct || 0
              });
              return; // Use real progress data instead of hardcoded values
            }
          } catch (error) {
            console.debug('Progress endpoint not available yet, using task status');
          }
          
          // Fallback to hardcoded progress based on task status if progress endpoint not available
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
          console.log('=== ANALYSIS COMPLETED (async) ===', { citations: result.citations?.length ?? 0, clusters: result.clusters?.length ?? 0 });
          console.log('Task completed:', result);
          
          // The async task result should now have the same flat structure as sync results
          const citations = result.citations || [];
          const clusters = result.clusters || [];
          
          console.log('Async task result structure:', {
            hasCitations: !!result.citations,
            citationsCount: citations.length,
            hasClusters: !!result.clusters,
            clustersCount: clusters.length,
            hasNestedResult: !!result.result,
            resultKeys: Object.keys(result)
          });
          
          if (citations.length > 0 || clusters.length > 0) {
            const mappedClusters = clusters.map(cluster => ({
              ...cluster,
              citations: cluster.citation_objects || cluster.citations || []
            }));
            
            analysisResults.value = {
              citations: citations,
              clusters: mappedClusters,
              cluster_sections: result.cluster_sections || {}, // Add cluster_sections
              result: {
                citations: citations,
                clusters: clusters,
                cluster_sections: result.cluster_sections || {} // Add cluster_sections
              },
              message: result.message || 'Analysis completed successfully',
              metadata: result.metadata || {},
              success: true,
              total_citations: citations.length
            };
          } else {
            analysisResults.value = {
              clusters: [],
              citations: [],
              message: 'Analysis completed but no citations found',
              metadata: result.metadata || {},
              success: result.success !== false,
              total_citations: 0
            };
          }
          
          // Clear async task state
          activeAsyncTask.value = null;
          asyncTaskProgress.value = null;
          isAsyncProcessing.value = false; // Clear async flag
          isAnalyzing.value = false; // NOW reset spinner since async is complete
          // showProcessing removed - SimpleProgress component handles progress display
          
          // Complete progress tracking with route scoping
          globalProgress.completeProgress(analysisResults.value, 'home');
          
          console.log('Async task results stored:', analysisResults.value);
        },
        // Error callback
        (errorMessage) => {
          console.error('Task failed:', errorMessage);
          
          analysisError.value = `Task failed: ${errorMessage}`;
          
          // Clear async task state
          activeAsyncTask.value = null;
          asyncTaskProgress.value = null;
          isAsyncProcessing.value = false; // Clear async flag
          isAnalyzing.value = false; // Reset spinner on error
          // showProcessing removed - SimpleProgress component handles progress display
          
          // Complete progress tracking
          globalProgress.completeProgress(null);
        }
      );
      
      return; // Don't navigate, show progress on current page
    } else if (response && response.task_id && (response.citations || response.clusters)) {
      // api.js already polled and got results - process them directly
      console.log('Results already retrieved by api.js polling:', {
        citationsCount: response.citations?.length || 0,
        clustersCount: response.clusters?.length || 0
      });
      
      const citations = response.citations || [];
      const clusters = response.clusters || [];
      
      if (citations.length > 0 || clusters.length > 0) {
        const mappedClusters = clusters.map(cluster => ({
          ...cluster,
          citations: cluster.citation_objects || cluster.citations || []
        }));
        
        analysisResults.value = {
          citations: citations,
          clusters: mappedClusters,
          cluster_sections: response.cluster_sections || {},
          result: {
            citations: citations,
            clusters: clusters,
            cluster_sections: response.cluster_sections || {}
          },
          message: response.message || 'Analysis completed successfully',
          metadata: response.metadata || {},
          success: true,
          total_citations: citations.length
        };
      } else {
        analysisResults.value = {
          clusters: [],
          citations: [],
          message: 'Analysis completed but no citations found',
          metadata: response.metadata || {},
          success: response.success !== false,
          total_citations: 0
        };
      }
      
      isAsyncProcessing.value = false;
      isAnalyzing.value = false;
      globalProgress.completeProgress(analysisResults.value, 'home');
      
      return;
    } else if (response) {
      console.log('Response received but no task_id or immediate results - storing for display');
      
      try {
        // Response should now have a flat structure with citations and clusters at the top level
        let resultData = response;
        
        console.log('Response structure analysis:', {
          hasDirectCitations: !!response.citations,
          hasDirectClusters: !!response.clusters,
          citationsCount: response.citations?.length || 0,
          clustersCount: response.clusters?.length || 0,
          success: response.success
        });
        
        // Map citation_objects to citations for component compatibility
        const mappedClusters = (resultData.clusters || []).map(cluster => ({
          ...cluster,
          citations: cluster.citation_objects || cluster.citations || []
        }));
        
        // Extract citations from clusters if not in root
        const allCitations = [
          ...(resultData.citations || []),
          ...mappedClusters.flatMap(cluster => cluster.citations || [])
        ];
        
        // Remove duplicate citations by citation text
        const uniqueCitations = Array.from(new Map(
          allCitations.map(item => [item.citation || item.citation_text, item])
        ).values());
        
        console.log('Response structure analysis (post-processing):', {
          clustersCount: mappedClusters.length,
          hasMessage: !!response.message,
          hasMetadata: !!response.metadata
        });
        
        // Store results in analysisResults
        analysisResults.value = {
          citations: uniqueCitations,
          clusters: mappedClusters,
          cluster_sections: response.cluster_sections || {},
          message: response.message || 'Analysis completed successfully',
          metadata: response.metadata || {},
          success: true,
          total_citations: uniqueCitations.length
        };
        
        analysisError.value = '';
      } catch (error) {
        console.error('Error in analyzeContent:', {
          error,
          message: error.message,
          code: error.code,
          status: error.response?.status,
          statusText: error.response?.statusText,
          responseData: error.response?.data,
          stack: error.stack
        });
        
        // Enhanced error handling (from EnhancedValidator)
        let errorMessage = 'An unexpected error occurred during analysis';
        
        if (error.code === 'ECONNABORTED') {
          errorMessage = 'Request timed out. Large documents may take longer to process. Please try again.';
        } else if (error.response) {
          // The request was made and the server responded with a status code
          const { status, data } = error.response;
          console.error('Server responded with error:', { status, data });
          
          if (status === 400) {
            errorMessage = data?.message || 'Bad request. Please check your input and try again.';
          } else if (status === 401) {
            errorMessage = 'Session expired. Please refresh the page and try again.';
          } else if (status === 403) {
            errorMessage = 'You do not have permission to perform this action.';
          } else if (status === 404) {
            errorMessage = 'The requested resource was not found.';
          } else if (status === 429) {
            errorMessage = 'Rate limit exceeded. Please wait a moment and try again.';
          } else if (status === 502) {
            errorMessage = 'Server is processing your request. Please wait and try again.';
          } else if (status >= 500) {
            errorMessage = 'A server error occurred. Please try again later.';
          } else {
            errorMessage = `Request failed with status code ${status}`;
          }
        } else if (error.request) {
          // The request was made but no response was received
          console.error('No response received:', error.request);
          errorMessage = 'No response from server. Please check your network connection.';
        } else {
          // Something happened in setting up the request
          console.error('Request setup error:', error.message);
          errorMessage = `Request failed: ${error.message}`;
        }
          
        analysisError.value = errorMessage;
      }
      // REMOVED INNER FINALLY BLOCK - consolidating with outer finally
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
    } else if (error.code === 'ETIMEDOUT' || error.code === 'EUNKNOWNSTATE') {
      errorMessage = error.message || 'Analysis took too long. The document may be large or the server is busy. You can try again or use a smaller document.';
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
    // Only run "completion" cleanup when we're NOT in async mode. In async mode we returned
    // after starting polling, so this finally runs too early - don't log "COMPLETED" or reset
    // spinner; the polling onComplete callback will handle that.
    const inAsyncMode = isAsyncProcessing.value || activeAsyncTask.value;
    if (!inAsyncMode) {
      console.log('=== ANALYSIS COMPLETED (sync path) ===');
    }
    
    // CRITICAL: Ensure polling is stopped in all cases (success, error, timeout)
    try {
      if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
        console.log('Cleanup: Stopped polling in finally block');
      }
    } catch (e) {
      // ignore
    }
    
    if (!inAsyncMode) {
      console.log('isAsyncProcessing:', isAsyncProcessing.value);
      console.log('activeAsyncTask:', activeAsyncTask.value);
    }
    
    // Only reset isAnalyzing if we're NOT in async processing mode
    if (!isAsyncProcessing.value && !activeAsyncTask.value) {
      isAnalyzing.value = false;
      if (!inAsyncMode) console.log('Spinner reset (sync mode)');
    } else {
      if (!inAsyncMode) console.log('Spinner still active (async mode - will reset in callback)');
    }
    
    // Ensure any loading states are reset for non-async cases
    if (!isAsyncProcessing.value && activeAsyncTask.value) {
      activeAsyncTask.value = null;
      asyncTaskProgress.value = null;
    }
    
    // Complete progress tracking if not already completed (and not async)
    if (!isAsyncProcessing.value && globalProgress.progressState.isActive) {
      globalProgress.completeProgress();
    }
    
    // Force UI update in case we're in a weird state
    if (!isAsyncProcessing.value) {
      nextTick(() => {
        setTimeout(() => {
          if (analysisError.value) {
            const errorEl = document.querySelector('.error-message');
            errorEl?.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }, 100);
      });
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
  // showProcessing removed - SimpleProgress component handles progress display
  
  // Complete progress tracking
  globalProgress.completeProgress(null);
  
  console.log('Async task error handled');
};
</script>

<style>
/* Global spinner animation - must be unscoped for animations to work */
@keyframes spin {
  from { 
    transform: rotate(0deg); 
  }
  to { 
    transform: rotate(360deg); 
  }
}

.spinning-loader {
  width: 1rem !important;
  height: 1rem !important;
  border: 0.15rem solid var(--spinner-track) !important;
  border-top-color: var(--primary) !important;
  border-radius: 50% !important;
  animation: spin 0.75s linear infinite !important;
  display: inline-block !important;
}
</style>

<style scoped>
/* Main Layout */
.home {
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
  --home-page-bg: #f6f8fc;
  --home-surface: rgba(255, 255, 255, 0.95);
  --home-surface-solid: #ffffff;
  --home-panel-bg: #fcfcff;
  --home-panel-border: #ebe7f5;
  --home-muted-bg: #f8f9fa;
  --home-active-tint: #f8f9ff;
  --home-input-border: rgba(75, 46, 131, 0.14);
  --home-hero-badge-fg: #3e2a69;
  --home-hero-badge-bg: #f1ecfb;
  --home-hero-badge-border: #dfd3f4;
  --home-dropzone-bg: color-mix(in srgb, var(--home-muted-bg) 65%, var(--home-surface-solid));
  --home-dropzone-hover-bg: color-mix(in srgb, var(--primary-color) 6%, var(--home-surface-solid));
  --home-dropzone-drag-bg: color-mix(in srgb, var(--primary-color) 11%, var(--home-surface-solid));
  --home-focus-ring: color-mix(in srgb, var(--primary-color) 28%, transparent);
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: radial-gradient(circle at top right, rgba(75, 46, 131, 0.08), transparent 45%),
              radial-gradient(circle at bottom left, rgba(13, 110, 253, 0.06), transparent 40%),
              var(--home-page-bg);
  color: var(--text-primary);
}

.background-pattern {
  position: absolute;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  filter: blur(70px);
  opacity: 0.2;
  pointer-events: none;
}

.background-pattern:nth-of-type(1) {
  top: -140px;
  right: -120px;
  background: #6a4c93;
}

.background-pattern:nth-of-type(2) {
  bottom: -160px;
  left: -120px;
  background: #0d6efd;
}

.container {
  position: relative;
  z-index: 1;
}

.main-content-wrapper {
  display: block;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2.5rem 0 3rem;
}

.main-input-area {
  background: var(--home-surface);
  border-radius: 20px;
  padding: 2.2rem;
  box-shadow: 0 10px 30px rgba(31, 38, 135, 0.08);
  border: 1px solid var(--home-input-border);
  backdrop-filter: blur(6px);
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
  font-size: 1.08rem;
  color: var(--text-secondary);
  line-height: 1.65;
  max-width: 34rem;
  margin: 0 auto;
}

.hero-badges {
  margin-top: 1rem;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.55rem;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 600;
  color: #3e2a69;
  background: #f1ecfb;
  border: 1px solid #dfd3f4;
}

.experimental-banner {
  background: linear-gradient(135deg, #fff3cd, #ffeaa7);
  border: 1px solid #ffeaa7;
  border-radius: 10px;
  padding: 0.85rem 1.1rem;
  color: #856404;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  text-align: center;
  line-height: 1.45;
}

.home-form-hint {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

/* Input Container */
.input-container {
  max-width: 1000px;
  margin: 0 auto;
}

/* Input Methods */
.input-methods {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
  align-items: stretch;
}

.input-method-card {
  background: var(--home-surface-solid);
  border: 2px solid var(--border-color);
  border-radius: 14px;
  padding: 1.35rem 1.5rem;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease, background 0.2s ease;
  position: relative;
  display: flex;
  align-items: center;
  gap: 1rem;
  min-height: 108px;
  overflow: hidden;
}

.input-method-card:focus-visible {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--home-focus-ring);
}

.input-method-card:hover:not(.disabled) {
  border-color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px color-mix(in srgb, var(--primary-color) 18%, transparent);
}

.input-method-card.active {
  border-color: var(--primary-color);
  background: var(--home-active-tint);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--primary-color) 25%, transparent);
}

.input-method-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.method-icon {
  width: 3.25rem;
  height: 3.25rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 1.55rem;
  color: var(--primary-color);
  background: color-mix(in srgb, var(--primary-color) 14%, transparent);
}

.method-content {
  flex: 1;
  min-width: 0;
  padding-right: 1.75rem; /* Reserve room for active check icon */
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
  overflow-wrap: anywhere;
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

.panel-surface {
  background: var(--home-panel-bg);
  border: 1px solid var(--home-panel-border);
  border-radius: 16px;
  padding: 1.5rem 1.75rem 1.75rem;
  box-shadow: 0 2px 12px color-mix(in srgb, var(--home-panel-border) 35%, transparent);
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
  border: 2px solid var(--border-color);
  border-radius: 8px;
  padding: 0.75rem;
  font-size: 1rem;
  transition: all 0.2s ease;
  background: var(--home-surface-solid);
  color: var(--text-primary);
}

.input-field:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--home-focus-ring);
  outline: none;
}

.paste-field-wrap {
  margin-top: 0.25rem;
}

.textarea-legal {
  min-height: 220px;
  resize: vertical;
  line-height: 1.55;
  padding-right: 3rem;
  font-size: 0.98rem;
}

.textarea-clear-btn {
  position: absolute;
  top: 0.55rem;
  right: 0.55rem;
  z-index: 2;
  border-radius: 8px;
  padding: 0.25rem 0.45rem;
  line-height: 1;
  opacity: 0.9;
}

.textarea-clear-btn:hover {
  opacity: 1;
}

.char-count-pill {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--home-muted-bg);
  border: 1px solid var(--border-color);
  border-radius: 999px;
  padding: 0.28rem 0.7rem;
}

.input-keyboard-hint {
  margin: 0.65rem 0 0;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
  line-height: 1.4;
}

.input-keyboard-hint-label {
  font-weight: 600;
  color: var(--text-primary);
  margin-right: 0.15rem;
}

.input-keyboard-hint-rest {
  margin-left: 0.1rem;
}

.input-keyboard-hint kbd {
  font-family: ui-monospace, 'Cascadia Code', 'Segoe UI Mono', monospace;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.12rem 0.38rem;
  border-radius: 5px;
  border: 1px solid var(--border-color);
  background: var(--home-muted-bg);
  color: var(--text-primary);
  box-shadow: 0 1px 0 var(--border-color);
}

.input-keyboard-hint .kbd-plus {
  font-size: 0.75rem;
  color: var(--text-secondary);
  user-select: none;
}

.home-url-input-group .input-group-text {
  background: var(--home-muted-bg);
  border-color: var(--border-color);
  color: var(--text-secondary);
}

.home-url-input-group .input-field {
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}

.home-url-input-group .input-group-text {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.url-preview-card {
  padding: 1rem 1.2rem;
  border-radius: 12px;
  border: 1px solid var(--home-panel-border);
  background: var(--home-muted-bg);
}

.url-preview-card-title {
  margin: 0 0 0.65rem 0;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-secondary);
}

.url-preview-card-link {
  color: var(--primary-color);
  text-decoration: none;
  font-weight: 500;
  word-break: break-all;
}

.url-preview-card-link:hover {
  text-decoration: underline;
}

.analyze-status-line {
  font-size: 0.9rem;
  max-width: 28rem;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.45;
}

.analyze-status-line--muted {
  color: var(--text-secondary);
}

.analyze-status-line--ready {
  color: var(--success-color);
  font-weight: 500;
}

.home-file-dropzone {
  cursor: pointer;
  transition: background 0.25s ease, border-color 0.25s ease, transform 0.2s ease;
  background: var(--home-dropzone-bg) !important;
}

.home-file-dropzone:hover:not(.border-danger) {
  background: var(--home-dropzone-hover-bg) !important;
}

.home-file-dropzone.home-file-dropzone--drag {
  background: var(--home-dropzone-drag-bg) !important;
}

.home .file-dropzone.border-primary {
  border-color: var(--primary-color) !important;
}

.home-file-dropzone .file-dropzone-content h5 {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 1.1rem;
}

/* File Drop Zone */
.file-drop-zone {
  border: 3px dashed var(--border-color);
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  background: var(--home-surface-solid);
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
  background: var(--home-muted-bg);
  border: 1px solid var(--border-color);
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
  border-style: dashed;
  transition: all 0.3s ease;
}

.file-dropzone:hover {
  background-color: var(--home-muted-bg);
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
  background: var(--home-surface-solid);
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
  background: var(--home-muted-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
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

/* Ensure SimpleProgress fits nicely when replacing the button */
.analyze-button-container .simple-progress-container {
  margin: 0;
  max-width: 100%;
}

/* Progress Bar Styles */
.progress-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid var(--border-color);
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
  background: color-mix(in srgb, var(--home-surface-solid) 85%, transparent);
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  border: 1px solid var(--border-color);
}

.progress-container {
  margin: 1.5rem 0;
}

.progress {
  background: color-mix(in srgb, var(--home-surface-solid) 88%, transparent);
  border: 2px solid color-mix(in srgb, var(--primary) 35%, var(--border-color));
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.08);
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

/* Enhanced Phase Indicators */
.processing-phases {
  margin-top: 1.5rem;
}

.phase-indicators {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.phase-indicator {
  flex: 1;
  min-width: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem 0.5rem;
  background: color-mix(in srgb, var(--home-surface-solid) 88%, transparent);
  border: 2px solid var(--border-color);
  border-radius: 12px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.phase-indicator i {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  transition: all 0.3s ease;
}

.phase-indicator span {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-align: center;
  transition: all 0.3s ease;
}

.phase-indicator.active {
  border-color: #007bff;
  background: rgba(0, 123, 255, 0.1);
}

.phase-indicator.active i,
.phase-indicator.active span {
  color: #007bff;
}

.phase-indicator.current {
  border-color: #ffc107;
  background: rgba(255, 193, 7, 0.15);
  animation: pulse 2s infinite;
}

.phase-indicator.current i,
.phase-indicator.current span {
  color: #ffc107;
}

.phase-indicator.completed {
  border-color: #28a745;
  background: rgba(40, 167, 69, 0.1);
}

.phase-indicator.completed i,
.phase-indicator.completed span {
  color: #28a745;
}

.phase-indicator.completed i::before {
  content: '\f26b'; /* Bootstrap check-circle icon */
}

.phase-progress {
  position: absolute;
  bottom: 0.25rem;
  right: 0.25rem;
  background: rgba(0, 123, 255, 0.9);
  color: white;
  padding: 0.2rem 0.4rem;
  border-radius: 0.5rem;
  font-size: 0.7rem;
  font-weight: 600;
  min-width: 2rem;
  text-align: center;
}

.phase-indicator.completed .phase-progress {
  background: rgba(40, 167, 69, 0.9);
}

.phase-indicator.current .phase-progress {
  background: rgba(255, 193, 7, 0.9);
  color: #000;
}

@keyframes pulse {
  0%, 100% { 
    transform: scale(1); 
    box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.4);
  }
  50% { 
    transform: scale(1.02); 
    box-shadow: 0 0 0 8px rgba(255, 193, 7, 0);
  }
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
  background: color-mix(in srgb, var(--home-surface-solid) 92%, transparent);
  border-radius: 1rem;
  padding: 1rem;
  text-align: center;
  box-shadow: var(--shadow-light);
  border: 1px solid var(--border-color);
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
  background: var(--home-surface-solid);
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
  background: var(--border-color);
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
  background: var(--home-active-tint);
  border-radius: 0.65rem;
  box-shadow: 0 1.5px 6px rgba(75, 46, 131, 0.06);
  border: 1.2px solid var(--home-panel-border);
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
  color: var(--primary-color);
  margin-bottom: 0.05rem;
}

.stat-label {
  font-size: 0.78rem;
  color: var(--text-secondary);
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

@media (max-width: 1024px) {
  .input-methods {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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
    gap: 1rem;
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

  .input-methods {
    grid-template-columns: 1fr;
    gap: 0.9rem;
  }

  .input-method-card {
    min-height: 96px;
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
  margin-top: 1.5rem;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  padding: 1.25rem 1.4rem;
  background: linear-gradient(135deg, var(--home-active-tint) 0%, var(--home-muted-bg) 100%);
  border-radius: 14px;
  border: 1px solid var(--home-panel-border);
  box-shadow: 0 4px 14px rgba(37, 56, 88, 0.08);
}

.results-heading {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.results-title {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.35rem;
  font-weight: 700;
}

.results-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.results-meta-note {
  margin: 0;
  color: #4b5d78;
  font-size: 0.88rem;
}

.result-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.28rem 0.62rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 600;
  color: #334e74;
  background: #edf4ff;
  border: 1px solid #cfe1ff;
}

.result-chip.chip-error {
  color: #8b1e2d;
  background: #fdecef;
  border-color: #f5c2c8;
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
  .hero-badges {
    justify-content: flex-start;
  }

  .panel-surface {
    padding: 0.9rem;
  }

  .results-header {
    flex-direction: column;
    gap: 1rem;
    text-align: left;
  }
  
  .results-title {
    font-size: 1.25rem;
  }
  
  .new-analysis-btn {
    width: 100%;
    padding: 1rem;
  }
}

/* Progress bar and button animations */
@keyframes progressBar {
  0% { 
    width: 0%; 
    transform: translateX(0); 
  }
  50% { 
    width: 100%; 
    transform: translateX(0); 
  }
  100% { 
    width: 0%; 
    transform: translateX(100%); 
  }
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

@media (prefers-color-scheme: dark) {
  .home {
    --primary-color: #c4a8fc;
    --primary-light: #d4bdfc;
    --primary-dark: #9b7ce8;
    --secondary-color: #1e2228;
    --accent-color: #ff6b35;
    --success-color: #4caf50;
    --warning-color: #ff9800;
    --error-color: #f44336;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --border-color: #3d4451;
    --shadow-light: 0 2px 12px 0 rgba(0, 0, 0, 0.35);
    --shadow-medium: 0 4px 24px 0 rgba(0, 0, 0, 0.45);
    --home-page-bg: #12141a;
    --home-surface: rgba(37, 40, 48, 0.92);
    --home-surface-solid: #252830;
    --home-panel-bg: #2a2d35;
    --home-panel-border: #3d4451;
    --home-muted-bg: #1e2228;
    --home-active-tint: rgba(196, 168, 252, 0.12);
    --home-input-border: rgba(196, 168, 252, 0.22);
    --home-hero-badge-fg: #e9deff;
    --home-hero-badge-bg: rgba(75, 46, 131, 0.35);
    --home-hero-badge-border: rgba(196, 168, 252, 0.35);
    --home-dropzone-bg: #1a1d24;
    --home-dropzone-hover-bg: rgba(196, 168, 252, 0.1);
    --home-dropzone-drag-bg: rgba(196, 168, 252, 0.18);
    --home-focus-ring: color-mix(in srgb, var(--primary-color) 28%, transparent);
  }

  .experimental-banner {
    background: linear-gradient(135deg, #3d3520, #3a3220);
    border-color: #5c4d28;
    color: #fde68a;
  }

  .main-input-area {
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
  }

  .results-header {
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
  }

  .new-analysis-btn {
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.35);
  }

  .features-section {
    background: rgba(0, 0, 0, 0.22);
    border-color: var(--border-color);
  }

  .main-content-wrapper {
    background: transparent;
  }

  .container {
    background: transparent;
  }
}
</style>
