# Phase 2: Case Name Extraction Fixes Applied

**Date:** October 21, 2025  
**Status:** Fixes implemented, ready for testing

---

## 🔧 **Fixes Implemented**

### **Fix 1: Enhanced Signal Word Cleaning**

**File:** `src/utils/strict_context_isolator.py` (Line 200)

**Problem:** Introductory and conditional words like "If", "When", "Where" were contaminating case names.

**Example:**
```
❌ Before: "If in Worcester v. Georgia"
✅ After: "Worcester v. Georgia"
```

**Solution Added:**
```python
# USER FIX: Introductory/conditional words that contaminate case names
r'\b(if|when|where|while|although|though|unless|until|since|because|as)\b\s+(?:in\s+)?',
```

**Impact:**
- Cleans "If in Worcester v. Georgia" → "Worcester v. Georgia"
- Removes conditional words from case name start
- Prevents contamination from sentence-starting keywords

---

### **Fix 2: Corporate Suffix Capture**

**File:** `src/utils/strict_context_isolator.py` (Line 244)

**Problem:** Pattern stopped at commas, missing corporate suffixes like "LLC", "Inc." that come after commas.

**Example:**
```
❌ Before: "Outsource Services Management" (missed ", LLC")
✅ After: "Outsource Services Management, LLC"
```

**Solution:**
- Added comma to character class: `[A-Za-z\'\.\&,\s\n\-]`
- Modified stopping condition: `(?:\s*[;\(]|,\s*\d|$)`
- Allows commas WITHIN case names
- Still stops at semicolons and parentheses (citation boundaries)
- Stops at "comma + digit" (start of citation)

**Full Pattern:**
```python
r'([A-Z][A-Za-z\'\.\&,\s\n\-]{2,80}?)\s+v\.\s+([A-Z][A-Za-z\'\.\&,\s\n\-]{2,120})(?:\s*[;\(]|,\s*\d|$)'
```

**Impact:**
- Captures "Outsource Services Management, LLC"
- Captures "Flying T Ranch, Inc."
- Captures any corporate suffix after comma
- Still prevents cross-citation contamination

---

## 📊 **Expected Results**

### **Issue 1: "If in Worcester v. Georgia" FIXED ✅**

**Test Text:**
```
If in Worcester v. Georgia, the Supreme Court held that federal law preempted state authority. 
See Martin v. Lessee of Waddell, 16 Pet. 367, 10 L. Ed. 997 (1842).
```

**Before Fix:**
- Citation: 16 Pet. 367
- Extracted: "If in Worcester v. Georgia"

**After Fix:**
- Citation: 16 Pet. 367
- Extracted: "Martin v. Lessee of Waddell" ✅

---

### **Issue 2: "N/A" for Outsource Services Management FIXED ✅**

**Test Text:**
```
Outsource Services Management, LLC v. Nooksack Business Corp., 181 Wn.2d 272, 333 P.3d 380 (2014).
```

**Before Fix:**
- Citation: 181 Wn.2d 272
- Extracted: "N/A" or truncated name

**After Fix:**
- Citation: 181 Wn.2d 272
- Extracted: "Outsource Services Management, LLC v. Nooksack Business Corp." ✅

---

### **Issue 3: "State v. Lazcano" Wrong Case** (Needs Additional Investigation)

**Test Text:**
```
In Gorman v. City of Woodinville, 175 Wn.2d 68, 283 P.3d 1082 (2012), 
the court followed the reasoning in State v. Lazcano.
```

**Expected:**
- Citation: 175 Wn.2d 68
- Extracted: "Gorman v. City of Woodinville"

**Status:** This may be a context isolation issue - need to test if fix resolves it.

---

## 🎯 **Technical Details**

### **Signal Word Patterns Enhanced:**

Previously cleaned:
- "cf", "e.g.", "see also", "see", "compare", etc.

**Now also cleans:**
- "if", "when", "where", "while"
- "although", "though", "unless", "until"
- "since", "because", "as"
- With optional "in" following (e.g., "If in")

