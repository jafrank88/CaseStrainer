# 🚨 CRITICAL: Case Name Extraction Fixes

**Date:** October 16, 2025, 5:02 PM  
**Status:** ✅ FIXES DEPLOYED! Testing in progress...

---

## ✅ **What's Working:**
- **PDF Extraction:** 44 seconds (was 2-3 minutes) - PDFMiner logging spam FIXED
- **Citation Finding:** 79 citations found
- **Verification:** Working
- **Clustering:** Working

---

## ❌ **CRITICAL ISSUES Found:**

### **Issue #1: Wrong Extraction File Being Used**
**Problem:** Our "In re" fixes were applied to `unified_case_extraction_master.py` but the system is using `unified_case_name_extractor_v2.py` → `extract_case_name_and_date_master()`

**Files to fix:**
- ✅ Fix applied to: `src/unified_case_extraction_master.py` (WRONG FILE!)
- ❌ Need to fix: `src/unified_case_name_extractor_v2.py` (ACTUAL FILE USED!)

---

### **Issue #2: Corporate Name Truncation**
**Examples from today's run:**
- ❌ "Inc. v. Stillaguamish Tribe of Indians"
- ✅ Should be: "Flying T Ranch, Inc. v. Stillaguamish Tribe of Indians"

**Root Cause:** Extraction starts at "Inc." instead of beginning of company name

---

### **Issue #3: Multiple N/A Case Names**
**Affected clusters:** cluster_43, 47, 48, 64, 67, 70

**Examples:**
- `cluster_47: N/A (2021) - 197 Wn.2d 868`
- `cluster_48: N/A (2021) - 489 P.3d 631`
- `cluster_64: N/A (2021) - 17 F.4th 901`

**Likely cause:** "In re" or special case types not being extracted

---

### **Issue #4: Hamaatsa Year Inconsistency**
- `cluster_7_vol2`: Hamaatsa (2011) - 388 P.3d 977 ❌
- `cluster_72`: Hamaatsa (2016) - 2017-NM-007 ✅

**Same case, two different years!**

---

### **Issue #5: Wrong Volume Numbers**
- `cluster_24_vol1`: "3 Wn.2d 1031" 
- Should be: "31 Wn. App. 2d" (based on cluster naming)

---

## ✅ **FIXES APPLIED (October 16, 5:02 PM):**

### **Fix #1: Reduced Context Window** ⭐ CRITICAL
**Problem:** Context window was 400 chars - picking up case names from OTHER citations  
**Fix:** Reduced to 150 chars for strict proximity  
**Location:** `src/unified_case_extraction_master.py` line 859  
**Impact:** Should stop wrong case names like "Oneida Indian Nation" for "76 Idaho 374"

### **Fix #2: Proximity Validation** ⭐ CRITICAL  
**Problem:** No validation of how far the extracted name was from the citation  
**Fix:** Added check - reject if name is >100 chars from citation  
**Location:** `src/unified_case_extraction_master.py` lines 936-943  
**Impact:** Ensures extracted name actually belongs to this citation

### **Fix #3: Strip Citation Patterns** ⭐ HIGH PRIORITY
**Problem:** Extracted names included citations: "Inc. v. Tribe, 31 Wn. App. 2d 343"  
**Fix:** Added regex to remove citation patterns from extracted names  
**Location:** `src/unified_case_extraction_master.py` lines 1202-1210  
**Impact:** Clean case names without trailing citations

---

## 🔧 **Fixes to Apply Next (If Issues Remain):**

### **Fix #1: Move "In re" Fixes to Correct File** ⭐ HIGHEST PRIORITY
**Location:** `src/unified_case_name_extractor_v2.py`
**Function:** `extract_case_name_and_date_master()` around line 1420

**Changes needed:**
1. Add "In re" pattern support
2. Add "In the matter of" pattern support  
3. Add "Matter of" pattern support
4. Add "Ex parte" pattern support
5. Add "Estate of" pattern support

