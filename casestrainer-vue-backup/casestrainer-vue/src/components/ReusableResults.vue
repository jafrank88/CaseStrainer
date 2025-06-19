<template>
  <div v-if="results">
    <!-- Summary Bar (Total, Valid, Invalid) -->
    <div class="summary-bar mb-3">
      <span class="badge badge-total">Total: {{ totalCount }}</span>
      <span class="badge badge-valid">Valid: {{ validCount }}</span>
      <span class="badge badge-invalid">Invalid: {{ invalidCount }}</span>
    </div>
    <!-- Gamified Summary Bar -->
    <div class="summary-bar mb-3">
      <span class="summary-count verified"><i class="fas fa-check-circle"></i> Verified: {{ verifiedCount }}</span>
      <span class="summary-count unverified"><i class="fas fa-exclamation-triangle"></i> Unverified: {{ unverifiedCount }}</span>
      <span class="summary-count hallucinated"><i class="fas fa-bug"></i> Hallucinated: {{ hallucinatedCount }}</span>
      <span class="summary-score" v-if="scoreBadge">
        <i :class="scoreBadge.icon"></i> {{ scoreBadge.label }}
      </span>
    </div>
    <div v-if="showConfetti" class="confetti">🎉</div>
    <!-- Download Report Button -->
    <div class="mb-3 text-end">
      <button class="btn btn-outline-primary btn-sm" @click="downloadReport">
        <i class="fas fa-download"></i> Download Report
      </button>
    </div>
    <!-- Inline Highlighted Document -->
    <div class="document-view mb-4" v-if="results.documentText">
      <span v-for="(segment, idx) in highlightedSegments" :key="'seg-'+idx">
        <template v-if="segment.citation">
          <span v-if="segment.status==='verified' && segment.authoritative_url">
            <a :href="segment.authoritative_url" target="_blank" class="citation-inline-link">
              <span
                class="citation-inline"
                :class="segment.status"
                @click.stop="showCitationDetails(segment)"
                @mouseenter="hoverCitation(segment)"
                @mouseleave="hoverCitation(null)"
                tabindex="0"
                :aria-label="segment.status + ' citation: ' + segment.text"
              >
                <i class="fas fa-trophy text-warning me-1"></i>
                {{ segment.text }}
              </span>
            </a>
          </span>
          <span v-else
            class="citation-inline"
            :class="segment.status"
            @click="showCitationDetails(segment)"
            @mouseenter="hoverCitation(segment)"
            @mouseleave="hoverCitation(null)"
            tabindex="0"
            :aria-label="segment.status + ' citation: ' + segment.text"
          >
            <i v-if="segment.status==='verified'" class="fas fa-trophy text-warning me-1"></i>
            <i v-else-if="segment.status==='unverified'" class="fas fa-question-circle text-warning me-1"></i>
            <i v-else class="fas fa-bug text-danger me-1"></i>
            {{ segment.text }}
          </span>
        </template>
        <template v-else>
          {{ segment.text }}
        </template>
      </span>
    </div>
    <!-- Citation Details Popup/Sidebar -->
    <div v-if="activeCitation" class="citation-details-popup">
      <button class="btn-close float-end" @click="activeCitation=null"></button>
      <h5>
        <span :class="'badge ' + statusClass(activeCitation.status)">
          {{ activeCitation.status | capitalize }}
        </span>
        <span v-if="activeCitation.status==='verified'" class="ms-2"><i class="fas fa-trophy text-warning"></i> Verified!</span>
      </h5>
      <p><strong>Citation:</strong> {{ activeCitation.text }}</p>
      <p><strong>Case Name:</strong> {{ activeCitation.case_name }}</p>
      <p><strong>Status:</strong> {{ activeCitation.status }}</p>
      <p><strong>Reason:</strong> {{ activeCitation.reason }}</p>
      <p><strong>Context:</strong> <span class="context-snippet">{{ activeCitation.context }}</span></p>
      <div v-if="activeCitation.suggestions && activeCitation.suggestions.length">
        <h6>Suggestions:</h6>
        <ul>
          <li v-for="(s, i) in activeCitation.suggestions" :key="'sugg-'+i">
            <span class="suggestion-citation">{{ s.corrected_citation }}</span>
            <span class="suggestion-explanation">({{ s.explanation }})</span>
          </li>
        </ul>
      </div>
      <div v-if="activeCitation.authoritative_url">
        <a :href="activeCitation.authoritative_url" target="_blank" class="btn btn-outline-success btn-sm mt-2">
          <i class="fas fa-link"></i> View Authoritative Source
        </a>
      </div>
      <div v-if="activeCitation.similar_matches && activeCitation.similar_matches.length">
        <h6 class="mt-3">Similar Matches:</h6>
        <ul>
          <li v-for="(m, i) in activeCitation.similar_matches" :key="'match-'+i">
            {{ m.corrected_citation }} <span class="text-muted">({{ m.similarity | percent }})</span>
          </li>
        </ul>
      </div>
    </div>
    <!-- Fallback Table View -->
    <div class="card mt-4">
      <div class="card-header">
        <h5>Analysis Results (Table)</h5>
      </div>
      <div class="card-body">
        <div class="table-responsive">
          <table class="table table-striped table-hover">
            <thead>
              <tr>
                <th>Citation</th>
                <th>Status</th>
                <th>Validation Method</th>
                <th>Case Name</th>
                <th>Suggestions</th>
                <th>Authoritative Link</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(result, index) in results.validation_results" :key="'citation-'+index">
                <td>
                  <span v-if="result.verified && result.authoritative_url">
                    <a :href="result.authoritative_url" target="_blank">
                      <strong v-if="result.case_name">{{ result.case_name }}</strong>
                      <span v-else>{{ result.text }}</span>
                    </a>
                  </span>
                  <span v-else>
                    <strong v-if="result.case_name">{{ result.case_name }}</strong>
                    <span v-else>{{ result.text }}</span>
                  </span>
                  <span v-if="result.case_name && result.text && result.case_name !== result.text" class="ms-2 text-muted">({{ result.text }})</span>
                </td>
                <td><span :class="'badge ' + statusClass(result.status)">{{ result.status | capitalize }}</span></td>
                <td>{{ result.source }}</td>
                <td>{{ result.case_name }}</td>
                <td>
                  <ul v-if="result.suggestions && result.suggestions.length">
                    <li v-for="(s, i) in result.suggestions" :key="'sugg-table-'+i">
                      {{ s.corrected_citation }} <span class="text-muted">({{ s.explanation }})</span>
                    </li>
                  </ul>
                  <span v-else>-</span>
                </td>
                <td>
                  <a v-if="result.authoritative_url" :href="result.authoritative_url" target="_blank">
                    <i class="fas fa-link"></i> Source
                  </a>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { formatCitation } from '@/utils/citationFormatter';

