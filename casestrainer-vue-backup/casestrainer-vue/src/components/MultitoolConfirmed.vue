<template>
  <div class="multitool-confirmed">
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
            <pre v-if="currentContext">{{ currentContext }}</pre>
            <div v-else>No context available.</div>
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
import ResultsViewer from './ResultsViewer.vue';

export default {
  name: 'MultitoolConfirmed',
  components: {
    ResultsViewer
  },
  data() {
    return {
      citations: [],
      loading: true,
      error: null,
      currentContext: null,
      contextModal: null
    };
  },
  computed: {
    transformedResults() {
      return {
        validation_results: this.citations.map(citation => ({
          citation: citation.citation_text,
          case_name: citation.case_name || 'Unknown',
          verified: true,
          validation_method: 'Multi-tool',
          metadata: {
            explanation: 'Verified using multiple sources',
            source: citation.source,
            volume: citation.volume,
            reporter: citation.reporter,
            page: citation.page,
            court: citation.court,
            year: citation.year,
            confidence: citation.confidence ? Math.round(citation.confidence * 100) + '%' : null,
            url: citation.url
          }
        })),
        confirmedCount: this.citations.length,
        totalCitations: this.citations.length
      };
    }
  },
  methods: {
    async fetchCitations() {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get('/api/citations/multitool-confirmed');
        this.citations = response.data.citations || [];
      } catch (err) {
        console.error('Error fetching multitool confirmed citations:', err);
        this.error = 'Failed to load citations. Please try again later.';
      } finally {
        this.loading = false;
      }
    },
    showContext(citation) {
      this.currentContext = citation.context || 'No context available.';
      if (!this.contextModal) {
        this.contextModal = new Modal(document.getElementById('contextModal'));
      }
      this.contextModal.show();
    }
  },
  mounted() {
    this.fetchCitations();
  }
};
</script>

<style scoped>
.multitool-confirmed {
  margin-bottom: 2rem;
}
</style>
