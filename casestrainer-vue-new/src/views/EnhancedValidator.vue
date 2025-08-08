<template>
  <div class="enhanced-validator">
    <!-- Header -->
    <div class="header text-center mb-4">
      <h1 class="results-title">{{ headerTitle }}</h1>
      <div style="background: yellow; color: black; padding: 10px; margin: 10px; border: 2px solid red;">
        <strong>DEBUG: EnhancedValidator component is rendering!</strong>
        <br>shouldShowInput: {{ shouldShowInput }}
        <br>results: {{ !!results }}
        <br>error: {{ !!error }}
        <br>simpleLoading: {{ simpleLoading }}
        <br>hasActiveRequest: {{ hasActiveRequest }}
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="showLoading && !results" class="loading-container">
      <div class="loading-content">
        <div class="spinner-container">
          <div class="custom-spinner" role="status" ref="spinnerElement">
            <div class="spinner-circle" ref="spinnerCircle"></div>
            <span class="visually-hidden">Processing...</span>
          </div>
        </div>
        <h3>Processing Citations</h3>
        <p class="text-muted">Extracting and analyzing citations from your document...</p>
        <div class="loading-info">
          <p class="timeout-info">This may take up to 30 seconds. Please don't close this page.</p>
          <div class="progress-indicator">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: loadingProgress + '%' }"></div>
            </div>
            <span class="progress-text">{{ loadingProgressText }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error && !showLoading" class="error-container">
      <div class="error-content">
        <div class="error-icon">
          <i class="bi bi-exclamation-triangle"></i>
        </div>
        <h3>Analysis Failed</h3>
        <p>{{ error }}</p>
      </div>
    </div>

    <!-- Main Content Layout -->
    <div v-else class="main-content-wrapper">
      <!-- Input Form Section -->
      <div v-if="shouldShowInput" class="input-section">
        <UnifiedInput :isAnalyzing="showLoading" @analyze="handleUnifiedAnalyze" />
      </div>

      <!-- Results Section -->
      <div v-if="results" class="results-section">
        <CitationResults 
          :results="results"
          :show-loading="showLoading"
          :error="error"
          @copy-results="copyResults"
          @download-results="downloadResults"
          @toast="showToast"
          @new-analysis="startNewAnalysis"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue';
import UnifiedInput from '@/components/UnifiedInput.vue';
import CitationResults from '@/components/CitationResults.vue';

export default {
  name: 'EnhancedValidator',
  components: {
    UnifiedInput,
    CitationResults
  },
  setup() {
    // ===== REACTIVE STATE =====
    const results = ref(null);
    const error = ref(null);
    const simpleLoading = ref(false);
    const hasActiveRequest = ref(false);
    const loadingStartTime = ref(null);
    const loadingProgress = ref(0);
    const loadingProgressText = ref('');

    // Debug: Log results every time it changes
    watch(results, (newVal) => {
      console.log('🟢 EnhancedValidator.vue results.value changed:', newVal);
    });

    // Computed property to determine loading state
    const showLoading = computed(() => {
      const result = simpleLoading.value || hasActiveRequest.value;
      console.log('🔄 showLoading computed - simpleLoading:', simpleLoading.value, 'hasActiveRequest:', hasActiveRequest.value, 'result:', result);
      return result;
    });

    // Computed property to determine when to show input form
    const shouldShowInput = computed(() => {
      const show = !results.value && !error.value && !showLoading.value;
      console.log('🔍 shouldShowInput computed -', { 
        show, 
        hasResults: !!results.value, 
        hasError: !!error.value, 
        isLoading: showLoading.value 
      });
      return show;
    });

    // Computed property for dynamic header title
    const headerTitle = computed(() => {
      return results.value ? 'Citation Verification Results' : 'Citation Verification';
    });

    // Handler for unified analyze requests
    const handleUnifiedAnalyze = async (data) => {
      console.log('🚀 handleUnifiedAnalyze called with data:', data);
      
      try {
        // Set loading state
        simpleLoading.value = true;
        hasActiveRequest.value = true;
        error.value = null;
        loadingStartTime.value = Date.now();
        loadingProgress.value = 0;
        loadingProgressText.value = 'Starting...';

        let response;
        const formData = new FormData();
        let endpoint = '';

        // Prepare request based on input type
        if (data.type === 'file') {
          // File upload
          endpoint = '/api/upload';
          // data is already a FormData object with the file
          formData.append('file', data.get('file'));
        } else if (data.type === 'text') {
          // Text input
          endpoint = '/api/text';
          formData.append('text', data.text);
        } else if (data.type === 'url') {
          // URL input
          endpoint = '/api/url';
          formData.append('url', data.url);
        }

        console.log('📤 Sending request to:', endpoint);
        
        // Make the API request
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout

        try {
          response = await fetch(endpoint, {
            method: 'POST',
            body: formData,
            signal: controller.signal,
            // Don't set Content-Type header, let the browser set it with the correct boundary
          });

          clearTimeout(timeoutId);
        } catch (fetchError) {
          clearTimeout(timeoutId);
          if (fetchError.name === 'AbortError') {
            throw new Error('Request timed out. The server is taking too long to respond.');
          }
          throw fetchError;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.message || `Server returned ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        console.log('✅ API Response:', result);
        
        // Update results
        results.value = result;
        
      } catch (err) {
        console.error('❌ Error in handleUnifiedAnalyze:', err);
        error.value = err.message || 'An error occurred while processing your request';
      } finally {
        // Reset loading state
        simpleLoading.value = false;
        hasActiveRequest.value = false;
        loadingProgress.value = 100;
        loadingProgressText.value = 'Complete';
      }
    };

    // Placeholder methods - implement as needed
    const copyResults = () => console.log('Copy results');
    const downloadResults = () => console.log('Download results');
    const showToast = (message) => console.log('Toast:', message);
    const startNewAnalysis = () => {
      results.value = null;
      error.value = null;
    };

    // Debug: Log the initial state
    console.log('EnhancedValidator setup completed', { 
      shouldShowInput: shouldShowInput.value,
      results: !!results.value,
      error: !!error.value,
      showLoading: showLoading.value
    });

    return {
      // State
      results,
      error,
      simpleLoading,
      hasActiveRequest,
      loadingProgress,
      loadingProgressText,
      
      // Computed
      showLoading,
      shouldShowInput,
      headerTitle,
      
      // Methods
      handleUnifiedAnalyze,
      copyResults,
      downloadResults,
      showToast,
      startNewAnalysis
    };
  }
};
</script>

<style scoped>
.enhanced-validator {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.error-container {
  text-align: center;
  padding: 20px;
  color: #dc3545;
}

.main-content-wrapper {
  margin-top: 20px;
}

.input-section, .results-section {
  margin-bottom: 30px;
}
</style>
