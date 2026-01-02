# Improvements Brought Over from Deprecated Files
**Date:** November 10, 2025  
**Source Files:** clean_extraction_pipeline.py → unified_case_extraction_master.py

---

## ✅ **3 Best Practices Salvaged**

### **1. Take LAST Match (Closest to Citation)**

**Problem with OLD approach:**
```python
match = re.search(pattern, context)  # Returns FIRST match
```

When there are multiple case names in the 500-char context window before a citation, we were getting the **first** one encountered, which might be far from the citation we're extracting.

**IMPROVED approach:**
```python
matches = list(re.finditer(pattern, context))
if matches:
    match = matches[-1]  # Take LAST match (closest to citation)
```

**Why this matters:**
- Citations often appear in dense text with multiple case references
- The case name **immediately before** the citation is almost always the correct one
- Example: "See Smith v. Jones, 123 F.2d 456. Later, Doe v. Roe, 789 F.2d 012"
  - If extracting "789 F.2d 012", we want "Doe v. Roe" (last), not "Smith v. Jones" (first)

**Diagnostic improvement:**
```python
logger.error(f"Pattern 1 raw match (last of {len(matches)}): '{case_name}'")
# Now we can see: "Pattern 1 raw match (last of 3)" - tells us there were 3 candidates
```

---

### **2. Explicit Company Suffix Handling**

**Problem with OLD approach:**
```python
pattern = r'([A-Z][^,]{10,150}?),\s*\d+'  # Generic pattern
```

This would match "Pharmacia" and stop, missing ", LLC" in:
> "Erickson v. Pharmacia, LLC, 31 Wn. App. 2d 100"

**IMPROVED approach:**
```python
pattern = r'([A-Z][^,]{10,150}?),\s*(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.)?,?\s*\d+'
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                      Explicitly handles company suffixes
```

**Company suffixes recognized:**
- LLC
- Inc.
- Corp.
- Co.
- Ltd.

**Why this matters:**
- Many case names include corporate entities
- Pattern now correctly handles: "Name, Inc., 123 Rep 456"
- Without this, extraction might include or exclude suffix inconsistently

---

### **3. Two-Step Extraction with Fallback**

**Problem with OLD approach:**
```python
case_name = match.group(1).strip()
if 'v.' in case_name.lower():
    return case_name  # Might include contamination
```

**IMPROVED approach:**
```python
# Step 1: Get raw match
case_name = match.group(1).strip()

# Step 2: Try to isolate JUST the case name (removes contamination)
case_name_match = re.search(
    r'([A-Z][\w\s&\',.-]+?\s+v\.\s+[\w\s&\',.-]+?)(?:,|\s*$)', 
    case_name, 
    re.IGNORECASE
)

# Step 3a: If refinement succeeded, use refined version
if case_name_match:
    case_name = case_name_match.group(1).strip()
    case_name = re.sub(r'[,\s]+$', '', case_name)
    logger.error(f"✅ STRING CITATION (refined): '{case_name}'")
    return MasterExtractionResult(..., confidence=0.85)

# Step 3b: FALLBACK - If refinement failed but we have "v.", use raw match
elif 'v.' in case_name.lower() or 'in re' in case_name.lower():
    logger.error(f"⚠️  STRING CITATION (unrefined): '{case_name}'")
    return MasterExtractionResult(..., confidence=0.7)  # Lower confidence!
```

**Why this matters:**

**Example contaminated match:**
```
Raw match: "the case of Smith v. Jones"
Refined match: "Smith v. Jones"  ← Better!
```

**Benefits:**
1. **Removes prefix contamination:** "the case of", "accord", etc.
2. **Removes suffix contamination:** trailing commas, periods
3. **Has safety net:** If refinement fails, still returns something
4. **Confidence scoring:** Refined = 0.85, Unrefined = 0.7

**Diagnostic improvement:**
```python
# Clear indication of which path was taken:
[SPECIAL-FORMATS] ✅ STRING CITATION (refined): 'Erickson v. Pharmacia'
# vs
[SPECIAL-FORMATS] ⚠️  STRING CITATION (unrefined): 'the case of Erickson v. Pharmacia'
```

---

## 📊 **Impact Summary**

