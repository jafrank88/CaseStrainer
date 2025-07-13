// src/composables/useCitationNormalization.js

export function useCitationNormalization() {
  const normalizeCitation = (citation) => {
    let score = 0;
    let scoreColor = 'text-muted';
    
    // Check if we have canonical name
    if (citation.canonical_name && citation.canonical_name !== 'N/A') {
      score += 2;
    }
    
    // Check if extracted and canonical names match
    if (citation.extracted_case_name && citation.extracted_case_name !== 'N/A' &&
        citation.canonical_name && citation.canonical_name !== 'N/A') {
      const canonicalWords = citation.canonical_name.toLowerCase().split(/\s+/).filter(w => w.length > 2);
      const extractedWords = citation.extracted_case_name.toLowerCase().split(/\s+/).filter(w => w.length > 2);
      
      const commonWords = canonicalWords.filter(word => extractedWords.includes(word));
      const similarity = commonWords.length / Math.max(canonicalWords.length, extractedWords.length);
      
      if (similarity >= 0.5) {
        score += 1;
      }
    }
    
    // Check if we have canonical date
    if (citation.canonical_date && citation.canonical_date !== 'N/A') {
      score += 1;
    }
    
    // Check if we have URL
    if (citation.url && citation.url !== '') {
      score += 1;
    }
    
    // Determine color based on score
    if (score >= 4) {
      scoreColor = 'text-success';
    } else if (score >= 2) {
      scoreColor = 'text-warning';
    } else {
      scoreColor = 'text-danger';
    }
    
    return {
      score,
      scoreColor,
      normalized: {
        canonical_name: citation.canonical_name || 'N/A',
        extracted_case_name: citation.extracted_case_name || 'N/A',
        canonical_date: citation.canonical_date || 'N/A',
        extracted_date: citation.extracted_date || 'N/A',
        url: citation.url || '',
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
    if (citation.canonical_name && citation.canonical_name !== 'N/A') {
      return 1.0;
    }
    
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