<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-8">
        <div class="card">
          <div class="card-header bg-primary text-white">
            <h2 class="h4 mb-0">Backend Connection Test</h2>
          </div>
          <div class="card-body">
            <div v-if="loading" class="text-center">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
              <p class="mt-2">Testing backend connection...</p>
            </div>
            
            <div v-else>
              <div v-if="error" class="alert alert-danger">
                <h4 class="alert-heading">Connection Failed</h4>
                <p>{{ error }}</p>
                <pre class="bg-dark text-white p-3 rounded">{{ errorDetails }}</pre>
              </div>
              
              <div v-else class="alert alert-success">
                <h4 class="alert-heading">Connection Successful!</h4>
                <p>Backend is responding correctly.</p>
                <pre class="bg-dark text-white p-3 rounded">{{ JSON.stringify(apiResponse, null, 2) }}</pre>
              </div>
              
              <div class="mt-4">
                <h3>Test Backend Endpoints</h3>
                <div class="d-grid gap-2">
                  <button @click="testEndpoint('/api/health')" class="btn btn-outline-primary">
                    Test Health Endpoint
                  </button>
                  <button @click="testEndpoint('/api/analyze', { text: '410 U.S. 113 (1973)' })" class="btn btn-outline-secondary">
                    Test Analyze Endpoint
                  </button>
                </div>
              </div>
              
              <div v-if="testResult" class="mt-4">
                <h4>Test Result</h4>
                <pre class="bg-light p-3 rounded">{{ JSON.stringify(testResult, null, 2) }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'BackendTest',
  data() {
    return {
      loading: true,
      error: null,
      errorDetails: null,
      apiResponse: null,
      testResult: null,
      apiUrl: process.env.VUE_APP_API_URL || 'http://localhost:5000/casestrainer'
    };
  },
  async created() {
    await this.testConnection();
  },
  methods: {
    async testConnection() {
      this.loading = true;
      this.error = null;
      this.errorDetails = null;
      this.apiResponse = null;
      
      try {
        const response = await axios.get(`${this.apiUrl}/api/health`);
        this.apiResponse = response.data;
      } catch (error) {
        this.handleError(error);
      } finally {
        this.loading = false;
      }
    },
    
    async testEndpoint(endpoint, data = null) {
      this.loading = true;
      this.testResult = null;
      
      try {
        let response;
        const url = `${this.apiUrl}${endpoint}`;
        
        if (data) {
          response = await axios.post(url, data, {
            headers: { 'Content-Type': 'application/json' }
          });
        } else {
          response = await axios.get(url);
        }
        
        this.testResult = response.data;
      } catch (error) {
        this.handleError(error);
      } finally {
        this.loading = false;
      }
    },
    
    handleError(error) {
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        this.error = `Server responded with status ${error.response.status}`;
        this.errorDetails = {
          status: error.response.status,
          statusText: error.response.statusText,
          data: error.response.data,
          headers: error.response.headers
        };
      } else if (error.request) {
        // The request was made but no response was received
        this.error = 'No response received from server';
        this.errorDetails = error.request;
      } else {
        // Something happened in setting up the request that triggered an Error
        this.error = 'Error setting up request';
        this.errorDetails = error.message;
      }
      console.error('API Error:', error);
    }
  }
};
</script>
