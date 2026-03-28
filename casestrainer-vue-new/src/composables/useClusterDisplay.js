/**
 * Display helpers for clusters and citations (names, dates, URLs, status, formatting).
 * Used by CitationResults and ClusterCard.
 */

/**
 * Extract base reporter citation (e.g. "422 U.S. 490") from full citation text.
 */
export function extractBaseReporterCitation(text) {
  if (!text || typeof text !== 'string') return null
  const specificPatterns = [
    /(\d+)\s+(Wn\.\s*App\.\s*[23]d)\s+(\d+)/i,
    /(\d+)\s+(Wash\.\s*App\.\s*[23]d)\s+(\d+)/i,
    /(\d+)\s+(Wn\.\s*[23]d)\s+(\d+)/i,
    /(\d+)\s+(Wash\.\s*[23]d)\s+(\d+)/i,
    /(\d+)\s+(F\.\s*Supp\.\s*[23]d)\s+(\d+)/i,
    /(\d+)\s+(F\.\s*Supp\.)\s+(\d+)/i,
    /(\d+)\s+(F\.\s*R\.\s*D\.)\s+(\d+)/i,
    /(\d+)\s+(L\.\s*Ed\.\s*2d)\s+(\d+)/i,
    /(\d+)\s+(S\.\s*Ct\.)\s+(\d+)/i,
    /(\d+)\s+(F\.[234](?:th|d))\s+(\d+)/i,
    /(\d+)\s+(A\.[23]d)\s+(\d+)/i,
    /(\d+)\s+(So\.\s*[23]d)\s+(\d+)/i,
    /(\d+)\s+(N\.\s*[EW]\.\s*[23]d)\s+(\d+)/i,
    /(\d+)\s+(S\.\s*[EW]\.\s*[23]d)\s+(\d+)/i,
    /(\d+)\s+(P\.[23]d)\s+(\d+)/i,
    /(\d+)\s+(Cal\.\s*(?:App\.\s*)?[234](?:th|d))\s+(\d+)/i,
    /(\d+)\s+(Ohio\s+App\.\s*[23]d)\s+(\d+)/i,
  ]
  for (const pat of specificPatterns) {
    const m = text.match(pat)
    if (m) return `${m[1]} ${m[2].trim()} ${m[3]}`
  }
  const wlMatch = text.match(/(\d{4})\s+(WL|U\.?\s*S\.?\s*LEXIS|LEXIS)\s+(\d+)/i)
  if (wlMatch) return `${wlMatch[1]} ${wlMatch[2].trim()} ${wlMatch[3]}`
  const match = text.match(/(\d+)\s+([A-Za-z][A-Za-z.\s]+?(?:\d+[a-z]{0,2})?)\s+(\d+)/)
  if (match) return `${match[1]} ${match[2].trim()} ${match[3]}`
  return null
}

export function getRepresentativeCitation(cluster) {
  if (!cluster) return null
  const cits = cluster.citations || cluster.citation_objects || []
  if (!Array.isArray(cits) || cits.length === 0) return null
  const indices = cluster.mismatch_indices || []
  if (Array.isArray(indices) && indices.length > 0) {
    const idx = indices[0]
    if (typeof idx === 'number' && idx >= 0 && idx < cits.length) return cits[idx] || null
  }
  const withUrl = cits.find(c => c && (c.canonical_url || c.url) && (c.verified === true || c.verified === 'true' || c.is_verified === true))
  if (withUrl) return withUrl
  const firstVerified = cits.find(c => c && (c.verified === true || c.verified === 'true'))
  if (firstVerified) return firstVerified
  return cits[0] || null
}

export function getClusterVerifyingUrl(cluster) {
  // Render-only: trust backend-prepared display URL.
  return cluster?.display_canonical_url || cluster?.canonical_url || null
}

export function getClusterVerifyingName(cluster) {
  // Render-only: trust backend-prepared display name.
  return cluster?.verifying_display_name || 'Not Found'
}

