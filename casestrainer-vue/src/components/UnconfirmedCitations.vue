<template>
  <div class="unconfirmed-citations">
    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Loading unconfirmed citations...</p>
    </div>
    
    <div v-else-if="error" class="alert alert-danger">
      <h5>Error</h5>
      <p>{{ error }}</p>
    </div>
    
    <div v-else>
      <ResultsViewer :results="transformedResults" />
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
              <h6>Citation: <span v-html="formatCitation(selectedCitation.citation_text)"></span></h6>
              
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
              <p class="context-text">{{ selectedCitation.context || 'No context available' }}</p>
              
              <div v-if="selectedCitation.file_link" class="mt-3">
                <a :href="selectedCitation.file_link" target="_blank" class="btn btn-outline-primary">
                  <i class="bi bi-file-earmark-text"></i> View Source Document
                </a>
              </div>
            </div>
            <div v-else>
              <p>No citation selected or citation data is not available.</p>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Suggestions Modal -->
    <div class="modal fade" id="suggestionsModal" tabindex="-1" aria-labelledby="suggestionsModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="suggestionsModalLabel">Citation Correction Suggestions</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div v-if="loadingSuggestions" class="text-center py-4">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
              <p class="mt-2">Loading suggestions...</p>
            </div>
            
            <div v-else-if="suggestionError" class="alert alert-danger">
              <h5>Error</h5>
              <p>{{ suggestionError }}</p>
            </div>
            
            <div v-else-if="suggestions.length === 0" class="alert alert-info">
              <p>No correction suggestions available for this citation.</p>
            </div>
            
            <div v-else>
              <h6>Original Citation: {{ selectedCitation?.citation_text }}</h6>
              <div class="list-group mt-3">
                <a 
                  v-for="(suggestion, index) in suggestions" 
                  :key="index"
                  href="#" 
                  class="list-group-item list-group-item-action"
                  @click.prevent="applySuggestion(suggestion)"
                >
                  <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1" v-html="formatCitation(suggestion.corrected_citation)"></h6>
                    <small class="text-success">{{ Math.round(suggestion.confidence * 100) }}% match</small>
                  </div>
                  <p class="mb-1">{{ suggestion.explanation }}</p>
                  <small v-if="suggestion.source_url">
                    <a :href="suggestion.source_url" target="_blank">View Source</a>
                  </small>
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
import { formatCitation } from '@/utils/citationFormatter';
import NotCitationFeedback from './NotCitationFeedback.vue';
import ResultsViewer from './ResultsViewer.vue';

