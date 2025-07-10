// src/composables/useCitationNormalization.js

export function useCitationNormalization() {
  // Normalize citations for frontend display
  const normalizeCitations = (citations) => {
    return (citations || []).map(citation => {
      // Convert citation array to string
      let citationText = citation.citation;
      if (Array.isArray(citationText)) {
        citationText = citationText.join('; ');
      }

      // Convert verified to boolean
      let verified = false;
      if (typeof citation.verified === 'string') {
        verified = citation.verified === 'true' || citation.verified === 'true_by_parallel';
      } else {
        verified = !!citation.verified;
      }

      // Calculate citation score (0-4)
      let score = 0;
      if (citation.case_name && citation.case_name !== 'N/A') {
        score += 2;
      }
      if (citation.extracted_case_name && citation.extracted_case_name !== 'N/A' && 
          citation.case_name && citation.case_name !== 'N/A') {
        const canonicalWords = citation.case_name.toLowerCase().split(/\s+/).filter(w => w.length > 2);
        const extractedWords = citation.extracted_case_name.toLowerCase().split(/\s+/).filter(w => w.length > 2);
        const commonWords = canonicalWords.filter(word => extractedWords.includes(word));
        const similarity = commonWords.length / Math.max(canonicalWords.length, extractedWords.length);
        if (similarity >= 0.5) {
          score += 1;
        }
      }
      if (citation.extracted_date && citation.canonical_date) {
        const extractedYear = citation.extracted_date.toString().substring(0, 4);
        const canonicalYear = citation.canonical_date.toString().substring(0, 4);
        if (extractedYear === canonicalYear && extractedYear.length === 4) {
          score += 1;
        }
      }
      let scoreColor = 'red';
      if (score === 4) scoreColor = 'green';
      else if (score === 3) scoreColor = 'green';
      else if (score === 2) scoreColor = 'yellow';
      else if (score === 1) scoreColor = 'orange';

      const normalizedCitation = {
        ...citation,
        citation: citationText,
        verified: verified,
        valid: verified,
        score: score,
        scoreColor: scoreColor,
        case_name: citation.case_name || 'N/A',
        extracted_case_name: citation.extracted_case_name || 'N/A',
        canonical_date: citation.canonical_date || null,
        extracted_date: citation.extracted_date || null,
        metadata: {
          case_name: citation.case_name,
          canonical_date: citation.canonical_date,
          court: citation.court,
          confidence: citation.confidence,
          method: citation.method,
          pattern: citation.pattern
        },
        details: {
          case_name: citation.case_name,
          canonical_date: citation.canonical_date,
          court: citation.court,
          confidence: citation.confidence,
          method: citation.method,
          pattern: citation.pattern
        }
      };
      return normalizedCitation;
    });
  };

  // Optionally, extract scoring logic if needed separately
  const calculateCitationScore = (citation) => {
    let score = 0;
    if (citation.case_name && citation.case_name !== 'N/A') {
      score += 2;
    }
    if (citation.extracted_case_name && citation.extracted_case_name !== 'N/A' && 
        citation.case_name && citation.case_name !== 'N/A') {
      const canonicalWords = citation.case_name.toLowerCase().split(/\s+/).filter(w => w.length > 2);
      const extractedWords = citation.extracted_case_name.toLowerCase().split(/\s+/).filter(w => w.length > 2);
      const commonWords = canonicalWords.filter(word => extractedWords.includes(word));
      const similarity = commonWords.length / Math.max(canonicalWords.length, extractedWords.length);
      if (similarity >= 0.5) {
        score += 1;
      }
    }
    if (citation.extracted_date && citation.canonical_date) {
      const extractedYear = citation.extracted_date.toString().substring(0, 4);
      const canonicalYear = citation.canonical_date.toString().substring(0, 4);
      if (extractedYear === canonicalYear && extractedYear.length === 4) {
        score += 1;
      }
    }
    return score;
  };

  return { normalizeCitations, calculateCitationScore };
} 