/**
 * Cluster and citation grouping + verification helpers for CitationResults.
 * Accepts a ref/computed of results and returns computeds for citations, clusters, and grouped lists.
 */

import { computed } from 'vue'

const isPartialCitation = (cit) => {
  if (!cit) return false
  const text = (cit.citation || cit.text || '').toString().trim()
  return /\s_{2,}\s*(?:\(|$)/.test(text) || /\s_{2,}\)/.test(text) || /[.\s]_{2,}\s*$/.test(text)
}

export function isNaAndPartial(cit) {
  if (!cit) return false
  const caseName = (cit.extracted_case_name || cit.case_name || '').toString().trim().toUpperCase()
  return caseName === 'N/A' && isPartialCitation(cit)
}

export function hasCanonicalUrl(cit) {
  const u = cit?.canonical_url || cit?.url
  return u && String(u).trim().length > 0
}

export function isEffectivelyVerified(cit) {
  if (!cit) return false
  if (isNaAndPartial(cit)) return false
  
  // CRITICAL FIX: Preserve real canonical URLs even with date mismatch
  // Check if citation has a real (non-Google) canonical URL
  const url = cit?.canonical_url || cit?.url
  const hasRealUrl = url && 
    !String(url).startsWith('https://www.google.com/search?') &&
    !String(url).startsWith('http://www.google.com/search?')
  
  // Only reject on date mismatch if no real URL present
  if ((cit.date_mismatch === true || cit.date_mismatch === 'true') && !hasRealUrl) return false
  
  const status = (cit.verification_status || '').toString().toLowerCase()
  if (status === 'year_mismatch' || status === 'possible_match_with_url' || status === 'possible_match_gate_reject') {
    // Also check for real URL on year_mismatch
    if (status === 'year_mismatch' && hasRealUrl) {
      // Allow date differences with real URLs
    } else {
      return false
    }
  }
  if (!hasCanonicalUrl(cit)) return false
  const verified = cit.verified === true || cit.verified === 'true'
  const isVerified = cit.is_verified === true || cit.is_verified === 'true'
  return verified || isVerified
}

export function isEffectivelyVerifiedWithCluster(cit, cluster) {
  if (!cit) return false
  if (isNaAndPartial(cit)) return false
  const verified = cit.verified === true || cit.verified === 'true'
  const isVerified = cit.is_verified === true || cit.is_verified === 'true'
  if (!verified && !isVerified) return false
  const hasUrl = hasCanonicalUrl(cit) || (cluster && (cluster.canonical_url || cluster.display_canonical_url) && String(cluster.canonical_url || cluster.display_canonical_url || '').trim().length > 0)
  return hasUrl
}

export function getDisplayCaseName(cit) {
  if (!cit) return 'N/A'
  const verified = cit.verified === true || cit.verified === 'true'
  const canonical = (cit.canonical_name || '').toString().trim()
  if (verified && canonical && canonical !== 'N/A') return cit.canonical_name
  const extracted = (cit.extracted_case_name || '').toString().trim()
  if (extracted && extracted !== 'N/A') return cit.extracted_case_name
  return cit.canonical_name || cit.case_name || 'N/A'
}

function isRealCanonicalUrl(urlStr) {
  const u = (urlStr || '').toString().trim()
  if (!u || u.toUpperCase() === 'N/A') return false
  if (u.startsWith('https://www.google.com/search?') || u.startsWith('http://www.google.com/search?')) return false
  return true
}

function hasPossibleMatchEvidence(cit) {
  if (!cit || typeof cit !== 'object') return false
  const canonicalUrl = (cit.canonical_url || cit.url || '').toString().trim()
  const metadata = cit.metadata && typeof cit.metadata === 'object' ? cit.metadata : {}
  const pmUrl = (metadata.possible_match_url || '').toString().trim()
  return [canonicalUrl, pmUrl].some(v => isRealCanonicalUrl(v))
}

function hasDateMismatchEvidence(cit) {
  if (!cit || typeof cit !== 'object') return false
  const canonicalUrl = (cit.canonical_url || cit.url || '').toString().trim()
  const metadata = cit.metadata && typeof cit.metadata === 'object' ? cit.metadata : {}
  const pmUrl = (metadata.possible_match_url || '').toString().trim()
  return [canonicalUrl, pmUrl].some(v => isRealCanonicalUrl(v))
}

