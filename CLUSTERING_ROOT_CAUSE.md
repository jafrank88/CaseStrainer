# Root Cause: Missing Citations, Not Clustering Failure

## ❌ ORIGINAL DIAGNOSIS: Wrong
**Thought:** Parallel citations are being extracted but clustered separately  
**Reality:** Parallel citations **aren't being extracted at all**!

## ✅ ACTUAL PROBLEM: Extraction Failure

### Evidence
- **"148 Wn.2d 224" + "59 P.3d 655"** exist in document (confirmed with PyPDF2)
- **NEITHER appear in results** (confirmed with grep on output)
- Total citations found: 87 (should be ~90+)

### Root Cause
**Line breaks within citations break eyecite**

Document text (from PyPDF2):
```
148 Wn.2d  \n224, 239, 59 P.3d  655
```

**Problem:**
- `unified_citation_processor_v2.py` uses **eyecite directly** (line 47)
- **NO local regex fallback** when eyecite fails
- Eyecite **cannot handle line breaks within citations**
- Test confirmed: eyecite found **ZERO citations** in this context

### Impact
- **~10-15 citations missing** from extraction
- All parallel pairs with line breaks are lost
- Cannot cluster what isn't extracted!

## 🔧 SOLUTIONS

### Option 1: Pre-process Text (QUICK FIX - RECOMMENDED)
Normalize line breaks BEFORE eyecite:
```python
# Before calling eyecite
normalized_text = re.sub(r'(\d+)\s+([A-Z][a-z]*\.)\s*\n+\s*(\d+)', r'\1 \2 \3', text)
# This transforms: "148 Wn.2d  \n224" → "148 Wn.2d 224"
```

**Pros:**
- Simple, localized fix
- Preserves eyecite's advanced features
- Minimal code changes

**Cons:**
- May miss edge cases
- Text positions shift (need to track)

### Option 2: Add Local Regex Fallback (ROBUST - LONG TERM)
Use the CitationExtractor pattern from `src/services/citation_extractor.py`:
```python
def extract_citations(text: str):
    # Try eyecite first
    citations = list(get_citations(text))
    
    # Fallback to local regex for missed citations
    if len(citations) < expected_threshold:
        regex_citations = _extract_with_local_patterns(text)
        citations.extend(regex_citations)
        citations = _deduplicate(citations)
    
    return citations
```

**Pros:**
- Catches ALL citations (eyecite + regex)
- Already implemented in deprecated CitationExtractor
- Robust to PDF extraction quirks

**Cons:**
- More code complexity
- Need to merge two citation sources
- Position tracking more complex

### Option 3: Fix Text at PDF Extraction (IDEAL - FUTURE)
Improve PyPDF2 text extraction:
- Use better PDF libraries (pdfplumber, pymupdf)
- Preserve citation formatting
- Remove artificial line breaks

**Pros:**
- Fixes root cause
- Benefits all downstream processing

**Cons:**
- Large refactor
- May break existing code
- Need extensive testing

## 📊 RECOMMENDATION

**IMMEDIATE:** Option 1 (Pre-process text)
- Add line break normalization before eyecite
- Test with 1033940.pdf
- Deploy if successful

**NEXT SPRINT:** Option 2 (Add regex fallback)
- Port local patterns from deprecated CitationExtractor
- Add as fallback when eyecite returns < threshold
- More robust long-term solution

**FUTURE:** Option 3 (Better PDF extraction)
- Evaluate pdfplumber vs pymupdf
- Benchmark quality improvement
- Plan migration strategy

## 🧪 TEST CASES

After fix, verify these are extracted:
- ✅ "148 Wn.2d 224" (Fraternal Order)
- ✅ "59 P.3d 655" (parallel to above)
- ✅ Any other citations with mid-citation line breaks

Expected cluster count: ~40-50 (currently 57 due to missing parallels)

## 💡 KEY INSIGHT

**The "clustering" issues were actually extraction failures!**
- You can't cluster citations that don't exist
- Eyecite is powerful but fails on PDF extraction artifacts
- Local regex patterns are more forgiving of formatting issues

This explains why:
1. So many parallel pairs are "split" (actually: one half missing!)
2. Citation count is lower than expected
3. Manual grep finds citations that results don't show

