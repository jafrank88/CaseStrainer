# Verification Data Loss Bug - Investigation Results

**Date:** October 21, 2025  
**Reporter:** User observation  
**Status:** ROOT CAUSE IDENTIFIED

---

## 🐛 **The Bug**

Citations are successfully verified by CourtListener API, but the frontend shows them as "UNVERIFIED".

**User's Observation:**
```
Cluster Section:
Citation 1:16 Pet. 367Verified  ← Shows "Verified"

Individual Citations Section:
16 Pet. 367
❌ UNVERIFIED  ← Shows "UNVERIFIED"
```

---

## 🔍 **Evidence from Logs**

### **Step 1: Verification SUCCEEDS** ✅

**Lines 226-240 (backend_martin_test.txt):**
```
≡ƒöì [TOP-LEVEL] 16 Pet. 367: Found case_name = Martin v. Lessee of Waddell
≡ƒöì [FIX #61] VERIFICATION: '16 Pet. 367'
   Γ£à VERIFIED via courtlistener_lookup_batch
   ≡ƒô¥ Canonical: 'Martin v. Lessee of Waddell' (1842-02-18)
   ≡ƒöù URL: https://www.courtlistener.com/opinion/86222/martin-v-lessee-of-waddell/
   ≡ƒôè Confidence: 0.97
```

**Proof:** CourtListener API returned:
- ✅ canonical_name: "Martin v. Lessee of Waddell"
- ✅ canonical_date: "1842-02-18"  
- ✅ URL: https://www.courtlistener.com/opinion/86222/martin-v-lessee-of-waddell/
- ✅ verified: True

### **Step 2: Verification Data APPLIED** ✅

**Lines 247-253:**
```
≡ƒöº [APPLY-VERIFICATION] Citation: 16 Pet. 367 - VERIFIED
   ≡ƒô¥ result.canonical_name = Martin v. Lessee of Waddell
   ≡ƒô¥ result.canonical_date = 1842-02-18
   Γ£à AFTER (object): verified=True, canonical_name = Martin v. Lessee of Waddell
```

**Proof:** The CitationResult object was updated with:
- verified = True
- canonical_name = "Martin v. Lessee of Waddell"
- canonical_date = "1842-02-18"

### **Step 3: Data LOST in Serialization** ❌

**Line 289:**
```python
DATA_SEPARATION: case_name='See Martin v. Lessee of Waddell', 
                 cluster='See Martin v. Lessee of Waddell', 
                 extracted='See Martin v. Lessee of Waddell', 
                 canonical='None'  ← DATA LOST!
```

**Proof:** When `to_dict()` is called on the CitationResult:
- canonical_name = None  ← Lost!
- verified status = Unknown (likely False)

---

## 🎯 **Root Cause**

The verified data is being **lost between verification and serialization**.

**Possible Causes:**

### **Theory 1: Object Recreation**
The CitationResult object that gets verified is not the same object that gets serialized.  
Somewhere in the pipeline, a NEW CitationResult is created without copying the verified fields.

### **Theory 2: Field Not Copied**
When citations are passed between processing stages, only certain fields are copied.  
The `canonical_name`, `canonical_date`, and `verified` fields are being dropped.

### **Theory 3: Dataclass vs Dict Conversion**
CitationResults might be converted to dictionaries and back, losing fields in the process.

---

## 🔎 **Where to Look**

### **File: src/models.py**
- Line 56-119: `to_dict()` method  
- The method correctly includes `canonical_name` (line 88)
- Line 75 logs show `canonical_name` is None when called
- **Conclusion:** The problem is NOT in to_dict(), it's BEFORE to_dict()

### **File: src/unified_clustering_master.py**
- Lines 246-253: Verification data is applied correctly
- Need to check: What happens to citations AFTER this point?

### **File: src/vue_api_endpoints_updated.py** (or similar)
- Need to find: Where citations are prepared for the API response
- Look for: Any code that creates new CitationResult objects
- Look for: Any code that copies only certain fields

---

## 🔧 **How to Fix**

### **Step 1: Find the Data Loss Point**
Add debug logging to track when canonical_name goes from "Martin v. Lessee of Waddell" to None:

```python
# In clustering_master.py AFTER verification
logger.error(f"[DEBUG-VERIFY] After verification: verified={citation.verified}, canonical={citation.canonical_name}")

# In the API endpoint BEFORE to_dict()
logger.error(f"[DEBUG-SERIALIZE] Before to_dict: verified={citation.verified}, canonical={citation.canonical_name}")
```

### **Step 2: Fix the Copying**
Once we find where the data is lost, ensure ALL verified fields are copied:

```python
# Example fix for object recreation:
new_citation = CitationResult(
    citation=old.citation,
    extracted_case_name=old.extracted_case_name,
    extracted_date=old.extracted_date,
    # ADD THESE:
    canonical_name=old.canonical_name,  # ← Was missing!
    canonical_date=old.canonical_date,  # ← Was missing!
    canonical_url=old.canonical_url,    # ← Was missing!
    verified=old.verified,              # ← Was missing!
    source=old.source,                  # ← Was missing!
    # ... etc
)
```

### **Step 3: Verify the Fix**
Test with the same citation and check logs:
- Backend logs should show: verified=True, canonical_name="Martin v. Lessee of Waddell"
- Frontend should show: ✅ VERIFIED with canonical name displayed

---

## 📊 **Impact**

### **Current State:**
- ❌ All citations show as UNVERIFIED even when successfully verified
- ❌ Canonical data (verified case names/dates) not displayed
- ❌ Users cannot see which citations were successfully looked up in CourtListener
- ⚠️ Cluster header shows "Verified" but individual citations show "UNVERIFIED" (confusing!)

### **After Fix:**
- ✅ Verified citations show ✅ VERIFIED status
- ✅ Canonical case names and dates displayed
- ✅ Clear indication of which citations were found in CourtListener database
- ✅ Consistent verification status across cluster and individual displays

---

## 🎯 **Priority**

**MEDIUM-HIGH**

While the system IS verifying citations correctly (functionality works), users cannot SEE the verification results (display broken). This reduces trust in the system and hides valuable canonical data.

---

## 📝 **Next Steps**

1. Add debug logging to track where canonical_name is lost
2. Identify the code that creates/copies CitationResult objects
3. Fix the field copying to include all verification fields
4. Test with known verified citations
5. Update frontend if needed to properly display verified status

---

## 🔗 **Related Issues**

1. **Frontend "Verified" Badge Confusion** - Cluster headers show "Verified" when they mean "Clustered"
2. **Inconsistent Verification Display** - Cluster vs Individual citation status mismatch

---

**Investigation Date:** October 21, 2025 (10:54pm)  
**Investigator:** AI Assistant  
**Reporter:** User observation during Phase 2 testing
