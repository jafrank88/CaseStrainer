<template>
  <div class="file-upload">
    <div class="card">
      <div class="card-header">
        <h5>Upload a Document</h5>
      </div>
      <div class="card-body">
        <div class="mb-3">
          <label for="fileUpload" class="form-label">Select a file to analyze for citations</label>
          <input class="form-control" type="file" id="fileUpload" @change="handleFileChange" accept=".pdf,.docx,.txt,.rtf,.doc,.html,.htm">
          <div class="form-text">Supported formats: PDF, DOCX, TXT, RTF, DOC, HTML</div>
        </div>
        
        <div v-if="file" class="mb-3">
          <div class="alert alert-info">
            <strong>Selected file:</strong> {{ file.name }} ({{ formatFileSize(file.size) }})
          </div>
        </div>
        
        <ProgressBar :loading="isUploading" message="Uploading & Analyzing..." />
        <button class="btn btn-primary" @click="uploadFile" :disabled="!file || isUploading">
          <span v-if="isUploading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
          {{ isUploading ? 'Analyzing...' : 'Analyze Citations' }}
        </button>
      </div>
    </div>
    
    <ReusableResults v-if="results" :results="results" />
    
    <div v-if="error" class="mt-4 alert alert-danger">
      <h5>Error</h5>
      <p>{{ error }}</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

import ProgressBar from './ProgressBar.vue';
import ReusableResults from './ReusableResults.vue';

export default {
  name: 'FileUpload',
  components: {
    ProgressBar,
    ReusableResults
  },
  data() {
    return {
      file: null,
      isUploading: false,
      results: null,
      error: null,
      debugInfo: ''
    };
  },
  methods: {
    handleFileChange(event) {
      this.file = event.target.files[0];
      this.error = null;
      this.results = null;
    },
    formatFileSize(bytes) {
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      if (bytes === 0) return '0 Bytes';
      const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
      return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
    },
    async uploadFile() {
      if (!this.file) {
        this.error = 'Please select a file to upload';
        return;
      }
      
      this.isUploading = true;
      this.error = null;
      
      // Clear previous debug info
      this.debugInfo = 'Debug: Starting file analysis...\n';
      
      try {
        const formData = new FormData();
        formData.append('file', this.file);
        // Attach debug info for server-side logging
        formData.append('debug_info', this.debugInfo);
        
        // Add to debug info
        this.debugInfo += `Request to /api/analyze-document: [File data]\n`; // Only for backend logging
        
        const response = await axios.post('/api/analyze-document', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        // Add to debug info
        this.debugInfo += `Response received: Processing data...\n`;
        this.debugInfo += `Success: ${JSON.stringify(response.data, null, 2)}\n`;
        
        this.results = {
          totalCitations: response.data.citations.length,
          confirmedCount: response.data.citations.filter(c => c.valid).length,
          unconfirmedCount: response.data.citations.filter(c => !c.valid).length,
          multitoolCount: response.data.citations.filter(c => c.valid && c.source !== 'courtlistener_api').length,
          analysisId: response.data.analysis_id,
          citations: response.data.citations
        };
        
        // Store the results in localStorage for other components to access
        localStorage.setItem('lastAnalysisResults', JSON.stringify(this.results));
        
      } catch (error) {
        // console.error('Error uploading file:', error);
        this.error = error.response?.data?.error || 'An error occurred while analyzing the file';
        
        // Add error to debug info
        this.debugInfo += `Error: ${error.message}\n`;
        if (error.response) {
          this.debugInfo += `Response status: ${error.response.status}\n`;
          this.debugInfo += `Response data: ${JSON.stringify(error.response.data, null, 2)}\n`;
        }
      } finally {
        this.isUploading = false;
      }
    },
    viewConfirmedCitations() {
      // Navigate to confirmed citations view
      this.$router.push('/confirmed-citations');
    },
    viewUnconfirmedCitations() {
      // Navigate to unconfirmed citations view
      this.$router.push('/unconfirmed-citations');
    },
    viewMultitoolCitations() {
      // Navigate to multi-tool verified citations view
      this.$router.push('/multitool-confirmed');
    }
  }
};
</script>

<style scoped>
.file-upload {
  margin-bottom: 2rem;
}
</style>
