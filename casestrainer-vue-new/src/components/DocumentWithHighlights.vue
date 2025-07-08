<template>
  <div class="document-view">
    <span v-for="(segment, idx) in highlightedSegments" :key="'seg-'+idx">
      <template v-if="segment.citation">
        <span
          :id="'citation-' + segment.citationIndex"
          class="citation-inline"
          :class="segment.status"
          @click="$emit('citation-click', segment.citationIndex)"
        >
          {{ segment.text }}
        </span>
      </template>
      <template v-else>
        {{ segment.text }}
      </template>
    </span>
  </div>
</template>

<script>
export default {
  name: 'DocumentWithHighlights',
  props: {
    documentText: {
      type: String,
      required: true
    },
    citations: {
      type: Array,
      required: true
    }
  },
  computed: {
    highlightedSegments() {
      // Split the document text into segments, wrapping citations
      const doc = this.documentText || '';
      const citations = this.citations || [];
      if (!doc || citations.length === 0) return [{ text: doc }];
      // Sort citations by start_index
      const sorted = citations.slice().sort((a, b) => a.start_index - b.start_index);
      let segments = [];
      let lastIdx = 0;
      sorted.forEach((cit, idx) => {
        if (cit.start_index > lastIdx) {
          segments.push({ text: doc.slice(lastIdx, cit.start_index) });
        }
        segments.push({
          text: doc.slice(cit.start_index, cit.end_index),
          citation: true,
          citationIndex: idx,
          status: cit.verified ? 'verified' : (cit.status || 'unverified'),
          ...cit
        });
        lastIdx = cit.end_index;
      });
      if (lastIdx < doc.length) {
        segments.push({ text: doc.slice(lastIdx) });
      }
      return segments;
    }
  }
};
</script>

<style scoped>
.document-view {
  background: #f8fafc;
  border-radius: 8px;
  padding: 1rem;
  font-size: 1.08rem;
  line-height: 1.7;
  margin-bottom: 1rem;
}
.citation-inline {
  cursor: pointer;
  border-radius: 4px;
  padding: 0 2px;
  transition: background 0.2s;
}
.citation-inline.verified {
  background: #e6f9e6;
  border: 1px solid #198754;
}
.citation-inline.unverified {
  background: #fffbe6;
  border: 1px solid #ffc107;
}
.citation-inline.hallucinated {
  background: #fdeaea;
  border: 1px solid #dc3545;
}
.citation-inline.active {
  box-shadow: 0 0 0 2px #1976d2;
  background: #e3f2fd;
}
</style> 