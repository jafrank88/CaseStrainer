<template>
  <div class="text-paste">
    <div class="card">
      <div class="card-header" :class="isSingleCitation ? 'bg-success text-white' : 'bg-primary text-white'">
        <h5 class="mb-0">{{ isSingleCitation ? 'Single Citation Validation' : 'Paste Text' }}</h5>
      </div>
      <div class="card-body">
        <!-- Single Citation Mode -->
        <div v-if="isSingleCitation" class="single-citation-mode">
          <div class="mb-3">
            <label for="citationInput" class="form-label">
              Enter a legal citation to validate
            </label>
            <input
              id="citationInput"
              type="text"
              class="form-control form-control-lg"
              v-model="citationText"
              placeholder="e.g., 181 Wash.2d 391, 333 P.3d 440"
              :disabled="isAnalyzing"
              @keyup.enter="emitAnalyze"
            />
            <div class="form-text">
              Enter a single citation in standard legal format
            </div>
          </div>
          <button 
            class="btn btn-success btn-lg" 
            @click="emitAnalyze"
            :disabled="!citationText || isAnalyzing"
          >
            <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            {{ isAnalyzing ? 'Validating...' : 'Validate Citation' }}
          </button>
        </div>

        <!-- Multi-Text Mode -->
        <div v-else class="multi-text-mode">
          <div class="mb-3">
            <label for="textInput" class="form-label">Paste your legal text to analyze for citations</label>
            <textarea
              id="textInput"
              class="form-control"
              v-model="text"
              rows="10"
              placeholder="Paste your legal document text here..."
              :disabled="isAnalyzing"
            ></textarea>
          </div>
          <div class="form-check form-switch mb-3">
            <input 
              class="form-check-input" 
              type="checkbox" 
              id="includeContext" 
              v-model="includeContext"
            >
            <label class="form-check-label" for="includeContext">Include context around citations</label>
          </div>
          <button 
            class="btn btn-primary" 
            @click="emitAnalyze"
            :disabled="!text || isAnalyzing"
          >
            <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            {{ isAnalyzing ? 'Analyzing...' : 'Analyze Text' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, computed } from 'vue';

export default {
  name: 'TextPaste',
  emits: ['analyze'],
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
      default: 'multi', // 'single' or 'multi'
      validator: (value) => ['single', 'multi'].includes(value)
    }
  },
  setup(props, { emit }) {
    const text = ref(props.initialText);
    const citationText = ref(props.initialText);
    const includeContext = ref(false);

    // Determine if we're in single citation mode
    const isSingleCitation = computed(() => props.mode === 'single');

    // Watch for changes in initialText
    watch(() => props.initialText, (val) => {
      text.value = val;
      citationText.value = val;
    });

    const emitAnalyze = () => {
      if (isSingleCitation.value) {
        // In single citation mode, use the citation text as the input
        if (!citationText.value) return;
        emit('analyze', { 
          text: citationText.value, 
          options: { 
            includeContext: includeContext.value,
            mode: 'single',
            originalCitation: citationText.value
          } 
        });
      } else {
        // In multi-text mode, use the full text
        if (!text.value) return;
        emit('analyze', { 
          text: text.value, 
          options: { 
            includeContext: includeContext.value,
            mode: 'multi'
          } 
        });
      }
    };

    return {
      text,
      citationText,
      includeContext,
      isSingleCitation,
      emitAnalyze
    };
  }
};
</script>

<style scoped>
.text-paste {
  width: 100%;
}

.single-citation-mode .form-control {
  font-family: 'Courier New', monospace;
  font-size: 1.1rem;
}

.multi-text-mode .form-control {
  min-height: 150px;
  font-family: monospace;
  resize: vertical;
}

.form-check-input:checked {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.form-check-input:focus {
  border-color: #86b7fe;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.form-control:disabled {
  background-color: #e9ecef;
  cursor: not-allowed;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .card {
    margin-bottom: 1rem;
  }
  
  .btn {
    width: 100%;
    margin-top: 0.5rem;
  }
  
  .form-control {
    font-size: 16px; /* Prevent zoom on mobile */
  }
}
</style>
