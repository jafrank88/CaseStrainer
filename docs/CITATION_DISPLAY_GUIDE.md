# CaseStrainer Citation Display Guide

## Overview

CaseStrainer already extracts and displays case names and dates from citations. The system provides both **extracted data** (from user documents) and **canonical data** (from authoritative sources) for comparison.

## Data Flow

### 1. Backend Processing
- **Citation Extraction**: The system extracts citations from uploaded documents, pasted text, or URLs
- **Case Name Extraction**: Uses multiple methods to extract case names from the document context
- **Date Extraction**: Extracts dates from citations and surrounding text
- **Multi-Source Verification**: Verifies citations against multiple legal databases (CourtListener, Justia, Google Scholar, etc.)

### 2. API Response Structure
The backend returns citation data with the following key fields:

```json
{
  "citations": [
    {
      "citation": "Brown v. Board of Education, 347 U.S. 483 (1954)",
      "verified": true,
      "case_name": "Brown v. Board of Education",           // Canonical case name from API
      "case_name_extracted": "Brown v. Board of Education", // Extracted from document
      "canonical_case_name": "Brown v. Board of Education", // Canonical from authoritative source
      "extracted_date": "1954",                             // Date extracted from user's document
      "date_filed": "1954-05-17",                           // Canonical date from authoritative source
      "court": "Supreme Court of the United States",
      "docket_number": "1",
      "confidence": 0.95,
      "source": "Multiple Sources",
      "url": "https://www.courtlistener.com/opinion/...",
      "extraction_confidence": 0.9,
      "extraction_method": "pattern_matching",
      "verified_in_text": true,
      "similarity_score": 0.95,
      "verification_details": {
        "courtlistener": {"verified": true, "url": "..."},
        "justia": {"verified": true, "url": "..."},
        "google_scholar": {"verified": true}
      }
    }
  ]
}
```

### 3. Frontend Display
The Vue component `CitationResults.vue` displays this data in organized sections:

#### Case Information Section
- **Canonical Case Name**: Official case name from authoritative sources
- **Extracted Case Name**: Case name extracted from the user's document
- **Name Similarity**: Percentage match between extracted and canonical names
- **Name Mismatch Warning**: Alerts when names differ significantly

#### Decision Information Section
- **Extracted Date**: Date extracted from the user's document
- **Canonical Date**: Official date from authoritative sources
- **Date Match**: Shows whether extracted and canonical dates match

#### Court Information Section
- **Court**: Court that decided the case
- **Docket**: Docket number

#### Additional Information
- **Parallel Citations**: Alternative citation formats
- **Verification Sources**: Which databases confirmed the citation
- **Confidence Scores**: How confident the system is in the verification

## Helper Functions

The Vue component uses these helper functions to access citation data:

```javascript
// Case name functions
getCaseName(citation)           // Gets canonical case name
getExtractedCaseName(citation)  // Gets extracted case name
getCaseNameSimilarity(citation) // Gets similarity score
getCaseNameMismatch(citation)   // Checks for name mismatches

// Date functions
getDateFiled(citation)          // Gets canonical date
getExtractedDate(citation)      // Gets extracted date
formatDate(dateString)          // Formats dates for display

// Court functions
getCourt(citation)              // Gets court information
getDocket(citation)             // Gets docket number

// Other functions
getCitationUrl(citation)        // Gets citation URL
getSource(citation)             // Gets verification source
getParallelCitations(citation)  // Gets parallel citations
```

## Troubleshooting

If you're not seeing case names and dates in the frontend:

### 1. Check Backend Extraction
Verify that the backend is properly extracting case names and dates:

```python
# Check the citation processor
from src.citation_processor import CitationProcessor
processor = CitationProcessor()
citations = processor.extract_citations(text, extract_case_names=True)

# Check the enhanced verifier
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
verifier = EnhancedMultiSourceVerifier()
result = verifier.verify_citation(citation_text, extracted_case_name=extracted_case_name)
```

### 2. Check API Response
Verify that the API response includes the expected fields:

```javascript
// In browser console, check the API response
fetch('/api/analyze', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({text: 'Brown v. Board of Education, 347 U.S. 483 (1954)'})
})
.then(response => response.json())
.then(data => {
  console.log('API Response:', data);
  console.log('First citation:', data.citations[0]);
});
```

### 3. Check Vue Component
Verify that the Vue component is receiving and processing the data:

```javascript
// In browser console, check the component data
// Navigate to the citation results page and check:
console.log('Citation results:', this.results);
console.log('First citation:', this.results.citations[0]);
```

### 4. Check for JavaScript Errors
Open browser developer tools and check the console for any JavaScript errors that might prevent the data from displaying.

### 5. Verify Data Structure
Ensure the citation objects have the expected structure:

```javascript
// Expected citation object structure
const expectedStructure = {
  citation: "Brown v. Board of Education, 347 U.S. 483 (1954)",
  case_name: "Brown v. Board of Education",
  case_name_extracted: "Brown v. Board of Education",
  canonical_case_name: "Brown v. Board of Education",
  extracted_date: "1954",
  date_filed: "1954-05-17",
  court: "Supreme Court of the United States",
  docket_number: "1",
  verified: true,
  confidence: 0.95
};
```

## Common Issues and Solutions

### Issue: Case names not displaying
**Possible causes:**
- Backend not extracting case names properly
- API response missing `case_name` or `case_name_extracted` fields
- Vue component not receiving the data

**Solutions:**
1. Check backend logs for extraction errors
2. Verify API response structure
3. Check Vue component helper functions

### Issue: Dates not displaying
**Possible causes:**
- Date extraction failing in backend
- Date format issues
- Missing `extracted_date` or `date_filed` fields

**Solutions:**
1. Check date extraction logic in backend
2. Verify date formats are consistent
3. Check Vue date formatting function

### Issue: Data showing as "N/A"
**Possible causes:**
- Fields are null or undefined
- Helper functions not finding the data
- Data structure mismatch

**Solutions:**
1. Check if fields exist in API response
2. Verify helper function logic
3. Ensure consistent data structure

## Testing the System

Run the test script to verify the system is working:

```bash
python test_citation_display.py
```

This will demonstrate:
- The expected data structure
- How helper functions work
- What should be displayed in the frontend

## Enhancement Opportunities

While the system already works, here are potential enhancements:

1. **Better Date Parsing**: Improve date extraction from various formats
2. **Enhanced Case Name Matching**: Better fuzzy matching for case names
3. **Visual Indicators**: Add icons or colors to highlight matches/mismatches
4. **Export Functionality**: Allow users to export citation data with case names and dates
5. **Batch Processing**: Process multiple documents and compare case names across documents

## Conclusion

The CaseStrainer system already extracts and displays case names and dates effectively. The data flows from backend extraction through API responses to frontend display, providing users with both extracted and canonical information for comparison.

If you're experiencing issues with the display, follow the troubleshooting steps above to identify and resolve the problem. 