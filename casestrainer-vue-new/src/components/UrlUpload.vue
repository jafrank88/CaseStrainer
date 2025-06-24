<template>
  <div class="url-upload">
    <div class="card">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">Analyze Web Content</h5>
      </div>
      <div class="card-body">
        <div class="mb-3">
          <label for="urlInput" class="form-label">Enter a URL to analyze for citations</label>
          <div class="input-group">
            <span class="input-group-text"><i class="bi bi-link-45deg"></i></span>
            <input
              type="url"
              id="urlInput"
              class="form-control"
              v-model="url"
              placeholder="https://example.com/legal-document"
              :disabled="isAnalyzing"
              @keyup.enter="emitAnalyze"
            >
            <button 
              class="btn btn-primary" 
              @click="emitAnalyze"
              :disabled="!isValidUrl || isAnalyzing"
            >
              <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              {{ isAnalyzing ? 'Analyzing...' : 'Analyze' }}
            </button>
          </div>
          <div class="form-text">Enter a valid URL to a web page containing legal citations</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';

export default {
  name: 'UrlUpload',
  emits: ['analyze'],
  props: {
    isAnalyzing: {
      type: Boolean,
      default: false
    }
  },
  setup(props, { emit }) {
    const url = ref('');
    const isValidUrl = computed(() => {
      try {
        new URL(url.value);
        return true;
      } catch {
        return false;
      }
    });
    const emitAnalyze = () => {
      if (!isValidUrl.value) return;
      emit('analyze', { url: url.value });
    };
    return {
      url,
      isValidUrl,
      emitAnalyze
    };
  }
};
</script>

<style scoped>
.url-upload {
  width: 100%;
}

.input-group-text {
  background-color: #f8f9fa;
  border-right: none;
}

.input-group .form-control {
  border-left: none;
}

.input-group .form-control:focus {
  border-color: #86b7fe;
  box-shadow: none;
}

.input-group .form-control:focus + .input-group-text {
  border-color: #86b7fe;
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
  
  .input-group {
    flex-direction: column;
  }
  
  .input-group-text {
    border-radius: 0.25rem 0.25rem 0 0 !important;
    border-right: 1px solid #ced4da;
    border-bottom: none;
  }
  
  .input-group .form-control {
    border-radius: 0 0 0.25rem 0.25rem !important;
    border-left: 1px solid #ced4da;
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
