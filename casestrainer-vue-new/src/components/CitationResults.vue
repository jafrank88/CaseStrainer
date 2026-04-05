<template>
  <div class="citation-results" role="region" aria-label="Citation analysis details">
    <!-- Perfect Score Celebration (SHOW ONLY IF 100% VERIFIED AND NO MISMATCHES) -->
    <div v-if="allCitationsVerified && (mismatchClusters?.length || 0) === 0" class="perfect-score-celebration">
      <div class="celebration-content">
        <h2><span aria-hidden="true">🎉 </span>Perfect Score!</h2>
        <p>All {{ (verifiedCitations?.length || 0) + (verifiedByParallelCitations?.length || 0) }} citations have been successfully verified!</p>
        <div class="celebration-stats">
          <div><span aria-hidden="true">✅ </span>{{ verifiedCitations?.length || 0 }} Citations Verified</div>
          <div v-if="(verifiedByParallelCitations?.length || 0) > 0"><span aria-hidden="true">🟠 </span>{{ verifiedByParallelCitations?.length || 0 }} Verified by Parallel</div>
          <div><span aria-hidden="true">📚 </span>{{ clusters?.length || 0 }} Cases Found</div>
        </div>
      </div>
    </div>

    <!-- Coverage banner when there are mismatches -->
    <div v-if="allCitationsVerified && (mismatchClusters?.length || 0) > 0" class="results-content results-content-coverage">
      <div class="results-header">
        <h2><span aria-hidden="true">✅ </span>All Citations Verified</h2>
        <p>{{ (verifiedCitations?.length || 0) + (verifiedByParallelCitations?.length || 0) }} citation{{ ((verifiedCitations?.length || 0) + (verifiedByParallelCitations?.length || 0)) !== 1 ? 's' : '' }} verified • {{ mismatchClusters?.length || 0 }} with differences</p>
      </div>
    </div>

    <!-- Citation Results - Show clusters if they exist -->
    <div v-if="(clusters?.length || 0) > 0" class="results-content">
      <div class="results-header">
        <h2>{{ clusters?.length || 0 }} Case{{ (clusters?.length || 0) !== 1 ? 's' : '' }} Found</h2>
        <p>
          {{ citations?.length || 0 }} citation{{ (citations?.length || 0) !== 1 ? 's' : '' }} identified •
          {{ verifiedCitations?.length || 0 }} matched to a source
          <template v-if="clustersUnverified?.length > 0">
            • {{ clustersUnverified.length }} case{{ clustersUnverified.length !== 1 ? 's' : '' }} need review
          </template>
        </p>
        <p class="results-explainer">
          One case can include multiple citations, so citation totals are usually higher than case totals.
        </p>
        <div v-if="results?.metadata?.verification_requested_but_none_matched" class="verification-hint-banner" role="alert">
          <strong>Verification was requested but no citations were matched.</strong>
          {{ results?.metadata?.verification_hint || 'Ensure COURTLISTENER_API_KEY is set in the worker environment (check server/worker logs).' }}
        </div>
      </div>
      
      <div class="clusters-list">
        <template v-if="(clustersUnverified?.length || 0) > 0">
          <div class="results-header">
            <h3><span aria-hidden="true">⏳ </span>Unverified</h3>
            <p class="results-explainer">Some sites with cases block automated tools - click on the link to search the web for unverified cases.</p>
          </div>
          <ClusterCard v-for="cluster in clustersUnverified" :key="cluster.cluster_id + '-unv'" :cluster="cluster" section-key="unv" :helpers="clusterHelpers" :show-mismatch-badge="true" />
        </template>
        <template v-if="(clustersCaseMismatch?.length || 0) > 0">
          <div class="results-header"><h3><span aria-hidden="true">⚠️ </span>Name Differences</h3></div>
          <ClusterCard v-for="cluster in clustersCaseMismatch" :key="cluster.cluster_id + '-nm'" :cluster="cluster" section-key="nm" :helpers="clusterHelpers" :show-mismatch-badge="true" />
        </template>
        <template v-if="(clustersDateMismatch?.length || 0) > 0">
          <div class="results-header"><h3><span aria-hidden="true">📅 </span>Date Differences</h3></div>
          <ClusterCard v-for="cluster in clustersDateMismatch" :key="cluster.cluster_id + '-dm'" :cluster="cluster" section-key="dm" :helpers="clusterHelpers" :show-mismatch-badge="true" />
        </template>
        <template v-if="(clustersOther?.length || 0) > 0">
          <div class="results-header">
            <h3>Possible Matches</h3>
            <p class="results-explainer">These are likely candidates for review and may not include a canonical URL, case name, or year yet.</p>
          </div>
          <ClusterCard v-for="cluster in clustersOther" :key="cluster.cluster_id + '-oth'" :cluster="cluster" section-key="oth" :helpers="clusterHelpers" :show-mismatch-badge="false" />
        </template>
        <template v-if="(clustersVerifiedStrict?.length || 0) > 0">
          <div class="results-header"><h3><span aria-hidden="true">✅ </span>Verified</h3></div>
          <ClusterCard v-for="cluster in clustersVerifiedStrict" :key="cluster.cluster_id + '-verified'" :cluster="cluster" section-key="verified" :helpers="clusterHelpers" :show-mismatch-badge="false" />
        </template>
      </div>
    </div>

    <!-- SECTION 2: Individual Citations (SHOW ONLY IF NO CLUSTERS) -->
    <div v-if="(clusters?.length || 0) === 0 && (citations?.length || 0) > 0" class="results-content">
      <div class="results-header">
        <h2>Individual Citations</h2>
        <p>{{ citations?.length || 0 }} individual citation(s)</p>
      </div>
      
      <div class="citations-list">
        <div v-for="citation in citations" :key="citation.text || citation.citation" class="citation-item">
          <div class="citation-text">{{ formatCitationText(citation) }}</div>
          <div class="citation-status">
            <span
              class="citation-verdict"
              :style="{ color: isEffectivelyVerified(citation) ? 'green' : (citation.true_by_parallel ? '#FF9800' : 'red') }"
            >
              <span class="visually-hidden">Status: </span>
              {{ isEffectivelyVerified(citation) ? '✅ VERIFIED' : (citation.true_by_parallel ? '✅ VERIFIED BY PARALLEL' : '❌ UNVERIFIED') }}
            </span>
            <div v-if="!isEffectivelyVerified(citation) && citation.error" class="verification-error mt-1">
              <small>{{ citation.error }}</small>
            </div>
          </div>
          <div class="citation-details">
            <div><strong>Case:</strong> {{ getDisplayCaseName(citation) }}</div>
            <div><strong>Date:</strong> {{ citation.extracted_date }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- No citations found message -->
    <div v-if="(citations?.length || 0) === 0 && (clusters?.length || 0) === 0" class="no-citations">
      <h2>No Citations Found</h2>
      <p>No legal citations were detected in the provided text.</p>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useCitationClusters } from '@/composables/useCitationClusters'
