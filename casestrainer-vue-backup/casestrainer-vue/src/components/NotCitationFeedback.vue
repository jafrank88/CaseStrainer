<template>
  <div class="not-citation-feedback">
    <button v-if="!isFlagged" class="btn btn-outline-danger btn-sm" @click="flagNotCitation">
      Not a citation
    </button>
    <span v-else class="text-success">Flagged as not a citation</span>
    <div v-if="showPatternInput" class="mt-2">
      <input v-model="pattern" placeholder="Enter regex pattern (optional)" class="form-control form-control-sm" />
      <button class="btn btn-primary btn-sm mt-1" @click="submitPattern">Submit Pattern</button>
      <button class="btn btn-secondary btn-sm mt-1 ms-2" @click="cancelPattern">Cancel</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'NotCitationFeedback',
  props: {
    citation: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      isFlagged: false,
      showPatternInput: false,
      pattern: ''
    };
  },
  methods: {
    flagNotCitation() {
      this.showPatternInput = true;
      this.pattern = this.citation;
    },
    async submitPattern() {
      const isRegex = this.pattern !== this.citation;
      try {
        await axios.post('/casestrainer/api/not_citations', {
          pattern: this.pattern,
          is_regex: isRegex
        });
        this.isFlagged = true;
        this.showPatternInput = false;
      } catch (e) {
        alert('Failed to submit pattern: ' + e);
      }
    },
    cancelPattern() {
      this.showPatternInput = false;
    }
  }
};
</script>

<style scoped>
.not-citation-feedback {
  display: inline-block;
  margin-left: 1rem;
}
</style>
