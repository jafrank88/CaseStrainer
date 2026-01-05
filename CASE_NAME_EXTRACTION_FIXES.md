# Case Name Extraction Fixes - Summary

## Problem Statement

The case name extraction logic was picking up incorrect or truncated case names from document headers and captions, leading to contamination in citation extraction.

## Root Causes Identified

1. **Document headers** like "CARTER, Respondent, v. MARY E. JONES, Appellant" were not being properly filtered
2. **Sentence fragments** like "This was later cited in Smith v. Johnson" were being extracted instead of just "Smith v. Johnson"
3. **Role words** (Respondent, Appellant, etc.) in case names were not being cleaned properly
4. **Context window** was too small (40 chars) to capture full case names

## Fixes Implemented

### 1. Enhanced Document Primary Case Name Detection (`unified_clustering_master.py`)

- **Strategy 2 & 3**: Added robust cleaning of role words from both ends of party names
- Handles patterns like "CARTER, Respondent, v. MARY E. JONES, Appellant" → "CARTER v. MARY E. JONES"
- Cleans up double commas and extra spaces

### 2. Improved Header Contamination Filtering (`unified_case_extraction_master.py`)

- **Lines 1185-1186**: Added pattern to detect case caption headers with role words
- **Lines 1196-1216**: Enhanced logic to filter case captions while preserving legitimate case discussion
- Distinguishes between headers ("CARTER, Respondent, v. MARY E. JONES, Appellant") and discussion ("In Smith v. Jones, the court held...")

### 3. Enhanced Case Name Cleaning

- **Lines 2989-2999**: Added role word removal from extracted case names
- Removes patterns like ", Respondent" and "Appellant, " from case names
- Cleans up resulting punctuation

### 4. Improved Sentence-Level Extraction

- **Lines 1735-1754**: Added logic to extract case names from longer sentences
- Detects signal words (see, cited, established, etc.) to identify sentence contamination
- Uses precise regex pattern to extract just the case name: `r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"`
- Example: "As established in Davis v. Wilson" → "Davis v. Wilson"

### 5. Increased Context Window

- **Line 1448**: Increased default context window from 40 to 100 characters
- Ensures enough context to capture complete case names

### 6. Refined Contamination Indicators

- **Lines 1949-1963**: Made contamination indicators more specific
- Removed overly broad terms like "established" that caused false positives
- Now only rejects clear contamination patterns like "held that", "the court held that", etc.

## Test Results

All test cases now pass:

- ✅ Simple case: "Smith v. Johnson" from "The court ruled in Smith v. Johnson, 123 F.3d 456"
- ✅ Signal words: "Davis v. Wilson" from "As established in Davis v. Wilson, 456 U.S. 789"
- ✅ Header contamination: Properly filters "CARTER, Respondent, v. MARY E. JONES, Appellant"
- ✅ Role word cleaning: Removes "Respondent" and "Appellant" from case names

## Impact

1. **More accurate citation extraction** - No longer picks up document headers as case names
2. **Cleaner case names** - Role words and signal phrases properly removed
3. **Better contamination detection** - Distinguishes between headers and legitimate case discussion
4. **Improved clustering** - Correct case names lead to better citation clustering

## Files Modified

- `src/unified_clustering_master.py`: Enhanced primary case name extraction
- `src/unified_case_extraction_master.py`: Multiple improvements to extraction and filtering logic

## Testing

Created comprehensive test suites:

- `test_case_name_extraction_fixes.py`: Full pipeline testing
- `test_simple_case_extraction.py`: Focused testing of specific scenarios

All tests pass successfully, confirming the fixes work as expected.
