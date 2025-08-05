<template>
  <div class="enhanced-validator">
    
    <!-- Header -->
    <div class="header text-center mb-4">
      <h1 class="results-title">{{ headerTitle }}</h1>
    </div>

    <!-- Loading State -->
    <div v-if="showLoading && !results" class="loading-container">
      <div class="loading-content">
        <div class="spinner-container">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Processing...</span>
          </div>
        </div>
        <h3>Processing Citations</h3>
        <p class="text-muted">Extracting and analyzing citations from your document...</p>
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
    const hasActiveRequest = ref(false);
    const simpleLoading = ref(false);

    // Debug: Log results every time it changes and show an alert
    watch(results, (newVal) => {
      console.log('🟢 EnhancedValidator.vue results.value changed:', newVal);
      if (newVal && newVal.result && Array.isArray(newVal.result.citations)) {
        alert('Results received! Number of citations: ' + newVal.result.citations.length);
      }
    }, { immediate: true, deep: true });

    const showLoading = computed(() => {
      const result = simpleLoading.value || hasActiveRequest.value;
      return result;
    });

    // Computed property to determine when to show input form
    const shouldShowInput = computed(() => {
      return !results.value && !error.value && !simpleLoading.value && !hasActiveRequest.value;
    });

    // Computed property for dynamic header title
    const headerTitle = computed(() => {
      if (results.value) {
        return 'Citation Verification Results';
      } else {
        return 'Citation Verification';
      }
    });

    // Add onMounted hook
    onMounted(() => {
      console.log('EnhancedValidator component mounted successfully!');
    });

    // Handler for unified analyze requests
    const handleUnifiedAnalyze = async (data) => {
      console.log('🚀 handleUnifiedAnalyze called with data:', data);
      console.log('🚀 Data type:', typeof data);
      console.log('🚀 Is FormData:', data instanceof FormData);
      
      try {
        // Set loading state
        simpleLoading.value = true;
        hasActiveRequest.value = true;
        error.value = null;

        if (data instanceof FormData) {
          // Handle file uploads
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
          let response;

          try {
            response = await fetch('/casestrainer/api/analyze', {
              method: 'POST',
              body: data, // FormData will automatically set the correct Content-Type
              signal: controller.signal
            });

            clearTimeout(timeoutId);
          } catch (fetchError) {
            clearTimeout(timeoutId);
            if (fetchError.name === 'AbortError') {
              throw new Error('Request timed out after 30 seconds');
            }
            throw fetchError;
          }

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const result = await response.json();

          // Check if this is an async task (file processing)
          if (result.status === 'processing' && result.task_id) {
            console.log('File processing started, polling for results...');
            await pollForResults(result.task_id);
          } else {
            // Immediate result (text processing)
            results.value = result.result || result;
          }

        } else {
          // Handle text/URL data
          console.log('Text/URL data received:', data);
          
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
          let response;

          try {
            response = await fetch('/casestrainer/api/analyze', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(data),
              signal: controller.signal
            });

            clearTimeout(timeoutId);
          } catch (fetchError) {
            clearTimeout(timeoutId);
            if (fetchError.name === 'AbortError') {
              throw new Error('Request timed out after 30 seconds');
            }
            throw fetchError;
          }

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const result = await response.json();

          // Check if this is an async task (URL processing might be async for large documents)
          if (result.status === 'processing' && result.task_id) {
            console.log('URL processing started, polling for results...');
            await pollForResults(result.task_id);
          } else {
            // Immediate result (text/URL processing)
            results.value = result.result || result;
          }
        }

      } catch (err) {
        console.error('Error in handleUnifiedAnalyze:', err);
        error.value = err.message;
      } finally {
        // Clear loading state
        simpleLoading.value = false;
        hasActiveRequest.value = false;
      }
    };

    // Poll for async task results
    const pollForResults = async (taskId) => {
      const maxAttempts = 60; // 5 minutes with 5-second intervals
      let attempts = 0;
      const startTime = Date.now();

      while (attempts < maxAttempts) {
        try {
          const response = await fetch(`/casestrainer/api/task_status/${taskId}`);

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const result = await response.json();

          if (result.status === 'completed') {
            console.log('Task completed, setting results');
            // The task_status endpoint returns results in result.result
            results.value = result.result || result;
            break;
          } else if (result.status === 'failed') {
            throw new Error(result.error || 'Task failed');
          } else {
            // Still processing, update progress and wait
            const elapsedTime = (Date.now() - startTime) / 1000;
            const progress = Math.min((attempts / maxAttempts) * 100, 95); // Cap at 95% until complete
            
            // Update progress state for the progress bar
            results.value = {
              status: 'processing',
              progress: progress,
              elapsedTime: elapsedTime,
              remainingTime: Math.max(0, (maxAttempts - attempts) * 5),
              message: `Processing... (${attempts + 1}/${maxAttempts} attempts)`
            };
            
            console.log(`Task still processing (attempt ${attempts + 1}/${maxAttempts}, progress: ${progress.toFixed(1)}%)`);
            await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
            attempts++;
          }
        } catch (err) {
          console.error('Error polling for results:', err);
          error.value = err.message;
          break;
        }
      }

      if (attempts >= maxAttempts) {
        error.value = 'Processing timed out. Please try again.';
      }
    };

    // Toast notification handler
    const showToast = (toastData) => {
      // You can implement toast notifications here
      console.log('Toast:', toastData);
    };

    // Start new analysis - reset all state
    const startNewAnalysis = () => {
      console.log('🔄 Starting new analysis - resetting state');
      alert('🔄 New Analysis button clicked! Resetting state...');
      results.value = null;
      error.value = null;
      simpleLoading.value = false;
      hasActiveRequest.value = false;
      console.log('🔄 State reset complete. shouldShowInput:', shouldShowInput.value);
    };

    // Copy results handler
    const copyResults = () => {
      // Implementation for copying results
      console.log('Copying results...');
    };

    // Download results handler
    const downloadResults = () => {
      // Implementation for downloading results
      console.log('Downloading results...');
    };

    return {
      // State
      results,
      error,
      hasActiveRequest,
      simpleLoading,
      showLoading,
      shouldShowInput,
      headerTitle,

      // Methods
      handleUnifiedAnalyze,
      pollForResults,
      showToast,
      startNewAnalysis,
      copyResults,
      downloadResults
    };
  }
};
</script>

