<template>
  <div class="citation-results">
    <!-- Summary Bar -->
    <div class="alert alert-info mb-4">
      <h5 class="mb-0">
        <i class="fas fa-search me-2"></i>
        Found {{ totalCitations }} Citations
      </h5>
    </div>

    <!-- Tabs Navigation -->
    <ul class="nav nav-tabs mb-4" id="citationTabs" role="tablist">
      <li class="nav-item" role="presentation">
        <button 
          class="nav-link active" 
          id="courtlistener-tab" 
          data-bs-toggle="tab" 
          data-bs-target="#courtlistener" 
          type="button" 
          role="tab"
        >
          Found in CL
          <span class="badge bg-primary ms-2">{{ courtListenerCount }}</span>
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button 
          class="nav-link" 
          id="elsewhere-tab" 
          data-bs-toggle="tab" 
          data-bs-target="#elsewhere" 
          type="button" 
          role="tab"
        >
          Found Elsewhere
          <span class="badge bg-success ms-2">{{ elsewhereCount }}</span>
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button 
          class="nav-link" 
          id="notfound-tab" 
          data-bs-toggle="tab" 
          data-bs-target="#notfound" 
          type="button" 
          role="tab"
        >
          Not Found
          <span class="badge bg-danger ms-2">{{ notFoundCount }}</span>
        </button>
      </li>
    </ul>

    <!-- Tab Content -->
    <div class="tab-content" id="citationTabsContent">
      <!-- CourtListener Tab -->
      <div class="tab-pane fade show active" id="courtlistener" role="tabpanel">
        <div class="table-responsive">
          <table class="table table-striped table-hover">
            <thead>
              <tr>
                <th>Citation</th>
                <th>Case Name</th>
                <th>Court</th>
                <th>Year</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="citation in courtListenerCitations" :key="citation.citation_text">
                <td>{{ citation.citation_text }}</td>
                <td>{{ citation.case_name || 'N/A' }}</td>
                <td>{{ citation.court || 'N/A' }}</td>
                <td>{{ citation.year || 'N/A' }}</td>
                <td>
                  <a 
                    v-if="citation.url" 
                    :href="citation.url" 
                    target="_blank" 
                    class="btn btn-sm btn-outline-primary"
                  >
                    <i class="fas fa-external-link-alt"></i> View
                  </a>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Found Elsewhere Tab -->
      <div class="tab-pane fade" id="elsewhere" role="tabpanel">
        <div class="table-responsive">
          <table class="table table-striped table-hover">
            <thead>
              <tr>
                <th>Citation</th>
                <th>Case Name</th>
                <th>Source</th>
                <th>Validation Method</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="citation in elsewhereCitations" :key="citation.citation_text">
                <td>{{ citation.citation_text }}</td>
                <td>{{ citation.case_name || 'N/A' }}</td>
                <td>{{ citation.source }}</td>
                <td>
                  <span class="badge" :class="getBadgeClass(citation.validation_method)">
                    {{ citation.validation_method }}
                  </span>
                </td>
                <td>
                  <button 
                    class="btn btn-sm btn-outline-info"
                    @click="showCitationDetails(citation)"
                  >
                    <i class="fas fa-info-circle"></i> Details
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Not Found Tab -->
      <div class="tab-pane fade" id="notfound" role="tabpanel">
        <div class="table-responsive">
          <table class="table table-striped table-hover">
            <thead>
              <tr>
                <th>Citation</th>
                <th>Possible Case Name</th>
                <th>Confidence</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="citation in notFoundCitations" :key="citation.citation_text">
                <td>{{ citation.citation_text }}</td>
                <td>{{ citation.case_name || 'Unknown' }}</td>
                <td>
                  <div class="progress">
                    <div 
                      class="progress-bar bg-danger" 
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
                  <button 
                    class="btn btn-sm btn-outline-warning"
                    @click="showCitationSuggestions(citation)"
                  >
                    <i class="fas fa-lightbulb"></i> Suggestions
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Citation Details Modal -->
    <div class="modal fade" id="citationDetailsModal" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Citation Details</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body" v-if="selectedCitation">
            <div class="row">
              <div class="col-md-6">
                <h6>Citation Information</h6>
                <p><strong>Citation:</strong> {{ selectedCitation.citation_text }}</p>
                <p><strong>Case Name:</strong> {{ selectedCitation.case_name || 'N/A' }}</p>
                <p><strong>Source:</strong> {{ selectedCitation.source }}</p>
                <p><strong>Validation Method:</strong> {{ selectedCitation.validation_method }}</p>
              </div>
              <div class="col-md-6">
                <h6>Additional Details</h6>
                <p v-if="selectedCitation.volume"><strong>Volume:</strong> {{ selectedCitation.volume }}</p>
                <p v-if="selectedCitation.reporter"><strong>Reporter:</strong> {{ selectedCitation.reporter }}</p>
                <p v-if="selectedCitation.page"><strong>Page:</strong> {{ selectedCitation.page }}</p>
                <p v-if="selectedCitation.court"><strong>Court:</strong> {{ selectedCitation.court }}</p>
                <p v-if="selectedCitation.year"><strong>Year:</strong> {{ selectedCitation.year }}</p>
              </div>
            </div>
            <div v-if="selectedCitation.parallel_citations && selectedCitation.parallel_citations.length > 0" class="mt-3">
              <h6>Parallel Citations</h6>
              <ul class="list-group">
                <li v-for="citation in selectedCitation.parallel_citations" :key="citation" class="list-group-item">
                  {{ citation }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Citation Suggestions Modal -->
    <div class="modal fade" id="citationSuggestionsModal" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Citation Suggestions</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body" v-if="selectedCitation">
            <div class="alert alert-warning">
              <i class="fas fa-exclamation-triangle me-2"></i>
              This citation could not be verified. Here are some suggestions:
            </div>
            <div v-if="selectedCitation.suggestions && selectedCitation.suggestions.length > 0">
              <div v-for="(suggestion, index) in selectedCitation.suggestions" :key="index" class="card mb-3">
                <div class="card-body">
                  <h6 class="card-title">Suggestion {{ index + 1 }}</h6>
                  <p class="card-text">{{ suggestion.explanation }}</p>
                  <div v-if="suggestion.citation" class="mt-2">
                    <strong>Suggested Citation:</strong> {{ suggestion.citation }}
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="alert alert-info">
              No specific suggestions available for this citation.
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Modal } from 'bootstrap'

