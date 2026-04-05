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
          <span>{{ helpers.getClusterSubmittedName(cluster) }}</span>,
          <span>{{ helpers.getClusterSubmittedDate(cluster) }}</span>
        </a>
      </template>
      <template v-else>
        <span>{{ helpers.getClusterSubmittedName(cluster) }}</span>,
        <span>{{ helpers.getClusterSubmittedDate(cluster) }}</span>
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
    <div v-if="helpers.getClusterVerifyingName(cluster) || helpers.getClusterVerifyingDate(cluster)" class="cluster-line verifying-as">
      <strong>Verified as: </strong>
      <span :class="{ 'highlight-mismatch': helpers.hasNameMismatch(cluster) }">{{ helpers.getClusterVerifyingName(cluster) }}</span>,
      <span :class="{ 'highlight-mismatch': helpers.hasDateMismatch(cluster) }">{{ helpers.getClusterVerifyingDate(cluster) }}</span>
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
  background: var(--ui-surface);
  border: 1px solid var(--ui-border);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  transition: border-color 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease;
  box-shadow: 0 2px 4px var(--ui-card-shadow);
  color: var(--ui-text);
}
.cluster-item:hover {
  box-shadow: 0 8px 16px var(--ui-card-shadow-hover);
  border-color: var(--ui-accent);
  transform: translateY(-2px);
}
.cluster-line { margin-bottom: 8px; line-height: 1.6; }
.cluster-line:last-child { margin-bottom: 0; }
.verifying-source { font-size: 1.15em; font-weight: 600; color: var(--ui-text); }
.canonical-link { color: var(--ui-link); text-decoration: none; font-weight: 600; }
.canonical-link:hover { color: var(--ui-link-hover); }
.source-badge { color: var(--ui-text-muted); font-size: 0.9em; }
.mismatch-badge { margin-left: 8px; color: var(--status-parallel-fg); }
.merge-badge { margin-left: 8px; color: var(--ui-accent); }
.submitted-document { color: var(--ui-text-secondary); font-size: 0.95em; margin-top: 8px; padding-left: 4px; border-left: 3px solid var(--ui-divider-strong); }
.verifying-as { color: var(--ui-text-secondary); font-size: 0.95em; margin-top: 8px; padding-left: 4px; border-left: 3px solid var(--ui-divider-strong); }
.highlight-mismatch { background: var(--ui-mismatch-highlight-bg); padding: 2px 6px; border-radius: 3px; font-weight: 600; border: 1px solid var(--ui-mismatch-highlight-border); color: var(--ui-text); }
.found-canonical-date { color: var(--ui-text-muted); font-size: 0.9em; margin-left: 8px; font-style: italic; }
.cluster-citations { margin: 15px 0; }
.citation-line { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.citation-text { font-family: 'Courier New', Consolas, monospace; background: var(--ui-code-bg); padding: 4px 10px; border-radius: 6px; font-size: 0.9em; font-weight: 500; border: 1px solid var(--ui-code-border); color: var(--ui-code-fg); }
.citation-status { font-weight: 600; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; }
.citation-extracted-label { color: var(--ui-text-muted); font-size: 0.9em; }
.status-verified { color: var(--status-verified-fg); background: var(--status-verified-bg); }
.status-parallel { color: var(--status-parallel-fg); background: var(--status-parallel-bg); }
.status-unverified { color: var(--status-unverified-fg); background: var(--status-unverified-bg); }
.status-possible-match { color: var(--status-possible-fg); background: var(--status-possible-bg); border: 1px solid var(--status-possible-border); }
</style>
