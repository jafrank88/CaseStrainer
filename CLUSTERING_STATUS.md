# Clustering Status Summary

## ✅ What's Working

1. **Vacatur Pattern Detection:** ✅ WORKS
   - Correctly extracts "Oneida Indian Nation v. Madison County" (not "Cayuga")
   
2. **Case Name Extraction:** ✅ WORKS
   - All citations show correct case name

3. **Verification:** ✅ WORKS  
   - All three citations verified successfully

---

## ❌ Remaining Issue: Parallel Citation Clustering

### The Problem:

The three parallel Supreme Court citations are **NOT being clustered together**:

```
❌ SEPARATE CLUSTERS:
- 562 U.S. 42 (standalone)
- 131 S. Ct. 704 (standalone)
- 178 L. Ed. 2d 587 (standalone)

✅ SHOULD BE ONE CLUSTER:
- 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (all together)
```

### Diagnostic Information:

**All three show:**
- Verifying Source: Madison County v. Oneida Indian Nation of N.Y., **2011-01-10**
- Submitted Document: Oneida Indian Nation v. Madison County, **2010**

**The extracted year is "2010" but should be "2011" for the Supreme Court citations.**

---

## Root Cause Analysis

### Why Year is "2010" Instead of "2011":

The vacatur fix extracts the year from the Federal reporter citation:
```
"Oneida Indian Nation v. Madison County, 605 F.3d 149 (2010)"
                                                        ^^^^
```

This gives year "2010" (correct for the Circuit Court case).

But the Supreme Court citations should have year "2011":
```
"...vacated and remanded, 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)"
                                                                            ^^^^
```

### The Issue:

The year "2011" appears **at the end of all three parallel citations**, not after each individual citation. Our extraction looks for the year after the Federal citation, which gives us "2010".

---

## Possible Solutions

### Option 1: Look for Year at End of Parallel Citation Group

For parallel citations like "Citation1, Citation2, Citation3 (Year)", extract the year from the END of the group, not from the Federal citation.

### Option 2: Accept Both Years

The clustering logic could accept citations with year "2010" OR "2011" as the same case, recognizing that lower court and Supreme Court decisions may have different years.

### Option 3: Use Canonical Year for Clustering

Once a citation is verified, use the canonical year from CourtListener for clustering instead of the extracted year.

---

## Current Status

**Extraction:** ✅ FIXED - Correctly identifies "Oneida" case name  
**Year Detection:** ⚠️ PARTIAL - Gets "2010" from Federal citation  
**Clustering:** ❌ BROKEN - Citations not grouped as parallels due to missing year match

---

## Next Steps

1. Investigate why the year "2011" from the parallel citation group isn't being extracted
2. Consider extracting year from the END of the citation group, not just from the Federal citation
3. Test with the debug logs to see what year values are actually being extracted
4. Potentially adjust clustering logic to handle lower court vs. Supreme Court year differences

---

## Test Results Summary

**Test Text:**
```
"...Oneida Indian Nation v. Madison County, 605 F.3d 149 (2010)...
vacated and remanded, 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)"
```

**Expected:**
- All 4 citations clustered together (605 F.3d + 3 Supreme Court citations)
- Year: Mix of 2010 (Circuit) and 2011 (Supreme Court)

**Actual:**
- All citations verified ✅
- Correct case names extracted ✅  
- NOT clustered as parallels ❌
- All showing year "2010" (from Federal citation)

---

## Confidence Assessment

**What's Definitely Fixed:** Case name extraction (was "Cayuga", now "Oneida")  
**What's Still Broken:** Parallel citation clustering (year mismatch)  
**Impact:** Citations are verified but displayed as separate items instead of grouped together
