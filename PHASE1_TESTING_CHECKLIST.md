# PHASE 1 CONSOLIDATION - TESTING CHECKLIST

## 🎯 **What Was Changed**
- Centralized all citation patterns into `src/citation_patterns.py`
- Updated 3 files to use shared patterns
- Added deprecation warnings to `unified_citation_processor_v2.py`
- **No functional changes** - purely architectural consolidation

---

## ✅ **Pre-Deployment Steps**

### 1. Rebuild Containers
```bash
./cslaunch
```

**Expected:**
- Clean build with no import errors
- All services start successfully
- No pattern-related warnings (except deprecation notices)

---

## 🧪 **Test Cases**

### Test 1: Basic Citation Extraction
**Input:** Short text with standard citations
```
Smith v. Jones, 123 U.S. 456 (2020)
```

**Expected:**
- ✅ Extracts "123 U.S. 456"
- ✅ Case name: "Smith v. Jones"
- ✅ Date: "2020"
- ✅ Method: "clean_pipeline_v1"

---

### Test 2: Neutral Citations (NEW)
**Input:** Text with New Mexico neutral citation
```
Hamaatsa, Inc. v. Pueblo of San Felipe, 2017-NM-007, 388 P.3d 977 (2016)
```

**Expected:**
- ✅ Extracts TWO citations: "2017-NM-007" AND "388 P.3d 977"
- ✅ Both have case name: "Hamaatsa, Inc. v. Pueblo of San Felipe"
- ✅ "2017-NM-007" is NOT in the extracted case name
- ✅ Both citations clustered together as parallels

---

### Test 3: Washington Citations
**Input:** Washington state case
```
State v. Smith, 123 Wn.2d 456, 789 P.3d 101 (2020)
```

**Expected:**
- ✅ Extracts both "123 Wn.2d 456" and "789 P.3d 101"
- ✅ Clustered as parallel citations
- ✅ Case name: "State v. Smith"

---

### Test 4: Multiple Cases (Clustering)
**Input:** Multiple cases cited together
```
See Smith v. Jones, 123 U.S. 456 (2020); Brown v. Board, 347 U.S. 483 (1954).
```

**Expected:**
- ✅ TWO separate clusters
- ✅ Each with correct case name
- ✅ No case name bleeding between citations

---

### Test 5: Complex Document (Your Test Case)
**Input:** robert_cassell_doc.txt or similar

**Expected:**
- ✅ All citations extracted
- ✅ Proper clustering
- ✅ No "Inc. v. Robins" type truncations
- ✅ Neutral citations (if any) extracted properly

---

## 📊 **Metrics to Monitor**

### Logs to Check:
```bash
docker logs casestrainer-backend-prod 2>&1 | grep -i "pattern"
docker logs casestrainer-rqworker1-prod 2>&1 | grep -i "CLEAN-PIPELINE"
```

**Look for:**
- ✅ "Using shared citation patterns from citation_patterns.py"
- ✅ No import errors
- ⚠️  Deprecation warnings (expected, not an error)

---

## ❌ **Known Issues to Ignore**

1. **Deprecation Warnings**: 
   - `unified_citation_processor_v2.py` deprecation notice - EXPECTED
   - `_build_citation_patterns()` deprecated - EXPECTED

2. **Existing Bugs** (not related to Phase 1):
   - Case name extraction quality issues
   - Verification failures
   - Clustering edge cases

---

## 🚨 **Red Flags to Watch For**

### Critical Issues:
- ❌ Import errors related to `citation_patterns`
- ❌ Pattern matching failures (no citations extracted)
- ❌ Container startup failures
- ❌ Python syntax errors

### Regression Issues:
- ❌ Citations that worked before now fail
- ❌ Different clustering results from before
- ❌ Case names extracted differently

---

## ✅ **Success Criteria**

Phase 1 is successful if:

1. ✅ **All tests pass** with same results as before
2. ✅ **Neutral citations work** (2017-NM-007 extracted and clustered)
3. ✅ **No regressions** in existing functionality
4. ✅ **Clean logs** (except expected deprecation warnings)
5. ✅ **Containers stable** (no crashes or errors)

---

## 📝 **Testing Notes**

| Test | Status | Notes |
|------|--------|-------|
| Basic Citation | ⬜ | |
| Neutral Citation | ⬜ | **PRIMARY FIX** |
| Washington Citation | ⬜ | |
| Multiple Cases | ⬜ | |
| Complex Document | ⬜ | |
| Container Stability | ⬜ | |

---

## 🔄 **If Issues Found**

### Rollback Plan:
```bash
git revert 9a6029d4  # Revert Phase 1 consolidation
git push
./cslaunch
```

### Debug Steps:
1. Check logs for import errors
2. Verify pattern definitions match previous versions
3. Test individual patterns in Python console
4. Check that `citation_patterns.py` is accessible

---

## ➡️ **After Testing: Phase 2 Prep**

Once all tests pass, document:
- ✅ Which tests passed
- ⚠️  Any issues encountered (and how resolved)
- 📊 Performance notes
- 💡 Observations for Phase 2

Then proceed to Phase 2 planning!

---

**Test Date:** _________________  
**Tester:** _________________  
**Result:** ⬜ PASS  ⬜ FAIL  ⬜ PARTIAL  
**Notes:**
