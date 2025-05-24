<template>
  <div class="citation-table">
    <div v-if="citations && citations.length > 0" class="table-responsive">
      <table class="table table-striped table-hover">
        <thead>
          <tr>
            <th>Citation</th>
            <th>Status</th>
            <th>Validation Method</th>
            <th>Case Name</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(citation, index) in citations" :key="'citation-'+index">
            <td class="citation-text">
              <i v-if="citation.verified" class="fas fa-check-circle text-success me-1"></i>
              <i v-else class="fas fa-exclamation-triangle text-warning me-1"></i>
              {{ citation.citation }}
            </td>
            <td>
              <span class="badge" :class="citation.verified ? 'bg-success' : 'bg-warning text-dark'">
                {{ citation.verified ? 'Verified' : 'Unverified' }}
              </span>
            </td>
            <td>
              <span v-if="citation.validation_method" class="badge" :class="getBadgeClass(citation.validation_method)">
                {{ citation.validation_method }}
              </span>
              <span v-else>-</span>
            </td>
            <td>{{ citation.case_name || '-' }}</td>
            <td>
              <span v-if="citation.metadata && citation.metadata.explanation" 
                    class="text-muted small" 
                    :title="citation.metadata.explanation">
                <i class="fas fa-info-circle"></i> Info
              </span>
              <span v-else>-</span>
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
      default: () => []
    },
    emptyMessage: {
      type: String,
      default: 'No citations found.'
    }
  },
  methods: {
    getBadgeClass(method) {
      // Return appropriate Bootstrap badge classes based on validation method
      const methodMap = {
        'CourtListener': 'bg-success',
        'Landmark': 'bg-primary',
        'Multitool': 'bg-info',
        'Manual': 'bg-secondary',
        'Other': 'bg-secondary'
      };
      return methodMap[method] || 'bg-dark';
    }
  }
};
</script>

<style scoped>
.citation-table {
  margin-top: 1rem;
}

.citation-text {
  font-family: 'Courier New', Courier, monospace;
  font-weight: bold;
}

table {
  font-size: 0.9rem;
}

.table th {
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.8rem;
  letter-spacing: 0.5px;
  color: #495057;
  background-color: #f8f9fa;
}

.badge {
  font-weight: 500;
  padding: 0.35em 0.5em;
  font-size: 0.75em;
  letter-spacing: 0.5px;
}
</style>
