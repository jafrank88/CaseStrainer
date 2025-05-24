<template>
  <div class="multitool-confirmed">
    <div class="card">
      <div class="card-header bg-info text-white">
        <h5>Citations Confirmed with Multi-tool</h5>
        <p class="mb-0">These citations were verified using multiple sources but not found in CourtListener</p>
      </div>
      <div class="card-body">
        <div v-if="loading" class="text-center py-4">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2">Loading citations...</p>
        </div>
        
        <div v-else-if="error" class="alert alert-danger">
          <h5>Error</h5>
          <p>{{ error }}</p>
        </div>
        
        <div v-else-if="citations.length === 0" class="alert alert-info">
          <p>No citations verified with multi-tool found.</p>
        </div>
        
        <div v-else>
          <div class="mb-3">
            <input 
              type="text" 
              class="form-control" 
              placeholder="Search citations..." 
              v-model="searchQuery"
            >
          </div>
          
          <div class="table-responsive">
            <table class="table table-striped table-hover">
              <thead>
                <tr>
                  <th>Citation</th>
                  <th>Case Name</th>
                  <th>Source</th>
                  <th>Details</th>
                  <th>Confidence</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(citation, index) in filteredCitations" :key="index">
                  <td>{{ citation.citation_text }}</td>
                  <td>{{ citation.case_name || 'Unknown' }}</td>
                  <td>{{ citation.source }}</td>
                  <td>
                    <span v-if="citation.volume || citation.reporter || citation.page">
                      <strong>Vol:</strong> {{ citation.volume || 'N/A' }}
                      <strong>Rep:</strong> {{ citation.reporter || 'N/A' }}
                      <strong>Pg:</strong> {{ citation.page || 'N/A' }}
                      <br>
                    </span>
                    <span v-if="citation.court || citation.year">
                      <strong>Court:</strong> {{ citation.court || 'N/A' }}
                      <strong>Year:</strong> {{ citation.year || 'N/A' }}
                    </span>
                  </td>
                  <td>
                    <div class="progress">
                      <div 
                        class="progress-bar" 
                        :class="getConfidenceClass(citation.confidence)" 
                        role="progressbar" 
                        :style="{ width: (citation.confidence * 100) + '%' }" 
                        :aria-valuenow="citation.confidence * 100" 
                        aria-valuemin="0" 
                        aria-valuemax="100"
                      >
                        {{ Math.round(citation.confidence * 100) }}%
                      </div>
                    </div>
                  </td>
                  <td>
                    <a 
                      v-if="citation.url" 
                      :href="citation.url" 
                      target="_blank" 
                      class="btn btn-sm btn-outline-primary"
                    >
                      View Source
                    </a>
                    <a 
                      v-if="citation.file_link" 
                      :href="citation.file_link" 
                      target="_blank" 
                      class="btn btn-sm btn-outline-secondary ms-1"
                    >
                      Source File
                    </a>
                    <button 
                      v-if="citation.context" 
                      class="btn btn-sm btn-outline-info ms-1" 
                      @click="showContext(citation)"
                    >
                      View Context
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Context Modal -->
    <div class="modal fade" id="contextModal" tabindex="-1" aria-labelledby="contextModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="contextModalLabel">Citation Context</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div v-if="selectedCitation">
              <h6>Citation: {{ selectedCitation.citation_text }}</h6>
              
              <div class="citation-details mb-3" v-if="selectedCitation.volume || selectedCitation.reporter || selectedCitation.page || selectedCitation.court || selectedCitation.year">
                <h6>Citation Details:</h6>
                <div class="row">
                  <div class="col-md-4" v-if="selectedCitation.volume">
                    <strong>Volume:</strong> {{ selectedCitation.volume }}
                  </div>
                  <div class="col-md-4" v-if="selectedCitation.reporter">
                    <strong>Reporter:</strong> {{ selectedCitation.reporter }}
                  </div>
                  <div class="col-md-4" v-if="selectedCitation.page">
                    <strong>Page:</strong> {{ selectedCitation.page }}
                  </div>
                </div>
                <div class="row mt-2">
                  <div class="col-md-6" v-if="selectedCitation.court">
                    <strong>Court:</strong> {{ selectedCitation.court }}
                  </div>
                  <div class="col-md-6" v-if="selectedCitation.year">
                    <strong>Year:</strong> {{ selectedCitation.year }}
                  </div>
                </div>
              </div>
              
              <h6>Citation Context:</h6>
              <p class="context-text">{{ selectedCitation.context }}</p>
              
              <div v-if="selectedCitation.file_link" class="mt-3">
                <a :href="selectedCitation.file_link" target="_blank" class="btn btn-outline-primary">
                  <i class="bi bi-file-earmark-text"></i> View Source Document
                </a>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { Modal } from 'bootstrap';