export default {
  name: 'UnconfirmedCitations',
  data() {
    return {
      citations: [],
      loading: true,
      error: null,
      currentContext: null,
      contextModal: null,
      reprocessing: null,
      suggestions: [],
      selectedCitation: null,
      suggestionsModal: null
    };
  },
  computed: {
    transformedResults() {
      return {
        validation_results: this.citations.map(citation => ({
          citation: citation.citation_text,
          case_name: citation.case_name || 'Unknown',
          verified: false,
          validation_method: 'Unverified',
          metadata: {
            explanation: citation.explanation || 'Could not be verified in any source',
            source: citation.source,
            volume: citation.volume,
            reporter: citation.reporter,
            page: citation.page,
            court: citation.court,
            year: citation.year,
            confidence: citation.confidence ? Math.round(citation.confidence * 100) + '%' : 'N/A',
            url: citation.url
          }
        })),
        unconfirmedCount: this.citations.length,
        totalCitations: this.citations.length
      };
    }
  },
  components: {
    NotCitationFeedback,
    ResultsViewer
  },
  methods: {
    formatCitation,
    async fetchCitations() {
      this.loading = true;
      this.error = null;
      
      try {
        // First, try to load directly from the JSON file
        try {
          const jsonResponse = await axios.get('/citation_verification_results.json');
          // console.log('Citation verification results:', jsonResponse.data);
          
          if (jsonResponse.data && jsonResponse.data.still_unconfirmed && jsonResponse.data.still_unconfirmed.length > 0) {
            this.citations = jsonResponse.data.still_unconfirmed.map(citation => ({
              citation_text: citation.citation_text,
              case_name: citation.case_name || 'Unknown',
              confidence: citation.confidence || 0.3,
              explanation: citation.explanation || 'No explanation available',
              document: citation.document || '',
              summaries: citation.summaries || []
            }));
            console.log('Loaded', this.citations.length, 'unconfirmed citations from JSON file');
            this.loading = false;
            return;
          }
        } catch (jsonError) {
          console.warn('Error loading from JSON file directly:', jsonError);
        }
        
        // If JSON file loading failed, try API endpoints
        let response;
        try {
          response = await axios.get('/api/unconfirmed_citations_data');
        } catch (firstError) {
          console.warn('First endpoint attempt failed, trying alternate endpoint:', firstError);
          try {
            response = await axios.get('/api/unconfirmed-citations-data');
          } catch (secondError) {
            console.warn('Second endpoint attempt failed, trying with full path:', secondError);
            response = await axios.get('/casestrainer/api/unconfirmed_citations_data');
          }
        }
        
        // console.log('Unconfirmed citations data response:', response.data);
        if (response.data && response.data.citations) {
          this.citations = response.data.citations;
        }
      } catch (error) {
        console.error('Error fetching unconfirmed citations:', error);
        this.error = error.response?.data?.error || 'An error occurred while fetching citations';
      } finally {
        this.loading = false;
      }
    },
    showContext(citation) {
      this.selectedCitation = citation;
      this.contextModal.show();
    },
    async showSuggestions(citation) {
      this.selectedCitation = citation;
      this.loadingSuggestions = true;
      this.suggestionError = null;
      this.suggestions = [];
      this.suggestionsModal.show();
      
      try {
        const response = await axios.post('/casestrainer/api/suggest-citation-corrections', {
          citation: citation.citation_text
        });
        
        // Check if there's a warning about the correction engine not being available
        if (response.data.warning) {
          this.suggestionError = response.data.warning;
        }
        
        this.suggestions = response.data.suggestions || [];
      } catch (error) {
        console.error('Error fetching correction suggestions:', error);
        this.suggestionError = error.response?.data?.error || 'An error occurred while fetching suggestions';
      } finally {
        this.loadingSuggestions = false;
      }
    },
    async reprocessCitation(citation) {
      this.reprocessing = citation.citation_text;
      
      try {
        const response = await axios.post('/api/reprocess-citations', {
          citations: [citation.citation_text]
        });
        
        // Update the citation in the list
        const index = this.citations.findIndex(c => c.citation_text === citation.citation_text);
        if (index !== -1) {
          const resultsArray = Array.isArray(response.data.results) ? response.data.results : [];
const reprocessedCitation = resultsArray.find(r => r.citation_text === citation.citation_text);
          if (reprocessedCitation) {
            if (reprocessedCitation.found) {
              // If now confirmed, remove from unconfirmed list
              this.citations.splice(index, 1);
            } else {
              // Update the citation with new information
              this.citations[index] = { ...this.citations[index], ...reprocessedCitation };
            }
          }
        }
        
      } catch (error) {
        console.error('Error reprocessing citation:', error);
        alert('Error reprocessing citation: ' + (error.response?.data?.error || 'An unknown error occurred'));
      } finally {
        this.reprocessing = null;
      }
    },
    applySuggestion(suggestion) {
      if (this.selectedCitation) {
        this.reprocessCitation({
          ...this.selectedCitation,
          citation_text: suggestion.corrected_citation
        });
        this.suggestionsModal.hide();
      }
    }
  },
  mounted() {
    this.fetchCitations();
    this.contextModal = new Modal(document.getElementById('contextModal'));
    this.suggestionsModal = new Modal(document.getElementById('suggestionsModal'));
  }
};
</script>

<style scoped>
.unconfirmed-citations {
  margin-bottom: 2rem;
}
</style>
