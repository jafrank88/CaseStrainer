<template>
  <div class="cluster-item">
    <div class="cluster-line verifying-source">
      <template v-if="helpers.getClusterVerifyingUrl(cluster) && isGoogleSearchUrl(helpers.getClusterVerifyingUrl(cluster))">
        <a :href="helpers.getClusterVerifyingUrl(cluster)" target="_blank" rel="noopener" class="canonical-link">
          Search Google for: {{ cluster.search_fallback_label || helpers.getClusterSubmittedName(cluster) || 'case' }}
        </a>
      </template>
      <template v-else-if="helpers.getClusterVerifyingUrl(cluster)">
        <a :href="helpers.getClusterVerifyingUrl(cluster)" target="_blank" rel="noopener" class="canonical-link">
          <span :class="{ 'highlight-mismatch': helpers.hasNameMismatch(cluster) }">{{ helpers.getClusterVerifyingName(cluster) }}</span>,
          <span :class="{ 'highlight-mismatch': helpers.hasDateMismatch(cluster) }">{{ helpers.getClusterVerifyingDate(cluster) }}</span>
        </a>
      </template>
      <template v-else>
        <span :class="{ 'highlight-mismatch': helpers.hasNameMismatch(cluster) }">{{ helpers.getClusterVerifyingName(cluster) }}</span>,
        <span :class="{ 'highlight-mismatch': helpers.hasDateMismatch(cluster) }">{{ helpers.getClusterVerifyingDate(cluster) }}</span>
        <!-- FIX 2026-02-24: Show found canonical date when not verified but date differs -->
        <span v-if="helpers.getClusterFoundCanonicalDate(cluster)" class="found-canonical-date">
          (CourtListener: {{ helpers.getClusterFoundCanonicalDate(cluster) }})
        </span>
      </template>
      <span v-if="showMismatchBadge && (helpers.hasNameMismatch(cluster) || helpers.hasDateMismatch(cluster))" class="source-badge mismatch-badge">
        <strong>
          <template v-if="helpers.hasNameMismatch(cluster) && helpers.hasDateMismatch(cluster)">⚠️ Different name & date</template>
          <template v-else-if="helpers.hasNameMismatch(cluster)">⚠️ Different name</template>
          <template v-else-if="helpers.hasDateMismatch(cluster)">⚠️ Different date</template>
        </strong>
      </span>
    </div>
    <div class="cluster-line submitted-document">
      <strong>Extracted from Document: </strong>
      <span :class="{ 'highlight-mismatch': helpers.hasNameMismatch(cluster) }">{{ helpers.getClusterSubmittedName(cluster) }}</span>,
      <span :class="{ 'highlight-mismatch': helpers.hasDateMismatch(cluster) }">{{ helpers.getClusterSubmittedDate(cluster) }}</span>
      <span v-if="cluster.cross_document_merge" class="merge-badge">
        <strong>📄 Merged from {{ cluster.merge_source_count || 2 }} documents</strong>
      </span>
    </div>
    <div class="cluster-citations">
      <div v-for="(citation, index) in helpers.getClusterCitations(cluster)" :key="`${cluster.cluster_id}-${sectionKey}-${index}`" class="cluster-line citation-line">
        <strong>Citation {{ index + 1 }}: </strong>
        <span class="citation-text">{{ helpers.formatCitationText(citation) }}</span>
        <span class="citation-status" :class="helpers.getCitationStatusClass(citation, cluster)">{{ helpers.getCitationStatusText(citation, cluster) }}</span>
        <span v-if="helpers.getCitationExtractedLabel(citation, cluster)" class="citation-extracted-label"> (from document: {{ helpers.getCitationExtractedLabel(citation, cluster) }})</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ClusterCard',
  props: {
    cluster: { type: Object, required: true },
    sectionKey: { type: String, default: 'cluster' },
    helpers: {
      type: Object,
      required: true,
      // getClusterVerifyingUrl, getClusterVerifyingName, getClusterVerifyingDate,
      // getClusterSubmittedName, getClusterSubmittedDate, hasNameMismatch, hasDateMismatch,
      // getClusterCitations, formatCitationText, getCitationStatusClass, getCitationStatusText, getCitationExtractedLabel
    },
    showMismatchBadge: { type: Boolean, default: true },
  },
  methods: {
    isGoogleSearchUrl(url) {
      return typeof url === 'string' && url.startsWith('https://www.google.com/search?')
    },
  },
}
</script>

<style scoped>
.cluster-item {
  background: #ffffff;
  border: 1px solid #e8eaf0;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.cluster-item:hover {
  box-shadow: 0 8px 16px rgba(0,0,0,0.08);
  border-color: #2196F3;
  transform: translateY(-2px);
}
.cluster-line { margin-bottom: 8px; line-height: 1.6; }
.cluster-line:last-child { margin-bottom: 0; }
.verifying-source { font-size: 1.15em; font-weight: 600; color: #1a1a1a; }
.canonical-link { color: #1976D2; text-decoration: none; font-weight: 600; }
.canonical-link:hover { color: #1565C0; }
.source-badge { color: #666; font-size: 0.9em; }
.mismatch-badge { margin-left: 8px; color: #FF6F00; }
.merge-badge { margin-left: 8px; color: #2196F3; }
.submitted-document { color: #5f6368; font-size: 0.95em; margin-top: 8px; padding-left: 4px; border-left: 3px solid #f0f0f0; }
.highlight-mismatch { background: #FFEB3B; padding: 2px 6px; border-radius: 3px; font-weight: 600; border: 1px solid #FBC02D; }
.found-canonical-date { color: #666; font-size: 0.9em; margin-left: 8px; font-style: italic; }
.cluster-citations { margin: 15px 0; }
.citation-line { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.citation-text { font-family: 'Courier New', Consolas, monospace; background: #e8f4fd; padding: 4px 10px; border-radius: 6px; font-size: 0.9em; font-weight: 500; border: 1px solid #d0e9ff; color: #0d47a1; }
.citation-status { font-weight: 600; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; }
.citation-extracted-label { color: #666; font-size: 0.9em; }
.status-verified { color: #4CAF50; background: #E8F5E8; }
.status-parallel { color: #FF9800; background: #FFF3E0; }
.status-unverified { color: #f44336; background: #FFEBEE; }
.status-possible-match { color: #FF9800; background: #FFF8E1; border: 1px solid #FFB74D; }
</style>
