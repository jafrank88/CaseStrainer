# Feature Extraction Plan - Pre-Deprecation

## Overview
This document outlines the unique features that need to be extracted from deprecated files before they are removed. These features are not present in the current consolidated modules and should be preserved.

## 🔍 **Unique Features Identified**

### **1. Enhanced Extraction Utils (`src/enhanced_extraction_utils.py`)**

#### **Missing Features:**
- **`extract_date_multi_pattern()`** - Multi-pattern date extraction with fallback strategies
- **`fallback_extraction_pipeline()`** - Comprehensive fallback extraction pipeline
- **`cross_validate_extraction_results()`** - Cross-validation of extraction results
- **`validate_extraction_quality()`** - Quality validation for extraction results
- **`calculate_extraction_confidence()`** - Advanced confidence calculation
- **`get_cache_key()`** - Cache key generation for extraction results
- **`clear_extraction_cache()`** - Cache management functions
- **`get_cache_stats()`** - Cache statistics
- **`optimize_extraction_early_termination()`** - Early termination optimization
- **`efficient_context_extraction()`** - Efficient context extraction
- **`extract_case_info_enhanced_with_position()`** - Position-aware extraction

#### **Enhanced Classes:**
- **`EnhancedCaseNameExtractor`** - Advanced case name extraction with validation
- **`EnhancedDateExtractor`** - Comprehensive date extraction with multiple patterns
- **`EnhancedExtractionManager`** - Management class for enhanced extraction

### **2. Legal Case Extractor Enhanced (`src/legal_case_extractor_enhanced.py`)**

#### **Missing Features:**
- **`extract_from_table_of_authorities()`** - TOA-specific extraction
- **`validate_against_toa()`** - TOA validation against body text
- **`_find_best_toa_match()`** - TOA matching algorithm
- **`_calculate_similarity()`** - Similarity calculation for TOA matching
- **`get_extraction_stats()`** - Extraction statistics
- **`get_cases_by_year_range()`** - Year range filtering
- **`get_cases_by_court()`** - Court-based filtering
- **`export_to_csv_format()`** - CSV export functionality
- **`convert_to_citation_result()`** - Conversion to CitationResult format

#### **Enhanced Data Classes:**
- **`DateInfo`** - Comprehensive date information structure
- **`CaseExtraction`** - Enhanced case extraction with metadata

### **3. Unified Citation Processor (`src/unified_citation_processor.py`)**

#### **Missing Classes:**
- **`OCRCorrector`** - OCR text correction utilities
- **`StatuteFilter`** - Statute citation filtering
- **`ExtractionDebugger`** - Debugging utilities for extraction pipeline
- **`ConfidenceScorer`** - Advanced confidence scoring system

#### **Missing Functions:**
- **`debug_extraction_pipeline()`** - Pipeline debugging
- **`safe_set_extracted_date()`** - Safe date setting
- **`validate_citation_dates()`** - Date validation
- **`setup_date_tracing()`** - Date tracing utilities
- **`extract_case_name_with_better_boundaries()`** - Boundary-aware extraction
- **`group_parallel_citations()`** - Parallel citation grouping

### **4. Citation Normalizer (`src/citation_normalizer.py`)**

#### **Already Consolidated:**
- All functions have been moved to `citation_utils_consolidated.py`
- No unique features remaining

## 📋 **Extraction Priority**

### **High Priority (Critical Features)**
1. **TOA Processing Functions** - `extract_from_table_of_authorities()`, `validate_against_toa()`
2. **Multi-Pattern Date Extraction** - `extract_date_multi_pattern()`
3. **Fallback Extraction Pipeline** - `fallback_extraction_pipeline()`
4. **OCR Correction** - `OCRCorrector` class
5. **Statute Filtering** - `StatuteFilter` class

### **Medium Priority (Useful Features)**
1. **Cross-Validation** - `cross_validate_extraction_results()`
2. **Quality Validation** - `validate_extraction_quality()`
3. **Advanced Confidence Scoring** - `ConfidenceScorer` class
4. **Extraction Debugging** - `ExtractionDebugger` class
5. **Cache Management** - Cache-related functions

### **Low Priority (Nice-to-Have)**
1. **Statistics Functions** - `get_extraction_stats()`, `get_cases_by_year_range()`
2. **Export Functions** - `export_to_csv_format()`
3. **Date Tracing** - `setup_date_tracing()`

## 🛠️ **Implementation Plan**

### **Phase 1: Extract Critical Features**
1. Move TOA processing functions to `toa_utils_consolidated.py`
2. Move multi-pattern date extraction to `citation_utils_consolidated.py`
3. Move fallback extraction pipeline to `citation_utils_consolidated.py`
4. Move OCR correction to `citation_utils_consolidated.py`
5. Move statute filtering to `citation_utils_consolidated.py`

### **Phase 2: Extract Useful Features**
1. Move cross-validation and quality validation to `citation_utils_consolidated.py`
2. Move confidence scoring to `citation_utils_consolidated.py`
3. Move extraction debugging to `test_utilities_consolidated.py`
4. Move cache management to `citation_utils_consolidated.py`

### **Phase 3: Extract Nice-to-Have Features**
1. Move statistics functions to `toa_utils_consolidated.py`
2. Move export functions to `toa_utils_consolidated.py`
3. Move date tracing to `citation_utils_consolidated.py`

## ✅ **Verification Steps**
1. Test all extracted functions in their new locations
2. Update import statements in files that use these functions
3. Verify no functionality is lost
4. Run comprehensive tests to ensure system stability
5. Remove deprecated files only after successful verification

## 🚨 **Risk Assessment**
- **Low Risk**: Most functions are self-contained and can be moved safely
- **Medium Risk**: Functions that depend on specific data structures may need adaptation
- **High Risk**: Functions that integrate deeply with existing pipelines may require careful testing

## 📝 **Next Steps**
1. Begin Phase 1 extraction
2. Test each extracted function
3. Update import statements
4. Proceed to Phase 2 and 3
5. Final verification before deprecation 