import * as clusterDisplay from '@/composables/useClusterDisplay'
import ClusterCard from './ClusterCard.vue'

export default {
  name: 'CitationResults',
  components: { ClusterCard },
  props: {
    results: { type: Object, default: null },
    error: { type: String, default: null },
    componentId: { type: String, default: 'default' },
  },
  setup(props) {
    const resultsRef = computed(() => props.results)
    const clusterData = useCitationClusters(resultsRef)
    const { isEffectivelyVerified, isNaAndPartial } = clusterData

    const clusterHelpers = {
      getClusterVerifyingUrl: clusterDisplay.getClusterVerifyingUrl,
      getClusterVerifyingName: clusterDisplay.getClusterVerifyingName,
      getClusterVerifyingDate: clusterDisplay.getClusterVerifyingDate,
      getClusterFoundCanonicalDate: clusterDisplay.getClusterFoundCanonicalDate,
      getClusterSubmittedName: clusterDisplay.getClusterSubmittedName,
      getClusterSubmittedDate: clusterDisplay.getClusterSubmittedDate,
      hasNameMismatch: clusterDisplay.hasNameMismatch,
      hasDateMismatch: clusterDisplay.hasDateMismatch,
      getClusterCitations: clusterDisplay.getClusterCitations,
      getCitationExtractedLabel: clusterDisplay.getCitationExtractedLabel,
      formatCitationText: clusterDisplay.formatCitationText,
      getCitationStatusClass: (citation, cluster) => clusterDisplay.getCitationStatusClass(citation, cluster, isEffectivelyVerified, isNaAndPartial),
      getCitationStatusText: (citation, cluster) => clusterDisplay.getCitationStatusText(citation, cluster, isEffectivelyVerified, isNaAndPartial),
    }

    function inlineCitationStatusClass(citation) {
      if (isEffectivelyVerified(citation)) return 'cite-inline-verified'
      if (citation && citation.true_by_parallel) return 'cite-inline-parallel'
      return 'cite-inline-unverified'
    }

    return {
      ...clusterData,
      clusterHelpers,
      formatCitationText: clusterDisplay.formatCitationText,
      inlineCitationStatusClass,
    }
  },
}
</script>