export function getClusterVerifyingDate(cluster) {
  // Render-only: trust backend-prepared display date.
  return cluster?.verifying_display_date || 'Not Found'
}

export function getClusterFoundCanonicalDate(cluster) {
  // Returns the canonical date found from CourtListener, even when not verified
  // Used to show "Different date" information (e.g., 1831 vs 2023)
  return cluster?.found_canonical_date || null
}

export function getClusterSubmittedName(cluster) {
  return cluster?.submitted_display_name || cluster?.extracted_case_name || 'N/A'
}

export function getClusterSubmittedDate(cluster) {
  return cluster?.submitted_display_date || cluster?.extracted_date || 'N/A'
}

export function hasNameMismatch(cluster) {
  return Boolean(cluster?.has_name_mismatch)
}

export function hasDateMismatch(cluster) {
  return Boolean(cluster?.has_date_mismatch)
}

/**
 * Stable key for collapsing duplicate case-card lines (e.g. 171 Wash. 2d 486 vs 171 Wn.2d 486).
 * Aligns with backend citation_core_key Wash./Wn. normalization so UI matches deduped API output.
 */
export function citationMergeKeyForDisplay(displayStr) {
  if (!displayStr || typeof displayStr !== 'string') return ''
  const base = extractBaseReporterCitation(displayStr.trim()) || displayStr.trim()
  if (!base) return ''
  let s = base
  s = s.replace(/\bWash\.\s*App\.\s*/gi, 'Wn.App. ')
  s = s.replace(/\bWash\.\s*/gi, 'Wn.')
  s = s.replace(/\bWn\.\s*App\.\s*/gi, 'Wn.App. ')
  s = s.replace(/\bWn\.\s*(\d)/gi, 'Wn.$1')
  return s.replace(/\s+/g, ' ').trim().toLowerCase()
}

export function getClusterCitations(cluster) {
  const displayCits = cluster?.display_citations
  const list =
    Array.isArray(displayCits) && displayCits.length > 0
      ? displayCits
      : cluster?.citations || cluster?.citation_objects || []
  if (!Array.isArray(list)) return []
  const seen = new Set()
  const deduped = []
  for (const cit of list) {
    const display = formatCitationText(cit)
    const key = citationMergeKeyForDisplay(display)
    if (!key || seen.has(key)) continue
    seen.add(key)
    deduped.push(cit)
  }
  return deduped
}

export function getCitationExtractedLabel(citation, cluster) {
  const extracted = (citation?.extracted_case_name || '').toString().trim()
  if (!extracted || extracted === 'N/A') return null
  if (!cluster?.cross_document_merge) return null
  const clusterName = (cluster?.submitted_display_name || '').toString().trim()
  const cits = cluster?.citations || cluster?.citation_objects || []
  const multiCitation = Array.isArray(cits) && cits.length > 1
  if (multiCitation || (clusterName && extracted !== clusterName)) return extracted
  return null
}

function isClusterGoogleSearchUrl(cluster) {
  const u = (cluster?.display_canonical_url || cluster?.canonical_url || '').toString().trim()
  return u.startsWith('https://www.google.com/search?') || u.startsWith('http://www.google.com/search?')
}

/**
 * Status class/text depend on isEffectivelyVerified and related helpers - pass them in.
 * When cluster is provided and cluster is verified, show Verified for every citation (e.g. WL citations with proprietary message).
 * USER RULE: When cluster has only Google search URL, all citations are unverified (no "Verified by Parallel", "Proprietary format", etc.).
 */
