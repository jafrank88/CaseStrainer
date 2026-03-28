<template>
  <div class="citation-results">
    <!-- Perfect Score Celebration (SHOW ONLY IF 100% VERIFIED AND NO MISMATCHES) -->
    <div v-if="allCitationsVerified && (mismatchClusters?.length || 0) === 0" class="perfect-score-celebration">
      <div class="celebration-content">
        <h2>🎉 Perfect Score!</h2>
        <p>All {{ (verifiedCitations?.length || 0) + (verifiedByParallelCitations?.length || 0) }} citations have been successfully verified!</p>
        <div class="celebration-stats">
          <div>✅ {{ verifiedCitations?.length || 0 }} Citations Verified</div>
          <div v-if="(verifiedByParallelCitations?.length || 0) > 0">🟠 {{ verifiedByParallelCitations?.length || 0 }} Verified by Parallel</div>
          <div>📚 {{ clusters?.length || 0 }} Cases Found</div>
        </div>
      </div>
    </div>

    <!-- Coverage banner when there are mismatches -->
    <div v-if="allCitationsVerified && (mismatchClusters?.length || 0) > 0" class="results-content" style="border-color:#2196F3;background:#E3F2FD;">
      <div class="results-header">
        <h2>✅ All Citations Verified</h2>
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
        <div v-if="results?.metadata?.verification_requested_but_none_matched" class="verification-hint-banner">
          <strong>Verification was requested but no citations were matched.</strong>
          {{ results?.metadata?.verification_hint || 'Ensure COURTLISTENER_API_KEY is set in the worker environment (check server/worker logs).' }}
        </div>
      </div>
      
      <div class="clusters-list">
        <template v-if="(clustersUnverified?.length || 0) > 0">
          <div class="results-header">
            <h3>⏳ Unverified</h3>
            <p class="results-explainer">Some sites with cases block automated tools - click on the link to search the web for unverified cases.</p>
          </div>
          <ClusterCard v-for="cluster in clustersUnverified" :key="cluster.cluster_id + '-unv'" :cluster="cluster" section-key="unv" :helpers="clusterHelpers" :show-mismatch-badge="true" />
        </template>
        <template v-if="(clustersCaseMismatch?.length || 0) > 0">
          <div class="results-header"><h3>⚠️ Name Differences</h3></div>
          <ClusterCard v-for="cluster in clustersCaseMismatch" :key="cluster.cluster_id + '-nm'" :cluster="cluster" section-key="nm" :helpers="clusterHelpers" :show-mismatch-badge="true" />
        </template>
        <template v-if="(clustersDateMismatch?.length || 0) > 0">
          <div class="results-header"><h3>📅 Date Differences</h3></div>
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
          <div class="results-header"><h3>✅ Verified</h3></div>
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
            <span :style="{ color: isEffectivelyVerified(citation) ? 'green' : (citation.true_by_parallel ? '#FF9800' : 'red') }">
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

    return {
      ...clusterData,
      clusterHelpers,
      formatCitationText: clusterDisplay.formatCitationText,
    }
  },
}
</script>

<style scoped>
.citation-results {
  padding: 20px;
}

.results-content {
  margin-bottom: 30px;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
}

.results-header {
  margin-bottom: 20px;
}

.results-header h3 {
  font-size: 1.4em;
  color: #2c2c2c;
  margin: 28px 0 18px 0;
  font-weight: 700;
  letter-spacing: -0.01em;
  padding-bottom: 12px;
  border-bottom: 2px solid #f0f0f0;
}

.results-header h2 {
  font-size: 1.85em;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.results-explainer {
  margin: 6px 0 0 0;
  color: #5f6f86;
  font-size: 0.9rem;
}

.citation-details {
  margin-top: 8px;
  font-size: 0.9em;
  color: #666;
}

.verification-error {
  margin-top: 4px;
  font-size: 0.85em;
  color: #d32f2f;
  font-style: italic;
}

.verification-hint-banner {
  margin-top: 12px;
  padding: 12px 16px;
  background: #FFF3E0;
  border: 1px solid #FF9800;
  border-radius: 6px;
  font-size: 0.9em;
  color: #E65100;
}

.perfect-score-celebration {
  background: linear-gradient(135deg, #4CAF50, #45a049);
  color: white;
  padding: 30px;
  border-radius: 3px;
  font-weight: 600;
  border: 1px solid #FBC02D;
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

.unverified-cluster {
  border-left: 4px solid #f44336;
  background: #fff8f8;
}

.mismatch-cluster {
  border-left: 4px solid #FF9800;
  background: #fff9e6;
  border: 2px solid #FF9800;
}

.mismatch-header {
  color: #FF6F00;
  font-size: 1.05em;
  margin-bottom: 12px;
  padding: 8px;
  background: #FFE0B2;
  border-radius: 4px;
}

.mismatch-extracted {
  background: #FFF3E0;
  padding: 8px;
  border-radius: 4px;
  margin-top: 4px;
}

.highlight-mismatch {
  background: #FFEB3B;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 600;
  border: 1px solid #FBC02D;
}

.cluster-header-line {
  font-size: 1.1em;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.cluster-case-name {
  color: #333;
  font-weight: 500;
  padding: 40px;
  color: #666;
}

.cluster-date {
  color: #666;
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
  color: #1a1a1a;
  letter-spacing: -0.01em;
}

.canonical-link {
  color: #1976D2;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s ease;
}

.canonical-link:hover {
  color: #1565C0;
  text-decoration: none;
  background: linear-gradient(to right, #E3F2FD, transparent);
  border-bottom: 2px solid #2196F3;
}

.source-badge {
  color: #666;
  font-weight: normal;
  font-size: 0.9em;
}

.submitted-document {
  color: #5f6368;
  font-size: 0.95em;
  margin-top: 8px;
  padding-left: 4px;
  border-left: 3px solid #f0f0f0;
}

.citation-extracted-label {
  color: var(--text-muted, #666);
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
  color: #4CAF50;
  background: #E8F5E8;
}

.status-parallel {
  color: #FF9800;
  background: #FFF3E0;
}

.status-unverified {
  color: #f44336;
  background: #FFEBEE;
}

.status-possible-match {
  color: #FF9800;
  background: #FFF8E1;
  border: 1px solid #FFB74D;
}

.possible-match-cluster {
  border-left: 4px solid #FF9800;
  background: #FFF8E1;
}

.citation-card, .cluster-card {
  border: 1px solid #eee;
  border-radius: 6px;
  padding: 15px;
  background: #f9f9f9;
}

.cluster-header h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.cluster-meta {
  display: flex;
  gap: 20px;
  color: #666;
  font-size: 0.9em;
}

.cluster-citations {
  margin: 15px 0;
}

.cluster-citation {
  background: #e3f2fd;
  padding: 5px 10px;
  margin: 5px 0;
  border-radius: 4px;
  font-family: monospace;
}

.citations-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.citation-item {
  border-left: 4px solid #2196F3;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 4px;
}

.citation-status {
  margin: 10px 0;
  font-weight: bold;
}

.citation-details {
  font-size: 0.9em;
  color: #666;
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
  color: #6c757d;
}

.unverified-info .help-text {
  margin: 0;
  padding: 12px;
  background-color: #e3f2fd;
  border-left: 4px solid #2196f3;
  border-radius: 4px;
  color: #1565c0;
  font-style: italic;
}
</style>
