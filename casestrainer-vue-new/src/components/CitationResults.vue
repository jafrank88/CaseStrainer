<template>
  <div class="citation-results">
    <!-- SECTION 1: Unverified Clusters (SHOW FIRST) -->
    <div v-if="false && (unverifiedClusters?.length || 0) > 0" class="results-content">
      <div class="results-header">
        <h2>🔍 SECTION 1: Unverified Clusters</h2>
        <p>{{ unverifiedClusters?.length || 0 }} cluster(s) with unverified citations</p>
        
        <!-- Informational message about unverified cases -->
        <div class="unverified-info">
          <h3>ℹ️ Why are these cases unverified?</h3>
          <ul>
            <li><strong>Recent Cases (2022-2024):</strong> May not yet be indexed in legal databases</li>
            <li><strong>State Cases:</strong> CourtListener focuses on federal cases; state coverage varies</li>
            <li><strong>North Carolina Cases:</strong> Limited coverage in current verification sources</li>
            <li><strong>Database Limitations:</strong> Not all cases are available in public databases</li>
          </ul>
          <p class="help-text">
            💡 <strong>Tip:</strong> These cases may still be valid - consider checking official court websites or legal databases manually.
          </p>
        </div>
      </div>
      
      <div class="clusters-list">
        <div v-for="cluster in unverifiedClusters" :key="cluster.cluster_id" class="cluster-item unverified-cluster">
          <!-- Cluster Header -->
          <div class="cluster-line cluster-header-line">
            <strong>📚</strong>
            <span class="cluster-case-name">{{ cluster.citations?.[0]?.extracted_case_name || 'N/A' }}</span>
            <span v-if="cluster.citations?.[0]?.extracted_date" class="cluster-date">({{ cluster.citations[0].extracted_date }})</span>
          </div>
          
          <!-- Citations in Cluster -->
          <div class="cluster-citations">
            <div v-for="(citation, index) in getClusterCitations(cluster)" :key="`${cluster.cluster_id}-${index}`" class="cluster-line citation-line">
              <strong>Citation {{ index + 1 }}: </strong>
              <span class="citation-text">{{ citation.citation }}</span>
              <span class="citation-status" :class="getCitationStatusClass(citation)">
                {{ getCitationStatusText(citation) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    

    <!-- SECTION 1.25: Name/Date Mismatches (DEBUGGING) -->
    <div v-if="false && (mismatchClusters?.length || 0) > 0" class="results-content">
      <div class="results-header">
        <h2>⚠️ SECTION 1.25: Extraction Mismatches</h2>
        <p>{{ mismatchClusters?.length || 0 }} cluster(s) with extracted/canonical mismatch</p>
      </div>
      
      <div class="clusters-list">
        <div v-for="cluster in mismatchClusters" :key="cluster.cluster_id" class="cluster-item mismatch-cluster">
          <!-- Cluster Header -->
          <div class="cluster-line mismatch-header">
            <strong v-if="hasNameMismatch(cluster) && hasDateMismatch(cluster)">🔴 NAME & DATE MISMATCH DETECTED</strong>
            <strong v-else-if="hasNameMismatch(cluster)">🔴 NAME MISMATCH DETECTED</strong>
            <strong v-else-if="hasDateMismatch(cluster)">🔴 DATE MISMATCH DETECTED</strong>
          </div>
          
          <!-- Verifying Source (Canonical) -->
          <div class="cluster-line verifying-source">
            <strong>Verifying Source: </strong>
            <template v-if="getMismatchDisplayCitation(cluster)?.canonical_url">
              <a :href="getMismatchDisplayCitation(cluster).canonical_url" target="_blank" class="canonical-link">
                <span :class="{ 'highlight-mismatch': hasNameMismatch(cluster) }">{{ getMismatchDisplayCitation(cluster).canonical_name || 'N/A' }}</span>, 
                <span :class="{ 'highlight-mismatch': hasDateMismatch(cluster) }">{{ getMismatchDisplayCitation(cluster).canonical_date || 'N/A' }}</span>
              </a>
            </template>
            <template v-else>
              <span :class="{ 'highlight-mismatch': hasNameMismatch(cluster) }">{{ getMismatchDisplayCitation(cluster)?.canonical_name || 'N/A' }}</span>, 
              <span :class="{ 'highlight-mismatch': hasDateMismatch(cluster) }">{{ getMismatchDisplayCitation(cluster)?.canonical_date || 'N/A' }}</span>
            </template>
          </div>
          
          <!-- Submitted Document (Extracted) -->
          <div class="cluster-line submitted-document mismatch-extracted">
            <strong>Submitted Document: </strong>
            <span :class="{ 'highlight-mismatch': hasNameMismatch(cluster) }">{{ getMismatchDisplayCitation(cluster)?.extracted_case_name || 'N/A' }}</span>, 
            <span :class="{ 'highlight-mismatch': hasDateMismatch(cluster) }">{{ getMismatchDisplayCitation(cluster)?.extracted_date || 'N/A' }}</span>
          </div>
          
          <!-- Citations -->
          <div class="cluster-citations">
            <div v-for="(citation, index) in getClusterCitations(cluster)" :key="`${cluster.cluster_id}-${index}`" class="cluster-line citation-line">
              <strong>Citation {{ index + 1 }}: </strong>
              <span class="citation-text">{{ citation.text || citation.citation }}</span>
              <span class="citation-status" :class="getCitationStatusClass(citation)">
                {{ getCitationStatusText(citation) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Perfect Score Celebration (SHOW ONLY IF 100% VERIFIED AND NO MISMATCHES) -->
    <div v-else-if="allCitationsVerified && (mismatchClusters?.length || 0) === 0" class="perfect-score-celebration">
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

    <!-- Coverage banner when there are mismatches (Option A) -->
    <div v-else-if="allCitationsVerified && (mismatchClusters?.length || 0) > 0" class="results-content" style="border-color:#2196F3;background:#E3F2FD;">
      <div class="results-header">
        <h2>✅ 100% Verified Coverage</h2>
        <p>{{ (verifiedCitations?.length || 0) + (verifiedByParallelCitations?.length || 0) }} citation(s) verified • {{ mismatchClusters?.length || 0 }} mismatch cluster(s) detected</p>
      </div>
    </div>

    <!-- Clustered Results Display -->
    <div v-if="(clusters?.length || 0) > 0" class="results-content">
      <div class="results-header">
        <h2>Clustered Results Display</h2>
        <p>{{ clusters?.length || 0 }} cluster(s) found</p>
      </div>
      
      <div class="clusters-list">
        <!-- Group 1: Unverified -->
        <template v-if="(clustersUnverified?.length || 0) > 0">
          <div class="results-header"><h3>Unverified</h3></div>
          <div v-for="cluster in clustersUnverified" :key="cluster.cluster_id + '-unv'" class="cluster-item">
            <div class="cluster-line verifying-source">
              <strong>Verifying Source: </strong>
              <template v-if="getRepresentativeCitation(cluster)?.canonical_url">
                <a :href="getRepresentativeCitation(cluster).canonical_url" target="_blank" class="canonical-link">
                  <span :class="{ 'highlight-mismatch': hasNameMismatch(cluster) }">{{ getClusterVerifyingName(cluster) }}</span>,
                  <span :class="{ 'highlight-mismatch': hasDateMismatch(cluster) }">{{ getClusterVerifyingDate(cluster) }}</span>
                </a>
              </template>
              <template v-else>
                <span :class="{ 'highlight-mismatch': hasNameMismatch(cluster) }">{{ getClusterVerifyingName(cluster) }}</span>,
                <span :class="{ 'highlight-mismatch': hasDateMismatch(cluster) }">{{ getClusterVerifyingDate(cluster) }}</span>
              </template>
              <span v-if="getClusterSource(cluster)" class="source-badge">({{ getClusterSource(cluster) }})</span>
              <span v-if="hasNameMismatch(cluster) || hasDateMismatch(cluster)" class="source-badge" style="margin-left:8px;color:#FF6F00;">
                <strong>
                  <template v-if="hasNameMismatch(cluster) && hasDateMismatch(cluster)">NAME & DATE MISMATCH</template>
                  <template v-else-if="hasNameMismatch(cluster)">NAME MISMATCH</template>
                  <template v-else>DATE MISMATCH</template>
                </strong>
              </span>
            </div>
            <div class="cluster-line submitted-document">
              <strong>Submitted Document: </strong>
              <span :class="{ 'highlight-mismatch': hasNameMismatch(cluster) }">{{ getClusterSubmittedName(cluster) }}</span>,
              <span :class="{ 'highlight-mismatch': hasDateMismatch(cluster) }">{{ getClusterSubmittedDate(cluster) }}</span>
            </div>
            <div class="cluster-citations">
              <div v-for="(citation, index) in getClusterCitations(cluster)" :key="`${cluster.cluster_id}-unv-${index}`" class="cluster-line citation-line">
                <strong>Citation {{ index + 1 }}: </strong>
                <span class="citation-text">{{ citation.text || citation.citation }}</span>
                <span class="citation-status" :class="getCitationStatusClass(citation)">{{ getCitationStatusText(citation) }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- Group 2: Case mismatch -->
        <template v-if="(clustersCaseMismatch?.length || 0) > 0">
          <div class="results-header"><h3>Case mismatch</h3></div>
          <div v-for="cluster in clustersCaseMismatch" :key="cluster.cluster_id + '-nm'" class="cluster-item">
            <div class="cluster-line verifying-source">
              <strong>Verifying Source: </strong>
              <template v-if="getRepresentativeCitation(cluster)?.canonical_url">
                <a :href="getRepresentativeCitation(cluster).canonical_url" target="_blank" class="canonical-link">
                  <span :class="{ 'highlight-mismatch': hasNameMismatch(cluster) }">{{ getClusterVerifyingName(cluster) }}</span>,
                  <span :class="{ 'highlight-mismatch': hasDateMismatch(cluster) }">{{ getClusterVerifyingDate(cluster) }}</span>
                </a>
              </template>
              <template v-else>
                <span :class="{ 'highlight-mismatch': hasNameMismatch(cluster) }">{{ getClusterVerifyingName(cluster) }}</span>,
                <span :class="{ 'highlight-mismatch': hasDateMismatch(cluster) }">{{ getClusterVerifyingDate(cluster) }}</span>
              </template>
              <span v-if="getClusterSource(cluster)" class="source-badge">({{ getClusterSource(cluster) }})</span>
              <span class="source-badge" style="margin-left:8px;color:#FF6F00;"><strong>NAME MISMATCH</strong></span>
            </div>
            <div class="cluster-line submitted-document">
              <strong>Submitted Document: </strong>
              <span class="highlight-mismatch">{{ getClusterSubmittedName(cluster) }}</span>,
              <span>{{ getClusterSubmittedDate(cluster) }}</span>
            </div>
            <div class="cluster-citations">
              <div v-for="(citation, index) in getClusterCitations(cluster)" :key="`${cluster.cluster_id}-nm-${index}`" class="cluster-line citation-line">
                <strong>Citation {{ index + 1 }}: </strong>
                <span class="citation-text">{{ citation.text || citation.citation }}</span>
                <span class="citation-status" :class="getCitationStatusClass(citation)">{{ getCitationStatusText(citation) }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- Group 3: Date mismatch -->
        <template v-if="(clustersDateMismatch?.length || 0) > 0">
          <div class="results-header"><h3>Date mismatch</h3></div>
          <div v-for="cluster in clustersDateMismatch" :key="cluster.cluster_id + '-dm'" class="cluster-item">
            <div class="cluster-line verifying-source">
              <strong>Verifying Source: </strong>
              <template v-if="getRepresentativeCitation(cluster)?.canonical_url">
                <a :href="getRepresentativeCitation(cluster).canonical_url" target="_blank" class="canonical-link">
                  <span>{{ getClusterVerifyingName(cluster) }}</span>,
                  <span class="highlight-mismatch">{{ getClusterVerifyingDate(cluster) }}</span>
                </a>
              </template>
              <template v-else>
                <span>{{ getClusterVerifyingName(cluster) }}</span>,
                <span class="highlight-mismatch">{{ getClusterVerifyingDate(cluster) }}</span>
              </template>
              <span v-if="getClusterSource(cluster)" class="source-badge">({{ getClusterSource(cluster) }})</span>
              <span class="source-badge" style="margin-left:8px;color:#FF6F00;"><strong>DATE MISMATCH</strong></span>
            </div>
            <div class="cluster-line submitted-document">
              <strong>Submitted Document: </strong>
              <span>{{ getClusterSubmittedName(cluster) }}</span>,
              <span class="highlight-mismatch">{{ getClusterSubmittedDate(cluster) }}</span>
            </div>
            <div class="cluster-citations">
              <div v-for="(citation, index) in getClusterCitations(cluster)" :key="`${cluster.cluster_id}-dm-${index}`" class="cluster-line citation-line">
                <strong>Citation {{ index + 1 }}: </strong>
                <span class="citation-text">{{ citation.text || citation.citation }}</span>
                <span class="citation-status" :class="getCitationStatusClass(citation)">{{ getCitationStatusText(citation) }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- Group 4: All other clusters -->
        <template v-if="(clustersOther?.length || 0) > 0">
          <div class="results-header"><h3>All other clusters</h3></div>
          <div v-for="cluster in clustersOther" :key="cluster.cluster_id + '-oth'" class="cluster-item">
            <div class="cluster-line verifying-source">
              <strong>Verifying Source: </strong>
              <template v-if="getRepresentativeCitation(cluster)?.canonical_url">
                <a :href="getRepresentativeCitation(cluster).canonical_url" target="_blank" class="canonical-link">
                  <span>{{ getClusterVerifyingName(cluster) }}</span>,
                  <span>{{ getClusterVerifyingDate(cluster) }}</span>
                </a>
              </template>
              <template v-else>
                <span>{{ getClusterVerifyingName(cluster) }}</span>,
                <span>{{ getClusterVerifyingDate(cluster) }}</span>
              </template>
              <span v-if="getClusterSource(cluster)" class="source-badge">({{ getClusterSource(cluster) }})</span>
            </div>
            <div class="cluster-line submitted-document">
              <strong>Submitted Document: </strong>
              <span>{{ getClusterSubmittedName(cluster) }}</span>,
              <span>{{ getClusterSubmittedDate(cluster) }}</span>
            </div>
            <div class="cluster-citations">
              <div v-for="(citation, index) in getClusterCitations(cluster)" :key="`${cluster.cluster_id}-oth-${index}`" class="cluster-line citation-line">
                <strong>Citation {{ index + 1 }}: </strong>
                <span class="citation-text">{{ citation.text || citation.citation }}</span>
                <span class="citation-status" :class="getCitationStatusClass(citation)">{{ getCitationStatusText(citation) }}</span>
              </div>
            </div>
          </div>
        </template>
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
    
    // NEW: Unverified clusters (clusters with at least one unverified citation)
    const unverifiedClusters = computed(() => {
      if (!clusters.value || clusters.value.length === 0) return []
      
      return clusters.value.filter(cluster => {
        const clusterCitations = cluster.citations || []
        // A cluster is "unverified" if it has at least one citation that is not verified, not true_by_parallel, and not possible_match
        return clusterCitations.some(cit => !cit.verified && !cit.true_by_parallel && !cit.possible_match)
      })
    })
    
    // NEW: Possible match clusters (clusters with at least one possible match citation)
    const possibleMatchClusters = computed(() => {
      if (!clusters.value || clusters.value.length === 0) return []
      
      return clusters.value.filter(cluster => {
        const clusterCitations = cluster.citations || []
        // A cluster is "possible match" if it has at least one citation with possible_match=true
        return clusterCitations.some(cit => cit.possible_match)
      })
    })
    
    // NEW: Name/Date mismatch clusters (use backend flags)
    const mismatchClusters = computed(() => {
      if (!clusters.value || clusters.value.length === 0) {
        console.log('⚠️ [MISMATCH] No clusters available')
        return []
      }
      const mismatches = clusters.value.filter(cluster => {
        return Boolean(cluster?.has_name_mismatch || cluster?.has_date_mismatch)
      })
      console.log(`⚠️ [MISMATCH] Found ${mismatches.length} clusters with mismatches (backend)`) 
      return mismatches
    })
    
    // Helper function to check if cluster has name mismatch (backend)
    const hasNameMismatch = (cluster) => {
      return Boolean(cluster?.has_name_mismatch)
    }
    
    // Helper function to check if cluster has date mismatch (backend)
    const hasDateMismatch = (cluster) => {
      return Boolean(cluster?.has_date_mismatch)
    }
    
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

    // For displaying the specific mismatched citation for a cluster (backend indices)
    const getMismatchDisplayCitation = (cluster) => {
      const cits = cluster.citations || cluster.citation_objects || []
      if (cits.length === 0) return null
      const indices = cluster.mismatch_indices || []
      if (indices.length > 0) {
        const idx = indices[0]
        if (idx >= 0 && idx < cits.length) return cits[idx]
      }
      // Fallback: first citation
      return cits[0]
    }

    const getRepresentativeCitation = (cluster) => {
      const cits = cluster.citations || cluster.citation_objects || []
      if (!cits || cits.length === 0) return null
      const indices = cluster.mismatch_indices || []
      if (indices.length > 0) {
        const idx = indices[0]
        if (idx >= 0 && idx < cits.length) return cits[idx]
      }
      const firstVerified = cits.find(c => c && c.verified)
      if (firstVerified) return firstVerified
      return cits[0]
    }

    // Backend-driven display fields with safe fallbacks
    const getClusterVerifyingName = (cluster) => {
      return cluster?.verifying_display_name
        || getRepresentativeCitation(cluster)?.canonical_name
        || 'N/A'
    }
    const getClusterVerifyingDate = (cluster) => {
      return cluster?.verifying_display_date
        || getRepresentativeCitation(cluster)?.canonical_date
        || getRepresentativeCitation(cluster)?.extracted_date
        || 'N/A'
    }
    const getClusterSubmittedName = (cluster) => {
      return cluster?.submitted_display_name
        || getRepresentativeCitation(cluster)?.extracted_case_name
        || 'N/A'
    }
    const getClusterSubmittedDate = (cluster) => {
      return cluster?.submitted_display_date
        || getRepresentativeCitation(cluster)?.extracted_date
        || 'N/A'
    }

    const getCitationStatusClass = (citation) => {
      if (citation.verified) {
        return 'status-verified'
      } else if (citation.true_by_parallel) {
        return 'status-parallel'
      } else if (citation.possible_match) {
        return 'status-possible-match'
      } else {
        return 'status-unverified'
      }
    }

    const getCitationStatusText = (citation) => {
      if (citation.verified) {
        return 'Verified'
      } else if (citation.true_by_parallel) {
        return 'Verified by Parallel'
      } else if (citation.possible_match) {
        return 'Possible Match'
      } else {
        return 'Unverified'
      }
    }

    // Unified grouping for single display
    const clustersUnverified = unverifiedClusters
    const clustersCaseMismatch = computed(() => {
      const base = clusters.value || []
      const unvIds = new Set((clustersUnverified.value || []).map(c => c.cluster_id))
      return base.filter(c => !unvIds.has(c.cluster_id) && Boolean(c?.has_name_mismatch))
    })
    const clustersDateMismatch = computed(() => {
      const base = clusters.value || []
      const unvIds = new Set((clustersUnverified.value || []).map(c => c.cluster_id))
      const caseIds = new Set((clustersCaseMismatch.value || []).map(c => c.cluster_id))
      return base.filter(c => !unvIds.has(c.cluster_id) && !caseIds.has(c.cluster_id) && Boolean(c?.has_date_mismatch))
    })
    const clustersOther = computed(() => {
      const base = clusters.value || []
      const unvIds = new Set((clustersUnverified.value || []).map(c => c.cluster_id))
      const caseIds = new Set((clustersCaseMismatch.value || []).map(c => c.cluster_id))
      const dateIds = new Set((clustersDateMismatch.value || []).map(c => c.cluster_id))
      return base.filter(c => !unvIds.has(c.cluster_id) && !caseIds.has(c.cluster_id) && !dateIds.has(c.cluster_id))
    })

    return {
      citations,
      clusters,
      verifiedCitations,
      unverifiedCitations,
      verifiedByParallelCitations,
      unverifiedClusters,
      possibleMatchClusters,
      mismatchClusters,
      hasNameMismatch,
      hasDateMismatch,
      allCitationsVerified,
      getClusterSource,
      getClusterCitations,
      getMismatchDisplayCitation,
      getRepresentativeCitation,
      getClusterVerifyingName,
      getClusterVerifyingDate,
      getClusterSubmittedName,
      getClusterSubmittedDate,
      getCitationStatusClass,
      getCitationStatusText
      ,clustersUnverified
      ,clustersCaseMismatch
      ,clustersDateMismatch
      ,clustersOther
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
