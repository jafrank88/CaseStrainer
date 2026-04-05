<template>
  <div class="unified-input">
    <ul
      class="nav nav-tabs mb-4"
      role="tablist"
      aria-label="Document input method"
      @keydown="onTabListKeydown"
    >
      <li class="nav-item" role="presentation">
        <button
          id="tab-unified-file"
          class="nav-link"
          :class="{ active: activeTab === 'file' }"
          type="button"
          role="tab"
          :tabindex="activeTab === 'file' ? 0 : -1"
          :aria-selected="activeTab === 'file'"
          aria-controls="panel-unified-file"
          @click="selectTab('file')"
        >
          <i class="bi bi-upload me-2" aria-hidden="true"></i>File Upload
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button
          id="tab-unified-text"
          class="nav-link"
          :class="{ active: activeTab === 'text' }"
          type="button"
          role="tab"
          :tabindex="activeTab === 'text' ? 0 : -1"
          :aria-selected="activeTab === 'text'"
          aria-controls="panel-unified-text"
          @click="selectTab('text')"
        >
          <i class="bi bi-text-paragraph me-2" aria-hidden="true"></i>Paste Text
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button
          id="tab-unified-url"
          class="nav-link"
          :class="{ active: activeTab === 'url' }"
          type="button"
          role="tab"
          :tabindex="activeTab === 'url' ? 0 : -1"
          :aria-selected="activeTab === 'url'"
          aria-controls="panel-unified-url"
          @click="selectTab('url')"
        >
          <i class="bi bi-link-45deg me-2" aria-hidden="true"></i>Enter URL
        </button>
      </li>
    </ul>

    <div class="tab-content">
      <div
        v-show="activeTab === 'file'"
        id="panel-unified-file"
        class="tab-pane"
        role="tabpanel"
        aria-labelledby="tab-unified-file"
        :hidden="activeTab !== 'file'"
        :aria-hidden="activeTab !== 'file'"
      >
        <FileUpload
          @analyze="handleAnalyze"
          :is-loading="isLoading"
          ref="fileUpload"
        />
      </div>

      <div
        v-show="activeTab === 'text'"
        id="panel-unified-text"
        class="tab-pane"
        role="tabpanel"
        aria-labelledby="tab-unified-text"
        :hidden="activeTab !== 'text'"
        :aria-hidden="activeTab !== 'text'"
      >
        <TextPaste
          @analyze="handleAnalyze"
          :is-loading="isLoading"
          ref="textPaste"
        />
      </div>

      <div
        v-show="activeTab === 'url'"
        id="panel-unified-url"
        class="tab-pane"
        role="tabpanel"
        aria-labelledby="tab-unified-url"
        :hidden="activeTab !== 'url'"
        :aria-hidden="activeTab !== 'url'"
      >
        <div class="url-input-container">
          <div class="input-group mb-3">
            <span class="input-group-text" aria-hidden="true">
              <i class="bi bi-link-45deg" aria-hidden="true"></i>
            </span>
            <input
              id="input-unified-url"
              type="url"
              class="form-control"
              v-model="url"
              placeholder="Enter URL to analyze"
              aria-label="URL to analyze"
              aria-describedby="hint-unified-url"
              :disabled="isLoading"
              @keyup.enter="analyzeUrl"
            />
            <button
              class="btn btn-primary"
              type="button"
              @click="analyzeUrl"
              :disabled="!isValidUrl || isLoading"
            >
              <span v-if="isLoading" class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Analyzing</span>
              </span>
              <span v-else><i class="bi bi-search me-2" aria-hidden="true"></i>Analyze</span>
            </button>
          </div>
          <small id="hint-unified-url" class="text-muted">Enter a valid URL to analyze its content</small>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, defineEmits, defineExpose } from 'vue';
import FileUpload from './FileUpload.vue';
import TextPaste from './TextPaste.vue';
import { analyze } from '../api/api';

const emit = defineEmits(['analyze', 'error']);

const TAB_ORDER = ['file', 'text', 'url'];

const activeTab = ref('file');
const isLoading = ref(false);
const url = ref('');

const fileUpload = ref(null);
const textPaste = ref(null);

const isValidUrl = computed(() => {
  try {
    new URL(url.value);
    return true;
  } catch (e) {
    return false;
  }
});

function selectTab(tab) {
  if (!TAB_ORDER.includes(tab)) return;
  activeTab.value = tab;
  nextTick(() => {
    document.getElementById(`tab-unified-${tab}`)?.focus();
  });
}

function onTabListKeydown(e) {
  const i = TAB_ORDER.indexOf(activeTab.value);
  if (i < 0) return;

  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
    e.preventDefault();
    selectTab(TAB_ORDER[(i + 1) % TAB_ORDER.length]);
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    e.preventDefault();
    selectTab(TAB_ORDER[(i - 1 + TAB_ORDER.length) % TAB_ORDER.length]);
  } else if (e.key === 'Home') {
    e.preventDefault();
    selectTab(TAB_ORDER[0]);
  } else if (e.key === 'End') {
    e.preventDefault();
    selectTab(TAB_ORDER[TAB_ORDER.length - 1]);
  }
}

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

const analyzeUrl = async () => {
  if (!isValidUrl.value) {
    console.error('Invalid URL:', url.value);
    return;
  }

  try {
    isLoading.value = true;
    const response = await analyze({
      type: 'url',
      url: url.value
    });

    emit('analyze', {
      ...response,
      type: 'url',
      source: url.value
    });
  } catch (error) {
    console.error('Error analyzing URL:', error);
    emit('error', {
      type: 'url_analysis_error',
      message: `Failed to analyze URL: ${error.message}`,
      details: error.response?.data || {},
      timestamp: new Date().toISOString()
    });
  } finally {
    isLoading.value = false;
  }
};

defineExpose({
  fileUpload,
  textPaste,
  analyzeUrl
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
  color: #1a1d21;
  border: 1px solid transparent;
  border-top-left-radius: 0.25rem;
  border-top-right-radius: 0.25rem;
  padding: 0.5rem 1rem;
  transition: all 0.2s ease-in-out;
}

.nav-tabs .nav-link:hover {
  border-color: #e9ecef #e9ecef #dee2e6;
  color: #0d6efd;
}

.nav-tabs .nav-link:focus-visible {
  outline: 3px solid #0d6efd;
  outline-offset: 2px;
  z-index: 1;
  position: relative;
}

.nav-tabs .nav-link.active {
  color: #0a58ca;
  background-color: #fff;
  border-color: #dee2e6 #dee2e6 #fff;
  font-weight: 600;
}

.tab-content {
  padding: 0 0.5rem;
}

.tab-pane:focus-visible {
  outline: none;
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

.btn-primary:focus-visible {
  outline: 3px solid #0d6efd;
  outline-offset: 3px;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.text-muted {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.875em;
  color: #495057 !important;
}

.spinner-border {
  width: 1rem;
  height: 1rem;
  border-width: 0.15em;
}
</style>