/**
 * @param {import('vue').Ref|import('vue').ComputedRef} resultsRef - ref/computed of API results { citations, clusters, cluster_sections? }
 */
export function useCitationClusters(resultsRef) {
  const citations = computed(() => resultsRef.value?.citations || [])

  const getReporterTier = (citationText) => {
    const text = (citationText || '').toString().toUpperCase()
    if (!text) return 'other'
    if (/\d+\s+U\.?\s*S\.?\s+(?:\d+|_+)/.test(text)) return 'supreme'
    if (/\d+\s+S\.?\s*CT\.?\s+(?:\d+|_+)/.test(text)) return 'supreme'
    if (/\d+\s+L\.?\s*ED\.?\s*(?:2D\s+)?\d+/.test(text)) return 'supreme'
    if (/\d+\s+F\.?\s*SUPP\.?\s*(?:2D\s+|3D\s+)?\d+/.test(text)) return 'district'
    if (/\d+\s+F\.?\s*(?:2D|3D|4TH)\s+\d+/.test(text)) return 'circuit'
    return 'other'
  }

  const isWlCitation = (citationText) => /\b\d{4}\s+WL\s+\d+\b/i.test((citationText || '').toString())

  const normalizedCitationKey = (citationText) => (citationText || '').toString().replace(/\s+/g, ' ').trim().toLowerCase()

  const clusterCitationSetKey = (cluster) => {
    const cits = cluster?.citations || cluster?.citation_objects || []
    const keys = cits
      .filter(c => c && typeof c === 'object')
      .map(c => normalizedCitationKey(c.citation || c.text || ''))
      .filter(Boolean)
      .sort()
    return keys.join('|')
  }

  const splitMixedFederalTiers = (cluster) => {
    if (!cluster || typeof cluster !== 'object') return [cluster]
    const cits = Array.isArray(cluster.citations) ? cluster.citations : (cluster.citation_objects || [])
    if (!Array.isArray(cits) || cits.length === 0) return [cluster]

    const byTier = { supreme: [], district: [], circuit: [], other: [] }
    cits.forEach((c) => {
      const tier = getReporterTier(c?.citation || c?.text || '')
      byTier[tier].push(c)
    })

    const hasSupreme = byTier.supreme.length > 0
    const hasDistrict = byTier.district.length > 0
    const hasCircuit = byTier.circuit.length > 0
    const tierCount = [hasSupreme, hasDistrict, hasCircuit].filter(Boolean).length
    if (tierCount <= 1) return [cluster]

    const wlOther = byTier.other.filter(c => isWlCitation(c?.citation || c?.text || ''))
    const nonWlOther = byTier.other.filter(c => !isWlCitation(c?.citation || c?.text || ''))

    const tierGroups = {
      supreme: [...byTier.supreme],
      district: [...byTier.district],
      circuit: [...byTier.circuit],
    }
    if (hasSupreme) {
      tierGroups.supreme.push(...wlOther, ...nonWlOther)
    } else {
      const dominant = tierGroups.circuit.length >= tierGroups.district.length ? 'circuit' : 'district'
      tierGroups[dominant].push(...wlOther, ...nonWlOther)
    }

    const baseId = cluster.cluster_id || 'cluster'
    const output = []
    ;['supreme', 'circuit', 'district'].forEach((label) => {
      const group = tierGroups[label]
      if (!group.length) return
      output.push({
        ...cluster,
        cluster_id: `${baseId}_clienttier_${label}`,
        citations: group,
        citation_objects: group,
        cluster_size: group.length,
        __clientTierSplit: true,
      })
    })
    return output.length ? output : [cluster]
  }

  // Render-only frontend with defensive normalization:
  // 1) Use backend clusters when present
  // 2) FALLBACK: when backend returns citations but no clusters (e.g. worker path), build one cluster per citation so we show "Cases" instead of "Individual Citations"
  // 3) split mixed federal court tiers if backend payload still mixes them
  // 4) remove exact duplicate cards by normalized citation-set key
  const clusters = computed(() => {
    let base = resultsRef.value?.clusters || []
    const citations = resultsRef.value?.citations || []
    if (!Array.isArray(base)) base = []
    if (base.length === 0 && Array.isArray(citations) && citations.length > 0) {
      // Backend sent citations but no clusters – build one cluster per citation so UI shows "Cases" not "Individual Citations"
      const name = (c) => (c && (c.extracted_case_name || c.canonical_name || c.case_name)) || 'N/A'
      const date = (c) => (c && (c.extracted_date || c.canonical_date)) || ''
      base = citations.map((cit, i) => ({
        cluster_id: `single_${i}_${(cit.citation || cit.text || '').toString().slice(0, 30).replace(/\s+/g, '_')}`,
        cluster_case_name: name(cit),
        submitted_display_name: name(cit),
        verifying_display_name: name(cit),
        submitted_display_date: date(cit),
        verifying_display_date: date(cit),
        citations: [cit],
        citation_objects: [cit],
        cluster_size: 1,
        cluster_members: [cit.citation || cit.text || ''].filter(Boolean),
        verified: cit.verified,
        canonical_url: cit.canonical_url,
      }))
    }
    if (!Array.isArray(base) || base.length === 0) return []

    const expanded = base.flatMap((cluster) => splitMixedFederalTiers(cluster))
    const seen = new Set()
    const deduped = []
    expanded.forEach((cluster) => {
      const key = clusterCitationSetKey(cluster)
      const fallbackKey = `${cluster?.verifying_display_name || ''}|${cluster?.submitted_display_name || ''}|${cluster?.verifying_display_date || ''}`
      const finalKey = key || fallbackKey
      if (!finalKey) {
        deduped.push(cluster)
        return
      }
      if (seen.has(finalKey)) return
      seen.add(finalKey)
      deduped.push(cluster)
    })
    return deduped
  })

  const clusterSections = computed(() => resultsRef.value?.cluster_sections || {})
  // Always use backend sections - no frontend fallback categorization
  const keys = ['unverified', 'case_mismatch', 'date_mismatch', 'verified_by_parallel', 'verified_strict', 'other']
  const normalizeId = (id) => {
    if (id === null || id === undefined) return null
    return String(id)
  }
  const sectionEntryToId = (entry) => {
    if (entry === null || entry === undefined) return null
    if (typeof entry === 'object') return normalizeId(entry.cluster_id ?? entry.id)
    return normalizeId(entry)
  }
  const sectionIds = (key) => {
    const ids = new Set()
    const values = clusterSections.value?.[key] || []
    if (!Array.isArray(values)) return ids
    values.forEach((entry) => {
      const id = sectionEntryToId(entry)
      if (id) ids.add(id)
    })
    return ids
  }
  // Use backend cluster_sections when present; when empty (e.g. fallback clusters), categorize by verification so cards show
  const hasSectionMapping = computed(() => {
    const s = clusterSections.value
    if (!s || typeof s !== 'object') return false
    return keys.some(k => Array.isArray(s[k]) && s[k].length > 0)
  })
  const clustersBySection = (key) => {
    if (!clusters.value?.length) return []
    const ids = sectionIds(key)
    if (ids.size > 0) return clusters.value.filter(c => ids.has(normalizeId(c?.cluster_id)))
    // No backend section mapping (e.g. fallback one-per-citation clusters) – categorize by citation verification so cards render
    const list = clusters.value
    if (key === 'verified_strict') return list.filter(c => (c.citations || c.citation_objects || []).some(cit => isEffectivelyVerified(cit)))
    if (key === 'verified_by_parallel') return list.filter(c => (c.citations || c.citation_objects || []).some(cit => cit?.true_by_parallel && !isEffectivelyVerified(cit)))
    if (key === 'case_mismatch') return list.filter(c => clusterHasNameMismatch(c))
    if (key === 'date_mismatch') return list.filter(c => clusterHasDateMismatch(c))
    // Helper: cluster has a real case URL (CourtListener, etc.), not just Google search
    const clusterHasRealUrl = (cluster) => {
      const cu = (cluster?.canonical_url || cluster?.display_canonical_url || '').toString().trim()
      if (isRealCanonicalUrl(cu)) return true
      const cits = cluster?.citations || cluster?.citation_objects || []
      return (cits || []).some(cit => hasPossibleMatchEvidence(cit))
    }
    // Unverified = no verified, no by_parallel, and (has mismatch OR only has Google search URL)
    if (key === 'unverified') return list.filter(c => {
      const cits = c.citations || c.citation_objects || []
      const anyVerified = cits.some(cit => isEffectivelyVerified(cit) || cit?.true_by_parallel)
      const hasMismatch = clusterHasNameMismatch(c) || clusterHasDateMismatch(c)
      const onlyGoogleUrl = !clusterHasRealUrl(c)
      return !anyVerified && (hasMismatch || onlyGoogleUrl)
    })
    // Other (Possible Matches) = no verified, no by_parallel, no mismatch, AND has real case URL
    // Clusters with only Google search URLs must NOT appear in Possible Matches
    if (key === 'other') return list.filter(c => {
      const cits = c.citations || c.citation_objects || []
      const anyVerified = cits.some(cit => isEffectivelyVerified(cit) || cit?.true_by_parallel)
      return !anyVerified && !clusterHasNameMismatch(c) && !clusterHasDateMismatch(c) && clusterHasRealUrl(c)
    })
    return []
  }

  const verifiedCitations = computed(() => citations.value.filter(c => isEffectivelyVerified(c)) || [])
  const unverifiedCitations = computed(() => citations.value.filter(c => !isEffectivelyVerified(c) && !c.true_by_parallel) || [])
  const verifiedByParallelCitations = computed(() => citations.value.filter(c => !isEffectivelyVerified(c) && c.true_by_parallel && !isNaAndPartial(c)) || [])

  const clustersVerified = computed(() => {
    if (!clusters.value?.length) return []
    return clusters.value.filter(cluster => {
      const cits = cluster.citations || cluster.citation_objects || []
      return Array.isArray(cits) && cits.length > 0 && cits.some(cit => isEffectivelyVerified(cit))
    })
  })

  const clusterHasNameMismatch = (cluster) => {
    const cits = cluster?.citations || cluster?.citation_objects || []
    const citationLevel = Array.isArray(cits) && cits.some(
      c => c && (c.name_mismatch === true || c.name_mismatch === 'true')
    )
    return Boolean(cluster?.has_name_mismatch) || citationLevel
  }

  const clusterHasDateMismatch = (cluster) => {
    const cits = cluster?.citations || cluster?.citation_objects || []
    const citationLevel = Array.isArray(cits) && cits.some((c) => {
      if (!c) return false
      const status = (c.verification_status || '').toString().toLowerCase()
      const mismatch = c.date_mismatch === true || c.date_mismatch === 'true' || status === 'year_mismatch'
      return mismatch && hasDateMismatchEvidence(c)
    })
    return Boolean(cluster?.has_date_mismatch) || citationLevel
  }

  const unverifiedClusters = computed(() => clustersBySection('unverified'))
  const clustersVerifiedByParallel = computed(() => clustersBySection('verified_by_parallel'))
  const clustersVerifiedStrict = computed(() => clustersBySection('verified_strict'))

  const mismatchClusters = computed(() => {
    const map = new Map()
    for (const c of [...clustersBySection('case_mismatch'), ...clustersBySection('date_mismatch')]) {
      if (c && c.cluster_id != null) map.set(c.cluster_id, c)
    }
    return [...map.values()]
  })

  const clustersUnverified = computed(() => clustersBySection('unverified'))
  const clustersCaseMismatch = computed(() => clustersBySection('case_mismatch'))
  const clustersDateMismatch = computed(() => clustersBySection('date_mismatch'))
  const clustersOther = computed(() => clustersBySection('other'))

  const allCitationsVerified = computed(() => citations.value?.length > 0 && unverifiedCitations.value.length === 0)

  return {
    citations,
    clusters,
    verifiedCitations,
    unverifiedCitations,
    verifiedByParallelCitations,
    clustersVerified,
    unverifiedClusters,
    clustersVerifiedByParallel,
    clustersVerifiedStrict,
    mismatchClusters,
    clustersUnverified,
    clustersCaseMismatch,
    clustersDateMismatch,
    clustersOther,
    allCitationsVerified,
    isEffectivelyVerified,
    isNaAndPartial,
    hasCanonicalUrl,
    getDisplayCaseName,
    clusterSections,
    clustersBySection,
  }
}
