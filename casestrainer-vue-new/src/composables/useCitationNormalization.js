// src/composables/useCitationNormalization.js

export function useCitationNormalization() {
  const normalizeCitation = (citation) => {
    // Prefer backend-provided score/color when present
    let score = typeof citation.citation_score === 'number' ? citation.citation_score : null;
    let scoreColor = citation.score_color || null;
    if (score === null) {
      score = 0;
      if (citation.canonical_name && citation.canonical_name !== 'N/A') score += 2;
      if (citation.extracted_case_name && citation.extracted_case_name !== 'N/A' &&
          citation.canonical_name && citation.canonical_name !== 'N/A') {
        const canonicalWords = citation.canonical_name.toLowerCase().split(/\s+/).filter(w => w.length > 2);
        const extractedWords = citation.extracted_case_name.toLowerCase().split(/\s+/).filter(w => w.length > 2);
        const commonWords = canonicalWords.filter(word => extractedWords.includes(word));
        const similarity = commonWords.length / Math.max(canonicalWords.length, extractedWords.length);
        if (similarity >= 0.5) score += 1;
      }
      if (citation.canonical_date && citation.canonical_date !== 'N/A') score += 1;
      if ((citation.url || citation.canonical_url) && (citation.url || citation.canonical_url || '').trim() !== '') score += 1;
    }
    if (!scoreColor) {
      scoreColor = score >= 4 ? 'text-success' : (score >= 2 ? 'text-warning' : 'text-danger');
    }
    return {
      score: typeof score === 'number' ? score : 0,
      scoreColor: scoreColor || 'text-muted',
      normalized: {
        canonical_name: citation.canonical_name || 'N/A',
        extracted_case_name: citation.extracted_case_name || 'N/A',
        canonical_date: citation.canonical_date || 'N/A',
        extracted_date: citation.extracted_date || 'N/A',
        url: citation.url || citation.canonical_url || '',
        verified: citation.verified || false
      }
    };
  };

  const normalizeCitations = (citations) => {
    if (!Array.isArray(citations)) {
      return [];
    }
    
    return citations.map(citation => {
      const normalized = normalizeCitation(citation);
      return {
        ...citation,
        // Don't overwrite original canonical data - only add score and color
        score: normalized.score,
        scoreColor: normalized.scoreColor
      };
    });
  };

  const calculateCitationScore = (citation) => {
    return normalizeCitation(citation).score;
  };
  
  const calculateSimilarity = (citation) => {
    if (typeof citation.name_similarity === 'number') return citation.name_similarity;
    if (citation.canonical_name && citation.canonical_name !== 'N/A') return 1.0;
    if (citation.extracted_case_name && citation.extracted_case_name !== 'N/A' &&
        citation.canonical_name && citation.canonical_name !== 'N/A') {
      const canonicalWords = citation.canonical_name.toLowerCase().split(/\s+/).filter(w => w.length > 2);
      const extractedWords = citation.extracted_case_name.toLowerCase().split(/\s+/).filter(w => w.length > 2);
      const commonWords = canonicalWords.filter(word => extractedWords.includes(word));
      return commonWords.length / Math.max(canonicalWords.length, extractedWords.length);
    }
    return 0.0;
  };
  
  return {
    normalizeCitation,
    normalizeCitations,
    calculateCitationScore,
    calculateSimilarity
  };
} 