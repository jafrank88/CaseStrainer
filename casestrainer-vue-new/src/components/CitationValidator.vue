<template>
  <div class="citation-validator">
    <h2>Validate Citation</h2>
    
    <form @submit.prevent="handleSubmit" class="validator-form">
      <div class="form-group">
        <label for="citation">Enter a legal citation:</label>
        <input
          type="text"
          id="citation"
          v-model="citation"
          placeholder="e.g., 123 U.S. 456"
          required
          class="form-control"
          :disabled="loading"
        >
      </div>
      
      <button type="submit" class="btn btn-primary" :disabled="loading">
        <span v-if="loading">Validating...</span>
        <span v-else>Validate</span>
      </button>
    </form>
    
    <div v-if="error" class="alert alert-error">
      {{ error }}
    </div>
    
    <div v-if="result" class="result-container">
      <h3>Validation Result</h3>
      <div class="result-details">
        <p><strong>Citation:</strong> {{ result.citation }}</p>
        <p><strong>Status:</strong> 
          <span :class="['status-badge', result.isValid ? 'valid' : 'invalid']">
            {{ result.isValid ? 'Valid' : 'Invalid' }}
          </span>
        </p>
        <p v-if="result.message">{{ result.message }}</p>
        
        <div v-if="result.metadata" class="metadata">
          <h4>Metadata:</h4>
          <pre>{{ JSON.stringify(result.metadata, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useCitationsStore } from '@/store/citations';

export default {
  name: 'CitationValidator',
  
  setup() {
    const citationsStore = useCitationsStore();
    const citation = ref('');
    const result = ref(null);
    const loading = ref(false);
    const error = ref(null);
    
    const handleSubmit = async () => {
      if (!citation.value.trim()) return;
      
      loading.value = true;
      error.value = null;
      result.value = null;
      
      try {
        await citationsStore.validateCitation(citation.value);
        result.value = {
          citation: citation.value,
          isValid: citationsStore.currentCitation?.isValid || false,
          message: citationsStore.currentCitation?.message || '',
          metadata: citationsStore.currentCitation?.metadata || null
        };
      } catch (err) {
        error.value = err.message || 'An error occurred while validating the citation';
        console.error('Validation error:', err);
      } finally {
        loading.value = false;
      }
    };
    
    return {
      citation,
      result,
      loading,
      error,
      handleSubmit
    };
  }
};
</script>

<style scoped>
.citation-validator {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.validator-form {
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-control {
  width: 100%;
  padding: 0.75rem;
  font-size: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  transition: border-color 0.2s;
}

.form-control:focus {
  border-color: #42b983;
  outline: none;
  box-shadow: 0 0 0 2px rgba(66, 185, 131, 0.2);
}

.btn {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 500;
  color: #fff;
  background-color: #42b983;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn:hover {
  background-color: #3aa876;
}

.btn:disabled {
  background-color: #a0d9b8;
  cursor: not-allowed;
}

.alert {
  padding: 1rem;
  margin-bottom: 1.5rem;
  border-radius: 4px;
}

.alert-error {
  background-color: #ffebee;
  color: #c62828;
  border-left: 4px solid #ef5350;
}

.result-container {
  margin-top: 2rem;
  padding: 1.5rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.result-details {
  margin-top: 1rem;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-badge.valid {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.status-badge.invalid {
  background-color: #ffebee;
  color: #c62828;
}

.metadata {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #fff;
  border: 1px solid #eee;
  border-radius: 4px;
  overflow-x: auto;
}

pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

h2, h3, h4 {
  color: #2c3e50;
  margin-top: 0;
}

h2 {
  margin-bottom: 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #eee;
}

h3 {
  margin-bottom: 1rem;
}

h4 {
  margin-bottom: 0.5rem;
}
</style>
