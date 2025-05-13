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
        
        <button class="btn btn-primary" @click="uploadFile" :disabled="!file || isUploading">
          <span v-if="isUploading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
          {{ isUploading ? 'Analyzing...' : 'Analyze Citations' }}
        </button>
      </div>
    </div>
    
    <div v-if="results" class="mt-4">
      <div class="card">
        <div class="card-header">
          <h5>Analysis Results</h5>
        </div>
        <div class="card-body">
          <div class="alert alert-success">
            <h5>Analysis complete!</h5>
            <p>Found {{ results.totalCitations }} citations in your document.</p>
          </div>
          
          <div class="mt-3">
            <h6>Citation Summary:</h6>
            <ul class="list-group">
              <li class="list-group-item d-flex justify-content-between align-items-center">
                Confirmed Citations
                <span class="badge bg-success rounded-pill">{{ results.confirmedCount }}</span>
              </li>
              <li class="list-group-item d-flex justify-content-between align-items-center">
                Unconfirmed Citations
                <span class="badge bg-danger rounded-pill">{{ results.unconfirmedCount }}</span>
              </li>
              <li class="list-group-item d-flex justify-content-between align-items-center">
                Verified with Multi-tool
                <span class="badge bg-info rounded-pill">{{ results.multitoolCount }}</span>
              </li>
            </ul>
          </div>
          
          <div class="mt-3">
            <button class="btn btn-outline-primary me-2" @click="viewConfirmedCitations">
              View Confirmed Citations
            </button>
            <button class="btn btn-outline-danger me-2" @click="viewUnconfirmedCitations">
              View Unconfirmed Citations
            </button>
            <button class="btn btn-outline-info" @click="viewMultitoolCitations">
              View Multi-tool Verified
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="error" class="mt-4 alert alert-danger">
      <h5>Error</h5>
      <p>{{ error }}</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'FileUpload',
  data() {
    return {
      file: null,
      isUploading: false,
      results: null,
      error: null
    };
  },
  methods: {
    handleFileChange(event) {
      this.file = event.target.files[0];
      this.error = null;
      this.results = null;
    },
    formatFileSize(bytes) {
      if (bytes < 1024) {
        return bytes + ' bytes';
      } else if (bytes < 1024 * 1024) {
        return (bytes / 1024).toFixed(2) + ' KB';
      } else {
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
      }
    },
    async uploadFile() {
      if (!this.file) {
        this.error = 'Please select a file to upload';
        return;
      }
      
      this.isUploading = true;
      this.error = null;
      
      try {
        const formData = new FormData();
        formData.append('file', this.file);
        
        const response = await axios.post('/api/analyze', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        this.results = {
          totalCitations: response.data.citations.length,
          confirmedCount: response.data.citations.filter(c => c.found).length,
          unconfirmedCount: response.data.citations.filter(c => !c.found).length,
          multitoolCount: response.data.citations.filter(c => c.found && c.source !== 'CourtListener').length,
          analysisId: response.data.analysis_id,
          citations: response.data.citations
        };
        
        // Store the results in localStorage for other components to access
        localStorage.setItem('lastAnalysisResults', JSON.stringify(this.results));
        
      } catch (error) {
        console.error('Error uploading file:', error);
        this.error = error.response?.data?.error || 'An error occurred while analyzing the file';
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
