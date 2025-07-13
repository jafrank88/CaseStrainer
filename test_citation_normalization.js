// Test script to verify citation normalization works
import { useCitationNormalization } from './casestrainer-vue-new/src/composables/useCitationNormalization.js';

// Test the normalization function
const { normalizeCitations, calculateCitationScore } = useCitationNormalization();

// Test data similar to what the backend returns
const testCitations = [
  {
    citation: "200 Wn.2d 72, 73, 514 P.3d 643 (2022)",
    canonical_name: "Convoyant, LLC v. DeepThink, LLC",
    extracted_case_name: "Convoyant, LLC v. DeepThink, LLC",
    canonical_date: "2022",
    extracted_date: "2022",
    url: "https://example.com/case1",
    verified: true
  },
  {
    citation: "171 Wn.2d 486, 493, 256 P.3d 321 (2011)",
    canonical_name: "Carlson v. Glob. Client Sols., LLC",
    extracted_case_name: "Carlson v. Glob. Client Sols., LLC",
    canonical_date: "2011",
    extracted_date: "2011",
    url: "https://example.com/case2",
    verified: true
  }
];

console.log("Testing normalizeCitations function...");
console.log("Input citations:", testCitations);

try {
  const normalized = normalizeCitations(testCitations);
  console.log("✓ normalizeCitations function works!");
  console.log("Normalized citations:", normalized);
  
  // Test individual citation scoring
  const score = calculateCitationScore(testCitations[0]);
  console.log("✓ calculateCitationScore function works!");
  console.log("Score for first citation:", score);
  
} catch (error) {
  console.error("✗ Error in normalizeCitations:", error);
} 