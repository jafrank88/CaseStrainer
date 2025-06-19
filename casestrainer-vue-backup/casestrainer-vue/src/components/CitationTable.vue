<template>
  <div class="citation-table">
    <div class="table-responsive">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>Citation</th>
            <th v-if="showVerificationStatus">Status</th>
            <th v-if="showMetadata">Case Name</th>
            <th v-if="showMetadata">Source</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="citation in citations" :key="citation.citation_text" 
              :class="getRowClass(citation)">
            <td>
              <span class="citation-text">{{ citation.citation_text }}</span>
              <div class="small text-muted mt-1">
                <i :class="['fas', getSuggestionsText(citation).icon, 'me-1']"></i>
                {{ getSuggestionsText(citation).text }}
              </div>
            </td>
            <td v-if="showVerificationStatus">
              <span class="badge" :class="getStatusBadgeClass(citation)">
                {{ getStatusText(citation) }}
              </span>
            </td>
            <td v-if="showMetadata">{{ citation.case_name || 'N/A' }}</td>
            <td v-if="showMetadata">{{ citation.source || 'Unknown' }}</td>
            <td>
              <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-primary" 
                        @click="$emit('show-details', citation)"
                        title="View Details">
                  <i class="fas fa-info-circle"></i>
                </button>
                <button v-if="citation.suggestions && citation.suggestions.length > 0"
                        class="btn btn-outline-warning"
                        @click="$emit('show-suggestions', citation)"
                        title="View Suggestions">
                  <i class="fas fa-lightbulb"></i>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="alert alert-info mb-0">
      {{ emptyMessage || 'No citations found.' }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'CitationTable',
  props: {
    citations: {
      type: Array,
      required: true,
      validator: (value) => Array.isArray(value) && value.every(c => c.citation_text)
    },
    showVerificationStatus: {
      type: Boolean,
      default: true
    },
    showMetadata: {
      type: Boolean,
      default: true
    },
    emptyMessage: {
      type: String,
      default: 'No citations found.'
    }
  },
  computed: {
    getSuggestionsText() {
      return (citation) => {
        if (citation.suggestions && citation.suggestions.length > 0) {
          return {
            icon: 'fa-lightbulb',
            text: `${citation.suggestions.length} suggestion(s) available`
          };
        }
        return {
          icon: 'fa-info-circle',
          text: 'No suggestions available'
        };
      };
    }
  },
  methods: {
    getRowClass(citation) {
      if (citation.verified) return 'table-success';
      if (citation.status === 'unverified') return 'table-warning';
      return '';
    },
    getStatusBadgeClass(citation) {
      if (citation.verified) {
        return citation.source === 'CourtListener' ? 'bg-success' : 'bg-info';
      }
      return 'bg-warning text-dark';
    },
    getStatusText(citation) {
      if (citation.verified) {
        return citation.source === 'CourtListener' ? 'Verified' : 'Verified (Other)';
      }
      return 'Unverified';
    }
  },
  mounted() {
    console.log('CitationTable mounted with citations:', this.citations);
  },
  updated() {
    console.log('CitationTable updated with citations:', this.citations);
  }
};
</script>

<style scoped>
.citation-table {
  margin-top: 1rem;
}
.citation-text {
  font-family: monospace;
  font-size: 0.9rem;
}
.btn-group {
  white-space: nowrap;
}
</style>