export function getCitationStatusClass(citation, clusterOrVoid, isEffectivelyVerifiedFn, isNaAndPartialFn) {
  const cluster = clusterOrVoid && typeof clusterOrVoid === 'object' ? clusterOrVoid : null
  if (cluster && isClusterGoogleSearchUrl(cluster)) return 'status-unverified'
  const citUrl = (citation?.canonical_url || citation?.url || '').toString().trim()
  if (citUrl && (citUrl.startsWith('https://www.google.com/search?') || citUrl.startsWith('http://www.google.com/search?'))) return 'status-unverified'
  if (cluster && (cluster.verified === true || cluster.verified === 'true')) return 'status-verified'
  const hasPossibleEvidence = hasPossibleMatchEvidence(citation)
  if (isNaAndPartialFn(citation)) return 'status-unverified'
  if (isEffectivelyVerifiedFn(citation)) return 'status-verified'
  if (citation?.true_by_parallel === true || citation?.true_by_parallel === 'true') return 'status-parallel'
  if ((citation?.possible_match === true || citation?.possible_match === 'true') && hasPossibleEvidence) return 'status-possible-match'
  return 'status-unverified'
}

export function getCitationStatusText(citation, clusterOrVoid, isEffectivelyVerifiedFn, isNaAndPartialFn) {
  const cluster = clusterOrVoid && typeof clusterOrVoid === 'object' ? clusterOrVoid : null
  if (cluster && isClusterGoogleSearchUrl(cluster)) return 'Unverified'
  // Citation's own URL is Google search = unverified (never show Verified by Parallel)
  const citUrl = (citation?.canonical_url || citation?.url || '').toString().trim()
  if (citUrl && (citUrl.startsWith('https://www.google.com/search?') || citUrl.startsWith('http://www.google.com/search?'))) return 'Unverified'
  if (cluster && (cluster.verified === true || cluster.verified === 'true')) return 'Verified'
  const hasPossibleEvidence = hasPossibleMatchEvidence(citation)
  if (isNaAndPartialFn(citation)) return 'Unverified'
  if (isEffectivelyVerifiedFn(citation)) return 'Verified'
  if (citation?.true_by_parallel === true || citation?.true_by_parallel === 'true') {
    if (citation?.metadata?.parallel_not_in_document === true || citation?.metadata?.parallel_not_in_document === 'true') {
      return 'Verified by Parallel (Not in document)'
    }
    return 'Verified by Parallel'
  }
  if ((citation?.possible_match === true || citation?.possible_match === 'true') && hasPossibleEvidence) return 'Possible Match'
  if (citation?.error) return citation.error
  return 'Unverified'
}

function isRealCanonicalUrl(urlStr) {
  const u = (urlStr || '').toString().trim()
  if (!u || u.toUpperCase() === 'N/A') return false
  if (u.startsWith('https://www.google.com/search?') || u.startsWith('http://www.google.com/search?')) return false
  return true
}

function hasPossibleMatchEvidence(citation) {
  if (!citation || typeof citation !== 'object') return false
  const canonicalUrl = (citation.canonical_url || citation.url || '').toString().trim()
  const metadata = citation.metadata && typeof citation.metadata === 'object' ? citation.metadata : {}
  const pmUrl = (metadata.possible_match_url || '').toString().trim()
  // Only show "Possible Match" when there is a real case URL (CourtListener, etc.); Google search URLs do NOT qualify.
  return [canonicalUrl, pmUrl].some(v => isRealCanonicalUrl(v))
}

export function formatCitationText(citation) {
  if (citation && citation.display_base_citation) return citation.display_base_citation
  let rawText = null
  if (typeof citation === 'string') rawText = citation
  else if (citation?.text) rawText = citation.text
  else if (citation?.citation && typeof citation.citation === 'string') rawText = citation.citation
  else if (citation?.citation && typeof citation.citation === 'object') {
    const groups = citation.citation.groups || {}
    const volume = groups.volume || ''
    const reporter = groups.reporter || ''
    const page = groups.page || ''
    if (volume && reporter && page) return `${volume} ${reporter} ${page}`
    if (reporter && page) return `${reporter} ${page}`
    rawText = citation.citation.toString()
  }
  if (!rawText) return citation?.citation || 'N/A'
  const base = extractBaseReporterCitation(rawText)
  return base || rawText
}
