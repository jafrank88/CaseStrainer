<template>
  <div class="citation-results">
    <!-- SECTION 1: Citations That Need Attention OR Celebration (SHOW FIRST) -->
    <div v-if="(unverifiedCitations?.length || 0) > 0" class="results-content">
      <div class="results-header">
        <h2>🔍 SECTION 1: Citation Status</h2>
        <p>{{ unverifiedCitations?.length || 0 }} citation(s) not directly verified</p>
      </div>
      
      <div class="citations-grid">
        <div v-for="citation in unverifiedCitations" :key="citation.citation" class="citation-card">
          <div class="citation-text">{{ citation.citation }}</div>
          <div class="citation-details">
            <div><strong>Extracted:</strong> {{ citation.extracted_case_name }} ({{ citation.extracted_date }})</div>
            <div><strong>Status:</strong> 
              <span :style="{ color: citation.true_by_parallel ? '#FF9800' : 'red' }">
                {{ citation.true_by_parallel ? '✅ VERIFIED BY PARALLEL' : '❌ UNVERIFIED' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- SECTION 1.5: Citations Verified by Parallel (SHOW SECOND) -->
    <div v-if="(verifiedByParallelCitations?.length || 0) > 0" class="results-content">
      <div class="results-header">
        <h2>🟠 SECTION 1.5: Verified by Parallel</h2>
        <p>{{ verifiedByParallelCitations?.length || 0 }} citation(s) verified by parallel citations</p>
      </div>
      
      <div class="citations-grid">
        <div v-for="citation in verifiedByParallelCitations" :key="citation.citation" class="citation-card">
          <div class="citation-text">{{ citation.citation }}</div>
          <div class="citation-details">
            <div><strong>Extracted:</strong> {{ citation.extracted_case_name }} ({{ citation.extracted_date }})</div>
            <div><strong>Status:</strong> 
              <span style="color: #FF9800;">
                ✅ VERIFIED BY PARALLEL
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Perfect Score Celebration (SHOW IF NO ISSUES) -->
    <div v-else-if="allCitationsVerified" class="perfect-score-celebration">
      <div class="celebration-content">
        <h2>🎉 Perfect Score!</h2>
        <p>All {{ (verifiedCitations?.length || 0) + (verifiedByParallelCitations?.length || 0) }} citations have been successfully verified!</p>
        <div class="celebration-stats">
          <div>✅ {{ verifiedCitations?.length || 0 }} Citations Verified</div>
          <div v-if="(verifiedByParallelCitations?.length || 0) > 0">🟠 {{ verifiedByParallelCitations?.length || 0 }} Verified by Parallel</div>
          <div>📚 {{ clusters?.length || 0 }} Clusters Found</div>
        </div>
      </div>
    </div>

    <!-- Clustered Results Display -->
    <div v-if="(clusters?.length || 0) > 0" class="results-content">
      <div class="results-header">
        <h2>Clustered Results Display</h2>
        <p>{{ clusters?.length || 0 }} cluster(s) found</p>
      </div>
      
      <div class="clusters-list">
        <div v-for="cluster in clusters" :key="cluster.cluster_id" class="cluster-item">
          <!-- Line 1: Verifying Source (linked to canonical URL) -->
          <div class="cluster-line verifying-source">
            <strong>Verifying Source:</strong>
            <template v-if="cluster.canonical_url">
              <a :href="cluster.canonical_url" target="_blank" class="canonical-link">
                {{ cluster.canonical_name || 'N/A' }}, {{ cluster.canonical_date || cluster.extracted_date || 'N/A' }}
              </a>
            </template>
            <template v-else>
              {{ cluster.canonical_name || 'N/A' }}, {{ cluster.canonical_date || cluster.extracted_date || 'N/A' }}
            </template>
            <span v-if="getClusterSource(cluster)" class="source-badge">
              ({{ getClusterSource(cluster) }})
            </span>
          </div>
          
          <!-- Line 2: Submitted Document -->
          <div class="cluster-line submitted-document">
            <strong>Submitted Document:</strong>
            {{ cluster.extracted_case_name || 'N/A' }}, {{ cluster.extracted_date || 'N/A' }}
          </div>
          
          <!-- Lines 3+: Individual Citations with Status -->
          <div class="cluster-citations">
            <div v-for="(citation, index) in getClusterCitations(cluster)" :key="`${cluster.cluster_id}-${index}`" class="cluster-line citation-line">
              <strong>Citation {{ index + 1 }}:</strong>
              <span class="citation-text">{{ citation.text || citation.citation }}</span>
              <span class="citation-status" :class="getCitationStatusClass(citation)">
                {{ getCitationStatusText(citation) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- SECTION 2: Individual Citations (SHOW THIRD) -->
    <div v-if="(citations?.length || 0) > 0" class="results-content">
      <div class="results-header">
        <h2>Individual Citations</h2>
        <p>{{ citations?.length || 0 }} individual citation(s)</p>
      </div>
      
      <div class="citations-list">
        <div v-for="citation in citations" :key="citation.citation" class="citation-item">
          <div class="citation-text">{{ citation.citation }}</div>
          <div class="citation-status">
            <span :style="{ color: citation.verified ? 'green' : (citation.true_by_parallel ? '#FF9800' : 'red') }">
              {{ citation.verified ? '✅ VERIFIED' : (citation.true_by_parallel ? '✅ VERIFIED BY PARALLEL' : '❌ UNVERIFIED') }}
            </span>
          </div>
          <div class="citation-details">
            <div><strong>Case:</strong> {{ citation.extracted_case_name }}</div>
            <div><strong>Date:</strong> {{ citation.extracted_date }}</div>
            <div v-if="citation.verification_source"><strong>Source:</strong> {{ citation.verification_source }}</div>
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
import { ref, computed } from 'vue'

export default {
  name: 'CitationResults',
  props: {
    results: {
      type: Object,
      default: null
    },
    error: {
      type: String,
      default: null
    },
    componentId: {
      type: String,
      default: 'default'
    }
  },

  setup(props) {
    
    // Based on our testing: data is in results.citations (not results.result.citations)
    const citations = computed(() => {
      return props.results?.citations || []
    })
    
    const clusters = computed(() => {
      console.log('🔍 CitationResults DEBUG - props.results:', props.results)
      console.log('🔍 CitationResults DEBUG - clusters data:', props.results?.clusters)
      if (props.results?.clusters) {
        props.results.clusters.forEach((cluster, index) => {
          console.log(`🔍 Cluster ${index}:`, {
            cluster_id: cluster.cluster_id,
            extracted_case_name: cluster.extracted_case_name,
            extracted_date: cluster.extracted_date,
            canonical_name: cluster.canonical_name,
            canonical_date: cluster.canonical_date
          })
        })
      }
      return props.results?.clusters || []
    })
    
    const verifiedCitations = computed(() => {
      return citations.value?.filter(c => c.verified) || []
    })
    
    const unverifiedCitations = computed(() => {
      return citations.value?.filter(c => !c.verified && !c.true_by_parallel) || []
    })
    
    const verifiedByParallelCitations = computed(() => {
      return citations.value?.filter(c => !c.verified && c.true_by_parallel) || []
    })
    
    const allCitationsVerified = computed(() => {
      return citations.value?.length > 0 && unverifiedCitations.value.length === 0
    })
    
    const allCitationsVerifiedOrParallel = computed(() => {
      return citations.value?.length > 0 && unverifiedCitations.value.length === 0
    })
    
    // Helper methods for the new cluster display format
    const getClusterSource = (cluster) => {
      // Get verification source from the first verified citation in cluster
      const citationList = cluster.citations || cluster.citation_objects || []
      if (citationList.length > 0) {
        for (const citation of citationList) {
          if (citation.verification_source) {
            return citation.verification_source
          }
        }
      }
      return null
    }

    const getClusterCitations = (cluster) => {
      // Return citation objects with their verification status
      // Backend sends 'citations', but also check 'citation_objects' for backward compatibility
      return cluster.citations || cluster.citation_objects || []
    }

    const getCitationStatusClass = (citation) => {
      if (citation.verified) {
        return 'status-verified'
      } else if (citation.true_by_parallel) {
        return 'status-parallel'
      } else {
        return 'status-unverified'
      }
    }

    const getCitationStatusText = (citation) => {
      if (citation.verified) {
        return 'Verified'
      } else if (citation.true_by_parallel) {
        return 'Verified by Parallel'
      } else {
        return 'Unverified'
      }
    }

    return {
      citations,
      clusters,
      verifiedCitations,
      unverifiedCitations,
      allCitationsVerified,
      getClusterSource,
      getClusterCitations,
      getCitationStatusClass,
      getCitationStatusText
    }
  }
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

.results-header h2 {
  margin: 0 0 10px 0;
  font-size: 1.5em;
}

.perfect-score-celebration {
  background: linear-gradient(135deg, #4CAF50, #45a049);
  color: white;
  padding: 30px;
  border-radius: 12px;
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
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  background: #f9f9f9;
}

.cluster-line {
  margin-bottom: 8px;
  line-height: 1.6;
}

.cluster-line:last-child {
  margin-bottom: 0;
}

.verifying-source {
  font-size: 1.1em;
}

.canonical-link {
  color: #2196F3;
  text-decoration: none;
  font-weight: 500;
}

.canonical-link:hover {
  text-decoration: underline;
}

.source-badge {
  color: #666;
  font-weight: normal;
  font-size: 0.9em;
}

.submitted-document {
  color: #555;
}

.citation-line {
  display: flex;
  align-items: center;
  gap: 10px;
}

.citation-text {
  font-family: monospace;
  background: #e3f2fd;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.95em;
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
</style>
