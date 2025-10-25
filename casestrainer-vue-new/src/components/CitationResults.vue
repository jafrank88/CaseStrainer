<template>
  <div class="citation-results">
    <!-- SECTION 1: Unverified Clusters (SHOW FIRST) -->
    <div v-if="(unverifiedClusters?.length || 0) > 0" class="results-content">
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

    <!-- SECTION 1.1: Possible Match Clusters -->
    <div v-if="(possibleMatchClusters?.length || 0) > 0" class="results-content">
      <div class="results-header">
        <h2>🔍 SECTION 1.1: Possible Match Clusters</h2>
        <p>{{ possibleMatchClusters?.length || 0 }} cluster(s) with possible matches</p>
      </div>
      
      <div class="clusters-list">
        <div v-for="cluster in possibleMatchClusters" :key="cluster.cluster_id" class="cluster-item possible-match-cluster">
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
    <div v-if="(mismatchClusters?.length || 0) > 0" class="results-content">
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

    <!-- SECTION 1.5: Citations Verified by Parallel (SHOW THIRD) -->
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
            <strong>Verifying Source: </strong>
            <template v-if="cluster.citations?.[0]?.canonical_url">
              <a :href="cluster.citations[0].canonical_url" target="_blank" class="canonical-link">
                {{ cluster.citations[0].canonical_name || 'N/A' }}, {{ cluster.citations[0].canonical_date || cluster.citations[0].extracted_date || 'N/A' }}
              </a>
            </template>
            <template v-else>
              {{ cluster.citations?.[0]?.canonical_name || 'N/A' }}, {{ cluster.citations?.[0]?.canonical_date || cluster.citations?.[0]?.extracted_date || 'N/A' }}
            </template>
            <span v-if="getClusterSource(cluster)" class="source-badge">
              ({{ getClusterSource(cluster) }})
            </span>
          </div>
          
          <!-- Line 2: Submitted Document -->
          <div class="cluster-line submitted-document">
            <strong>Submitted Document: </strong>
            {{ cluster.citations?.[0]?.extracted_case_name || 'N/A' }}, {{ cluster.citations?.[0]?.extracted_date || 'N/A' }}
          </div>
          
          <!-- Lines 3+: Individual Citations with Status -->
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
    
    // Helper function to extract year from date string
    const extractYear = (dateStr) => {
      if (!dateStr) return null
      const str = String(dateStr).trim()
      // Match 4-digit year (handles "2014", "1987-05-26", "2014-01-01", etc.)
      const yearMatch = str.match(/\b(\d{4})\b/)
      return yearMatch ? yearMatch[1] : null
    }
    
    // Helper function to check if names are similar (handles abbreviations)
    const areNamesSimilar = (extracted, canonical) => {
      if (!extracted || !canonical) return true; // Skip if either is missing
      
      const norm1 = extracted.trim().toLowerCase().replace(/\s+/g, ' ')
      const norm2 = canonical.trim().toLowerCase().replace(/\s+/g, ' ')
      
      // Exact match
      if (norm1 === norm2) return true
      
      // Common abbreviation expansions
      const abbreviations = {
        'ins.': 'insurance',  // ADDED: Handle 'ins.' with period
        'ins': 'insurance',  // FIXED: 'ins' should expand to 'insurance', not 'immigration and naturalization service'
        'mut.': 'mutual',  // ADDED: Missing abbreviation for 'mutual'
        'mut': 'mutual',
        'dep\'t': 'department',
        'dept': 'department',
        'att\'y': 'attorney',
        'atty': 'attorney',
        'gen.': 'general',
        'gen': 'general',
        'sec.': 'secretary',
        'sec': 'secretary',
        'comm\'r': 'commissioner',
        'gov\'t': 'government',
        'govt': 'government',
        'co.': 'company',
        'co': 'company',
        'company': 'company',  // Ensure consistency
        'inc.': 'incorporated',
        'inc': 'incorporated',
        'auth.': 'authority',
        'auth': 'authority',
        'ctr.': 'center',
        'ctr': 'center',
        'servs.': 'services',
        'servs': 'services',
        'mach.': 'machine',
        'mach': 'machine',
        'hosp.': 'hospital',
        'hosp': 'hospital',
        'pub.': 'public',
        'pub': 'public',
        'ry.': 'railway',
        'ry': 'railway',
        'r.r.': 'railroad',
        'r.r': 'railroad',
        'railroad': 'railway',  // Railroad and Railway are often interchangeable
        'railway': 'railroad',  // Bidirectional mapping
        'railroad company': 'railway company',  // Specific company name mapping
        'railway company': 'railroad company',  // Bidirectional company mapping
        // US STATE ABBREVIATIONS - Comprehensive list
        'al.': 'alabama', 'al': 'alabama', 'alabama': 'alabama',
        'ak.': 'alaska', 'ak': 'alaska', 'alaska': 'alaska',
        'az.': 'arizona', 'az': 'arizona', 'arizona': 'arizona',
        'ar.': 'arkansas', 'ar': 'arkansas', 'arkansas': 'arkansas',
        'ca.': 'california', 'ca': 'california', 'california': 'california',
        'co.': 'colorado', 'co': 'colorado', 'colorado': 'colorado',
        'ct.': 'connecticut', 'ct': 'connecticut', 'connecticut': 'connecticut',
        'de.': 'delaware', 'de': 'delaware', 'delaware': 'delaware',
        'fl.': 'florida', 'fl': 'florida', 'florida': 'florida',
        'ga.': 'georgia', 'ga': 'georgia', 'georgia': 'georgia',
        'hi.': 'hawaii', 'hi': 'hawaii', 'hawaii': 'hawaii',
        'id.': 'idaho', 'id': 'idaho', 'idaho': 'idaho',
        'il.': 'illinois', 'il': 'illinois', 'illinois': 'illinois',
        'in.': 'indiana', 'in': 'indiana', 'indiana': 'indiana',
        'ia.': 'iowa', 'ia': 'iowa', 'iowa': 'iowa',
        'ks.': 'kansas', 'ks': 'kansas', 'kansas': 'kansas',
        'ky.': 'kentucky', 'ky': 'kentucky', 'kentucky': 'kentucky',
        'la.': 'louisiana', 'la': 'louisiana', 'louisiana': 'louisiana',
        'me.': 'maine', 'me': 'maine', 'maine': 'maine',
        'md.': 'maryland', 'md': 'maryland', 'maryland': 'maryland',
        'ma.': 'massachusetts', 'ma': 'massachusetts', 'massachusetts': 'massachusetts',
        'mi.': 'michigan', 'mi': 'michigan', 'michigan': 'michigan',
        'mn.': 'minnesota', 'mn': 'minnesota', 'minnesota': 'minnesota',
        'ms.': 'mississippi', 'ms': 'mississippi', 'mississippi': 'mississippi',
        'mo.': 'missouri', 'mo': 'missouri', 'missouri': 'missouri',
        'mt.': 'montana', 'mt': 'montana', 'montana': 'montana',
        'ne.': 'nebraska', 'ne': 'nebraska', 'nebraska': 'nebraska',
        'nv.': 'nevada', 'nv': 'nevada', 'nevada': 'nevada',
        'nh.': 'new hampshire', 'nh': 'new hampshire', 'new hampshire': 'new hampshire',
        'nj.': 'new jersey', 'nj': 'new jersey', 'new jersey': 'new jersey',
        'nm.': 'new mexico', 'nm': 'new mexico', 'new mexico': 'new mexico',
        'ny.': 'new york', 'ny': 'new york', 'new york': 'new york',
        'n.c.': 'north carolina', 'nc': 'north carolina', 'north carolina': 'north carolina',
        'nd.': 'north dakota', 'nd': 'north dakota', 'north dakota': 'north dakota',
        'oh.': 'ohio', 'oh': 'ohio', 'ohio': 'ohio',
        'ok.': 'oklahoma', 'ok': 'oklahoma', 'oklahoma': 'oklahoma',
        'or.': 'oregon', 'or': 'oregon', 'oregon': 'oregon',
        'pa.': 'pennsylvania', 'pa': 'pennsylvania', 'pennsylvania': 'pennsylvania',
        'ri.': 'rhode island', 'ri': 'rhode island', 'rhode island': 'rhode island',
        's.c.': 'south carolina', 'sc': 'south carolina', 'south carolina': 'south carolina',
        'sd.': 'south dakota', 'sd': 'south dakota', 'south dakota': 'south dakota',
        'tn.': 'tennessee', 'tn': 'tennessee', 'tennessee': 'tennessee',
        'tx.': 'texas', 'tx': 'texas', 'texas': 'texas',
        'ut.': 'utah', 'ut': 'utah', 'utah': 'utah',
        'vt.': 'vermont', 'vt': 'vermont', 'vermont': 'vermont',
        'va.': 'virginia', 'va': 'virginia', 'virginia': 'virginia',
        'wa.': 'washington', 'wa': 'washington', 'washington': 'washington',
        'wv.': 'west virginia', 'wv': 'west virginia', 'west virginia': 'west virginia',
        'wi.': 'wisconsin', 'wi': 'wisconsin', 'wisconsin': 'wisconsin',
        'wy.': 'wyoming', 'wy': 'wyoming', 'wyoming': 'wyoming',
        // DC and territories
        'd.c.': 'district of columbia', 'dc': 'district of columbia', 'district of columbia': 'district of columbia',
        'pr.': 'puerto rico', 'pr': 'puerto rico', 'puerto rico': 'puerto rico',
        'vi.': 'virgin islands', 'vi': 'virgin islands', 'virgin islands': 'virgin islands',
        'gu.': 'guam', 'gu': 'guam', 'guam': 'guam',
        'as.': 'american samoa', 'as': 'american samoa', 'american samoa': 'american samoa',
        'mp.': 'northern mariana islands', 'mp': 'northern mariana islands', 'northern mariana islands': 'northern mariana islands',
        // COMMON LEGAL ABBREVIATIONS
        'mut.': 'mutual', 'mut': 'mutual', 'mutual': 'mutual',
        'ins.': 'insurance', 'ins': 'insurance', 'insurance': 'insurance',
        'corp.': 'corporation', 'corp': 'corporation', 'corporation': 'corporation',
        'ltd.': 'limited', 'ltd': 'limited', 'limited': 'limited',
        'llc': 'limited liability company', 'l.l.c.': 'limited liability company', 'limited liability company': 'limited liability company',
        'assoc.': 'association', 'assoc': 'association', 'association': 'association',
        'soc.': 'society', 'soc': 'society', 'society': 'society',
        'found.': 'foundation', 'found': 'foundation', 'foundation': 'foundation',
        'trust': 'trust', 'tr.': 'trust', 'tr': 'trust',
        'est.': 'estate', 'est': 'estate', 'estate': 'estate',
        'part.': 'partnership', 'part': 'partnership', 'partnership': 'partnership',
        'lp': 'limited partnership', 'l.p.': 'limited partnership', 'limited partnership': 'limited partnership',
        'llp': 'limited liability partnership', 'l.l.p.': 'limited liability partnership', 'limited liability partnership': 'limited liability partnership',
        'gp': 'general partnership', 'g.p.': 'general partnership', 'general partnership': 'general partnership',
        'jv': 'joint venture', 'j.v.': 'joint venture', 'joint venture': 'joint venture',
        'hold.': 'holding', 'hold': 'holding', 'holding': 'holding', 'holdings': 'holding',
        'grp.': 'group', 'grp': 'group', 'group': 'group',
        'intl.': 'international', 'intl': 'international', 'international': 'international',
        'natl.': 'national', 'natl': 'national', 'national': 'national',
        'fed.': 'federal', 'fed': 'federal', 'federal': 'federal',
        'govt.': 'government', 'govt': 'government', 'government': 'government',
        'admin.': 'administration', 'admin': 'administration', 'administration': 'administration',
        'dept.': 'department', 'dept': 'department', 'department': 'department',
        'div.': 'division', 'div': 'division', 'division': 'division',
        'sect.': 'section', 'sect': 'section', 'section': 'section',
        'subdiv.': 'subdivision', 'subdiv': 'subdivision', 'subdivision': 'subdivision',
        'dist.': 'district', 'dist': 'district', 'district': 'district',
        'ctr.': 'center', 'ctr': 'center', 'center': 'center', 'cent.': 'center', 'cent': 'center',
        'inst.': 'institute', 'inst': 'institute', 'institute': 'institute',
        'univ.': 'university', 'univ': 'university', 'university': 'university',
        'coll.': 'college', 'coll': 'college', 'college': 'college',
        'sch.': 'school', 'sch': 'school', 'school': 'school',
        'elem.': 'elementary', 'elem': 'elementary', 'elementary': 'elementary',
        'sec.': 'secondary', 'sec': 'secondary', 'secondary': 'secondary',
        'high': 'high school', 'hs': 'high school', 'h.s.': 'high school', 'high school': 'high school',
        'middle': 'middle school', 'ms': 'middle school', 'm.s.': 'middle school', 'middle school': 'middle school',
        'jr.': 'junior', 'jr': 'junior', 'junior': 'junior',
        'sr.': 'senior', 'sr': 'senior', 'senior': 'senior',
        'inter.': 'intermediate', 'inter': 'intermediate', 'intermediate': 'intermediate',
        'adv.': 'advanced', 'adv': 'advanced', 'advanced': 'advanced',
        'tech.': 'technical', 'tech': 'technical', 'technical': 'technical',
        'voc.': 'vocational', 'voc': 'vocational', 'vocational': 'vocational',
        'prof.': 'professional', 'prof': 'professional', 'professional': 'professional',
        'comm.': 'community', 'comm': 'community', 'community': 'community',
        'pub.': 'public', 'pub': 'public', 'public': 'public',
        'priv.': 'private', 'priv': 'private', 'private': 'private',
        'munic.': 'municipal', 'munic': 'municipal', 'municipal': 'municipal',
        'county': 'county', 'co.': 'county',
        'state': 'state', 'st.': 'state', 'st': 'state',
        'city': 'city', 'town': 'town', 'village': 'village', 'borough': 'borough', 'township': 'township',
        'parish': 'parish', 'province': 'province', 'territory': 'territory', 'region': 'region',
        'area': 'area', 'zone': 'zone', 'ward': 'ward', 'precinct': 'precinct',
        'block': 'block', 'lot': 'lot', 'parcel': 'parcel', 'tract': 'tract',
        'development': 'development', 'suburb': 'suburb', 'neighborhood': 'neighborhood',
        'club': 'club', 'organization': 'organization', 'org.': 'organization', 'org': 'organization',
        'academy': 'academy', 'hospital': 'hospital', 'hosp.': 'hospital', 'hosp': 'hospital',
        'medical': 'medical', 'med.': 'medical', 'med': 'medical', 'health': 'health', 'care': 'care',
        'service': 'service', 'serv.': 'service', 'serv': 'service',
        'facility': 'facility', 'fac.': 'facility', 'fac': 'facility',
        'building': 'building', 'bldg.': 'building', 'bldg': 'building',
        'structure': 'structure', 'complex': 'complex', 'plaza': 'plaza', 'mall': 'mall',
        'shopping': 'shopping', 'retail': 'retail', 'commercial': 'commercial',
        'business': 'business', 'enterprise': 'enterprise', 'firm': 'firm',
        'agency': 'agency', 'bureau': 'bureau', 'office': 'office', 'off.': 'office', 'off': 'office',
        'headquarters': 'headquarters', 'hq': 'headquarters', 'h.q.': 'headquarters',
        'branch': 'branch', 'unit': 'unit', 'team': 'team',
        'committee': 'committee', 'comm.': 'committee', 'comm': 'committee',
        'board': 'board', 'council': 'council', 'commission': 'commission', 'authority': 'authority',
        // ADD MISSING ABBREVIATIONS
        'equip.': 'equipment',
        'equip': 'equipment',
        'express co.': 'express company',
        'express co': 'express company',
        's. express co.': 'southern express company',
        's. express co': 'southern express company',
        'southern railway company': 'railway company',
        'railway company': 'railroad company',
        'farm bureau mut. ins. co.': 'farm bureau mutual insurance company',
        'farm bureau mut ins co': 'farm bureau mutual insurance company',
        'n.c. farm bureau mut. ins. co.': 'north carolina farm bureau mutual insurance company',
        'n.c. farm bureau mut ins co': 'north carolina farm bureau mutual insurance company',
        'n.c. farm bureau mutual insurance': 'north carolina farm bureau mutual insurance company',
        'north carolina farm bureau mutual insurance': 'north carolina farm bureau mutual insurance company',
        'monarch elevator & mach. co.': 'monarch elevator and machine company',
        'monarch elevator & mach co': 'monarch elevator and machine company',
        'alexander tank & equip. co.': 'alexander tank and equipment company',
        'alexander tank & equip co': 'alexander tank and equipment company',
        // ADDITIONAL RAILWAY/RAILROAD MAPPINGS
        'p.r. co.': 'pennsylvania railroad company',
        'p.r. co': 'pennsylvania railroad company',
        'pennsylvania railroad co.': 'pennsylvania railroad company',
        'pennsylvania railroad co': 'pennsylvania railroad company',
        'milwaukee & saint paul railway co.': 'milwaukee and saint paul railway company',
        'milwaukee & saint paul railway co': 'milwaukee and saint paul railway company',
        'milwaukee & saint paul railroad co.': 'milwaukee and saint paul railroad company',
        'milwaukee & saint paul railroad co': 'milwaukee and saint paul railroad company',
        // COMPREHENSIVE RAILWAY COMPANY MAPPINGS
        'milwaukee & saint paul railway co.': 'railway company',
        'milwaukee & saint paul railway co': 'railway company',
        'southern railway company': 'railway company',
        'railway company': 'railroad company',  // Railway and railroad are interchangeable
        'railroad company': 'railway company'
      }
      
      // Expand abbreviations in both names
      let expanded1 = norm1
      let expanded2 = norm2
      
      // Sort abbreviations by length (longest first) to handle nested abbreviations
      const sortedAbbreviations = Object.entries(abbreviations).sort((a, b) => b[0].length - a[0].length)
      
      sortedAbbreviations.forEach(([abbr, full]) => {
        // Create a regex that matches the abbreviation with proper word boundaries
        const escapedAbbr = abbr.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        
        // Handle abbreviations with periods differently
        if (abbr.includes('.')) {
          // For abbreviations with periods, match word boundary at start and space/punctuation at end
          const regex = new RegExp(`\\b${escapedAbbr}(?=\\s|$)`, 'gi')
          expanded1 = expanded1.replace(regex, full)
          expanded2 = expanded2.replace(regex, full)
        } else {
          // For abbreviations without periods, use standard word boundaries
          const regex = new RegExp(`\\b${escapedAbbr}\\b`, 'gi')
          expanded1 = expanded1.replace(regex, full)
          expanded2 = expanded2.replace(regex, full)
        }
      })
      
      // NEW: Check for simplified vs. full legal names
      // Handle cases where extracted name is simplified version of canonical name
      if (norm1.length < norm2.length * 0.6) { // Extracted is significantly shorter
        // Extract the core parts (before "v.")
        const extractedParts = norm1.split(/\s+v\.?\s+/)
        const canonicalParts = norm2.split(/\s+v\.?\s+/)
        
        if (extractedParts.length === 2 && canonicalParts.length === 2) {
          const extractedPlaintiff = extractedParts[0].trim()
          const canonicalPlaintiff = canonicalParts[0].trim()
          const extractedDefendant = extractedParts[1].trim()
          const canonicalDefendant = canonicalParts[1].trim()
          
          // Check if plaintiff last names match
          const extractedPlaintiffWords = extractedPlaintiff.split(/\s+/)
          const canonicalPlaintiffWords = canonicalPlaintiff.split(/\s+/)
          const extractedPlaintiffLastName = extractedPlaintiffWords[extractedPlaintiffWords.length - 1]
          const canonicalPlaintiffLastName = canonicalPlaintiffWords[canonicalPlaintiffWords.length - 1]
          
          // Check if last names match or extracted plaintiff is contained in canonical
          if (extractedPlaintiffLastName === canonicalPlaintiffLastName || 
              canonicalPlaintiff.includes(extractedPlaintiff)) {
            
            // Check defendant side - check if extracted defendant is contained in canonical
            if (canonicalDefendant.includes(extractedDefendant) || 
                extractedDefendant.includes(canonicalDefendant)) {
              return true // Simplified name is valid
            }
          }
        }
      }
      
      // NEW: Check for full vs. simplified legal names (reverse case)
      if (norm2.length < norm1.length * 0.6) { // Canonical is significantly shorter
        // Check if canonical name is contained in extracted name
        if (norm1.includes(norm2)) {
          return true // Canonical is simplified version of extracted
        }
      }
      
      // Check if extracted is a reasonable abbreviation of canonical
      // (e.g., "Wang v. INS" vs "Jiamu Wang v. Immigration and Naturalization Service")
      const extractedParts = norm1.split(/\s+v\.?\s+/)
      const canonicalParts = norm2.split(/\s+v\.?\s+/)
      
      if (extractedParts.length === 2 && canonicalParts.length === 2) {
        // Check if the last names match
        const extractedLastName = extractedParts[0].split(/\s+/).pop()
        const canonicalLastName = canonicalParts[0].split(/\s+/).pop()
        
        // If last names match and defendants match (possibly abbreviated), consider similar
        if (extractedLastName === canonicalLastName) {
          // Check defendant side
          const extDef = extractedParts[1]
          const canDef = canonicalParts[1]
          
          // Expand abbreviations and check
          let expExtDef = extDef
          let expCanDef = canDef
          Object.entries(abbreviations).forEach(([abbr, full]) => {
            // FIXED: Use word boundaries with proper handling of periods
            const regex = new RegExp('(^|\\s)' + abbr.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(\\s|$)', 'g')
            expExtDef = expExtDef.replace(regex, '$1' + full + '$2')
            expCanDef = expCanDef.replace(regex, '$1' + full + '$2')
          })
          
          if (expExtDef === expCanDef || canDef.includes(extDef) || expCanDef.includes(expExtDef)) {
            return true
          }
          
          // SPECIAL CASE: Both defendants are railway/railroad companies
          // Even if names are different, if both are railway companies, consider similar
          const railwayKeywords = ['railway', 'railroad', 'r.r.', 'p.r. co.', 'southern railway', 'milwaukee', 'saint paul']
          const extIsRailway = railwayKeywords.some(keyword => expExtDef.includes(keyword))
          const canIsRailway = railwayKeywords.some(keyword => expCanDef.includes(keyword))
          
          if (extIsRailway && canIsRailway) {
            return true
          }
        }
      }
      
      // Check if one name is contained in the other (for partial name extraction)
      if (norm2.includes(norm1) && norm1.length > 10) return true
      if (norm1.includes(norm2) && norm2.length > 10) return true
      
      // IMPROVED: More permissive similarity check for legal case names
      // Check word overlap - if most words match, consider similar
      const words1 = new Set(norm1.split(/\s+/).filter(w => w.length > 2))
      const words2 = new Set(norm2.split(/\s+/).filter(w => w.length > 2))
      
      if (words1.size > 0 && words2.size > 0) {
        const intersection = new Set([...words1].filter(x => words2.has(x)))
        const union = new Set([...words1, ...words2])
        
        // If more than 50% of words overlap, consider similar
        const similarity = intersection.size / union.size
        if (similarity > 0.5) return true
        
        // Special case: if all words from shorter name are in longer name
        const shorter = words1.size <= words2.size ? words1 : words2
        const longer = words1.size <= words2.size ? words2 : words1
        const shorterInLonger = [...shorter].every(word => longer.has(word))
        if (shorterInLonger && shorter.size >= 2) return true
      }
      
      return false
    }
    
    // Check per-citation mismatches (name/date)
    const citationHasNameMismatch = (cit) => {
      if (!cit) return false
      const extractedName = cit.extracted_case_name
      const canonicalName = cit.canonical_name
      if (!extractedName || !canonicalName) return false
      if (extractedName === 'N/A') return true
      return !areNamesSimilar(extractedName, canonicalName)
    }
    
    const citationHasDateMismatch = (cit) => {
      if (!cit) return false
      const extractedYear = extractYear(cit.extracted_date)
      const canonicalYear = extractYear(cit.canonical_date)
      if (!extractedYear || !canonicalYear) return false
      
      const yearDiff = Math.abs(parseInt(extractedYear) - parseInt(canonicalYear))
      // Only flag as mismatch if years are more than 5 years apart
      // This prevents flagging minor date variations as mismatches
      return yearDiff > 5
    }
    
    // NEW: Name/Date mismatch clusters (for debugging extraction issues)
    const mismatchClusters = computed(() => {
      if (!clusters.value || clusters.value.length === 0) {
        console.log('⚠️ [MISMATCH] No clusters available')
        return []
      }
      console.log(`⚠️ [MISMATCH] Checking ${clusters.value.length} clusters for mismatches`)
      const mismatches = clusters.value.filter(cluster => {
        const clusterCitations = cluster.citations || []
        if (clusterCitations.length === 0) return false
        // Any citation in the cluster with a mismatch counts
        return clusterCitations.some(cit => citationHasNameMismatch(cit) || citationHasDateMismatch(cit))
      })
      console.log(`⚠️ [MISMATCH] Found ${mismatches.length} clusters with mismatches`)
      return mismatches
    })
    
    // Helper function to check if cluster has name mismatch
    const hasNameMismatch = (cluster) => {
      const clusterCitations = cluster.citations || []
      if (clusterCitations.length === 0) return false
      return clusterCitations.some(citationHasNameMismatch)
    }
    
    // Helper function to check if cluster has date mismatch
    const hasDateMismatch = (cluster) => {
      const clusterCitations = cluster.citations || []
      if (clusterCitations.length === 0) return false
      return clusterCitations.some(citationHasDateMismatch)
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

    // For displaying the specific mismatched citation for a cluster
    const getMismatchDisplayCitation = (cluster) => {
      const cits = cluster.citations || cluster.citation_objects || []
      if (cits.length === 0) return null
      // Prefer name mismatch over date mismatch for display
      const nameMismatch = cits.find(citationHasNameMismatch)
      if (nameMismatch) return nameMismatch
      const dateMismatch = cits.find(citationHasDateMismatch)
      if (dateMismatch) return dateMismatch
      // Fallback to first citation
      return cits[0]
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
