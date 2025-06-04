<template>
  <div class="enhanced-file-upload">
    <div class="card">
      <div class="bg-primary text-white p-3 rounded-top">
  <h5 class="mb-0">Upload Document</h5>
</div>
      <div class="card-body">
        <div class="mb-3">
          <label for="enhancedFileUpload" class="form-label">Select a file to analyze for citations</label>
          <input class="form-control" type="file" id="enhancedFileUpload" ref="fileUpload" 
                 @change="handleFileChange" accept=".pdf,.docx,.txt,.rtf,.doc,.html,.htm">
          <div class="form-text">Supported formats: PDF, DOCX, TXT, RTF, DOC, HTML</div>
        </div>
        
        <div v-if="file" class="mb-3">
          <div class="alert alert-info">
            <strong>Selected file:</strong> {{ file.name }} ({{ formatFileSize(file.size) }})
          </div>
        </div>
        
        <ProgressBar :loading="isAnalyzing" message="Analyzing..." />
        <button class="btn btn-primary" @click="analyzeDocument" :disabled="!file || isAnalyzing">
          <span v-if="isAnalyzing" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
          {{ isAnalyzing ? 'Analyzing...' : 'Analyze Citations' }}
        </button>
      </div>
    </div>
    
    <!-- Analysis Results -->
    <div v-if="documentAnalysisResult" class="mt-4">
      <ResultsViewer :results="documentAnalysisResult" />
<!-- Tabs Navigation -->
<ul class="nav nav-tabs mb-3" id="citationTabs" role="tablist">
  <li class="nav-item" role="presentation">
    <button class="nav-link active" id="confirmed-tab" data-bs-toggle="tab" data-bs-target="#confirmed" type="button" role="tab" aria-controls="confirmed" aria-selected="true">
      Confirmed ({{ confirmedCount }})
    </button>
  </li>
  <li class="nav-item" role="presentation">
    <button class="nav-link" id="unconfirmed-tab" data-bs-toggle="tab" data-bs-target="#unconfirmed" type="button" role="tab" aria-controls="unconfirmed" aria-selected="false">
      Unconfirmed ({{ unconfirmedCount }})
    </button>
  </li>
</ul>
<div class="tab-content" id="citationTabsContent">
  <div class="tab-pane fade show active" id="confirmed" role="tabpanel" aria-labelledby="confirmed-tab">
    <div class="table-responsive">
      <table class="table table-striped table-hover">
        <thead>
          <tr>
            <th>Citation</th>
            <th>Status</th>
            <th>Validation Method</th>
            <th>Case Name</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(result, index) in (documentAnalysisResult.validation_results || []).filter(r => r.verified)" :key="index">
            <td v-html="result.citation.replace(/</g, '&lt;').replace(/>/g, '&gt;')"></td>
            <td>
              <span class="badge bg-success">Verified</span>
            </td>
            <td>
              <span v-if="result.validation_method" class="badge" :class="getBadgeClass(result.validation_method)">
                {{ result.validation_method }}
              </span>
              <span v-else>-</span>
            </td>
            <td>{{ result.case_name || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
  <div class="tab-pane fade" id="unconfirmed" role="tabpanel" aria-labelledby="unconfirmed-tab">
    <div class="table-responsive">
      <table class="table table-striped table-hover">
        <thead>
          <tr>
            <th>Citation</th>
            <th>Status</th>
            <th>Validation Method</th>
            <th>Case Name</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(result, index) in (documentAnalysisResult.validation_results || []).filter(r => !r.verified)" :key="index">
            <td v-html="result.citation.replace(/</g, '&lt;').replace(/>/g, '&gt;')"></td>
            <td>
              <span class="badge bg-danger">Not Verified</span>
            </td>
            <td>
              <span v-if="result.validation_method" class="badge" :class="getBadgeClass(result.validation_method)">
                {{ result.validation_method }}
              </span>
              <span v-else>-</span>
            </td>
            <td>{{ result.case_name || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { formatCitation } from '@/utils/citationFormatter';
import ProgressBar from './ProgressBar.vue';
import ResultsViewer from './ResultsViewer.vue';

export default {
  name: 'EnhancedFileUpload',
  components: {
    ProgressBar,
    ResultsViewer
  },
  data() {
    return {
      file: null,
      isAnalyzing: false,
      documentAnalysisResult: null,
      error: null,
      debugInfo: ''
    };
  },
  computed: {
    confirmedCount() {
      if (!this.documentAnalysisResult || !this.documentAnalysisResult.validation_results) {
        return 0;
      }
      return this.documentAnalysisResult.validation_results.filter(r => r.verified).length;
    },
    unconfirmedCount() {
      if (!this.documentAnalysisResult || !this.documentAnalysisResult.validation_results) {
        return 0;
      }
      return this.documentAnalysisResult.validation_results.filter(r => !r.verified).length;
    },
    basePath() {
      // Determine the base path for API requests
      const path = window.location.pathname;
      if (path.includes('/casestrainer/')) {
        return '/casestrainer';
      } else {
        return '';
      }
    }
  },
  methods: {
    formatCitation,
    handleFileChange(event) {
      this.file = event.target.files[0];
      this.documentAnalysisResult = null;
    },
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    analyzeDocument() {
      if (!this.file) {
        alert('Please select a file to upload');
        return;
      }
      
      this.isAnalyzing = true;
      this.documentAnalysisResult = null;
      
      // Clear previous debug info
      this.debugInfo = 'Debug: Starting file analysis...\n';
      this.debugInfo += `Request to /casestrainer/api/analyze: [File data]\n`; // Only for backend logging

      const formData = new FormData();
      formData.append('file', this.file);
      // Attach debug info for server-side logging
      formData.append('debug_info', this.debugInfo);

      axios.post(`/casestrainer/api/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      .then(response => {
        // Add to debug info
        this.debugInfo += `Response received: Processing data...\n`;
        this.debugInfo += `Success: ${JSON.stringify(response.data, null, 2)}\n`;

        this.documentAnalysisResult = response.data;
      })
      .catch(error => {
        alert(`Error analyzing document: ${error.response?.data?.message || error.message || 'Unknown error'}`);
        this.debugInfo += `Error: ${error.message}\n`;
        if (error.response) {
          this.debugInfo += `Response status: ${error.response.status}\n`;
          this.debugInfo += `Response data: ${JSON.stringify(error.response.data, null, 2)}\n`;
        }
      })
      .finally(() => {
        this.isAnalyzing = false;
      });
    },
    getBadgeClass(validationMethod) {
      // Return appropriate Bootstrap badge classes based on validation method
      switch(validationMethod) {
        case 'Landmark':
          return 'bg-primary';
        case 'CourtListener':
          return 'bg-success';
        case 'Multitool':
          return 'bg-info';
        case 'Other':
          return 'bg-secondary';
        default:
          return 'bg-dark';
      }
    },
    viewConfirmedCitations() {
      this.$router.push('/unconfirmed-citations?filter=confirmed');
    },
    viewUnconfirmedCitations() {
      this.$router.push('/unconfirmed-citations?filter=unconfirmed');
    }
  }
};
</script>

<style scoped>
.enhanced-file-upload {
  margin-bottom: 2rem;
}
</style>
