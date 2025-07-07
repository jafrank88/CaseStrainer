# Case Name Selection Logic Improvements

## Overview

The case name selection logic has been improved to implement better prioritization between canonical, hinted, and extracted case names. The new logic ensures that the best available case name is always selected for display.

## Key Improvements

### 1. **Enhanced Priority System**

**New Priority Order:**
1. **Canonical Name** (highest priority) - Always used when available
2. **Hinted Name** - Used if better than extracted name
3. **Extracted Name** - Used if better than hinted name or only option
4. **N/A** - Used when no good quality names are available

### 2. **Improved Hinted Extraction**

The `extract_case_name_hinted()` function has been enhanced with:

- **Fuzzy Matching**: Uses multiple similarity metrics (ratio, partial_ratio, token_sort_ratio)
- **High Quality Threshold**: 85% similarity threshold for quality control
- **Pattern Matching**: Looks for case name patterns in context
- **Better Context Analysis**: Improved sentence and phrase analysis

### 3. **Sophisticated Comparison Logic**

When both hinted and extracted names are available (and no canonical name):

- **Fuzzy Similarity**: Compares both names to canonical name if available
- **Length Assessment**: Considers name completeness
- **Scoring System**: Combines similarity and length for decision making
- **Quality Control**: Discards poor quality names

### 4. **Better Quality Control**

- **Discard Poor Names**: If neither hinted nor extracted names are good quality, both are discarded
- **Validation**: All names are validated using `is_valid_case_name()` and `clean_case_name()`
- **Logging**: Enhanced logging for debugging and monitoring

## Code Changes

### Files Modified:

1. **`src/case_name_extraction_core.py`**
   - Updated `extract_case_name_triple()` function with improved selection logic
   - Added fuzzy matching comparison between hinted and extracted names
   - Enhanced logging for decision tracking

2. **`src/extract_case_name.py`**
   - Improved `extract_case_name_hinted()` function with fuzzy matching
   - Added multiple similarity metrics and pattern matching
   - Better context analysis and quality thresholds

### Key Functions:

```python
def extract_case_name_triple(text, citation, api_key=None, context_window=500):
    """
    Extract all three pieces: canonical, extracted, and hinted case names.
    Improved logic with better prioritization and quality control.
    """
    # Priority 1: Always use canonical name if available
    if canonical_name:
        case_name = canonical_name
    
    # Priority 2: Compare hinted vs extracted if no canonical
    elif canonical_name == "":
        if hinted_name != "N/A" and extracted_name != "N/A":
            # Use fuzzy matching to compare quality
            hinted_score = similarity_hinted + (hinted_length * 0.1)
            extracted_score = similarity_extracted + (extracted_length * 0.1)
            
            if hinted_score > extracted_score:
                case_name = hinted_name
            else:
                case_name = extracted_name
        elif hinted_name != "N/A":
            case_name = hinted_name
        elif extracted_name != "N/A":
            case_name = extracted_name
        else:
            case_name = "N/A"  # Discard both if poor quality
```

## Testing

### Test Files Created:

1. **`test_improved_case_name_logic.py`** - General logic testing
2. **`test_hinted_vs_extracted.py`** - Specific comparison testing

### Test Scenarios:

- ✅ Canonical name priority (always used when available)
- ✅ Hinted vs extracted comparison (better name selected)
- ✅ Poor quality names discarded (both set to N/A)
- ✅ Priority order verification
- ✅ Edge cases and error handling

## Benefits

### 1. **Better Accuracy**
- Canonical names always take priority (most reliable)
- Hinted names can improve over extracted names when better
- Poor quality names are discarded rather than used

### 2. **Improved User Experience**
- More consistent case name display
- Better quality names shown to users
- Clear indication when no good name is available (N/A)

### 3. **Enhanced Debugging**
- Detailed logging of decision-making process
- Clear tracking of which name type was selected and why
- Better error handling and validation

### 4. **Maintainability**
- Clear priority system that's easy to understand
- Modular design with separate functions for each name type
- Comprehensive test coverage

## Usage Examples

### Example 1: Canonical Name Available
```python
# Input: Citation with verified canonical name
triple = extract_case_name_triple(text, "199 Wn. App. 280")
# Result: case_name = "Doe P v. Thurston County" (canonical)
```

### Example 2: Hinted Better Than Extracted
```python
# Input: Citation without canonical, but good hinted extraction
triple = extract_case_name_triple(text, "123 U.S. 456")
# Result: case_name = hinted_name (if better quality)
```

### Example 3: Poor Quality Names
```python
# Input: Citation with poor context
triple = extract_case_name_triple(text, "123 U.S. 456")
# Result: case_name = "N/A" (both names discarded)
```

## Future Enhancements

1. **Machine Learning**: Consider ML-based quality assessment
2. **User Feedback**: Incorporate user corrections for training
3. **Performance**: Optimize fuzzy matching for large documents
4. **Caching**: Improve caching of similarity calculations

## Conclusion

The improved case name selection logic provides better accuracy, consistency, and user experience while maintaining the flexibility to handle various document formats and citation styles. The priority system ensures that the most reliable information is always used when available. 