export default {
  name: 'MultitoolConfirmed',
  data() {
    return {
      citations: [],
      loading: true,
      error: null,
      searchQuery: '',
      selectedCitation: null,
      contextModal: null
    };
  },
  computed: {
    filteredCitations() {
      if (!this.searchQuery) {
        return this.citations;
      }
      
      const query = this.searchQuery.toLowerCase();
      return this.citations.filter(citation => 
        citation.citation_text.toLowerCase().includes(query) || 
        (citation.case_name && citation.case_name.toLowerCase().includes(query))
      );
    }
  },
  methods: {
    async fetchCitations() {
      this.loading = true;
      this.error = null;
      
      try {
        // First, try to load directly from the JSON file
        try {
          const jsonResponse = await axios.get('/citation_verification_results.json');
          // console.log('Citation verification results:', jsonResponse.data);
          
          if (jsonResponse.data && jsonResponse.data.newly_confirmed && jsonResponse.data.newly_confirmed.length > 0) {
            this.citations = jsonResponse.data.newly_confirmed.map(citation => ({
              citation_text: citation.citation_text,
              case_name: citation.case_name || 'Unknown',
              confidence: citation.confidence || 0.8,
              source: citation.source || 'Multi-source Verification',
              url: citation.url || '',
              explanation: citation.explanation || 'No explanation available',
              document: citation.document || ''
            }));
            console.log('Loaded', this.citations.length, 'citations from JSON file');
            this.loading = false;
            return;
          }
        } catch (jsonError) {
          console.warn('Error loading from JSON file directly:', jsonError);
        }
        
        // If JSON file loading failed, try API endpoints
        let response;
        try {
          response = await axios.get('/api/confirmed_with_multitool_data');
        } catch (firstError) {
          console.warn('First endpoint attempt failed, trying alternate endpoint:', firstError);
          try {
            response = await axios.get('/api/confirmed-with-multitool-data');
          } catch (secondError) {
            console.warn('Second endpoint attempt failed, trying with full path:', secondError);
            response = await axios.get('/casestrainer/api/confirmed_with_multitool_data');
          }
        }
        
        // console.log('Multitool confirmed data response:', response.data);
        if (response.data && response.data.citations) {
          this.citations = response.data.citations;
        }
      } catch (error) {
        console.error('Error fetching multitool confirmed citations:', error);
        this.error = error.response?.data?.error || 'An error occurred while fetching citations';
      } finally {
        this.loading = false;
      }
    },
    getConfidenceClass(confidence) {
      if (confidence >= 0.8) {
        return 'bg-success';
      } else if (confidence >= 0.6) {
        return 'bg-info';
      } else if (confidence >= 0.4) {
        return 'bg-warning';
      } else {
        return 'bg-danger';
      }
    },
    showContext(citation) {
      this.selectedCitation = citation;
      this.contextModal.show();
    }
  },
  mounted() {
    this.fetchCitations();
    this.contextModal = new Modal(document.getElementById('contextModal'));
  }
};
</script>

<style scoped>
.multitool-confirmed {
  margin-bottom: 2rem;
}
</style>
