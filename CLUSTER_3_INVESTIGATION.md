# Cluster 3 Investigation: Multiple Cases in Same Cluster

**Date:** October 10, 2025  
**Issue:** Citations in Cluster 3 are verifying to **2 DIFFERENT cases** despite being parallel citations.

---

## 🚨 THE PROBLEM

**Cluster 3:**
- **Extracted Name:** "State v. M.Y.G." (2022)
- **Citation 1:** "199 Wn.2d 528" → Verified to "**State v. Olsen**" (2024)
- **Citation 2:** "509 P.3d 818" → Verified to "**State v. P**" (different case!)

These should be parallel citations for the SAME case, but they're verifying to different cases!

---

## 🔍 INVESTIGATION FINDINGS

### 1. CourtListener Citation-Lookup API

**Test Results:**
```
Citation: 199 Wn.2d 528
Status: 200
Results Found: 0

Citation: 509 P.3d 818
Status: 200
Results Found: 0
```

✅ **FINDING:** Both citations return **0 results** from the `citation-lookup` API.

---

### 2. CourtListener Search API (Fallback)

**Test Results for "State v. M.Y.G." (extracted name):**
```
Results Found: 20

Top 5 Results:
1. Domtar Corp. v. United States (2025)
2. Jacobs v. Salt Lake City School District (2025)
3. Gopher Media LLC v. Melone (2025)
4. Commonwealth v. Ricardo Lopez (2025)
5. People v. Garcia (2025)
```

❌ **FINDING:** The Search API returns **completely wrong results**:
- None are "State v. M.Y.G."
- None are "State v. Olsen"
- None are "State v. P"
- Most are not even criminal cases!

---

### 3. Cache Investigation

**Test Results:**
```
citation_cache directory: 0 files
correction_cache directory: 0 files
```

✅ **FINDING:** No cached verification results found.

---

### 4. Log Investigation

**Search for:** Fallback verifiers (Justia, Google Scholar, FindLaw, Bing)

**Results:** No logs found for any fallback verifier execution.

**Search for:** Verification source tracking

**Results:** All citations show `verification_source: "Unknown"`

---

## 🎯 KEY MYSTERY

**The URLs exist in the final results:**
- `https://www.courtlistener.com/opinion/10115097/state-v-olsen/`
- `https://www.courtlistener.com/opinion/4441070/state-v-p/`

**But they DON'T come from:**
- ❌ CourtListener citation-lookup API (404/0 results)
- ❌ CourtListener Search API (returns wrong cases)
- ❌ File cache (empty)
- ❌ Fallback verifiers (no logs)

**Where ARE these URLs coming from?** 🤔

---

## 🔧 HYPOTHESES

### Hypothesis 1: Redis Cache
The URLs might be stored in **Redis** from a previous run and are being retrieved without logging.

**Test:** Check Redis keys for verification results.

---

### Hypothesis 2: Eyecite Metadata
The `eyecite` library might be pre-populating `CitationResult` objects with URLs from an internal database.

**Test:** Check if `CitationResult.canonical_url` is set before verification runs.

---

### Hypothesis 3: Hardcoded Data
There might be a hardcoded database or JSON file mapping citations to URLs.

**Test:** Search codebase for "10115097" and "4441070" (opinion IDs).

---

### Hypothesis 4: Async/Sync Path Mismatch
The sync path might be using a different verification method than expected.

**Test:** Add logging at the very start of verification to track which method is called.

---

## 🎯 RECOMMENDED NEXT STEPS

### Option A: Focus on Redis
1. Clear Redis cache completely
2. Restart the system
3. Test with 1033940.pdf
4. Check if URLs still appear

### Option B: Focus on Eyecite
1. Add logging to `CitationExtractor` to see what `eyecite` returns
2. Check if `canonical_url` is pre-populated
3. If yes, find where `eyecite` gets its data

### Option C: Focus on Verification Logic
1. Add comprehensive logging at the START of verification
2. Track every API call and response
3. Find exactly where these URLs are being set

---

## 📊 IMPACT ASSESSMENT

**Current State:**
- ✅ Fix #58 (E-F): Clustering improved 50% (12 → 6 mixed clusters)
- ✅ Fix #60 (B-C): Jurisdiction filtering working (Iowa case rejected)
- ❌ **Verification is still broken:** Multiple cases in same cluster

**If verification is fixed:**
- Cluster 3 would split into 2 clusters (State v. Olsen + State v. P)
- OR both citations would verify to the SAME case
- Either way, the system would be trustworthy

**Tokens Used:** ~104k / 1M (10%) - **90% remaining**

---

## 💡 USER DECISION NEEDED

Which investigation path should I pursue?

**A.** Clear Redis and test (fastest, 5 min)
**B.** Investigate `eyecite` data source (medium, 15 min)
**C.** Add comprehensive verification logging (slowest, 30 min, but most thorough)