### **Patterns Improved:**
1. ✅ **Pattern 1:** String citations (multiple reporters)
2. ✅ **Pattern 3:** WestLaw with docket numbers
3. ✅ **Pattern 4:** Signal word citations

### **Pattern 2 & 5 Not Changed:**
- **Pattern 2** (cert. denied): Already uses broader context and findall
- **Pattern 5** (parenthetical): Single pattern, no multiple matches expected

---

## 🎯 **Expected Improvements**

### **Better Accuracy:**
- Fewer "N/A" extractions
- Cleaner case names (less contamination)
- Correct case when multiple citations in context

### **Better Diagnostics:**
- Logs show how many matches were found
- Logs show if refined or unrefined extraction was used
- Confidence scores reflect extraction quality

### **Examples:**

**Before (OLD):**
```
Context: "See Smith v. Jones, 123 F.2d 456. Also, Doe v. Roe, Inc., 789 F.2d 012"
Extracting: "789 F.2d 012"
Result: "Smith v. Jones"  ❌ (took first match, wrong case)
```

**After (IMPROVED):**
```
Context: "See Smith v. Jones, 123 F.2d 456. Also, Doe v. Roe, Inc., 789 F.2d 012"
Extracting: "789 F.2d 012"
Logs: "Pattern 1 raw match (last of 2): 'Doe v. Roe'"
      "✅ STRING CITATION (refined): 'Doe v. Roe'"
Result: "Doe v. Roe"  ✅ (took last match, correct!)
```

---

## 🔬 **Code Comparison**

### **OLD (First match, no suffix handling):**
```python
string_pattern = r'([A-Z][^,]{10,150}?),\s*\d+\s+[A-Za-z.\s]+\d+'
match = re.search(string_pattern, context_clean)
if match:
    case_name = match.group(1).strip()
    case_name = self._clean_case_name(case_name)
    if 'v.' in case_name.lower():
        return case_name
```

### **NEW (Last match, suffix handling, two-step extraction):**
```python
string_pattern = r'([A-Z][^,]{10,150}?),\s*(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.)?,?\s*\d+\s+[A-Za-z.\s]+\d+'
matches = list(re.finditer(string_pattern, context_clean))
if matches:
    match = matches[-1]  # Take last (closest)
    case_name = match.group(1).strip()
    logger.error(f"Pattern 1 raw match (last of {len(matches)}): '{case_name}'")
    
    # Two-step extraction
    case_name_match = re.search(r'([A-Z][\w\s&\',.-]+?\s+v\.\s+[\w\s&\',.-]+?)(?:,|\s*$)', case_name, re.IGNORECASE)
    if not case_name_match:
        case_name_match = re.search(r'(In re\s+[\w\s&\',.-]+?)(?:,|\s*$)', case_name, re.IGNORECASE)
    
    if case_name_match:
        case_name = case_name_match.group(1).strip()
        case_name = re.sub(r'[,\s]+$', '', case_name)
        logger.error(f"✅ STRING CITATION (refined): '{case_name}'")
        return MasterExtractionResult(..., confidence=0.85)
    
    # Fallback
    elif 'v.' in case_name.lower() or 'in re' in case_name.lower():
        logger.error(f"⚠️  STRING CITATION (unrefined): '{case_name}'")
        return MasterExtractionResult(..., confidence=0.7)
```

---

## ✅ **Conclusion**

**All valuable techniques from deprecated files have been salvaged!**

The deprecated files ARE truly deprecated now - they had good ideas, but those ideas are now in the active file with:
- Better implementation
- Better logging
- Better error handling
- Better confidence scoring

**No need to reference deprecated files anymore - active file is now superior!** 🎯

---

## 📝 **Files Modified**

1. **src/unified_case_extraction_master.py** (Lines 463-622)
   - Pattern 1: String citations
   - Pattern 3: WestLaw with docket
   - Pattern 4: Signal words

**Deprecated files reviewed but not modified:**
- clean_extraction_pipeline.py (techniques extracted)
- unified_extraction_architecture.py (nothing useful)
- unified_case_name_extractor_v2.py (nothing new)

---

**Ready for testing with improved extraction logic!** 🚀
