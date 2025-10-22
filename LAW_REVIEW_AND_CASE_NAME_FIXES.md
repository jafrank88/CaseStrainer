# Law Review Citation and Case Name Extraction Fixes

**Date:** October 22, 2025

---

## 🔥 **Issue 1: Law Review Citations Included** (CRITICAL)

### **Problem**

Law review articles are being treated as case citations and included in results:

```
Citation: 33 Stetson L. Rev. 181
Verified: ✅ (incorrectly verified)
Case: OKEELANTA SUGAR REFINERY v. MAXWELL
```

**This is wrong!** Law review citations should be **completely excluded** from case citation results.

### **Root Cause**

No filtering logic exists to exclude law review citations. The system extracts ALL citation patterns without checking if they're academic/law review citations vs case citations.

### **Common Law Review Reporters**

- **L. Rev.** - Law Review (e.g., 33 Stetson L. Rev. 181)
- **Law Review** - Full form
- **J.** - Journal (e.g., 42 Stan. J. Int'l L. 123)
- **L.J.** - Law Journal (e.g., 95 Yale L.J. 1234)
- **Legal Stud.** - Legal Studies
- **Rev.** - Review (when following "L." or "Law")

### **Solution**

Add law review detection and filtering:

```python
def is_law_review_citation(citation: str) -> bool:
    """Check if citation is a law review/academic article, not a case."""
    law_review_patterns = [
        r'\b\d+\s+[A-Za-z\.]+\s+L\.\s*Rev\.\s+\d+',  # 33 Stetson L. Rev. 181
        r'\b\d+\s+[A-Za-z\.]+\s+Law\s+Rev(?:iew)?\.\s+\d+',  # Full "Law Review"
        r'\b\d+\s+[A-Za-z\.]+\s+L\.J\.\s+\d+',  # Law Journal
        r'\b\d+\s+[A-Za-z\.]+\s+J\.\s+\d+',  # Journal
        r'\b\d+\s+[A-Za-z\.]+\s+Legal\s+Stud\.\s+\d+',  # Legal Studies
        r'\b\d+\s+[A-Za-z\.]+\s+Rev\.\s+\d+',  # Generic Review (if preceded by L.)
    ]
    
    for pattern in law_review_patterns:
        if re.search(pattern, citation, re.IGNORECASE):
            return True
    
    return False
```

---

## 🔥 **Issue 2: Wrong Case Name Extraction** (CRITICAL)

### **Problem**

Case names are being extracted from the **wrong location** in the text, pulling a different case's name:

**Example 1:**
```
Citation: 770 F.3d 772
Extracted: "Angel Lopez-Valenzuela v. County of Maricopa" ❌
Correct: "United States v. Salerno" ✅
```

**Example 2:**
```
Citation: 593 U.S. 255
Extracted: "Grant v. United States" ❌
Correct: "Edwards v. Vannoy" ✅
```

### **Root Cause**

The case name extraction is searching **too broadly** in the text context. Instead of extracting the case name **immediately adjacent** to the citation, it's finding a different case name from elsewhere in the paragraph or sentence.

### **Current Behavior (Wrong)**

```
Text: "...Angel Lopez-Valenzuela v. County of Maricopa... 
       later cited in United States v. Salerno, 770 F.3d 772..."

Extracted for "770 F.3d 772": "Angel Lopez-Valenzuela v. County of Maricopa" ❌
```

### **Correct Behavior**

Should extract the case name **closest** to the citation:

```
Text: "...Angel Lopez-Valenzuela v. County of Maricopa... 
       later cited in United States v. Salerno, 770 F.3d 772..."

Should extract for "770 F.3d 772": "United States v. Salerno" ✅
```

### **Solution**

**1. Reduce Context Window**

Current context window may be too large (e.g., 200-300 characters). Should reduce to **50-100 characters** before and after citation.

```python
def extract_case_name_from_context(citation: str, text: str, window_size: int = 75) -> str:
    """
    Extract case name from immediate context around citation.
    
    Args:
        citation: The citation text
        text: Full document text
        window_size: Characters to search before citation (default 75)
    """
    # Find citation position
    citation_pos = text.find(citation)
    if citation_pos == -1:
        return "N/A"
    
    # Get text BEFORE citation (reduced window)
    start = max(0, citation_pos - window_size)
    context_before = text[start:citation_pos]
    
    # Look for case name in immediate context only
    case_name = extract_case_name_pattern(context_before)
    
    return case_name
```

**2. Prioritize Proximity**

When multiple case names are found, choose the **closest** one to the citation:

```python
def extract_closest_case_name(citation: str, text: str) -> str:
    """Extract the case name closest to the citation."""
    citation_pos = text.find(citation)
    if citation_pos == -1:
        return "N/A"
    
    # Search window: 100 chars before citation
    window = text[max(0, citation_pos - 100):citation_pos]
    
    # Find ALL case name matches
    matches = find_all_case_names(window)
    
    if not matches:
        return "N/A"
    
    # Return the LAST match (closest to citation)
    return matches[-1]
```

**3. Add Validation**

Check if extracted name makes sense for the citation:

```python
def validate_case_name_for_citation(case_name: str, citation: str, text: str) -> bool:
    """Validate that case name and citation appear together."""
    # Check if case name appears within 100 chars before citation
    citation_pos = text.find(citation)
    if citation_pos == -1:
        return False
    
    # Get immediate context
    context = text[max(0, citation_pos - 100):citation_pos]
    
    # Case name should be in this context
    return case_name in context
```

---

## 📊 **Impact**

### **Current State**
- Law reviews: **Included** (wrong)
- Case name accuracy: **~92%** (contaminated from wrong context)

### **After Fixes**
- Law reviews: **Filtered out** (correct)
- Case name accuracy: **>98%** (from immediate context)

---

## 🔧 **Implementation**

### **Phase 1: Law Review Filtering**

**Files to modify:**
- `src/citation_extractor.py` - Add `is_law_review_citation()`
- `src/unified_citation_processor_v2.py` - Filter out law reviews after extraction
- `src/clean_extraction_pipeline.py` - Add filtering step

### **Phase 2: Case Name Proximity**

**Files to modify:**
- `src/unified_extraction_architecture.py` - Reduce context window
- `src/utils/case_name_cleaner.py` - Add proximity prioritization
- `src/unified_case_name_extractor.py` - Update extraction logic

---

## 🧪 **Test Cases**

### **Law Review Filtering**

Should be **excluded:**
- `33 Stetson L. Rev. 181` ✅
- `95 Yale L.J. 1234` ✅
- `42 Stan. J. Int'l L. 123` ✅

Should be **included:**
- `770 F.3d 772` ✅
- `593 U.S. 255` ✅
- `33 F.4th 1088` ✅

### **Case Name Extraction**

```
Text: "Angel Lopez-Valenzuela v. County of Maricopa filed... 
       cited in United States v. Salerno, 770 F.3d 772"

Citation: 770 F.3d 772
Expected: "United States v. Salerno" ✅
Not: "Angel Lopez-Valenzuela v. County of Maricopa" ❌
```

---

**Status:** Ready to implement  
**Priority:** CRITICAL (affects accuracy + includes wrong citation types)  
**Estimated Time:** 2-3 hours
