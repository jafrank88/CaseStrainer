<template>
  <div v-if="results">
    <div v-if="hasTechnicalError" class="alert alert-warning">
      <i class="fas fa-exclamation-triangle me-2"></i>
      Some citations could not be verified due to technical issues (such as a timeout or service error). Please try again later or contact support if the problem persists.
    </div>
    <div class="card mt-4">
      <div class="card-header">
        <h5>Analysis Results</h5>
      </div>
      <div class="card-body">
        <div class="alert alert-success mb-3">
          <h5>Analysis complete!</h5>
          <p>Found {{ results.totalCitations || results.citations_count }} citations.</p>
        </div>
        <div class="mt-3">
          <h6>Citation Summary:</h6>
          <ul class="list-group">
            <li class="list-group-item d-flex justify-content-between align-items-center">
              Confirmed Citations
              <span class="badge bg-success rounded-pill">{{ results.confirmedCount || results.confirmed_count }}</span>
            </li>
            <li class="list-group-item d-flex justify-content-between align-items-center" v-if="results.unconfirmedCount || results.unconfirmed_count">
              Unconfirmed Citations
              <span class="badge bg-danger rounded-pill">{{ results.unconfirmedCount || results.unconfirmed_count }}</span>
            </li>
            <li class="list-group-item d-flex justify-content-between align-items-center" v-if="results.multitoolCount || results.multitool_count">
              Verified with Multi-tool
              <span class="badge bg-info rounded-pill">{{ results.multitoolCount || results.multitool_count }}</span>
            </li>
          </ul>
        </div>
        <!-- Tabs for Citations and Unlikely Citations -->
        <ul class="nav nav-tabs mt-4" role="tablist">
          <li class="nav-item" role="presentation">
            <button class="nav-link" :class="{ active: activeTab === 'citations' }" @click="activeTab = 'citations'" type="button">Citations Found</button>
          </li>
          <li class="nav-item" role="presentation">
            <button class="nav-link" :class="{ active: activeTab === 'unlikely' }" @click="activeTab = 'unlikely'" type="button">
              Unlikely Citations <span v-if="results.unlikely_citations && results.unlikely_citations.length" class="badge bg-warning text-dark ms-1">{{ results.unlikely_citations.length }}</span>
            </button>
          </li>
        </ul>
        <div class="tab-content mt-3">
          <!-- Citations Found Tab -->
          <div class="tab-pane fade" :class="{ show: activeTab === 'citations', active: activeTab === 'citations' }">
            <div v-if="results.validation_results && results.validation_results.length">
              <h6>Citations Found:</h6>
              <div class="table-responsive">
                <table class="table table-striped table-hover">
                  <thead>
                    <tr>
                      <th>Citation</th>
                      <th>Status</th>
                      <th>Validation Method</th>
                      <th>Case Name</th>
                      <th>Error</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(result, index) in results.validation_results" :key="'citation-'+index">
                      <td v-html="result.citation ? formatCitation(result.citation) : '&nbsp;'"></td>
                      <td>
                        <span v-if="result.metadata && result.metadata.explanation">
                          <i class="fas fa-exclamation-triangle text-warning me-1"></i>
                          {{ result.metadata.explanation }}
                        </span>
                        <span v-else class="badge" :class="result.verified ? 'bg-success' : 'bg-danger'">
                          {{ result.verified ? 'Verified' : 'Not Verified' }}
                        </span>
                      </td>
                      <td>
                        <span v-if="result.validation_method" class="badge" :class="getBadgeClass(result.validation_method)">
                          {{ result.validation_method }}
                        </span>
                        <span v-else>-</span>
                      </td>
                      <td>{{ result.case_name || '-' }}</td>
                      <td>
                        <span v-if="result.metadata && result.metadata.explanation">
                          <i class="fas fa-exclamation-triangle text-warning me-1"></i>
                          {{ result.metadata.explanation }}
                        </span>
                        <span v-else>-</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else class="alert alert-info">No citations found.</div>
          </div>
          <!-- Unlikely Citations Tab -->
          <div class="tab-pane fade" :class="{ show: activeTab === 'unlikely', active: activeTab === 'unlikely' }">
            <div v-if="results.unlikely_citations && results.unlikely_citations.length">
              <h6>Unlikely Citations (Artifacts or Invalid):</h6>
              <div class="table-responsive">
                <table class="table table-striped table-hover">
                  <thead>
                    <tr>
                      <th>Citation Text</th>
                      <th>Reason</th>
                      <th>Metadata</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(citation, idx) in results.unlikely_citations" :key="'unlikely-'+idx">
                      <td>{{ citation.citation_text }}</td>
                      <td>
                        <span class="badge bg-warning text-dark">
                          {{ citation.metadata && citation.metadata.invalid_reason ? citation.metadata.invalid_reason : 'Unknown' }}
                        </span>
                      </td>
                      <td>
                        <pre class="mb-0">{{ citation.metadata }}</pre>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else class="alert alert-info">No unlikely citations detected.</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { formatCitation } from '@/utils/citationFormatter';

export default {
  name: 'ReusableResults',
  props: {
    results: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      activeTab: 'citations'
    }
  },
  computed: {
    hasTechnicalError() {
      if (!this.results || !Array.isArray(this.results.validation_results)) return false;
      return this.results.validation_results.some(r => r.metadata && r.metadata.explanation && r.metadata.explanation.toLowerCase().includes('technical error'));
    }
  },
  methods: {
    formatCitation,
    getBadgeClass(method) {
      if (!method) return 'bg-secondary';
      const map = {
        'CourtListener': 'bg-primary',
        'Eyecite': 'bg-info',
        'Regex': 'bg-secondary',
        'Multitool': 'bg-info',
      };
      return map[method] || 'bg-secondary';
    }
  }
};
</script>

<style scoped>
.table th, .table td {
  vertical-align: middle;
}
</style>


<style scoped>
.table th, .table td {
  vertical-align: middle;
}
</style>

<!--
Backend Python snippet for citation_utils.py:

# ... inside your error handling for verify_citation ...
except TypeError as e:
    error_message = str(e)
    if "unexpected keyword argument 'timeout'" in error_message:
        user_message = (
            "Verification failed due to a technical error. "
            "This may be a temporary issue with the verification service. "
            "Please try again later or contact support if the problem persists."
        )
    else:
        user_message = "Verification failed due to an unexpected error."
    citation['metadata']['explanation'] = user_message
# ...
-->