function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

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
      activeTab: 'citations',
      activeCitation: null,
      hoveredCitation: null
    }
  },
  computed: {
    totalCount() {
      return (this.results.validation_results || []).length;
    },
    validCount() {
      return (this.results.validation_results || []).filter(c => c.status === 'verified' || c.verified).length;
    },
    invalidCount() {
      return (this.results.validation_results || []).filter(c => c.status !== 'verified' && !c.verified).length;
    },
    verifiedCount() {
      return (this.results.validation_results || []).filter(c => c.status === 'verified').length;
    },
    unverifiedCount() {
      return (this.results.validation_results || []).filter(c => c.status === 'unverified').length;
    },
    hallucinatedCount() {
      return (this.results.validation_results || []).filter(c => c.status === 'hallucinated').length;
    },
    scoreBadge() {
      const total = (this.results.validation_results || []).length;
      const verified = this.verifiedCount;
      if (total === 0) return null;
      const percent = verified / total;
      if (percent === 1) return { label: 'Gold: 100% Verified!', icon: 'fas fa-trophy text-warning' };
      if (percent >= 0.8) return { label: 'Silver: 80%+ Verified', icon: 'fas fa-medal text-secondary' };
      if (percent >= 0.5) return { label: 'Bronze: 50%+ Verified', icon: 'fas fa-award text-warning' };
      return null;
    },
    showConfetti() {
      const total = (this.results.validation_results || []).length;
      return total > 0 && this.verifiedCount === total;
    },
    highlightedSegments() {
      // Split the document text into segments, wrapping citations
      const doc = this.results.documentText || '';
      const citations = this.results.validation_results || [];
      if (!doc || citations.length === 0) return [{ text: doc }];
      // Sort citations by start_index
      const sorted = citations.slice().sort((a, b) => a.start_index - b.start_index);
      let segments = [];
      let lastIdx = 0;
      sorted.forEach(cit => {
        if (cit.start_index > lastIdx) {
          segments.push({ text: doc.slice(lastIdx, cit.start_index) });
        }
        segments.push({
          text: doc.slice(cit.start_index, cit.end_index),
          citation: true,
          status: cit.status,
          ...cit
        });
        lastIdx = cit.end_index;
      });
      if (lastIdx < doc.length) {
        segments.push({ text: doc.slice(lastIdx) });
      }
      return segments;
    }
  },
  methods: {
    formatCitation,
    statusClass(status) {
      if (status === 'verified') return 'bg-success';
      if (status === 'unverified') return 'bg-warning text-dark';
      if (status === 'hallucinated') return 'bg-danger';
      return 'bg-secondary';
    },
    showCitationDetails(citation) {
      this.activeCitation = citation;
    },
    hoverCitation(citation) {
      this.hoveredCitation = citation;
    },
    downloadReport() {
      // Generate a CSV report of flagged citations
      const rows = [
        ['Citation', 'Status', 'Reason', 'Suggestions', 'Authoritative URL', 'Context']
      ];
      (this.results.validation_results || []).forEach(cit => {
        rows.push([
          cit.text,
          cit.status,
          cit.reason,
          (cit.suggestions || []).map(s => s.corrected_citation).join('; '),
          cit.authoritative_url || '',
          cit.context || ''
        ]);
      });
      const csv = rows.map(r => r.map(x => '"' + (x || '').replace(/"/g, '""') + '"').join(',')).join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'citation_report.csv';
      a.click();
      URL.revokeObjectURL(url);
    }
  },
  filters: {
    capitalize,
    percent(val) {
      if (typeof val !== 'number') return '';
      return Math.round(val * 100) + '%';
    }
  }
};
</script>

<style scoped>
.badge {
  font-size: 1.1rem;
  font-weight: 600;
  margin-right: 0.5rem;
  padding: 0.5em 1em;
  border-radius: 0.5em;
  display: inline-block;
}
.badge-total { background: #1976d2; color: #fff; }
.badge-valid { background: #2e7d32; color: #fff; }
.badge-invalid { background: #d32f2f; color: #fff; }
.summary-bar { margin-bottom: 1.5rem; }
.summary-bar {
  display: flex;
  gap: 1.5rem;
  align-items: center;
  font-size: 1.1rem;
  margin-bottom: 1rem;
}
.summary-count {
  font-weight: 500;
}
.summary-count.verified { color: #198754; }
.summary-count.unverified { color: #ffc107; }
.summary-count.hallucinated { color: #dc3545; }
.summary-score { font-size: 1.2rem; margin-left: auto; }
.confetti { font-size: 2.5rem; text-align: center; margin-bottom: 1rem; animation: pop 1s; }
@keyframes pop { 0% { transform: scale(0.5); } 80% { transform: scale(1.2); } 100% { transform: scale(1); } }
.document-view { background: #f8fafc; border-radius: 8px; padding: 1rem; font-size: 1.08rem; line-height: 1.7; margin-bottom: 1rem; }
.citation-inline { cursor: pointer; border-radius: 4px; padding: 0 2px; transition: background 0.2s; }
.citation-inline.verified { background: #e6f9e6; border: 1px solid #198754; }
.citation-inline.unverified { background: #fffbe6; border: 1px solid #ffc107; }
.citation-inline.hallucinated { background: #fdeaea; border: 1px solid #dc3545; }
.citation-details-popup { position: fixed; top: 10%; right: 2%; width: 350px; background: #fff; border: 1px solid #dee2e6; border-radius: 8px; box-shadow: 0 2px 16px rgba(0,0,0,0.12); z-index: 1000; padding: 1.5rem; max-height: 80vh; overflow-y: auto; }
.citation-details-popup .btn-close { float: right; }
.citation-details-popup h5 { margin-top: 0; }
.context-snippet { background: #f1f3f4; border-radius: 4px; padding: 2px 4px; }
.suggestion-citation { font-weight: 500; }
.suggestion-explanation { color: #6c757d; margin-left: 0.5rem; }
.citation-inline-link {
  text-decoration: none;
}
.citation-inline-link:hover .citation-inline {
  background: #e3fcec;
  box-shadow: 0 0 0 2px #19875433;
}
</style>