<style scoped>
.enhanced-validator {
  max-width: 1200px;
  margin: 0 auto;
  min-height: 100vh;
  padding: 2rem 1rem;
}

.header {
  background: #f8f9fa;
  padding: 2rem;
  text-align: center;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
  text-align: center;
}

.loading-content {
  max-width: 500px;
}

.spinner-container {
  margin-bottom: 2rem;
}

.spinner-border {
  width: 3rem;
  height: 3rem;
  border: 0.25em solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spinner-border 0.75s linear infinite;
  display: inline-block;
}

@keyframes spinner-border {
  to {
    transform: rotate(360deg);
  }
}

.text-primary {
  color: #0d6efd !important;
}

.text-muted {
  color: #6c757d !important;
}

.error-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
  text-align: center;
}

.error-content {
  max-width: 500px;
}

.error-icon {
  font-size: 3rem;
  color: #dc3545;
  margin-bottom: 1rem;
}

.main-content-wrapper {
  padding: 2rem;
}

.input-section {
  margin-bottom: 2rem;
}

.results-section {
  margin-top: 2rem;
}

.results-title {
  color: #333;
  margin-bottom: 2rem;
}

.visually-hidden {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: -1px !important;
  overflow: hidden !important;
  clip: rect(0, 0, 0, 0) !important;
  white-space: nowrap !important;
  border: 0 !important;
}
</style>
