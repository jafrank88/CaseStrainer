<template>
  <div class="modern-text-paste">
    <div class="paste-card">
      <div class="paste-header" :class="headerClass">
        <div class="header-icon">
          <i :class="headerIcon"></i>
        </div>
        <h3 class="header-title">{{ headerTitle }}</h3>
        <p class="header-subtitle">{{ headerSubtitle }}</p>
      </div>
      
      <div class="paste-body">
        <!-- Mode Toggle -->
        <div class="mode-toggle-section">
          <div class="mode-toggle">
            <button 
              :class="['mode-btn', { active: !isSingleCitation }]"
              @click="switchMode('multi')"
              :disabled="isAnalyzing"
            >
              <i class="bi bi-file-text me-2"></i>
              <span>Multi-Text Analysis</span>
            </button>
            <button 
              :class="['mode-btn', { active: isSingleCitation }]"
              @click="switchMode('single')"
              :disabled="isAnalyzing"
            >
              <i class="bi bi-search me-2"></i>
              <span>Single Citation</span>
            </button>
          </div>
        </div>

        <!-- Single Citation Mode -->
        <div v-if="isSingleCitation" class="input-section single-citation-mode">
          <div class="input-container">
            <label for="citationInput" class="form-label">
              <i class="bi bi-bookmark me-2"></i>
              Legal Citation
            </label>
            
            <div class="citation-input-wrapper">
              <input
                id="citationInput"
                type="text"
                class="citation-input"
                v-model="citationText"
                placeholder="e.g., 181 Wash.2d 391, 333 P.3d 440 (2014)"
                :disabled="isAnalyzing"
                @keyup.enter="emitAnalyze"
                @input="validateCitation"
                :class="{
                  'valid': isValidCitation && citationText.length > 0,
                  'analyzing': isAnalyzing
                }"
              />
              <div v-if="isValidCitation && citationText.length > 0" class="input-status valid">
                <i class="bi bi-check-circle-fill"></i>
              </div>
            </div>
            
            <!-- Citation Format Examples -->
            <div class="citation-examples">
              <div class="examples-header">
                <i class="bi bi-lightbulb me-2"></i>
                <span>Format Examples</span>
              </div>
              <div class="examples-list">
                <button 
                  v-for="example in citationExamples" 
                  :key="example.citation"
                  @click="setCitationExample(example.citation)"
                  class="example-citation"
                  :disabled="isAnalyzing"
                >
                  <div class="example-text">{{ example.citation }}</div>
                  <div class="example-type">{{ example.type }}</div>
                </button>
              </div>
            </div>
            
            <!-- Citation Analysis Preview -->
            <div v-if="citationAnalysis" class="citation-preview">
              <h6 class="preview-title">
                <i class="bi bi-eye me-2"></i>
                Citation Preview
              </h6>
              <div class="preview-content">
                <div class="preview-item">
                  <span class="preview-label">Volume:</span>
                  <span class="preview-value">{{ citationAnalysis.volume }}</span>
                </div>
                <div class="preview-item">
                  <span class="preview-label">Reporter:</span>
                  <span class="preview-value">{{ citationAnalysis.reporter }}</span>
                </div>
                <div class="preview-item">
                  <span class="preview-label">Page:</span>
                  <span class="preview-value">{{ citationAnalysis.page }}</span>
                </div>
                <div v-if="citationAnalysis.year" class="preview-item">
                  <span class="preview-label">Year:</span>
                  <span class="preview-value">{{ citationAnalysis.year }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Multi-Text Mode -->
        <div v-else class="input-section multi-text-mode">
          <div class="input-container">
            <label for="textInput" class="form-label">
              <i class="bi bi-file-text me-2"></i>
              Legal Document Text
            </label>
            
            <div class="textarea-wrapper">
              <textarea
                id="textInput"
                class="text-input"
                v-model="text"
                placeholder="Paste your legal document text here for comprehensive citation analysis..."
                :disabled="isAnalyzing"
                @input="analyzeTextContent"
                :class="{ 'analyzing': isAnalyzing }"
              ></textarea>
              
              <!-- Text Stats Overlay -->
              <div v-if="textStats.wordCount > 0" class="text-stats">
                <div class="stat-item">
                  <i class="bi bi-fonts"></i>
                  <span>{{ textStats.wordCount.toLocaleString() }} words</span>
                </div>
                <div class="stat-item">
                  <i class="bi bi-bookmark"></i>
                  <span>{{ textStats.estimatedCitations }} citations</span>
                </div>
                <div class="stat-item">
                  <i class="bi bi-calendar3"></i>
                  <span>{{ textStats.uniqueYears }} years</span>
                </div>
              </div>
            </div>
            
            <!-- Text Quality Indicator -->
            <div v-if="textStats.wordCount > 0" class="quality-indicator">
              <div class="quality-header">
                <span class="quality-label">Content Quality</span>
                <span :class="['quality-score', qualityScoreClass]">{{ qualityScore }}%</span>
              </div>
              <div class="quality-bar">
                <div 
                  :class="['quality-fill', qualityScoreClass]" 
                  :style="{ width: qualityScore + '%' }"
                ></div>
              </div>
              <div class="quality-details">
                <div class="quality-metric">
                  <span class="metric-label">Length:</span>
                  <span class="metric-value">{{ getLengthScore() }}/30</span>
                </div>
                <div class="quality-metric">
                  <span class="metric-label">Citations:</span>
                  <span class="metric-value">{{ getCitationScore() }}/40</span>
                </div>
                <div class="quality-metric">
                  <span class="metric-label">Diversity:</span>
                  <span class="metric-value">{{ getDiversityScore() }}/30</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Analysis Options -->
        <div class="options-section">
          <h6 class="options-title">
            <i class="bi bi-sliders me-2"></i>
            Analysis Options
          </h6>
          <div class="options-grid">
            <label class="option-item">
              <input 
                type="checkbox" 
                v-model="includeContext"
                :disabled="isAnalyzing"
              >
              <div class="option-content">
                <div class="option-icon">
                  <i class="bi bi-text-paragraph"></i>
                </div>
                <div class="option-text">
                  <div class="option-title">Include Context</div>
                  <div class="option-description">Show surrounding text around citations</div>
                </div>
              </div>
            </label>
            
            <label class="option-item">
              <input 
                type="checkbox" 
                v-model="deepAnalysis"
                :disabled="isAnalyzing"
              >
              <div class="option-content">
                <div class="option-icon">
                  <i class="bi bi-search"></i>
                </div>
                <div class="option-text">
                  <div class="option-title">Deep Analysis</div>
                  <div class="option-description">Comprehensive citation validation</div>
                </div>
              </div>
            </label>
            
            <label class="option-item">
              <input 
                type="checkbox" 
                v-model="highlightErrors"
                :disabled="isAnalyzing"
              >
              <div class="option-content">
                <div class="option-icon">
                  <i class="bi bi-exclamation-triangle"></i>
                </div>
                <div class="option-text">
                  <div class="option-title">Highlight Errors</div>
                  <div class="option-description">Mark potential citation issues</div>
                </div>
              </div>
            </label>
          </div>
        </div>
        
        <!-- Analyze Button -->
        <div class="analyze-section">
          <button 
            :class="['analyze-btn', { 'disabled': !canAnalyze || isAnalyzing }]"
            @click="emitAnalyze"
            :disabled="!canAnalyze || isAnalyzing"
          >
            <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2"></span>
            <i v-else :class="analyzeButtonIcon + ' me-2'"></i>
            {{ analyzeButtonText }}
          </button>
          
          <div v-if="canAnalyze && !isAnalyzing" class="analyze-info">
            <div class="info-text">
              <i class="bi bi-info-circle me-1"></i>
              {{ getAnalyzeInfoText() }}
            </div>
          </div>
        </div>
        
        <!-- Analysis Progress -->
        <div v-if="isAnalyzing" class="analysis-progress">
          <div class="progress-header">
            <h6 class="progress-title">
              <i class="bi bi-gear-fill spinning me-2"></i>
              {{ isSingleCitation ? 'Validating Citation' : 'Analyzing Text' }}
            </h6>
            <div class="progress-description">
              {{ isSingleCitation ? 'Checking citation format and validity...' : 'Processing text and extracting citations...' }}
            </div>
          </div>
          
          <div class="progress-steps">
            <div class="step" :class="{ active: progressStep >= 1 }">
              <i class="bi bi-file-text"></i>
              <span>{{ isSingleCitation ? 'Parsing' : 'Reading' }}</span>
            </div>
            <div class="step" :class="{ active: progressStep >= 2 }">
              <i class="bi bi-search"></i>
              <span>{{ isSingleCitation ? 'Validating' : 'Extracting' }}</span>
            </div>
            <div class="step" :class="{ active: progressStep >= 3 }">
              <i class="bi bi-shield-check"></i>
              <span>{{ isSingleCitation ? 'Verifying' : 'Validating' }}</span>
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
  name: 'ModernTextPaste',
  emits: ['analyze', 'mode-change'],
  props: {
    isAnalyzing: {
      type: Boolean,
      default: false
    },
    initialText: {
      type: String,
      default: ''
    },
    mode: {
      type: String,
      default: 'multi',
      validator: (value) => ['single', 'multi'].includes(value)
    }
  },
  setup(props, { emit }) {
    const text = ref(props.initialText);
    const citationText = ref(props.initialText);
    const includeContext = ref(false);
    const deepAnalysis = ref(false);
    const highlightErrors = ref(true);
    const progressStep = ref(1);
    const currentMode = ref(props.mode);
    
    // Text analysis state
    const textStats = ref({
      wordCount: 0,
      estimatedCitations: 0,
      uniqueYears: 0,
      characterCount: 0
    });
    
    const citationAnalysis = ref(null);
    
    // Citation examples
    const citationExamples = ref([
      {
        citation: "181 Wash.2d 391, 333 P.3d 440 (2014)",
        type: "Washington Supreme Court"
      },
      {
        citation: "123 Wn. App. 456, 789 P.2d 123 (2020)",
        type: "Washington Court of Appeals"
      },
      {
        citation: "555 U.S. 123 (2019)",
        type: "U.S. Supreme Court"
      },
      {
        citation: "891 F.3d 234 (9th Cir. 2018)",
        type: "Federal Circuit Court"
      }
    ]);
    
    // Computed properties
    const isSingleCitation = computed(() => currentMode.value === 'single');
    
    const headerClass = computed(() => 
      isSingleCitation.value ? 'header-single' : 'header-multi'
    );
    
    const headerIcon = computed(() => 
      isSingleCitation.value ? 'bi bi-search' : 'bi bi-file-text'
    );
    
    const headerTitle = computed(() => 
      isSingleCitation.value ? 'Single Citation Validator' : 'Text Citation Analysis'
    );
    
    const headerSubtitle = computed(() => 
      isSingleCitation.value 
        ? 'Validate and verify individual legal citations'
        : 'Analyze documents for comprehensive citation validation'
    );
    
    const isValidCitation = computed(() => {
      if (!citationText.value) return false;
      // Basic citation pattern matching
      const patterns = [
        /\d+\s+[A-Z][a-z]*\.?\s*(?:2d|3d)?\s+\d+/,
        /\d+\s+[A-Z]\.?\s*\d*\s+\d+/,
        /\d+\s+U\.?S\.?\s+\d+/
      ];
      return patterns.some(pattern => pattern.test(citationText.value));
    });
    
    const qualityScore = computed(() => {
      if (textStats.value.wordCount === 0) return 0;
      return Math.min(100, getLengthScore() + getCitationScore() + getDiversityScore());
    });
    
    const qualityScoreClass = computed(() => {
      const score = qualityScore.value;
      if (score >= 80) return 'excellent';
      if (score >= 60) return 'good';
      if (score >= 40) return 'fair';
      return 'poor';
    });
    
    const canAnalyze = computed(() => {
      return isSingleCitation.value 
        ? citationText.value.trim().length > 0
        : text.value.trim().length > 10;
    });
    
    const analyzeButtonIcon = computed(() => 
      isSingleCitation.value ? 'bi bi-shield-check' : 'bi bi-search'
    );
    
    const analyzeButtonText = computed(() => {
      if (isAnalyzing.value) {
        return isSingleCitation.value ? 'Validating Citation...' : 'Analyzing Text...';
      }
      if (!canAnalyze.value) {
        return isSingleCitation.value ? 'Enter Citation' : 'Enter Text';
      }
      return isSingleCitation.value ? 'Validate Citation' : 'Analyze Text';
    });
    
    // Methods
    const switchMode = (mode) => {
      currentMode.value = mode;
      emit('mode-change', mode);
    };
    
    const validateCitation = () => {
      if (!citationText.value) {
        citationAnalysis.value = null;
        return;
      }
      
      // Parse citation components
      const citationPattern = /(\d+)\s+([A-Z][a-z]*\.?\s*(?:2d|3d)?)\s+(\d+)(?:.*?\((\d{4})\))?/;
      const match = citationText.value.match(citationPattern);
      
      if (match) {
        citationAnalysis.value = {
          volume: match[1],
          reporter: match[2],
          page: match[3],
          year: match[4] || null
        };
      } else {
        citationAnalysis.value = null;
      }
    };
    
    const setCitationExample = (example) => {
      citationText.value = example;
      validateCitation();
    };
    
    const analyzeTextContent = () => {
      const textValue = text.value.trim();
      
      if (!textValue) {
        textStats.value = { wordCount: 0, estimatedCitations: 0, uniqueYears: 0, characterCount: 0 };
        return;
      }
      
      // Calculate word count
      const words = textValue.split(/\s+/).filter(word => word.length > 0);
      const wordCount = words.length;
      
      // Estimate citations
      const citationPatterns = [
        /\d+\s+[A-Z][a-z]*\.?\s*(?:2d|3d)?\s+\d+/g,
        /\d+\s+U\.?S\.?\s+\d+/g,
        /\d+\s+F\.?\s*(?:2d|3d)?\s+\d+/g
      ];
      
      let citationCount = 0;
      citationPatterns.forEach(pattern => {
        const matches = textValue.match(pattern);
        if (matches) citationCount += matches.length;
      });
      
      // Count unique years
      const yearMatches = textValue.match(/\b(19|20)\d{2}\b/g);
      const uniqueYears = yearMatches ? new Set(yearMatches).size : 0;
      
      textStats.value = {
        wordCount,
        estimatedCitations: citationCount,
        uniqueYears,
        characterCount: textValue.length
      };
    };
    
    const getLengthScore = () => {
      return Math.min(30, Math.floor((textStats.value.wordCount / 200) * 30));
    };
    
    const getCitationScore = () => {
      const density = textStats.value.estimatedCitations / Math.max(1, textStats.value.wordCount / 100);
      return Math.min(40, Math.floor(density * 10));
    };
    
    const getDiversityScore = () => {
      return Math.min(30, textStats.value.uniqueYears * 5);
    };
    
    const getAnalyzeInfoText = () => {
      if (isSingleCitation.value) {
        return 'Citation will be validated against legal databases';
      }
      const words = textStats.value.wordCount;
      const citations = textStats.value.estimatedCitations;
      return `${words.toLocaleString()} words • ${citations} potential citations detected`;
    };
    
    const emitAnalyze = () => {
      if (!canAnalyze.value || isAnalyzing.value) return;
      
      const analysisData = {
        text: isSingleCitation.value ? citationText.value : text.value,
        options: {
          includeContext: includeContext.value,
          deepAnalysis: deepAnalysis.value,
          highlightErrors: highlightErrors.value,
          mode: isSingleCitation.value ? 'single' : 'multi',
          ...(isSingleCitation.value && { originalCitation: citationText.value })
        },
        type: 'text'
      };
      
      emit('analyze', analysisData);
    };
    
    // Watch for prop changes
    watch(() => props.initialText, (val) => {
      text.value = val;
      citationText.value = val;
      if (val) {
        analyzeTextContent();
        validateCitation();
      }
    });
    
    watch(() => props.mode, (val) => {
      currentMode.value = val;
    });
    
    // Watch for analysis state
    watch(() => props.isAnalyzing, (newVal) => {
      if (newVal) {
        progressStep.value = 1;
        const interval = setInterval(() => {
          if (progressStep.value < 4 && props.isAnalyzing) {
            progressStep.value++;
          } else {
            clearInterval(interval);
          }
        }, 1000);
      }
    });
    
    // Initialize
    if (props.initialText) {
      analyzeTextContent();
      validateCitation();
    }
    
    return {
      text,
      citationText,
      includeContext,
      deepAnalysis,
      highlightErrors,
      progressStep,
      currentMode,
      textStats,
      citationAnalysis,
      citationExamples,
      isSingleCitation,
      headerClass,
      headerIcon,
      headerTitle,
      headerSubtitle,
      isValidCitation,
      qualityScore,
      qualityScoreClass,
      canAnalyze,
      analyzeButtonIcon,
      analyzeButtonText,
      switchMode,
      validateCitation,
      setCitationExample,
      analyzeTextContent,
      getLengthScore,
      getCitationScore,
      getDiversityScore,
      getAnalyzeInfoText,
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
  --warning-color: #ff9800;
  --error-color: #f44336;
  --text-primary: #212529;
  --text-secondary: #6c757d;
  --border-color: #e9ecef;
  --background-light: #f8f9fa;
  --shadow-light: 0 2px 12px 0 rgba(60, 72, 88, 0.08);
  --shadow-medium: 0 4px 24px 0 rgba(60, 72, 88, 0.12);
}

.modern-text-paste {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
}

.paste-card {
  background: white;
  border-radius: 2rem;
  box-shadow: var(--shadow-medium);
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s ease;
}

.paste-header {
  color: white;
  padding: 2rem;
  text-align: center;
  position: relative;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
}

.paste-header.header-single {
  background: linear-gradient(135deg, var(--success-color), #66bb6a);
}

.paste-header::before {
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

.paste-body {
  padding: 2.5rem;
}

.mode-toggle-section {
  margin-bottom: 2rem;
}

.mode-toggle {
  display: flex;
  background: var(--background-light);
  border-radius: 1.5rem;
  padding: 0.5rem;
  gap: 0.5rem;
}

.mode-btn {
  flex: 1;
  padding: 1rem 1.5rem;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-weight: 600;
  border-radius: 1rem;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.mode-btn.active {
  background: white;
  color: var(--primary-color);
  box-shadow: var(--shadow-light);
  transform: translateY(-1px);
}

.mode-btn:hover:not(.active):not(:disabled) {
  background: rgba(255, 255, 255, 0.7);
  color: var(--text-primary);
}

.mode-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-section {
  margin-bottom: 2rem;
}

.input-container {
  background: #f8fafe;
  border-radius: 1.5rem;
  padding: 2rem;
  border: 1px solid #e3f2fd;
  position: relative;
}

.input-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--primary-color), var(--primary-light));
  border-radius: 1.5rem 1.5rem 0 0;
}

.form-label {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
  font-size: 1.05rem;
  display: flex;
  align-items: center;
}

.citation-input-wrapper {
  position: relative;
  margin-bottom: 1.5rem;
}

.citation-input {
  width: 100%;
  padding: 1.25rem 1.5rem;
  border: 2px solid var(--border-color);
  border-radius: 1rem;
  font-size: 1.2rem;
  font-family: 'Courier New', monospace;
  font-weight: 500;
  transition: all 0.3s ease;
  background: white;
  color: var(--text-primary);
}

.citation-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 0.2rem rgba(25, 118, 210, 0.15);
}

.citation-input.valid {
  border-color: var(--success-color);
  padding-right: 3.5rem;
}

.citation-input.analyzing {
  background: var(--background-light);
  pointer-events: none;
}

.input-status {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.5rem;
}

.input-status.valid {
  color: var(--success-color);
}

.textarea-wrapper {
  position: relative;
  margin-bottom: 1.5rem;
}

.text-input {
  width: 100%;
  min-height: 250px;
  padding: 1.5rem;
  border: 2px solid var(--border-color);
  border-radius: 1rem;
  font-size: 1.05rem;
  font-family: 'Consolas', 'Monaco', monospace;
  line-height: 1.6;
  resize: vertical;
  transition: all 0.3s ease;
  background: white;
  color: var(--text-primary);
}

.text-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 0.2rem rgba(25, 118, 210, 0.15);
}