<style scoped>
.citation-results {
  padding: 20px;
  color: var(--ui-text);
}

.results-content {
  margin-bottom: 30px;
  border: 1px solid var(--ui-border);
  border-radius: 8px;
  padding: 20px;
  background: var(--ui-surface);
}

.results-content-coverage {
  border-color: var(--ui-accent);
  background: var(--ui-info-surface);
}

.results-header {
  margin-bottom: 20px;
}

.results-header h3 {
  font-size: 1.4em;
  color: var(--ui-text-heading);
  margin: 28px 0 18px 0;
  font-weight: 700;
  letter-spacing: -0.01em;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--ui-divider-strong);
}

.results-header h2 {
  font-size: 1.85em;
  color: var(--ui-text);
  margin-bottom: 0.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.results-explainer {
  margin: 6px 0 0 0;
  color: var(--ui-text-secondary);
  font-size: 0.9rem;
}

.citation-details {
  margin-top: 8px;
  font-size: 0.9em;
  color: var(--ui-text-muted);
}

.verification-error {
  margin-top: 4px;
  font-size: 0.85em;
  color: var(--ui-error-text);
  font-style: italic;
}

.verification-hint-banner {
  margin-top: 12px;
  padding: 12px 16px;
  background: var(--ui-warning-banner-bg);
  border: 1px solid var(--ui-warning-banner-border);
  border-radius: 6px;
  font-size: 0.9em;
  color: var(--ui-warning-banner-fg);
}

.perfect-score-celebration {
  background: linear-gradient(135deg, var(--ui-celebration-1), var(--ui-celebration-2));
  color: #fff;
  padding: 30px;
  border-radius: 3px;
  font-weight: 600;
  border: 1px solid var(--ui-celebration-border);
  text-align: center;
  margin-bottom: 30px;
}

.celebration-stats {
  display: flex;
  justify-content: space-around;
  margin-top: 20px;
  font-size: 1.1em;
}

.citations-grid, .clusters-grid {
  display: grid;
  gap: 15px;
}

.clusters-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.cluster-item {
  background: var(--ui-surface);
  border: 1px solid var(--ui-border);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  transition: border-color 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease;
  box-shadow: 0 2px 4px var(--ui-card-shadow);
}

.cluster-item:hover {
  box-shadow: 0 8px 16px var(--ui-card-shadow-hover);
  border-color: var(--ui-accent);
  transform: translateY(-2px);
}

.unverified-cluster {
  border-left: 4px solid var(--ui-danger-accent);
  background: var(--ui-danger-surface);
}

.mismatch-cluster {
  border-left: 4px solid var(--ui-warning-soft-border);
  background: var(--ui-warning-soft-bg);
  border: 2px solid var(--ui-warning-soft-border);
}

.mismatch-header {
  color: var(--status-parallel-fg);
  font-size: 1.05em;
  margin-bottom: 12px;
  padding: 8px;
  background: var(--ui-warning-header-bg);
  border-radius: 4px;
}

.mismatch-extracted {
  background: var(--ui-mismatch-extracted-bg);
  padding: 8px;
  border-radius: 4px;
  margin-top: 4px;
}

.highlight-mismatch {
  background: var(--ui-mismatch-highlight-bg);
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 600;
  border: 1px solid var(--ui-mismatch-highlight-border);
  color: var(--ui-text);
}

.cluster-header-line {
  font-size: 1.1em;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--ui-divider);
}

