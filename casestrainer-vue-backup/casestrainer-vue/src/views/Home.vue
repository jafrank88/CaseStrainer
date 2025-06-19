<template>
  <div class="home polished-home">
    <div class="card shadow-sm">
      <div class="card-header bg-primary text-white">
        <h4 class="mb-0">Citation Analyzer</h4>
      </div>
      <div class="card-body">
        <p class="lead text-center mb-4">Upload a file, paste text, or enter a URL to analyze for legal citations.</p>
        <div 
          class="dropzone polished-dropzone mb-4" 
          tabindex="0"
          @dragenter.prevent="onDragEnter" 
          @dragover.prevent 
          @dragleave.prevent="onDragLeave"
          @drop.prevent="onDrop" 
          @paste.prevent="onPaste"
          @click="() => $refs.fileInput.click()"
          :class="{ 'dropzone--active': dropZoneActive }"
          @keydown.enter.space="() => $refs.fileInput.click()"
          aria-label="Drop file here or click to select"
        >
          <input type="file" ref="fileInput" style="display: none;" @change="onFileChange" accept=".pdf,.docx,.txt,.rtf,.doc,.html,.htm" />
          <div class="dz-content">
            <i class="fas fa-cloud-upload-alt fa-2x mb-2 text-primary"></i>
            <div class="dz-label">Drag & drop a file here, <span class="dz-browse">or click to browse</span></div>
            <div class="dz-hint">(You can also paste text directly into this area)</div>
            <div v-if="file" class="dz-file mt-2"><i class="fas fa-file-alt me-1"></i> {{ file.name }}</div>
          </div>
        </div>
        <div class="or-divider my-4"><span>OR</span></div>
        <div class="mb-3">
          <label for="urlInput" class="form-label visually-hidden">URL</label>
          <input type="url" id="urlInput" v-model="urlInput" class="form-control form-control-lg" placeholder="Paste a document URL (e.g. https://...)" autocomplete="off" />
        </div>
        <div class="mb-4">
          <label for="textInput" class="form-label visually-hidden">Paste Text</label>
          <textarea id="textInput" v-model="pastedText" class="form-control form-control-lg" rows="6" placeholder="Paste your legal text here..."></textarea>
        </div>
        <div class="d-grid mb-3">
          <button class="btn btn-primary btn-lg" @click="analyze" :disabled="!canAnalyze || isAnalyzing">
            <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            {{ isAnalyzing ? 'Analyzing…' : 'Analyze Citations' }}
          </button>
        </div>
        <div v-if="error" class="alert alert-danger mt-3" role="alert">
          <strong>Error:</strong> {{ error }}
        </div>
        <div v-if="results" class="mt-4">
          <ReusableResults :results="results" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import ReusableResults from '@/components/ReusableResults.vue';

export default {
  name: 'Home',
  components: { ReusableResults },
  data() {
    return {
      dropZoneActive: false,
      file: null,
      pastedText: '',
      urlInput: '',
      isAnalyzing: false,
      error: null,
      results: null,
      apiBaseUrl: '/casestrainer/api'
    };
  },
  computed: {
    canAnalyze() {
      return !!(this.file || this.pastedText.trim() || this.urlInput.trim());
    }
  },
  methods: {
    onDragEnter() { this.dropZoneActive = true; },
    onDragLeave() { this.dropZoneActive = false; },
    onDrop(e) {
      this.dropZoneActive = false;
      const dt = e.dataTransfer;
      if (dt.files && dt.files.length) {
        this.file = dt.files[0];
        this.pastedText = '';
        this.urlInput = '';
      } else if (dt.getData('text') || dt.getData('Text')) {
        this.pastedText = dt.getData('text') || dt.getData('Text');
        this.file = null;
        this.urlInput = '';
      }
    },
    onPaste(e) {
      const pasted = (e.clipboardData || window.clipboardData).getData('text');
      if (pasted) {
        this.pastedText = pasted;
        this.file = null;
        this.urlInput = '';
      }
    },
    onFileChange(e) {
      if (e.target.files && e.target.files.length) {
        this.file = e.target.files[0];
        this.pastedText = '';
        this.urlInput = '';
      }
    },
    async analyze() {
      if (this.isAnalyzing || !this.canAnalyze) return;
      this.isAnalyzing = true;
      this.error = null;
      this.results = null;
      let payload = null;
      let endpoint = '/analyze';
      if (this.file) {
        const fd = new FormData();
        fd.append('file', this.file);
        payload = fd;
      } else if (this.pastedText.trim()) {
        payload = { type: 'text', text: this.pastedText };
      } else if (this.urlInput.trim()) {
        payload = { type: 'url', url: this.urlInput };
      } else {
        this.error = 'Please provide a file, text, or URL.';
        this.isAnalyzing = false;
        return;
      }
      try {
        const resp = await axios.post(this.apiBaseUrl + endpoint, payload, (this.file ? { headers: { 'Content-Type': 'multipart/form-data' } } : {}));
        this.results = resp.data;
      } catch (err) {
        this.error = (err.response?.data?.message) || err.message || 'An error occurred.';
      } finally {
        this.isAnalyzing = false;
      }
    }
  }
};
</script>

<style scoped>
.polished-home {
  max-width: 600px;
  margin: 2rem auto;
}
.card {
  border-radius: 1rem;
}
.card-header {
  border-radius: 1rem 1rem 0 0;
}
.lead {
  font-size: 1.15rem;
}
.polished-dropzone {
  border: 2px dashed #b6c2d2;
  border-radius: 8px;
  padding: 36px 20px;
  text-align: center;
  background: #f8fafc;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  outline: none;
}
.dropzone--active {
  border-color: #0d6efd;
  background: #e7f1ff;
}
.dz-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.dz-label {
  font-weight: 500;
  font-size: 1.1rem;
}
.dz-browse {
  color: #0d6efd;
  text-decoration: underline;
  cursor: pointer;
}
.dz-hint {
  font-size: 0.95rem;
  color: #6c757d;
}
.dz-file {
  font-size: 0.98rem;
  color: #495057;
  background: #e9ecef;
  border-radius: 4px;
  padding: 2px 8px;
  display: inline-block;
}
.or-divider {
  text-align: center;
  position: relative;
  margin: 1.5rem 0;
}
.or-divider span {
  background: #fff;
  padding: 0 1rem;
  color: #adb5bd;
  font-weight: 500;
  position: relative;
  z-index: 1;
}
.or-divider:before {
  content: '';
  display: block;
  border-top: 1px solid #dee2e6;
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  z-index: 0;
}
textarea.form-control-lg, input.form-control-lg {
  font-size: 1.1rem;
  border-radius: 0.5rem;
}
.btn-lg {
  font-size: 1.1rem;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
}
@media (max-width: 600px) {
  .polished-home { max-width: 100%; margin: 1rem; }
  .card { border-radius: 0.5rem; }
  .card-header { border-radius: 0.5rem 0.5rem 0 0; }
  .polished-dropzone { padding: 24px 8px; }
}
</style>