**Copy from:** Lines 518-546 in `unified_case_extraction_master.py`

---

### **Fix #2: Corporate Name Truncation Prevention**
**Location:** `src/unified_case_name_extractor_v2.py`
**Function:** Case name cleaning and validation

**Changes needed:**
1. Scan backwards from "Inc." to find full company name
2. Don't start extraction at corporate suffix
3. Validate extracted name doesn't start with suffix

**Reference:** Memory shows this was fixed in `unified_case_name_extractor_v2.py` before - need to verify it's still there

---

### **Fix #3: Improve "In re" Detection**
**Related to Fix #1**

Ensure `_looks_like_case_name()` accepts:
- "In re [Name]"
- "In the matter of [Name]"
- "Matter of [Name]"
- "Ex parte [Name]"
- "Estate of [Name]"

---

### **Fix #4: Year Extraction Consistency**
**Investigation needed:**
- Why does Hamaatsa show 2011 for one citation and 2016 for another?
- Check if it's extracting from different parts of the document
- Ensure date extraction is consistent within same case

---

## 📋 **Implementation Plan:**

### **Step 1: Verify Current Extractor** (5 min)
```python
# Check which function is actually being called:
# In unified_citation_processor_v2.py around line 3640-3650
```

### **Step 2: Copy "In re" Patterns** (15 min)
Copy the pattern list from `unified_case_extraction_master.py` lines 518-546 to `unified_case_name_extractor_v2.py`

### **Step 3: Update Validation** (10 min)
Update `_looks_like_case_name()` to accept special case types

### **Step 4: Test Corporate Names** (10 min)
Test that "Flying T Ranch, Inc. v. ..." extracts correctly

### **Step 5: Deploy & Test** (10 min)
- Run `./cslaunch`
- Test with same PDF
- Verify fixes work

---

## 🧪 **Test Cases:**

After fixes, these should work:

**Test 1: Corporate Names**
```
Input: "Flying T Ranch, Inc. v. Stillaguamish Tribe"
Expected: "Flying T Ranch, Inc. v. Stillaguamish Tribe of Indians"
Currently: "Inc. v. Stillaguamish Tribe of Indians" ❌
```

**Test 2: In re Cases**
```
Input: "In re Dependency of G.J.A."
Expected: "In re Dependency of G.J.A."
Currently: "N/A" ❌
```

**Test 3: Matter of Cases**
```
Input: "In the matter of [Name]"
Expected: "In the matter of [Name]"
Currently: "N/A" ❌
```

---

## ⏰ **Time Estimate:** 1 hour total
- Analysis: 15 min
- Code changes: 30 min
- Testing: 15 min

---

## 📊 **Expected Improvement:**

| Metric | Before | After (Expected) |
|--------|--------|------------------|
| N/A case names | 6/12 unverified (50%) | 0/12 (0%) |
| Corporate truncation | Yes ❌ | No ✅ |
| Special case support | No ❌ | Yes ✅ |
| Consistent years | No ❌ | Yes ✅ |

---

## 🎯 **Success Criteria:**

After fixes:
1. ✅ Zero "N/A" case names for valid citations
2. ✅ Full corporate names extracted (no truncation)
3. ✅ "In re" and special case types work
4. ✅ Consistent years for same case
5. ✅ Proper volume/reporter extraction

---

## 📝 **Key Discovery:**

**The async processing pipeline uses:**
- `src/unified_citation_processor_v2.py` (main processor)
- `src/unified_case_name_extractor_v2.py` (case name extraction)
- NOT `src/unified_case_extraction_master.py` ❌

**Our fixes went to the wrong file!**

---

## ⚠️ **Important Notes:**

1. **Don't modify:** `unified_case_extraction_master.py` (not used in production)
2. **Do modify:** `unified_case_name_extractor_v2.py` (actually used!)
3. **PDF extraction is FAST now** - don't touch that!
4. **The 44-second processing time is excellent** - keep it!

---

**Next session: Fix the extraction issues and get 100% correct case names!** 🚀
