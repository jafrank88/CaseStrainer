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
        <p v-if="(verifiedCitations?.length || 0) > 0">{{ verifiedCitations?.length || 0 }} citation{{ (verifiedCitations?.length || 0) !== 1 ? 's' : '' }} verified</p>
      </div>
      
      <div class="clusters-list">

        <!-- Unverified Cases (SHOW FIRST) -->
        <template v-if="(clustersUnverified?.length || 0) > 0">
          <div class="results-header"><h3>⏳ Unverified</h3></div>
          <div v-for="cluster in clustersUnverified" :key="cluster.cluster_id + '-unv'" class="cluster-item">
            <div class="cluster-line verifying-source">
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
              <span v-if="hasNameMismatch(cluster) || hasDateMismatch(cluster)" class="source-badge" style="margin-left:8px;color:#FF6F00;">
                <strong>
                  <template v-if="hasNameMismatch(cluster) && hasDateMismatch(cluster)">⚠️ Different name & date</template>
                  <template v-else-if="hasNameMismatch(cluster)">⚠️ Different name</template>
                  <template v-else>⚠️ Different date</template>
                </strong>
              </span>
            </div>
            <div class="cluster-line submitted-document">
              <strong>Extracted from Document: </strong>
              <span :class="{ 'highlight-mismatch': hasNameMismatch(cluster) }">{{ getClusterSubmittedName(cluster) }}</span>,
              <span :class="{ 'highlight-mismatch': hasDateMismatch(cluster) }">{{ getClusterSubmittedDate(cluster) }}</span>
              <span v-if="cluster.cross_document_merge" class="merge-badge" style="margin-left:8px;color:#2196F3;">
                <strong>📄 Merged from {{ cluster.merge_source_count || 2 }} documents</strong>
              </span>
            </div>
            <div class="cluster-citations">
              <div v-for="(citation, index) in getClusterCitations(cluster)" :key="`${cluster.cluster_id}-unv-${index}`" class="cluster-line citation-line">
                <strong>Citation {{ index + 1 }}: </strong>
                <span class="citation-text">{{ formatCitationText(citation) }}</span>
                <span class="citation-status" :class="getCitationStatusClass(citation)">{{ getCitationStatusText(citation) }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- Cases with Name Differences (SHOW SECOND) -->
        <template v-if="(clustersCaseMismatch?.length || 0) > 0">
          <div class="results-header"><h3>⚠️ Name Differences</h3></div>
          <div v-for="cluster in clustersCaseMismatch" :key="cluster.cluster_id + '-nm'" class="cluster-item">
            <div class="cluster-line verifying-source">
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
              <span class="source-badge" style="margin-left:8px;color:#FF6F00;"><strong>⚠️ Different name</strong></span>
            </div>
            <div class="cluster-line submitted-document">
              <strong>Extracted from Document: </strong>
              <span class="highlight-mismatch">{{ getClusterSubmittedName(cluster) }}</span>,
              <span>{{ getClusterSubmittedDate(cluster) }}</span>
            </div>
            <div class="cluster-citations">
              <div v-for="(citation, index) in getClusterCitations(cluster)" :key="`${cluster.cluster_id}-nm-${index}`" class="cluster-line citation-line">
                <strong>Citation {{ index + 1 }}: </strong>
                <span class="citation-text">{{ formatCitationText(citation) }}</span>
                <span class="citation-status" :class="getCitationStatusClass(citation)">{{ getCitationStatusText(citation) }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- Cases with Date Differences (SHOW THIRD) -->
        <template v-if="(clustersDateMismatch?.length || 0) > 0">
          <div class="results-header"><h3>📅 Date Differences</h3></div>
          <div v-for="cluster in clustersDateMismatch" :key="cluster.cluster_id + '-dm'" class="cluster-item">
            <div class="cluster-line verifying-source">
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
              <span class="source-badge" style="margin-left:8px;color:#FF6F00;"><strong>⚠️ Different date</strong></span>
            </div>
            <div class="cluster-line submitted-document">
              <strong>Extracted from Document: </strong>
              <span>{{ getClusterSubmittedName(cluster) }}</span>,
              <span class="highlight-mismatch">{{ getClusterSubmittedDate(cluster) }}</span>
            </div>
            <div class="cluster-citations">
              <div v-for="(citation, index) in getClusterCitations(cluster)" :key="`${cluster.cluster_id}-dm-${index}`" class="cluster-line citation-line">
                <strong>Citation {{ index + 1 }}: </strong>
                <span class="citation-text">{{ formatCitationText(citation) }}</span>
                <span class="citation-status" :class="getCitationStatusClass(citation)">{{ getCitationStatusText(citation) }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- Verified by Parallel (SHOW FOURTH) -->
        <template v-if="(clustersVerifiedByParallel?.length || 0) > 0">
          <div class="results-header"><h3>🟠 Verified by Parallel</h3></div>
          <div v-for="cluster in clustersVerifiedByParallel" :key="cluster.cluster_id + '-vbp'" class="cluster-item">
            <div class="cluster-line verifying-source">
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
            </div>
            <div class="cluster-line submitted-document">
              <strong>Extracted from Document: </strong>
              <span>{{ getClusterSubmittedName(cluster) }}</span>,
              <span>{{ getClusterSubmittedDate(cluster) }}</span>
            </div>
            <div class="cluster-citations">
              <div v-for="(citation, index) in getClusterCitations(cluster)" :key="`${cluster.cluster_id}-vbp-${index}`" class="cluster-line citation-line">
                <strong>Citation {{ index + 1 }}: </strong>
                <span class="citation-text">{{ formatCitationText(citation) }}</span>
                <span class="citation-status" :class="getCitationStatusClass(citation)">{{ getCitationStatusText(citation) }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- Verified Cases (strict: all verified, no mismatches, no parallel) (SHOW LAST) -->
        <template v-if="(clustersVerifiedStrict?.length || 0) > 0">
          <div class="results-header"><h3>✅ Verified</h3></div>
          <div v-for="cluster in clustersVerifiedStrict" :key="cluster.cluster_id + '-verified'" class="cluster-item">
            <div class="cluster-line verifying-source">
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
            </div>
            <div class="cluster-line submitted-document">
              <strong>Extracted from Document: </strong>
              <span>{{ getClusterSubmittedName(cluster) }}</span>,
              <span>{{ getClusterSubmittedDate(cluster) }}</span>
            </div>
            <div class="cluster-citations">
              <div v-for="(citation, index) in getClusterCitations(cluster)" :key="`${cluster.cluster_id}-verified-${index}`" class="cluster-line citation-line">
                <strong>Citation {{ index + 1 }}: </strong>
                <span class="citation-text">{{ formatCitationText(citation) }}</span>
                <span class="citation-status" :class="getCitationStatusClass(citation)">{{ getCitationStatusText(citation) }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- Other Cases -->
        <template v-if="(clustersOther?.length || 0) > 0">
          <div class="results-header"><h3>Other Cases</h3></div>
          <div v-for="cluster in clustersOther" :key="cluster.cluster_id + '-oth'" class="cluster-item">
            <div class="cluster-line verifying-source">
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
                          </div>
            <div class="cluster-line submitted-document">
              <strong>Extracted from Document: </strong>
              <span>{{ getClusterSubmittedName(cluster) }}</span>,
              <span>{{ getClusterSubmittedDate(cluster) }}</span>
            </div>
            <div class="cluster-citations">
              <div v-for="(citation, index) in getClusterCitations(cluster)" :key="`${cluster.cluster_id}-oth-${index}`" class="cluster-line citation-line">
                <strong>Citation {{ index + 1 }}: </strong>
                <span class="citation-text">{{ formatCitationText(citation) }}</span>
                <span class="citation-status" :class="getCitationStatusClass(citation)">{{ getCitationStatusText(citation) }}</span>
              </div>
            </div>
          </div>
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
            <span :style="{ color: citation.verified ? 'green' : (citation.true_by_parallel ? '#FF9800' : 'red') }">
              {{ citation.verified ? '✅ VERIFIED' : (citation.true_by_parallel ? '✅ VERIFIED BY PARALLEL' : '❌ UNVERIFIED') }}
            </span>
            <div v-if="!citation.verified && citation.error" class="verification-error mt-1">
              <small>{{ citation.error }}</small>
            </div>
          </div>
          <div class="citation-details">
            <div><strong>Case:</strong> {{ citation.extracted_case_name && citation.extracted_case_name !== 'N/A' ? citation.extracted_case_name : (citation.canonical_name || citation.case_name || 'N/A') }}</div>
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
      console.log('🔍 CitationResults DEBUG - props.results?.clusters:', props.results?.clusters)
      console.log('🔍 CitationResults DEBUG - clusters type:', Array.isArray(props.results?.clusters))
      console.log('🔍 CitationResults DEBUG - clusters length:', props.results?.clusters?.length)
      
      const serverClusters = props.results?.clusters || []
      console.log('🔍 CitationResults DEBUG - serverClusters after extraction:', {
        isArray: Array.isArray(serverClusters),
        length: serverClusters.length,
        firstCluster: serverClusters[0] ? {
          cluster_id: serverClusters[0].cluster_id,
          citationsCount: serverClusters[0].citations?.length || 0,
          hasCitations: !!serverClusters[0].citations
        } : null
      })
      
      if (serverClusters && serverClusters.length > 0) {
        console.log('🔍 CitationResults DEBUG - ✅ Returning server clusters:', serverClusters.length)
        return serverClusters
      }
      const citations = props.results?.citations || []
      if (!citations || citations.length === 0) return []
      const used = new Set()
      const groups = []
      const byUrl = new Map()
      citations.forEach((c, i) => {
        const u = c?.canonical_url
        if (u) {
          const arr = byUrl.get(u) || []
          arr.push(i)
          byUrl.set(u, arr)
        }
      })
      byUrl.forEach((idxs) => {
        if (idxs.length >= 2) {
          const g = idxs.map(j => citations[j])
          idxs.forEach(j => used.add(j))
          groups.push(g)
        }
      })
      const byParallel = new Map()
      citations.forEach((c, i) => {
        if (used.has(i)) return
        const pc = c?.parallel_citations || []
        if (pc && pc.length) {
          const key = [c.citation, ...pc].map(x => String(x)).sort().join('|')
          const arr = byParallel.get(key) || []
          arr.push(i)
          byParallel.set(key, arr)
        }
      })
      byParallel.forEach((idxs) => {
        if (idxs.length >= 2) {
          const g = idxs.map(j => citations[j])
          idxs.forEach(j => used.add(j))
          groups.push(g)
        }
      })
      citations.forEach((c, i) => { if (!used.has(i)) groups.push([c]) })
      
      // Build clusters and TRUST backend mismatch flags completely
      // Backend has all the sophisticated logic - frontend just displays
      const built = groups.map((g, idx) => {
        const rep = g.find(x => x?.canonical_name) || g[0]
        const vname = rep?.canonical_name || 'N/A'
        const vdate = rep?.canonical_date || rep?.extracted_date || 'N/A'
        const sname = (g.find(x => x?.extracted_case_name && x.extracted_case_name !== 'N/A')?.extracted_case_name) || 'N/A'
        const sdate = (g.find(x => x?.extracted_date && x.extracted_date !== 'N/A')?.extracted_date) || 'N/A'
        
        // ONLY use backend flags - don't calculate anything on frontend!
        // Backend sets name_mismatch and date_mismatch on each citation
        const hasNameMismatch = g.some(cit => cit?.name_mismatch === true)
        const hasDateMismatch = g.some(cit => cit?.date_mismatch === true)
        
        // Debug log for troubleshooting
        if (hasNameMismatch || hasDateMismatch) {
          console.log(`🔍 Cluster ${idx+1} mismatch flags:`, {
            canonical_name: vname,
            extracted_name: sname,
            canonical_date: vdate,
            extracted_date: sdate,
            has_name_mismatch: hasNameMismatch,
            has_date_mismatch: hasDateMismatch,
            citation_flags: g.map(c => ({
              citation: c.citation,
              name_mismatch: c.name_mismatch,
              date_mismatch: c.date_mismatch
            }))
          })
        }
        
        return {
          cluster_id: `fallback_${idx+1}`,
          citations: g,
          verifying_display_name: vname,
          verifying_display_date: vdate,
          submitted_display_name: sname,
          submitted_display_date: sdate,
          has_name_mismatch: hasNameMismatch,
          has_date_mismatch: hasDateMismatch
        }
      })
      console.log('🔍 CitationResults DEBUG - built fallback clusters:', built.length)
      return built
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
    
    // NEW: Verified clusters (clusters with at least one verified citation)
    const clustersVerified = computed(() => {
      if (!clusters.value || clusters.value.length === 0) return []
      
      return clusters.value.filter(cluster => {
        if (!cluster) return false
        const clusterCitations = cluster.citations || cluster.citation_objects || []
        if (!Array.isArray(clusterCitations) || clusterCitations.length === 0) return false
        
        // A cluster is "verified" if it has at least one verified citation
        return clusterCitations.some(cit => {
          if (!cit) return false
          return cit.verified === true || cit.verified === 'true'
        })
      })
    })
    
    // NEW: Unverified clusters (clusters with at least one unverified citation)
    const unverifiedClusters = computed(() => {
      if (!clusters.value || clusters.value.length === 0) return []
      
      return clusters.value.filter(cluster => {
        if (!cluster) return false
        const clusterCitations = cluster.citations || cluster.citation_objects || []
        if (!Array.isArray(clusterCitations) || clusterCitations.length === 0) return false
        
        // A cluster is "unverified" if it has at least one citation that is not verified, not true_by_parallel, and not possible_match
        return clusterCitations.some(cit => {
          if (!cit) return false
          const verified = cit.verified === true || cit.verified === 'true'
          const trueByParallel = cit.true_by_parallel === true || cit.true_by_parallel === 'true'
          const possibleMatch = cit.possible_match === true || cit.possible_match === 'true'
          return !verified && !trueByParallel && !possibleMatch
        })
      })
    })
    
    // NEW: Verified-by-parallel clusters (at least one true_by_parallel and no direct verified citations)
    const clustersVerifiedByParallel = computed(() => {
      if (!clusters.value || clusters.value.length === 0) return []
      return clusters.value.filter(cluster => {
        if (!cluster) return false
        const cits = cluster.citations || cluster.citation_objects || []
        if (!Array.isArray(cits) || cits.length === 0) return false
        
        const hasVbp = cits.some(c => {
          if (!c) return false
          return c.true_by_parallel === true || c.true_by_parallel === 'true'
        })
        const hasVerified = cits.some(c => {
          if (!c) return false
          return c.verified === true || c.verified === 'true'
        })
        return hasVbp && !hasVerified
      })
    })

    // NEW: Strict verified clusters (all citations verified, no mismatches, and no parallel flags)
    const clustersVerifiedStrict = computed(() => {
      if (!clusters.value || clusters.value.length === 0) return []
      return clusters.value.filter(cluster => {
        if (!cluster) return false
        const cits = cluster.citations || cluster.citation_objects || []
        if (!Array.isArray(cits) || cits.length === 0) return false
        
        const allVerified = cits.every(c => {
          if (!c) return false
          return c.verified === true || c.verified === 'true'
        })
        const noneParallel = !cits.some(c => {
          if (!c) return false
          return c.true_by_parallel === true || c.true_by_parallel === 'true'
        })
        const noNameMismatch = !Boolean(cluster?.has_name_mismatch)
        const noDateMismatch = !Boolean(cluster?.has_date_mismatch)
        return allVerified && noneParallel && noNameMismatch && noDateMismatch
      })
    })

    // NEW: Possible match clusters (clusters with at least one possible match citation)
    const possibleMatchClusters = computed(() => {
      if (!clusters.value || clusters.value.length === 0) return []
      
      return clusters.value.filter(cluster => {
        if (!cluster) return false
        const clusterCitations = cluster.citations || cluster.citation_objects || []
        if (!Array.isArray(clusterCitations) || clusterCitations.length === 0) return false
        
        // A cluster is "possible match" if it has at least one citation with possible_match=true
        return clusterCitations.some(cit => {
          if (!cit) return false
          return cit.possible_match === true || cit.possible_match === 'true'
        })
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
      const result = Boolean(cluster?.has_name_mismatch)
      if (result) {
        console.log('🔍 hasNameMismatch=true for cluster:', {
          cluster_id: cluster?.cluster_id,
          canonical_name: getClusterVerifyingName(cluster),
          extracted_name: getClusterSubmittedName(cluster),
          backend_flag: cluster?.has_name_mismatch
        })
      }
      return result
    }
    
    // Helper function to check if cluster has date mismatch (backend)
    const hasDateMismatch = (cluster) => {
      const result = Boolean(cluster?.has_date_mismatch)
      if (result) {
        console.log('🔍 hasDateMismatch=true for cluster:', {
          cluster_id: cluster?.cluster_id,
          canonical_date: getClusterVerifyingDate(cluster),
          extracted_date: getClusterSubmittedDate(cluster),
          backend_flag: cluster?.has_date_mismatch
        })
      }
      return result
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
          if (citation.source) {
            return citation.source
          }
        }
      }
      return null
    }

    const getClusterCitations = (cluster) => {
      // Return citation objects with their verification status
      // Backend sends 'citations', but also check 'citation_objects' for backward compatibility
      const list = cluster?.citations || cluster?.citation_objects || []
      
      // Ensure list is an array
      if (!Array.isArray(list)) {
        console.warn('⚠️ getClusterCitations: cluster.citations is not an array:', typeof list, cluster)
        return []
      }
      
      // If empty or single citation, return as-is (no deduplication needed)
      if (list.length <= 1) return list
      
      // Helper function to normalize citation text
      const normalizeCitation = (text) => {
        if (!text) return ''
        return text.toString().trim().replace(/\s+/g, ' ')
      }
      
      // Helper function to extract reporter and page (ignoring volume)
      // Examples: "227 Ill. 2d 147" -> { reporter: "Ill. 2d", page: "147", hasVolume: true }
      //           "Ill. 2d 147" -> { reporter: "Ill. 2d", page: "147", hasVolume: false }
      const parseCitation = (text) => {
        if (!text) return null
        const normalized = normalizeCitation(text)
        
        // Match pattern: [volume] reporter page
        // Examples: "227 Ill. 2d 147", "Ill. 2d 147", "879 N.E.2d 893"
        const match = normalized.match(/^(\d+)?\s*(.+?)\s+(\d+)$/)
        if (!match) return null
        
        const volume = match[1] || null
        const reporter = match[2] || ''
        const page = match[3] || ''
        
        return {
          fullText: normalized,
          volume: volume,
          reporter: reporter.trim(),
          page: page.trim(),
          hasVolume: volume !== null
        }
      }
      
      // Step 1: Remove exact duplicates
      const seen = new Set()
      const step1 = []
      for (const c of list) {
        if (!c) continue
        const key = normalizeCitation(c?.citation || c?.text || '')
        if (key && !seen.has(key)) {
          seen.add(key)
          step1.push(c)
        }
      }
      
      if (step1.length <= 1) return step1
      
      // Step 2: Remove duplicates where one lacks volume number but matches reporter + page
      // Build a map: reporter+page -> best citation (prefer one with volume)
      const reporterPageMap = new Map()
      const citationsByKey = new Map()
      
      for (const c of step1) {
        const citationText = normalizeCitation(c?.citation || c?.text || '')
        const parsed = parseCitation(citationText)
        
        if (!parsed) {
          // Can't parse - keep as-is
          const key = `exact_${citationText}`
          if (!citationsByKey.has(key)) {
            citationsByKey.set(key, c)
          }
          continue
        }
        
        // Create key from reporter + page (ignoring volume)
        const reporterPageKey = `${parsed.reporter}::${parsed.page}`.toLowerCase()
        
        const existing = reporterPageMap.get(reporterPageKey)
        if (!existing) {
          // First citation with this reporter+page
          reporterPageMap.set(reporterPageKey, {
            citation: c,
            parsed: parsed,
            citationText: citationText
          })
        } else {
          // Decide which to keep: prefer citation with volume number
          const existingHasVolume = existing.parsed.hasVolume
          const currentHasVolume = parsed.hasVolume
          
          if (currentHasVolume && !existingHasVolume) {
            // Current has volume, existing doesn't - replace
            reporterPageMap.set(reporterPageKey, {
              citation: c,
              parsed: parsed,
              citationText: citationText
            })
          } else if (!currentHasVolume && existingHasVolume) {
            // Existing has volume, current doesn't - keep existing
            // Do nothing
          } else if (currentHasVolume === existingHasVolume) {
            // Both have volume or both don't - prefer longer/more complete citation
            if (citationText.length > existing.citationText.length) {
              reporterPageMap.set(reporterPageKey, {
                citation: c,
                parsed: parsed,
                citationText: citationText
              })
            }
          }
        }
      }
      
      // Build final list from deduplicated citations
      const final = []
      const added = new Set()
      
      for (const [key, entry] of reporterPageMap.entries()) {
        const citationText = normalizeCitation(entry.citation?.citation || entry.citation?.text || '')
        if (!added.has(citationText)) {
          final.push(entry.citation)
          added.add(citationText)
        }
      }
      
      // Add any citations that couldn't be parsed (exact matches only)
      for (const [key, citation] of citationsByKey.entries()) {
        if (key.startsWith('exact_')) {
          const citationText = normalizeCitation(citation?.citation || citation?.text || '')
          if (!added.has(citationText)) {
            final.push(citation)
            added.add(citationText)
          }
        }
      }
      
      return final
    }

    // For displaying the specific mismatched citation for a cluster (backend indices)
    const getMismatchDisplayCitation = (cluster) => {
      if (!cluster) return null
      const cits = cluster.citations || cluster.citation_objects || []
      if (!Array.isArray(cits) || cits.length === 0) return null
      
      const indices = cluster.mismatch_indices || []
      if (Array.isArray(indices) && indices.length > 0) {
        const idx = indices[0]
        if (typeof idx === 'number' && idx >= 0 && idx < cits.length) {
          return cits[idx] || null
        }
      }
      // Fallback: first citation
      return cits[0] || null
    }

    const getRepresentativeCitation = (cluster) => {
      if (!cluster) return null
      const cits = cluster.citations || cluster.citation_objects || []
      if (!Array.isArray(cits) || cits.length === 0) return null
      
      // Check for mismatch indices first
      const indices = cluster.mismatch_indices || []
      if (Array.isArray(indices) && indices.length > 0) {
        const idx = indices[0]
        if (typeof idx === 'number' && idx >= 0 && idx < cits.length) {
          return cits[idx] || null
        }
      }
      
      // Try to find first verified citation
      const firstVerified = cits.find(c => c && (c.verified === true || c.verified === 'true'))
      if (firstVerified) return firstVerified
      
      // Fallback to first citation
      return cits[0] || null
    }

    // Backend-driven display fields with safe fallbacks
    const getClusterVerifyingName = (cluster) => {
      // Try verifying_display_name first
      if (cluster?.verifying_display_name && cluster.verifying_display_name !== 'N/A') {
        return cluster.verifying_display_name
      }
      
      // Try canonical_name
      const repCit = getRepresentativeCitation(cluster)
      if (repCit?.canonical_name && repCit.canonical_name !== 'N/A') {
        return repCit.canonical_name
      }
      
      // IMPORTANT FIX: Fall back to extracted_case_name before showing N/A
      // This fixes issue where 498 U.S. 941 showed "N/A" despite having extracted name
      if (repCit?.extracted_case_name && repCit.extracted_case_name !== 'N/A') {
        return repCit.extracted_case_name
      }
      
      // Try cluster-level extracted names from any citation
      const citations = cluster?.citations || cluster?.citation_objects || []
      for (const cit of citations) {
        if (cit?.extracted_case_name && cit.extracted_case_name !== 'N/A') {
          return cit.extracted_case_name
        }
      }
      
      return 'N/A'
    }
    const getClusterVerifyingDate = (cluster) => {
      return cluster?.verifying_display_date
        || getRepresentativeCitation(cluster)?.canonical_date
        || getRepresentativeCitation(cluster)?.extracted_date
        || 'N/A'
    }
    const getClusterSubmittedName = (cluster) => {
      // Always prefer the document's extracted case name for the Submitted line
      // Check ALL citations in cluster to find the longest/most complete name
      // This fixes truncated names like "Co. v. ABC-NACO" vs "Burlington Northern & Santa Fe Railway Co. v. ABC-NACO"
      
      const citations = cluster?.citations || cluster?.citation_objects || []
      if (Array.isArray(citations) && citations.length > 0) {
        // Find the longest extracted_case_name that's not generic or truncated
        const validNames = citations
          .map(cit => cit?.extracted_case_name)
          .filter(name => 
            name && 
            name !== 'N/A' && 
            !isGenericCaseName(name) &&
            // Skip obviously truncated names (starting with common truncation patterns)
            !name.match(/^(Co\.|Inc\.|LLC|Ltd\.|Corp\.)\s+v\./i)
          )
        
        if (validNames.length > 0) {
          // Return the longest name (most complete)
          const longestName = validNames.reduce((a, b) => a.length > b.length ? a : b)
          return longestName
        }
      }
      
      // Try cluster level submitted_display_name
      if (cluster?.submitted_display_name && 
          cluster.submitted_display_name !== 'N/A' &&
          !isGenericCaseName(cluster.submitted_display_name)) {
        return cluster.submitted_display_name
      }
      
      // DON'T fall back to canonical_name - only show actually extracted names!
      // If extraction failed, be honest and show 'N/A'
      
      return 'N/A'
    }
    
    // Helper function to detect generic case names
    const isGenericCaseName = (name) => {
      const genericPatterns = [
        'Washington State Case',
        'Pacific Reporter Case', 
        'Federal Appeals Case',
        'Federal District Case',
        'U.S. Supreme Court Case',
        'Case ('
      ]
      return genericPatterns.some(pattern => name.includes(pattern))
    }
    
    const getClusterSubmittedDate = (cluster) => {
      // Always prefer extracted_date from document (not canonical_date)
      // For citations with year-in-format (like "2002 WY 183"), prioritize citation text year
      // Check ALL citations to find the most common extracted date
      
      const citations = cluster?.citations || cluster?.citation_objects || []
      if (Array.isArray(citations) && citations.length > 0) {
        // Detect citations with year-in-format patterns (year is part of citation, not parenthetical)
        // Examples: "2002 WY 183", "2020 ND 123", "2017 OK 45", "2006 WL 3801910"
        const yearInFormatPattern = /\b(19|20)\d{2}\s+(?:WY|ND|OK|SD|UT|WI|MT|AL|AK|AR|AZ|CA|CO|CT|DE|FL|GA|HI|ID|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|NE|NV|NH|NJ|NM|NY|NC|OH|OR|PA|RI|SC|TN|TX|VT|VA|WA|WV|DC)\s+\d+/i
        
        // Check if any citations have year-in-format
        const hasYearInFormat = citations.some(cit => {
          const citationText = cit?.citation || ''
          return yearInFormatPattern.test(citationText)
        })
        
        // Collect all extracted dates
        const extractedDates = citations
          .map(cit => cit?.extracted_date)
          .filter(date => date && date !== 'N/A')
        
        // Extract years from citation text
        // For year-in-format citations, extract year from the format itself
        // For other citations, look for year in parentheses or at start
        const citationYears = citations
          .map(cit => {
            const citationText = cit?.citation || ''
            
            // For year-in-format citations, extract year from format (e.g., "2002 WY 183" -> "2002")
            if (yearInFormatPattern.test(citationText)) {
              // Match year at start followed by state abbreviation (e.g., "2002 WY 183")
              const formatMatch = citationText.match(/^(\d{4})\s+(?:WY|ND|OK|SD|UT|WI|MT|AL|AK|AR|AZ|CA|CO|CT|DE|FL|GA|HI|ID|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|NE|NV|NH|NJ|NM|NY|NC|OH|OR|PA|RI|SC|TN|TX|VT|VA|WA|WV|DC)/i)
              if (formatMatch) {
                return formatMatch[1] // Extract full 4-digit year
              }
            }
            
            // For WL citations (e.g., "2006 WL 3801910")
            const wlMatch = citationText.match(/^(\d{4})\s+WL\s+\d+/)
            if (wlMatch) {
              return wlMatch[1]
            }
            
            // Look for year in parentheses (e.g., "18 P.3d 49 (2001)")
            const parenMatch = citationText.match(/\((\d{4})\)/)
            if (parenMatch) {
              return parenMatch[1]
            }
            
            // Look for year at start of citation (e.g., "2002 WY 183")
            const startMatch = citationText.match(/^(\d{4})\s+/)
            if (startMatch) {
              return startMatch[1]
            }
            
            // Fallback: any 4-digit year
            const yearMatch = citationText.match(/\b(19|20)\d{2}\b/)
            return yearMatch ? yearMatch[0] : null
          })
          .filter(year => year !== null)
        
        // If citations have year-in-format, ALWAYS prioritize citation text years
        if (hasYearInFormat && citationYears.length > 0) {
          const citationYearCounts = {}
          citationYears.forEach(year => {
            citationYearCounts[year] = (citationYearCounts[year] || 0) + 1
          })
          const mostCommonCitationYear = Object.keys(citationYearCounts).length > 0
            ? Object.keys(citationYearCounts).reduce((a, b) => citationYearCounts[a] > citationYearCounts[b] ? a : b)
            : null
          if (mostCommonCitationYear) {
            return mostCommonCitationYear
          }
        }
        
        if (extractedDates.length > 0) {
          // Find most common extracted date year
          const dateCounts = {}
          extractedDates.forEach(date => {
            const yearMatch = String(date).match(/(19|20)\d{2}/)
            const year = yearMatch ? yearMatch[0] : String(date)
            dateCounts[year] = (dateCounts[year] || 0) + 1
          })
          
          const mostCommonExtractedYear = Object.keys(dateCounts).length > 0 
            ? Object.keys(dateCounts).reduce((a, b) => dateCounts[a] > dateCounts[b] ? a : b)
            : null
          
          // Check if citation text years match extracted years
          // If citation years are more consistent, prefer them (even if not year-in-format)
          if (citationYears.length > 0 && mostCommonExtractedYear) {
            const citationYearCounts = {}
            citationYears.forEach(year => {
              citationYearCounts[year] = (citationYearCounts[year] || 0) + 1
            })
            const mostCommonCitationYear = Object.keys(citationYearCounts).length > 0
              ? Object.keys(citationYearCounts).reduce((a, b) => citationYearCounts[a] > citationYearCounts[b] ? a : b)
              : null
            
            // If citation year is different and more consistent, use it
            if (mostCommonCitationYear && 
                mostCommonCitationYear !== mostCommonExtractedYear && 
                citationYearCounts[mostCommonCitationYear] >= citationYears.length * 0.5) {
              return mostCommonCitationYear
            }
          }
          
          // Return the full date string that matches the most common year
          if (mostCommonExtractedYear) {
            const matchingDate = extractedDates.find(date => 
              String(date).includes(mostCommonExtractedYear)
            )
            
            if (matchingDate) {
              return matchingDate
            }
          }
        } else if (citationYears.length > 0) {
          // No extracted dates, but we have citation years - use most common
          const citationYearCounts = {}
          citationYears.forEach(year => {
            citationYearCounts[year] = (citationYearCounts[year] || 0) + 1
          })
          const mostCommonCitationYear = Object.keys(citationYearCounts).length > 0
            ? Object.keys(citationYearCounts).reduce((a, b) => citationYearCounts[a] > citationYearCounts[b] ? a : b)
            : null
          if (mostCommonCitationYear) {
            return mostCommonCitationYear
          }
        }
      }
      
      // Try cluster level submitted_display_date
      if (cluster?.submitted_display_date && cluster.submitted_display_date !== 'N/A') {
        return cluster.submitted_display_date
      }
      
      // Try representative citation
      const repCitation = getRepresentativeCitation(cluster)
      if (repCitation?.extracted_date && repCitation.extracted_date !== 'N/A') {
        return repCitation.extracted_date
      }
      
      // Try first citation in cluster
      const firstCitation = cluster?.citations?.[0]
      if (firstCitation?.extracted_date && firstCitation.extracted_date !== 'N/A') {
        return firstCitation.extracted_date
      }
      
      return 'N/A'
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
      } else if (citation.error) {
        // Display error message (e.g., proprietary format)
        return citation.error
      } else {
        return 'Unverified'
      }
    }

    const formatCitationText = (citation) => {
      // If citation has a text property, use it
      if (citation.text) {
        return citation.text
      }
      
      // If citation is a string, return as-is
      if (typeof citation === 'string') {
        return citation
      }
      
      // If citation.citation exists and is a string
      if (citation.citation && typeof citation.citation === 'string') {
        return citation.citation
      }
      
      // If citation.citation is an object (eyecite citation), extract the basic citation text
      if (citation.citation && typeof citation.citation === 'object') {
        // Extract volume, reporter, and page from the eyecite object
        const groups = citation.citation.groups || {}
        const volume = groups.volume || ''
        const reporter = groups.reporter || ''
        const page = groups.page || ''
        
        if (volume && reporter && page) {
          return `${volume} ${reporter} ${page}`
        } else if (reporter && page) {
          return `${reporter} ${page}`
        } else {
          // Fallback: try to get a string representation
          const citStr = citation.citation.toString()
          // Try to extract the citation text from FullCaseCitation('text', ...)
          const match = citStr.match(/FullCaseCitation\('([^']+)'/)
          if (match) return match[1]
          
          const shortMatch = citStr.match(/ShortCaseCitation\('([^']+)'/)
          if (shortMatch) return shortMatch[1]
          
          const idMatch = citStr.match(/IdCitation\('([^']+)'/)
          if (idMatch) return idMatch[1]
          
          return citStr.substring(0, 100) + '...'
        }
      }
      
      // Fallback
      return citation.citation || 'N/A'
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
      const vbpIds = new Set((clustersVerifiedByParallel.value || []).map(c => c.cluster_id))
      const verifiedStrictIds = new Set((clustersVerifiedStrict.value || []).map(c => c.cluster_id))
      return base.filter(c => !unvIds.has(c.cluster_id) && !caseIds.has(c.cluster_id) && !dateIds.has(c.cluster_id) && !vbpIds.has(c.cluster_id) && !verifiedStrictIds.has(c.cluster_id))
    })

    return {
      citations,
      clusters,
      clustersVerified,
      verifiedCitations,
      unverifiedCitations,
      verifiedByParallelCitations,
      unverifiedClusters,
      clustersVerifiedByParallel,
      clustersVerifiedStrict,
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
      getCitationStatusText,
      formatCitationText
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

.citation-line {
  display: flex;
  align-items: center;
  gap: 10px;
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