export default {
  name: 'CitationResults',
  props: {
    citations: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      selectedCitation: null,
      detailsModal: null,
      suggestionsModal: null
    }
  },
  computed: {
    totalCitations() {
      return this.citations.length
    },
    courtListenerCitations() {
      return this.citations.filter(c => 
        c.validation_method === 'CourtListener' && c.verified
      )
    },
    elsewhereCitations() {
      return this.citations.filter(c => 
        c.verified && c.validation_method !== 'CourtListener'
      )
    },
    notFoundCitations() {
      return this.citations.filter(c => !c.verified)
    },
    courtListenerCount() {
      return this.courtListenerCitations.length
    },
    elsewhereCount() {
      return this.elsewhereCitations.length
    },
    notFoundCount() {
      return this.notFoundCitations.length
    }
  },
  methods: {
    getBadgeClass(method) {
      const classes = {
        'Landmark': 'bg-success',
        'Multitool': 'bg-info',
        'Other': 'bg-secondary',
        'LEXIS': 'bg-primary'
      }
      return classes[method] || 'bg-primary'
    },
    showCitationDetails(citation) {
      this.selectedCitation = citation
      this.detailsModal.show()
    },
    showCitationSuggestions(citation) {
      this.selectedCitation = citation
      this.suggestionsModal.show()
    }
  },
  mounted() {
    this.detailsModal = new Modal(document.getElementById('citationDetailsModal'))
    this.suggestionsModal = new Modal(document.getElementById('citationSuggestionsModal'))
  }
}
</script>

<style scoped>
.citation-results {
  margin-top: 2rem;
}

.nav-tabs .badge {
  font-size: 0.8em;
}

.progress {
  height: 1.5rem;
}

.progress-bar {
  line-height: 1.5rem;
  font-size: 0.8rem;
}

.table th {
  white-space: nowrap;
}

.modal-body {
  max-height: 70vh;
  overflow-y: auto;
}
</style> 