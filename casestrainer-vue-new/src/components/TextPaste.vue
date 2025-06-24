<template>
  <div class="text-paste">
    <div class="card">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">Paste Text</h5>
      </div>
      <div class="card-body">
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
</template>

<script>
import { ref, watch } from 'vue';

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
    }
  },
  setup(props, { emit }) {
    const text = ref(props.initialText);
    const includeContext = ref(false);

    watch(() => props.initialText, (val) => {
      text.value = val;
    });

    const emitAnalyze = () => {
      if (!text.value) return;
      emit('analyze', { text: text.value, options: { includeContext: includeContext.value } });
    };

    return {
      text,
      includeContext,
      emitAnalyze
    };
  }
};
</script>

<style scoped>
.text-paste {
  width: 100%;
}

.form-check-input:checked {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.form-check-input:focus {
  border-color: #86b7fe;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.form-control {
  min-height: 150px;
  font-family: monospace;
  resize: vertical;
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