.cluster-case-name {
  color: var(--ui-text-muted);
  font-weight: 500;
  padding: 40px;
}

.cluster-date {
  color: var(--ui-text-muted);
  font-size: 0.9em;
}

.cluster-line {
  margin-bottom: 8px;
  line-height: 1.6;
}

.cluster-line:last-child {
  margin-bottom: 0;
}

.verifying-source {
  font-size: 1.15em;
  font-weight: 600;
  color: var(--ui-text);
  letter-spacing: -0.01em;
}

.canonical-link {
  color: var(--ui-link);
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s ease;
}

.canonical-link:hover {
  color: var(--ui-link-hover);
  text-decoration: none;
  background: linear-gradient(to right, var(--ui-info-surface), transparent);
  border-bottom: 2px solid var(--ui-link-underline);
}

.source-badge {
  color: var(--ui-text-muted);
  font-weight: normal;
  font-size: 0.9em;
}

.submitted-document {
  color: var(--ui-text-secondary);
  font-size: 0.95em;
  margin-top: 8px;
  padding-left: 4px;
  border-left: 3px solid var(--ui-divider-strong);
}

.citation-extracted-label {
  color: var(--ui-text-muted);
  font-size: 0.9em;
}

.citation-line {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.citation-text {
  font-family: 'Courier New', Consolas, monospace;
  background: #e8f4fd;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.9em;
  font-weight: 500;
  border: 1px solid #d0e9ff;
  color: #0d47a1;
}

.citation-status {
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.85em;
}

.status-verified {
  color: var(--status-verified-fg);
  background: var(--status-verified-bg);
}

.status-parallel {
  color: var(--status-parallel-fg);
  background: var(--status-parallel-bg);
}

.status-unverified {
  color: var(--status-unverified-fg);
  background: var(--status-unverified-bg);
}

.status-possible-match {
  color: var(--status-possible-fg);
  background: var(--status-possible-bg);
  border: 1px solid var(--status-possible-border);
}

.possible-match-cluster {
  border-left: 4px solid var(--ui-warning-soft-border);
  background: var(--status-possible-bg);
}

.citation-card, .cluster-card {
  border: 1px solid var(--ui-divider);
  border-radius: 6px;
  padding: 15px;
  background: var(--ui-surface-3);
}

.cluster-header h3 {
  margin: 0 0 10px 0;
  color: var(--ui-text);
}

.cluster-meta {
  display: flex;
  gap: 20px;
  color: var(--ui-text-muted);
  font-size: 0.9em;
}

.cluster-citations {
  margin: 15px 0;
}

.cluster-citation {
  background: var(--ui-code-bg-alt);
  padding: 5px 10px;
  margin: 5px 0;
  border-radius: 4px;
  font-family: monospace;
  color: var(--ui-code-fg);
}

.citations-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.citation-item {
  border-left: 4px solid var(--ui-accent);
  padding: 15px;
  background: var(--ui-surface-2);
  border-radius: 4px;
}

.citation-status {
  margin: 10px 0;
  font-weight: bold;
}

.citation-details {
  font-size: 0.9em;
  color: var(--ui-text-muted);
}

.citation-details div {
  margin: 5px 0;
}

.no-citations {
  text-align: center;
  padding: 40px;
  color: #666;
}

/* Unverified cases informational styling */
.unverified-info {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  margin: 20px 0;
  font-size: 0.95em;
}

.unverified-info h3 {
  margin: 0 0 15px 0;
  color: #495057;
  font-size: 1.1em;
}

.unverified-info ul {
  margin: 0 0 15px 0;
  padding-left: 20px;
}

.unverified-info li {
  margin: 8px 0;
  color: var(--ui-text-secondary);
}

.unverified-info .help-text {
  margin: 0;
  padding: 12px;
  background-color: var(--ui-help-info-bg);
  border-left: 4px solid var(--ui-help-info-border);
  border-radius: 4px;
  color: var(--ui-help-info-fg);
  font-style: italic;
}
</style>