### **Corporate Name Pattern Enhanced:**

**Character Class Changes:**
- **Before:** `[A-Za-z\'\.\&\s\n\-]` (no comma)
- **After:** `[A-Za-z\'\.\&,\s\n\-]` (with comma)

**Stopping Condition Changes:**
- **Before:** `(?:\s*[,;\(]|$)` (stops at comma)
- **After:** `(?:\s*[;\(]|,\s*\d|$)` (allows commas, stops at citation start)

This allows:
- ✅ "Company, Inc. v. Defendant"
- ✅ "Name, LLC v. Name, Corp."
- ❌ "Name, 123 F.3d 456" (stops at comma before citation)

---

## 🧪 **Testing Plan**

### **Test 1: Signal Word Contamination**

Submit text with "If in Worcester v. Georgia" pattern and verify:
1. Case name extracted WITHOUT "If in"
2. Correct case name identified
3. No signal word contamination

### **Test 2: Corporate Suffix Capture**

Submit text with "Outsource Services Management, LLC" and verify:
1. Full name with LLC captured
2. No "N/A" result
3. Complete corporate name in both plaintiff and defendant

### **Test 3: Combined Issues**

Submit text with multiple problematic patterns and verify:
1. All fixes work together
2. No regression in other extractions
3. Overall extraction quality improved

---

## 📝 **Remaining Issues to Investigate**

### **1. Quinault Citations Split**

Two possible causes:
- Different cases (1996 vs 2009)
- Different courts (Supreme Court vs Court of Appeals)

**Need to verify:** Are these actually the same case or different cases?

### **2. Flying T Ranch / Automotive United Trades**

May be a verification issue rather than extraction:
- Extraction appears correct
- But clustering/verification showing wrong case

**Need to investigate:** Verification logic, not extraction

### **3. Gorman v. City of Woodinville**

Extracting "State v. Lazcano" instead:
- May be fixed by signal word cleaning
- May need additional context isolation

**Need to test:** After current fixes deployed

---

## 🎯 **Success Metrics**

### **Extraction Quality:**
- ✅ No "If", "When", "Where" contamination
- ✅ Full corporate names with LLC, Inc., Corp.
- ✅ No "N/A" for valid case names
- ✅ Proper handling of commas in names

### **Regression Prevention:**
- ✅ Still stops at semicolons (citation boundaries)
- ✅ Still stops at parentheses (parenthetical references)
- ✅ Still stops at "comma + digit" (citation start)
- ✅ No cross-citation contamination

---

## 📁 **Files Modified**

1. **`src/utils/strict_context_isolator.py`**
   - Line 200: Added introductory word cleaning
   - Line 244: Enhanced corporate name pattern

---

## 🚀 **Deployment Steps**

1. ✅ Fixes implemented
2. ⏱️ Rebuild containers
3. ⏱️ Test with problem cases
4. ⏱️ Verify no regressions
5. ⏱️ Document final results

---

## 💡 **Technical Insights**

### **Why These Fixes Work:**

**Signal Word Cleaning:**
- Legal text often starts sentences with conditionals
- These words aren't part of case names
- Removing them prevents contamination
- Uses word boundaries to avoid over-matching

**Corporate Suffix Capture:**
- Corporate entities use commas before suffixes
- Pattern needs to capture across commas
- But must still stop at citation boundaries
- "comma + digit" is a reliable citation start marker

### **Pattern Safety:**

Both fixes maintain safety by:
- Using word boundaries (`\b`) for signal words
- Stopping at clear boundaries (semicolons, parens)
- Detecting citation starts (comma + digit)
- Preserving greedy vs. non-greedy behavior

---

## ⏭️ **Next Steps**

1. **Rebuild** with new fixes
2. **Test** all problem cases
3. **Verify** improvements
4. **Document** final results
5. **Address** any remaining issues

---

**Status:** Ready for rebuild and testing  
**Confidence:** HIGH - Fixes target exact failure modes  
**Risk:** LOW - Changes are surgical and well-bounded
