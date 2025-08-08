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
    const hasActiveRequest = ref(false);
    const simpleLoading = ref(false);
    const loadingStartTime = ref(null);
    const loadingProgress = ref(0);
    const loadingProgressText = ref('');

    // Debug: Log results every time it changes and show an alert
    watch(results, (newVal) => {
      console.log('🟢 EnhancedValidator.vue results.value changed:', newVal);
      if (newVal && newVal.result && Array.isArray(newVal.result.citations)) {
        alert('Results received! Number of citations: ' + newVal.result.citations.length);
      }
    }, { immediate: true, deep: true });

    // Watch for loading state changes to start spinner animation
    watch(showLoading, (isLoading) => {
      if (isLoading) {
        // Start JavaScript fallback animation after a short delay
        setTimeout(() => {
          startSpinnerAnimation();
        }, 100);
      }
    });

    const showLoading = computed(() => {
      const result = simpleLoading.value || hasActiveRequest.value;
      console.log('🔄 showLoading computed - simpleLoading:', simpleLoading.value, 'hasActiveRequest:', hasActiveRequest.value, 'result:', result);
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

    // JavaScript fallback animation for spinner
    const startSpinnerAnimation = () => {
      console.log('🔄 Starting JavaScript spinner animation');
      const spinnerCircle = document.querySelector('.spinner-circle');
      if (spinnerCircle) {
        console.log('🔄 Spinner circle found, starting rotation');
        let rotation = 0;
        const animate = () => {
          rotation += 10;
          spinnerCircle.style.transform = `rotate(${rotation}deg)`;
          requestAnimationFrame(animate);
        };
        animate();
      } else {
        console.log('⚠️ Spinner circle not found');
      }
    };

    // Handler for unified analyze requests
    const handleUnifiedAnalyze = async (data) => {
      console.log('🚀 handleUnifiedAnalyze called with data:', data);
      console.log('🚀 Data type:', typeof data);
      console.log('🚀 Is FormData:', data instanceof FormData);
      
      try {
        // Set loading state
        console.log('🔄 Setting loading state to true');
        simpleLoading.value = true;
        hasActiveRequest.value = true;
        error.value = null;
        loadingStartTime.value = Date.now();
        loadingProgress.value = 0;
        loadingProgressText.value = 'Starting...';
        console.log('🔄 Loading state set - simpleLoading:', simpleLoading.value, 'hasActiveRequest:', hasActiveRequest.value);
        
        // Start progress tracking
        const progressInterval = setInterval(() => {
          if (loadingStartTime.value) {
            const elapsed = (Date.now() - loadingStartTime.value) / 1000;
            const progress = Math.min((elapsed / 30) * 100, 95); // Cap at 95% until complete
            loadingProgress.value = progress;
            loadingProgressText.value = `${Math.floor(elapsed)}s elapsed`;
          }
        }, 1000);

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
        console.log('🔄 Clearing loading state');
        simpleLoading.value = false;
        hasActiveRequest.value = false;
        loadingStartTime.value = null;
        loadingProgress.value = 0;
        loadingProgressText.value = '';
        console.log('🔄 Loading state cleared - simpleLoading:', simpleLoading.value, 'hasActiveRequest:', hasActiveRequest.value);
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
      loadingProgress,
      loadingProgressText,
      showLoading,
      shouldShowInput,
      headerTitle,
      // Methods
      startSpinnerAnimation,

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
  padding: 1rem 0.5rem;
}

.header {
  background: #f8f9fa;
  padding: 1rem;
  text-align: center;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 40vh;
  text-align: center;
}

.loading-content {
  max-width: 400px;
}

.spinner-container {
  margin-bottom: 1rem;
}

.loading-info {
  margin-top: 1.5rem;
}

.timeout-info {
  font-size: 0.9rem;
  color: #6c757d;
  margin-bottom: 1rem;
}

.progress-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.progress-bar {
  width: 200px;
  height: 6px;
  background-color: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: #0d6efd;
  transition: width 0.3s ease;
  border-radius: 3px;
}

.progress-text {
  font-size: 0.8rem;
  color: #6c757d;
  font-weight: 500;
}

.custom-spinner {
  width: 3rem;
  height: 3rem;
  position: relative;
  display: inline-block;
}

.spinner-circle {
  width: 100%;
  height: 100%;
  border: 0.25em solid #e9ecef;
  border-top: 0.25em solid #0d6efd;
  border-radius: 50%;
  animation: custom-spin 1s linear infinite;
  /* Force animation even with reduced motion */
  animation-duration: 1s !important;
  animation-iteration-count: infinite !important;
}

@keyframes custom-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Fallback for when animations are completely disabled */
@media (prefers-reduced-motion: reduce) {
  .spinner-circle {
    animation: custom-spin 1s linear infinite !important;
  }
  
  /* Alternative: pulsing effect if rotation is disabled */
  .spinner-circle:not([style*="animation"]) {
    animation: pulse 1.5s ease-in-out infinite !important;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
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
  min-height: 40vh;
  text-align: center;
}

.error-content {
  max-width: 400px;
}

.error-icon {
  font-size: 2.5rem;
  color: #dc3545;
  margin-bottom: 0.75rem;
}

.main-content-wrapper {
  padding: 1rem;
}

.input-section {
  margin-bottom: 1rem;
}

.results-section {
  margin-top: 1rem;
}

.results-title {
  color: #333;
  margin-bottom: 1rem;
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
