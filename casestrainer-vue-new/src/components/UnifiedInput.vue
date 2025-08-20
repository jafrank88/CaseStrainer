<template>
  <div class="unified-input">
    <!-- Tab Navigation -->
    <ul class="nav nav-tabs mb-4" id="inputTabs" role="tablist">
      <li class="nav-item" role="presentation">
        <button class="nav-link" :class="{ active: activeTab === 'file' }" 
                @click="activeTab = 'file'" type="button">
          <i class="bi bi-upload me-2"></i>File Upload
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" :class="{ active: activeTab === 'text' }" 
                @click="activeTab = 'text'" type="button">
          <i class="bi bi-text-paragraph me-2"></i>Paste Text
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" :class="{ active: activeTab === 'url' }" 
                @click="activeTab = 'url'" type="button">
          <i class="bi bi-link-45deg me-2"></i>Enter URL
        </button>
      </li>
    </ul>

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- File Upload Tab -->
      <div v-if="activeTab === 'file'" class="tab-pane fade show active">
        <FileUpload 
          @analyze="handleAnalyze"
          :is-loading="isLoading"
          ref="fileUpload"
        />
      </div>

      <!-- Text Input Tab -->
      <div v-if="activeTab === 'text'" class="tab-pane fade show active">
        <TextPaste 
          @analyze="handleAnalyze"
          :is-loading="isLoading"
          ref="textPaste"
        />
      </div>

      <!-- URL Input Tab -->
      <div v-if="activeTab === 'url'" class="tab-pane fade show active">
        <div class="url-input-container">
          <div class="input-group mb-3">
            <span class="input-group-text">
              <i class="bi bi-link-45deg"></i>
            </span>
            <input 
              type="url" 
              class="form-control" 
              v-model="url" 
              placeholder="Enter URL to analyze"
              :disabled="isLoading"
              @keyup.enter="analyzeUrl"
            >
            <button 
              class="btn btn-primary" 
              type="button"
              @click="analyzeUrl"
              :disabled="!isValidUrl || isLoading"
            >
              <span v-if="isLoading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              <span v-else><i class="bi bi-search me-2"></i>Analyze</span>
            </button>
          </div>
          <small class="text-muted">Enter a valid URL to analyze its content</small>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, defineEmits, defineExpose } from 'vue';
import FileUpload from './FileUpload.vue';
import TextPaste from './TextPaste.vue';

// Define emits
const emit = defineEmits(['analyze']);

// Component state
const activeTab = ref('file');
const isLoading = ref(false);
const url = ref('');

// Refs for child components
const fileUpload = ref(null);
const textPaste = ref(null);

// Computed property to validate URL
const isValidUrl = computed(() => {
  try {
    new URL(url.value);
    return true;
  } catch (e) {
    return false;
  }
});

// Handle analyze event from child components
const handleAnalyze = async (data) => {
  try {
    isLoading.value = true;
    emit('analyze', data);
  } catch (error) {
    console.error('Error during analysis:', error);
  } finally {
    isLoading.value = false;
  }
};

// Handle URL analysis
const analyzeUrl = async () => {
  if (!isValidUrl.value) return;
  
  try {
    isLoading.value = true;
    const response = await fetch(`/casestrainer/api/analyze/url?url=${encodeURIComponent(url.value)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    emit('analyze', { ...data, type: 'url', source: url.value });
  } catch (error) {
    console.error('Error analyzing URL:', error);
            console.error(`Failed to analyze URL: ${error.message}`);
  } finally {
    isLoading.value = false;
  }
};

// Expose methods to parent component
defineExpose({
  fileUpload,
  textPaste,
  analyzeUrl
});

// Component mounted hook
onMounted(() => {
  // Component initialization code here
});
</script>

<style scoped>
.unified-input {
  padding: 20px;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  background-color: #ffffff;
  margin: 20px 0;
  font-family: Arial, sans-serif;
}

.nav-tabs {
  border-bottom: 1px solid #dee2e6;
  margin-bottom: 1.5rem;
}

.nav-tabs .nav-link {
  color: #495057;
  border: 1px solid transparent;
  border-top-left-radius: 0.25rem;
  border-top-right-radius: 0.25rem;
  padding: 0.5rem 1rem;
  transition: all 0.2s ease-in-out;
}

.nav-tabs .nav-link:hover {
  border-color: #e9ecef #e9ecef #dee2e6;
}

.nav-tabs .nav-link.active {
  color: #0d6efd;
  background-color: #fff;
  border-color: #dee2e6 #dee2e6 #fff;
  font-weight: 500;
}

.tab-content {
  padding: 0 0.5rem;
}

.url-input-container {
  max-width: 800px;
  margin: 0 auto;
}

.input-group-text {
  background-color: #f8f9fa;
}

.btn-primary {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.btn-primary:hover {
  background-color: #0b5ed7;
  border-color: #0a58ca;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.text-muted {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.875em;
}

.spinner-border {
  width: 1rem;
  height: 1rem;
  border-width: 0.15em;
}
</style>
