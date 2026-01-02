# Why URL PDF Processing is Broken vs File Upload Processing

## Key Difference: PDF Text Extraction Method

### URL Processing (in rq_worker.py):
```python
# Lines 232-236 in rq_worker.py
pdf_processor = OptimizedPDFProcessor()
result = pdf_processor.process_pdf(temp_path)
text = result.text if result else ""
```

### File Upload Processing (in unified_input_processor.py):
```python
# Lines 395-403 in unified_input_processor.py
from src.robust_pdf_extractor import RobustPDFExtractor
extractor = RobustPDFExtractor()
result = extractor.extract_text(temp_file_path)

if isinstance(result, tuple):
    text, method = result
else:
    text = result
    method = 'robust_pdf_extractor'
```

## The Problem

1. **URL processing uses `OptimizedPDFProcessor`** - This appears to have issues with the extraction pipeline
2. **File upload uses `RobustPDFExtractor`** - This works correctly

## Root Cause Analysis

The issue is that when processing URLs, the worker:
1. Downloads the PDF to a temporary file
2. Uses `OptimizedPDFProcessor` to extract text
3. Passes the extracted text to `extract_citations_with_clustering`
4. The extraction gets stuck at 25% progress due to Unicode encoding errors in the pipeline

When processing file uploads:
1. The file is saved to a temporary location
2. `RobustPDFExtractor` is used instead
3. This extractor likely handles Unicode characters better
4. The text extraction succeeds and processing continues

## Evidence from Testing

Our tests showed:
- PDF contains em-dash characters (U+2014) that cause encoding errors
- Multiple print statements with emoji characters cause Windows console encoding failures
- The extraction pipeline fails with "'charmap' codec can't encode characters" errors

## Solution

To fix URL processing, we need to either:
1. Replace `OptimizedPDFProcessor` with `RobustPDFExtractor` in rq_worker.py
2. Or fix the Unicode encoding issues in `OptimizedPDFProcessor`
3. Or ensure proper text encoding handling after extraction

The file upload path works because it uses a different, more robust PDF extraction method that handles Unicode characters properly.
