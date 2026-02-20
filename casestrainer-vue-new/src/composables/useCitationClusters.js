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
  // 1) split mixed federal court tiers if backend payload still mixes them
  // 2) remove exact duplicate cards by normalized citation-set key
  const clusters = computed(() => {
    const base = resultsRef.value?.clusters || []
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
  const hasUsableSectionData = computed(() => {
    const base = clusters.value || []
    if (!base.length) return false
    if (base.some(c => c?.__clientTierSplit)) return false
    const clusterIds = new Set(base.map(c => normalizeId(c?.cluster_id)).filter(Boolean))
    if (!clusterIds.size) return false
    return keys.some((key) => {
      const ids = sectionIds(key)
      if (!ids.size) return false
      return [...ids].some(id => clusterIds.has(id))
    })
  })
  const clustersBySection = (key) => {
    if (!clusters.value?.length) return []
    if (!hasUsableSectionData.value) return []
    const ids = sectionIds(key)
    if (!ids.size) return []
    return clusters.value.filter(c => ids.has(normalizeId(c?.cluster_id)))
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

  const unverifiedClusters = computed(() => {
    if (hasUsableSectionData.value) return clustersBySection('unverified')
    if (!clusters.value?.length) return []
    return clusters.value.filter(cluster => {
      const cits = cluster.citations || cluster.citation_objects || []
      if (!Array.isArray(cits) || cits.length === 0) return false
      if (cits.some(cit => isEffectivelyVerified(cit))) return false
      return cits.some(cit => {
        if (!cit) return false
        const trueByParallel = cit.true_by_parallel === true || cit.true_by_parallel === 'true'
        const possibleMatch = cit.possible_match === true || cit.possible_match === 'true'
        return !isEffectivelyVerified(cit) && !trueByParallel && !possibleMatch
      })
    })
  })

  const clustersVerifiedByParallel = computed(() => {
    if (hasUsableSectionData.value) return clustersBySection('verified_by_parallel')
    if (!clusters.value?.length) return []
    return clusters.value.filter(cluster => {
      const cits = cluster.citations || cluster.citation_objects || []
      if (!Array.isArray(cits) || cits.length === 0) return false
      const hasVbp = cits.some(c => c && (c.true_by_parallel === true || c.true_by_parallel === 'true'))
      const hasVerified = cits.some(c => isEffectivelyVerified(c))
      return hasVbp && !hasVerified
    })
  })

  const clustersVerifiedStrict = computed(() => {
    if (hasUsableSectionData.value) return clustersBySection('verified_strict')
    if (!clusters.value?.length) return []
    return clusters.value.filter(cluster => {
      const cits = cluster.citations || cluster.citation_objects || []
      if (!Array.isArray(cits) || cits.length === 0) return false
      const allVerified = cits.every(c => isEffectivelyVerifiedWithCluster(c, cluster))
      const noneParallel = !cits.some(c => c && (c.true_by_parallel === true || c.true_by_parallel === 'true'))
      const noNameMismatch = !Boolean(cluster?.has_name_mismatch)
      const noDateMismatch = !Boolean(cluster?.has_date_mismatch)
      return allVerified && noneParallel && noNameMismatch && noDateMismatch
    })
  })

  const mismatchClusters = computed(() => {
    const map = new Map()
    for (const c of [...clustersBySection('case_mismatch'), ...clustersBySection('date_mismatch')]) {
      if (c && c.cluster_id != null) map.set(c.cluster_id, c)
    }
    return [...map.values()]
  })

  const clustersUnverified = computed(() => {
    if (hasUsableSectionData.value) return clustersBySection('unverified')
    return unverifiedClusters.value || []
  })
  const clustersCaseMismatch = computed(() => {
    if (hasUsableSectionData.value) return clustersBySection('case_mismatch')
    const base = clusters.value || []
    if (!base.length) return []
    const unvIds = new Set((clustersUnverified.value || []).map(c => c.cluster_id))
    return base.filter(c => !unvIds.has(c.cluster_id) && Boolean(c?.has_name_mismatch))
  })
  const clustersDateMismatch = computed(() => {
    if (hasUsableSectionData.value) return clustersBySection('date_mismatch')
    const base = clusters.value || []
    if (!base.length) return []
    const unvIds = new Set((clustersUnverified.value || []).map(c => c.cluster_id))
    const caseIds = new Set((clustersCaseMismatch.value || []).map(c => c.cluster_id))
    return base.filter(c => !unvIds.has(c.cluster_id) && !caseIds.has(c.cluster_id) && Boolean(c?.has_date_mismatch))
  })
  const clustersOther = computed(() => {
    if (hasUsableSectionData.value) return clustersBySection('other')
    const base = clusters.value || []
    if (!base.length) return []
    const unvIds = new Set((clustersUnverified.value || []).map(c => c.cluster_id))
    const caseIds = new Set((clustersCaseMismatch.value || []).map(c => c.cluster_id))
    const dateIds = new Set((clustersDateMismatch.value || []).map(c => c.cluster_id))
    const vbpIds = new Set((clustersVerifiedByParallel.value || []).map(c => c.cluster_id))
    const verifiedStrictIds = new Set((clustersVerifiedStrict.value || []).map(c => c.cluster_id))
    return base.filter(c => !unvIds.has(c.cluster_id) && !caseIds.has(c.cluster_id) && !dateIds.has(c.cluster_id) && !vbpIds.has(c.cluster_id) && !verifiedStrictIds.has(c.cluster_id))
  })

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
  }
}
