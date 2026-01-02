# Plan to Harmonize All Input Pipelines

## Current State
There are multiple different text extraction methods being used:

1. **URL Processing** (rq_worker.py): Uses `OptimizedPDFProcessor` - BROKEN
2. **File Upload** (unified_input_processor.py): Uses `RobustPDFExtractor` - WORKING
3. **UnifiedTextExtractor** exists but not used consistently

## Proposed Solution

### Step 1: Update rq_worker.py to use UnifiedTextExtractor
Replace the URL PDF extraction logic to use the same `UnifiedTextExtractor` that file uploads use.

### Step 2: Ensure unified_input_processor.py uses UnifiedTextExtractor
Currently it uses `RobustPDFExtractor` directly. We should use the unified extractor instead.

### Step 3: Create a single text extraction entry point
All inputs (URL, file upload, text) should go through the same text extraction pipeline.

## Implementation

### 1. Update rq_worker.py (lines 232-236)
```python
# OLD CODE:
pdf_processor = OptimizedPDFProcessor()
result = pdf_processor.process_pdf(temp_path)
text = result.text if result else ""

# NEW CODE:
from src.unified_text_extractor import extract_text_from_file_unified
text, method = extract_text_from_file_unified(temp_path, verbose=True)
logger.info(f"[TASK:{task_id}] Extracted {len(text)} characters using {method}")
```

### 2. Update unified_input_processor.py (lines 395-403)
```python
# OLD CODE:
from src.robust_pdf_extractor import RobustPDFExtractor
extractor = RobustPDFExtractor()
result = extractor.extract_text(temp_file_path)

# NEW CODE:
from src.unified_text_extractor import extract_text_from_file_unified
text, method = extract_text_from_file_unified(temp_file_path, verbose=True)
```

### 3. Benefits of This Approach
- Single source of truth for text extraction
- Multiple fallback methods (PyMuPDF, PyPDF2, RobustPDFExtractor)
- Better Unicode handling
- Caching support
- Consistent behavior across all input types
- Enhanced text normalization

### 4. Testing Required
After implementation, test:
- URL PDF processing
- File upload PDF processing  
- Text processing
- Large PDF handling
- Unicode character handling

This will ensure all inputs use the same robust text extraction pipeline.
