# Year Extraction Testing for WA Briefs

This document describes the year extraction testing capabilities built into the WA briefs pipeline.

## Overview

Year extraction is a critical component of citation processing. The pipeline includes comprehensive testing and validation of year extraction from various citation formats found in Washington State Courts briefs.

## Test Scripts

### 1. `test_year_extraction.py`
**Purpose**: Test year extraction on individual brief files

**Usage**:
```bash
python scripts/test_year_extraction.py path/to/brief.pdf -o results.json
```

**Features**:
- Extracts all years from PDF text
- Analyzes year extraction from citations
- Shows year distribution and extraction methods
- Provides detailed examples of year extraction

### 2. `validate_year_extraction.py`
**Purpose**: Validate year extraction accuracy against known test cases

**Usage**:
```bash
python scripts/validate_year_extraction.py --output validation.json --detailed
```

**Features**:
- Tests against 14 known citation formats
- Compares regex, core, and combined extraction methods
- Provides accuracy metrics and detailed error analysis
- Identifies problematic citation patterns

### 3. Enhanced Processing Pipeline
**Purpose**: Integrated year extraction analysis in the main processing pipeline

**Features**:
- Tracks year extraction rates across all briefs
- Aggregates year distributions
- Identifies best-performing briefs for year extraction
- Generates comprehensive analysis reports

## Year Extraction Methods

### Method 1: Regex Extraction
- **Patterns**: `(19|20)\d{2}`, `\((\d{4})\)`, `,\s*(\d{4})\s*$`
- **Accuracy**: 92.9%
- **Strengths**: Handles most standard citation formats
- **Weaknesses**: May miss complex patterns like `(9th Cir. 1997)`

### Method 2: Core Extraction
- **Function**: `extract_case_name_triple_comprehensive()`
- **Accuracy**: 28.6%
- **Status**: Needs improvement
- **Issues**: Not extracting years from most citation formats

### Method 3: Combined Approach
- **Strategy**: Use regex first, then core extraction
- **Accuracy**: 92.9%
- **Benefits**: Leverages strengths of both methods

## Test Cases

The validation script includes 14 test cases covering:

1. **Standard WA Supreme Court citations**
   - `Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)`

2. **WA Court of Appeals citations**
   - `State v. Johnson, 123 Wn. App. 456 (2004)`

3. **Federal citations**
   - `Brown v. Board of Education, 347 U.S. 483 (1954)`
   - `United States v. Doe, 123 F.3d 456 (9th Cir. 1997)`

4. **Complex citations**
   - Multiple years: `Smith v. Jones, 150 Wn.2d 123 (2003), overruled by Brown v. White, 160 Wn.2d 456 (2010)`

5. **Edge cases**
   - Citations without years: `RCW 2.60.020`
   - Decade references: `(2000s)`

## Current Performance

### Overall Metrics
- **Best Method**: Regex extraction (92.9% accuracy)
- **Problematic Pattern**: Ninth Circuit citations with `(9th Cir. YYYY)` format
- **Core Function Issue**: Not extracting years from most citation formats

### Recommendations

1. **Improve Core Extraction**: Enhance `extract_case_name_triple_comprehensive()` to better handle year extraction
2. **Extend Regex Patterns**: Add support for `(9th Cir. YYYY)` and similar formats
3. **Multiple Year Handling**: Improve detection of citations with multiple years
4. **Context Analysis**: Use surrounding text to validate extracted years

## Integration with Pipeline

The year extraction testing is integrated into the main WA briefs pipeline:

```powershell
# Run complete pipeline with year validation
.\scripts\wa_briefs_pipeline.ps1 -OutputDir "wa_briefs_test" -MaxBriefs 25

# Skip year validation if needed
.\scripts\wa_briefs_pipeline.ps1 -SkipYearValidation -MaxBriefs 25
```

## Output Files

### Processing Results
- `processing_summary.json`: Overall statistics including year extraction rates
- `analysis_report.txt`: Detailed analysis with year extraction metrics
- Individual brief results: `{filename}_results.json`

### Validation Results
- `year_extraction_validation.json`: Detailed validation results
- Console output: Real-time accuracy metrics and error analysis

## Next Steps

1. **Improve Core Function**: Fix year extraction in `extract_case_name_triple_comprehensive()`
2. **Add More Test Cases**: Include additional citation formats from real briefs
3. **Pattern Enhancement**: Extend regex patterns for edge cases
4. **Performance Optimization**: Optimize extraction speed for large brief collections
5. **Machine Learning**: Consider ML-based approaches for complex citation patterns 