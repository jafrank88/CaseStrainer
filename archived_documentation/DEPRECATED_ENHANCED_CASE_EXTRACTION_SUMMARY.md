# ⚠️ DEPRECATED - auto_deprecate_markdown.py

> **This file has been deprecated and moved to the archived documentation.**

## Deprecation Information
- **Date Deprecated**: 2025-07-19 15:12:58
- **Reason**: Definitely outdated - superseded by newer implementations
- **Replacement**: See `CONSOLIDATED_DOCUMENTATION.md` for current documentation

## Original Content
The original content has been preserved below for reference:

---

# Enhanced Case Name Extraction System

## Overview

The enhanced case name extraction system now provides comprehensive case name extraction capabilities from both source documents and verification URLs. This addresses the reliability issues with case name extraction by implementing a multi-layered approach.

## Key Features

### 1. **Dual Extraction Sources**
- **Source Document Extraction**: Extracts case names from the original document (PDF, text, etc.)
- **URL-Based Extraction**: Extracts case names from verification URLs when the source extraction is unreliable

### 2. **Site-Specific Extraction Patterns**
The system recognizes and uses specialized extraction patterns for major legal websites:

- **CourtListener**: Uses `class="case-name"`, `class="title"`, and citation-specific patterns
- **Justia**: Uses `class="case-title"` and site-specific HTML structures
- **FindLaw**: Uses `class="case-title"` and FindLaw-specific patterns
- **CaseText**: Uses `class="case-title"` and CaseText-specific patterns
- **Leagle**: Uses `class="case-title"` and Leagle-specific patterns
- **Supreme Court**: Uses official Supreme Court website patterns
- **Cornell LII**: Uses Cornell Legal Information Institute patterns
- **Google Scholar**: Uses `class="gs_rt"` and Google Scholar-specific patterns

### 3. **Intelligent Verification Logic**

#### **When Both Names Are Available:**
- Compares extracted case name with source case name
- Uses similarity threshold (0.7) to determine verification status
- If similar: Marks as verified and includes the link
- If not similar: Includes the link but marks as not verified with a note about the difference

#### **When Only Source Name Available:**
- No extracted name from document
- Uses source case name and marks as verified
- Always includes the URL

#### **When Only URL Available:**
- No case name from either source
- If a dedicated case page is found, marks as verified
- Always includes the URL

#### **When Nothing Found:**
- Not verified, no URL included

### 4. **Case Name Validation and Cleaning**

#### **Validation Criteria:**
- Must contain typical case name patterns (e.g., "v.", "In re", "ex rel.")
- Must be substantial length (>5 characters)
- Must not contain common non-legal terms

#### **Cleaning Process:**
- Removes HTML tags
- Normalizes whitespace
- Removes citations from case names
- Removes trailing punctuation
- Handles special legal terms properly

### 5. **Similarity Comparison**

Uses Jaccard similarity to compare case names:
- Exact match: 1.0
- Substring match: 0.8
- Word overlap: Calculated similarity score
- Normalizes names by removing common words and punctuation

## Implementation Details

### **Core Methods:**

1. **`_extract_case_name_from_page()`**: Main extraction method with site-specific patterns
2. **`_identify_site_type()`**: Identifies legal website type from URL
3. **`_extract_case_name_by_site()`**: Routes to site-specific extraction methods
4. **`_extract_case_name_from_url_content()`**: Fetches and extracts from URLs
5. **`_clean_case_name()`**: Cleans and normalizes case names
6. **`_is_valid_case_name()`**: Validates case name format
7. **`_calculate_case_name_similarity()`**: Compares case names

### **Site-Specific Methods:**
- `_extract_case_name_courtlistener()`
- `_extract_case_name_justia()`
- `_extract_case_name_findlaw()`
- `_extract_case_name_casetext()`
- `_extract_case_name_leagle()`
- `_extract_case_name_supreme_court()`
- `_extract_case_name_cornell()`
- `_extract_case_name_google_scholar()`

## Usage Examples

### **Basic Verification with Extracted Case Name:**
```python
verifier = EnhancedMultiSourceVerifier()
result = verifier.verify_citation(
    "181 Wash.2d 391", 
    extracted_case_name="Walston v. Boeing Co."
)
```

### **URL-Based Extraction:**
```python
# When CourtListener returns "Unknown Case" but provides a URL
case_name = verifier._extract_case_name_from_url_content(
    "https://www.courtlistener.com/opinion/12345/walston-v-boeing-co/",
    "181 Wash.2d 391"
)
```

### **Site-Specific Extraction:**
```python
# Extract from a specific legal website
case_name = verifier._extract_case_name_courtlistener(html_content, citation)
```

## Benefits

### **1. Improved Reliability**
- Multiple extraction sources reduce dependency on single method
- Site-specific patterns improve accuracy for major legal websites
- Fallback mechanisms ensure URLs are always included when found

### **2. Better User Experience**
- Always provides the best available link
- Clear indication of verification status
- Transparent notes about case name differences
- Detailed similarity scores for transparency

### **3. Comprehensive Coverage**
- Supports all major legal websites
- Handles various case name formats
- Robust error handling and fallbacks

### **4. Future-Proof Design**
- Easy to add new legal websites
- Modular pattern system
- Configurable similarity thresholds

## Testing

Use the `test_enhanced_case_extraction.py` script to test:
- Case name extraction from source documents
- URL-based case name extraction
- Site-specific extraction patterns
- Case name validation and cleaning
- Similarity comparison functionality

## Configuration

The system can be configured by modifying:
- Similarity threshold (currently 0.7)
- Site-specific patterns
- Validation criteria
- Cleaning rules

## Future Enhancements

1. **Machine Learning Integration**: Use ML models for better case name extraction
2. **More Legal Websites**: Add patterns for additional legal databases
3. **Context-Aware Extraction**: Use surrounding text for better case name identification
4. **Parallel Processing**: Extract case names from multiple URLs simultaneously
5. **Caching**: Cache extracted case names to improve performance

## Summary

This enhanced system provides a robust, multi-layered approach to case name extraction that:
- **Always includes URLs** when found, regardless of verification status
- **Uses site-specific patterns** for accurate extraction from legal websites
- **Compares case names intelligently** to determine verification status
- **Provides clear feedback** about verification decisions and case name differences
- **Handles edge cases gracefully** with comprehensive fallback mechanisms

The system addresses the reliability issues with case name extraction while maintaining the core requirement of always providing the best available link to users. 