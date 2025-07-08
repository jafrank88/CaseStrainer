<template>
  <div class="user-feedback">
    <div class="feedback-header">
      <h4>Citation Feedback & Corrections</h4>
      <p class="text-muted">Help improve our citation extraction by providing corrections or feedback.</p>
    </div>
    
    <div v-for="(citation, index) in citations" :key="citation.citation" class="feedback-item">
      <div class="citation-preview">
        <strong>{{ citation.citation }}</strong>
        <span :class="['status-badge', citation.verified ? 'verified' : 'unverified']">
          {{ citation.verified ? 'Verified' : 'Unverified' }}
        </span>
      </div>
      
      <div class="correction-fields">
        <!-- Case Name Correction -->
        <div class="field-group">
          <label>Case Name:</label>
          <div class="current-value">
            <span class="label">Current:</span>
            <span class="value">{{ citation.case_name || 'N/A' }}</span>
          </div>
          <input 
            v-model="corrections[index].case_name" 
            type="text" 
            placeholder="Correct case name..."
            class="correction-input"
          />
        </div>
        
        <!-- Date Correction -->
        <div class="field-group">
          <label>Date:</label>
          <div class="current-value">
            <span class="label">Current:</span>
            <span class="value">{{ citation.canonical_date || citation.year || 'N/A' }}</span>
          </div>
          <input 
            v-model="corrections[index].date" 
            type="text" 
            placeholder="Correct date (YYYY-MM-DD)..."
            class="correction-input"
          />
        </div>
        
        <!-- Citation Text Correction -->
        <div class="field-group">
          <label>Citation Text:</label>
          <div class="current-value">
            <span class="label">Current:</span>
            <span class="value">{{ citation.citation }}</span>
          </div>
          <input 
            v-model="corrections[index].citation_text" 
            type="text" 
            placeholder="Correct citation text..."
            class="correction-input"
          />
        </div>
        
        <!-- Feedback Type -->
        <div class="field-group">
          <label>Feedback Type:</label>
          <select v-model="corrections[index].feedback_type" class="feedback-select">
            <option value="">Select feedback type...</option>
            <option value="case_name_wrong">Case name is wrong</option>
            <option value="date_wrong">Date is wrong</option>
            <option value="citation_format_wrong">Citation format is wrong</option>
            <option value="false_positive">This is not a citation</option>
            <option value="missing_citation">Missing citation</option>
            <option value="other">Other issue</option>
          </select>
        </div>
        
        <!-- Additional Comments -->
        <div class="field-group">
          <label>Additional Comments:</label>
          <textarea 
            v-model="corrections[index].comments" 
            placeholder="Any additional comments or context..."
            class="comments-textarea"
            rows="2"
          ></textarea>
        </div>
      </div>
    </div>
    
    <div class="feedback-actions">
      <button @click="submitFeedback" class="btn btn-primary" :disabled="!hasChanges">
        Submit Feedback
      </button>
      <button @click="resetCorrections" class="btn btn-secondary">
        Reset Changes
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UserFeedback',
  props: {
    citations: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      corrections: {}
    };
  },
  computed: {
    hasChanges() {
      return Object.values(this.corrections).some(correction => 
        correction.case_name || correction.date || correction.citation_text || 
        correction.feedback_type || correction.comments
      );
    }
  },
  watch: {
    citations: {
      immediate: true,
      handler(newCitations) {
        // Initialize corrections object for each citation
        this.corrections = {};
        newCitations.forEach((citation, index) => {
          this.corrections[index] = {
            case_name: '',
            date: '',
            citation_text: '',
            feedback_type: '',
            comments: ''
          };
        });
      }
    }
  },
  methods: {
    submitFeedback() {
      const feedback = {
        timestamp: new Date().toISOString(),
        corrections: Object.entries(this.corrections)
          .filter(([index, correction]) => 
            correction.case_name || correction.date || correction.citation_text || 
            correction.feedback_type || correction.comments
          )
          .map(([index, correction]) => ({
            original_citation: this.citations[index],
            corrections: correction
          }))
      };
      
      this.$emit('feedback-submitted', feedback);
      this.resetCorrections();
    },
    
    resetCorrections() {
      this.citations.forEach((citation, index) => {
        this.corrections[index] = {
          case_name: '',
          date: '',
          citation_text: '',
          feedback_type: '',
          comments: ''
        };
      });
    }
  }
};
</script>

<style scoped>
.user-feedback {
  background: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.feedback-header {
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 1rem;
}

.feedback-header h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.feedback-item {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1rem;
  background: #fafafa;
}

.citation-preview {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-badge.verified {
  background: #d4edda;
  color: #155724;
}

.status-badge.unverified {
  background: #fff3cd;
  color: #856404;
}

.correction-fields {
  display: grid;
  gap: 1rem;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field-group label {
  font-weight: 500;
  color: #555;
  font-size: 0.9rem;
}

.current-value {
  display: flex;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #666;
}

.current-value .label {
  font-weight: 500;
}

.correction-input,
.feedback-select,
.comments-textarea {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.correction-input:focus,
.feedback-select:focus,
.comments-textarea:focus {
  outline: none;
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

.feedback-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary {
  background: #1976d2;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1565c0;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

.btn-secondary:hover {
  background: #e0e0e0;
}
</style> 