.text-input.analyzing {
  background: var(--background-light);
  pointer-events: none;
}

.text-stats {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 0.75rem;
  padding: 0.75rem;
  box-shadow: var(--shadow-light);
  display: flex;
  gap: 1rem;
  border: 1px solid var(--border-color);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.stat-item i {
  color: var(--primary-color);
}

.citation-examples {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid var(--border-color);
  margin-bottom: 1.5rem;
}

.examples-header {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  font-size: 0.95rem;
}

.examples-list {
  display: grid;
  gap: 0.75rem;
}

.example-citation {
  padding: 1rem;
  border: 2px solid var(--border-color);
  border-radius: 0.75rem;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
  width: 100%;
}

.example-citation:hover:not(:disabled) {
  border-color: var(--primary-color);
  background: rgba(25, 118, 210, 0.05);
  transform: translateY(-1px);
}

.example-citation:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.example-text {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.example-type {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.citation-preview {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid var(--border-color);
}

.preview-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  font-size: 0.95rem;
}

.preview-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

.preview-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.preview-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.preview-value {
  font-weight: 600;
  color: var(--primary-color);
  font-family: 'Courier New', monospace;
}

.quality-indicator {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid var(--border-color);
}

.quality-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.quality-label {
  font-weight: 600;
  color: var(--text-primary);
}

.quality-score {
  font-weight: 700;
  font-size: 1.1rem;
}

.quality-score.excellent { color: var(--success-color); }
.quality-score.good { color: var(--primary-color); }
.quality-score.fair { color: var(--warning-color); }
.quality-score.poor { color: var(--error-color); }

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

.quality-fill.excellent { background: var(--success-color); }
.quality-fill.good { background: var(--primary-color); }
.quality-fill.fair { background: var(--warning-color); }
.quality-fill.poor { background: var(--error-color); }

.quality-details {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.quality-metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  flex: 1;
}

.metric-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.metric-value {
  font-weight: 600;
  color: var(--primary-color);
  font-size: 0.9rem;
}

.options-section {
  background: var(--background-light);
  border-radius: 1.5rem;
  padding: 1.5rem;
  margin-bottom: 2rem;
  border: 1px solid var(--border-color);
}

.options-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  font-size: 1rem;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 1rem;
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

.option-item:has(input:checked) {
  border-color: var(--primary-color);
  background: rgba(25, 118, 210, 0.05);
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
  flex-shrink: 0;
}

.option-text {
  flex: 1;
}

.option-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
  font-size: 0.95rem;
}

.option-description {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.analyze-section {
  margin-bottom: 2rem;
}

.analyze-btn {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  border: none;
  border-radius: 1.5rem;
  padding: 1.25rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
  box-shadow: 0 6px 20px rgba(25, 118, 210, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  margin-bottom: 1rem;
}

.analyze-btn:hover:not(.disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(25, 118, 210, 0.4);
}

.analyze-btn.disabled {
  background: var(--text-secondary);
  box-shadow: none;
  cursor: not-allowed;
  transform: none;
}

.analyze-info {
  text-align: center;
  padding: 1rem;
  background: var(--background-light);
  border-radius: 0.75rem;
  border: 1px solid var(--border-color);
}

.info-text {
  color: var(--text-secondary);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
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

.progress-description {
  color: var(--text-secondary);
  font-size: 0.95rem;
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

/* Responsive Design */
@media (max-width: 768px) {
  .paste-card {
    margin: 0 1rem;
    border-radius: 1.5rem;
  }
  
  .paste-header {
    padding: 1.5rem;
  }
  
  .paste-body {
    padding: 1.5rem;
  }
  
  .mode-toggle {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .mode-btn {
    padding: 0.75rem 1rem;
  }
  
  .input-container {
    padding: 1.5rem;
  }
  
  .citation-input {
    font-size: 16px; /* Prevent zoom on mobile */
    padding: 1rem;
  }
  
  .text-input {
    font-size: 16px; /* Prevent zoom on mobile */
    min-height: 200px;
  }
  
  .text-stats {
    position: static;
    margin-top: 1rem;
    justify-content: center;
  }
  
  .options-grid {
    grid-template-columns: 1fr;
  }
  
  .quality-details {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .progress-steps {
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .step {
    min-width: calc(50% - 0.25rem);
  }
  
  .preview-content {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 480px) {
  .header-title {
    font-size: 1.5rem;
  }
  
  .header-subtitle {
    font-size: 1rem;
  }
  
  .step {
    min-width: 100%;
    margin-bottom: 0.5rem;
  }
  
  .preview-content {
    grid-template-columns: 1fr;
  }
  
  .examples-list {
    gap: 0.5rem;
  }
  
  .analyze-btn {
    padding: 1rem 1.5rem;
    font-size: 1rem;
  }
}

/* Focus styles for accessibility */
.mode-btn:focus,
.example-citation:focus,
.option-item:focus,
.analyze-btn:focus,
.citation-input:focus,
.text-input:focus {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

/* Loading animations */
.analyzing .citation-input,
.analyzing .text-input {
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

/* Step activation animation */
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

/* Enhanced interactions */
.citation-input:valid {
  border-color: var(--success-color);
}

.citation-input:invalid:not(:placeholder-shown) {
  border-color: var(--error-color);
}

/* Smooth transitions for all interactive elements */
* {
  transition: color 0.2s ease, background-color 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}
</style>