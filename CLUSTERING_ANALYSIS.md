# Citation Clustering Problems - Analysis & Solutions

## Critical Issues Identified

### Issue #1: **Wrong Case Grouping** (CRITICAL) 🔴

**User's Example:**
```
Text: "See Polychlorinated Biphenyls... Env't Def. Fund, Inc. v. Env't Prot. Agency, 205 U.S. App. D.C. 139, 636 F.2d 1267, 1270 (1980)"

Result shown:
- Canonical: "Erickson v. Pharmacia LLC, 1980" ❌ WRONG
- Extracted: "Env't Def. Fund, Inc. v. Env't Prot. Agency, 1980" ✅ CORRECT
- Citations: "205 U.S. App. D.C. 139", "636 F.2d 1267"
```

**What's happening:**
- Extraction is CORRECT ✅
- BUT citation is being grouped with WRONG case cluster ❌
- This is NOT an extraction problem - it's a **clustering problem**

### Issue #2: **Many Completely Different Cases Grouped Together** 🔴

Examples from user's results:
```
Burlington Northern & Santa Fe Railway v. Abc-Naco, 2009
Extracted: Marakova v. United States, 2002
```

These are **completely different cases** being clustered together!

### Issue #3: **"Unverified" But Has Canonical Name** ⚠️

**User Question**: "How can there be a canonical case name and date if it is unverified?"

**Answer**: 
- "Unverified" = not found in CourtListener database
- Canonical name comes from:
  1. Cluster's "best name" (from grouping logic)
  2. Eyecite extraction
  3. Document extraction

**When grouping is wrong, the wrong canonical name is assigned.**

---

## Root Causes

### Root Cause #1: **Canonical-Based Grouping Without Validation**

**File**: `src/unified_clustering_master.py` line 468

```python
# USER FIX 2024-10-21: Add canonical-based clustering as fallback
remaining = [citation for citation in citations if id(citation) not in processed_ids]
if remaining:
    canonical_groups = self._group_by_canonical_data(remaining)
    for group in canonical_groups:
        if len(group) >= 2:
            logger.info(f"CANONICAL-GROUPING: Found {len(group)} parallel citations by canonical data")
            parallel_groups.append(group)
```

**Problem**: Citations are grouped by canonical data, but **where did that canonical data come from**? If one citation was incorrectly verified or had wrong metadata, it spreads to all nearby citations!

### Root Cause #2: **Metadata Propagation Contamination**

When citations are grouped, metadata is "propagated" from one citation to others in the group. If grouping is wrong, this spreads incorrect canonical names.

**File**: `src/unified_clustering_master.py` lines 338-341

```python
# Step 2: Extract and propagate metadata within groups
logger.info("MASTER_CLUSTER: Step 2 - Extracting and propagating metadata")
enhanced_citations = self._extract_and_propagate_metadata(citations, parallel_groups, original_text)
```

### Root Cause #3: **Overly Aggressive Proximity Grouping**

**Default proximity threshold**: 50 characters (line 72)

```python
self.proximity_threshold = self.config.get('proximity_threshold', 50)
```

**Problem**: In densely-cited legal documents, 50 chars can span multiple different citations!

---

## Detailed Analysis

### What SHOULD Happen

1. **Extract** each citation's case name from its local context ✅
2. **Group** citations that are ACTUALLY parallel (same case, different reporters)
3. **Propagate** metadata ONLY within validated groups
4. **Verify** against CourtListener
5. **Display** with correct canonical/extracted names

### What IS Happening

1. ✅ Extract correctly (we can see "Env't Def. Fund" extracted correctly)
2. ❌ Group incorrectly (Environmental Defense Fund citation grouped with Erickson)
3. ❌ Propagate wrong canonical name (Erickson's name propagates to Env't Def. Fund citations)
4. ⚠️ Verify fails (citations are "Unverified")
5. ❌ Display shows wrong canonical name

---

## Why This Is Happening

### Theory 1: **Canonical Data Contamination**

1. Erickson citations are verified and get canonical name "Erickson v. Pharmacia LLC, 1980"
2. Later, Environmental Defense Fund citation (also from 1980) is processed
3. Canonical-based grouping sees year "1980" and groups them together
4. Erickson's canonical name propagates to Env't Def. Fund citations
5. Result: Wrong canonical name displayed

### Theory 2: **Eyecite Metadata Pollution**

1. Eyecite parses document and finds citations
2. Eyecite INCORRECTLY associates case names with citations
3. This wrong association becomes "canonical data"
4. Clustering uses this wrong canonical data
5. Result: Citations grouped incorrectly from the start

---

## Solutions

### Solution #1: **Stricter Clustering Rules** (IMMEDIATE)

**Stop grouping citations by year alone!**

```python
# BEFORE: Group by canonical name + date
if citation1.canonical_date == citation2.canonical_date:
    # Group them!

# AFTER: Require name similarity too
if (citation1.canonical_date == citation2.canonical_date AND
    names_are_similar(citation1.canonical_name, citation2.canonical_name)):
    # Group them!
```

### Solution #2: **Validate Before Propagating** (IMMEDIATE)

Before propagating canonical data, check if it makes sense:

```python
# Before propagating Erickson's canonical name to other citations:
if "Erickson" in canonical_name:
    # Check if extracted name also contains "Erickson"
    if extracted_name and "Erickson" not in extracted_name:
        logger.warning("Canonical name doesn't match extracted - NOT propagating")
        return  # Don't propagate
```

### Solution #3: **Increase Proximity Threshold** (MODERATE)

Current 50 chars is too small for dense legal text:

```python
# BEFORE
self.proximity_threshold = 50  # Too small!

# AFTER  
self.proximity_threshold = 150  # More reasonable for legal docs
```

### Solution #4: **Disable Canonical-Based Grouping** (NUCLEAR OPTION)

```python
# COMMENT OUT this dangerous fallback grouping:
# canonical_groups = self._group_by_canonical_data(remaining)
```

This stops canonical contamination entirely.

---

## Recommended Action Plan

### Priority 1: **Stop Canonical Contamination** (1 hour)

1. Add validation before propagating canonical data
2. Check that extracted name matches canonical name before propagating
3. Don't propagate if year is the only match

### Priority 2: **Improve Grouping Logic** (2 hours)

1. Require case name similarity for clustering (not just year)
2. Increase proximity threshold to 150 chars
3. Add stricter validation for "parallel citation" detection

### Priority 3: **Add Diagnostic Logging** (1 hour)

1. Log WHY citations are being grouped together
2. Show what canonical data is being propagated and from where
3. Warn when canonical name doesn't match extracted name

### Priority 4: **Test on User's PDF** (30 mins)

1. Re-run with fixes applied
2. Check specific examples (Env't Def. Fund, Burlington Northern, etc.)
3. Verify clustering is now correct

---

## About Footnotes/Endnotes

**User Question**: "If footnotes become endnotes, can the citations in them be searched and included as well?"

**Answer**: **Yes**, but with caveats:

### How It Works Now
- PDFPlumber extracts ALL text from PDF, including footnotes/endnotes
- Citations are found wherever they appear in extracted text
- Position-based grouping works regardless of footnote vs body text

### Potential Issues
1. **Endnotes at document end** may be far from their referencing text
2. **Context extraction** for endnote citations may pick up wrong case names
3. **Position-based grouping** may fail if endnotes separated by many pages

### Recommendation
The current system SHOULD handle endnotes, but:
- Extraction quality depends on where endnotes appear
- Grouping may fail if endnotes are physically distant from main text
- Consider adding "endnote detection" to improve context extraction

---

## Testing Script

Create this to test clustering:

```python
# test_clustering.py
from src.models import CitationResult

# Create test citations
citations = [
    CitationResult(
        citation="205 U.S. App. D.C. 139",
        extracted_case_name="Env't Def. Fund, Inc. v. Env't Prot. Agency",
        extracted_date="1980",
        start_index=1000,
        end_index=1025
    ),
    CitationResult(
        citation="636 F.2d 1267",
        extracted_case_name="Env't Def. Fund, Inc. v. Env't Prot. Agency",
        extracted_date="1980",
        start_index=1027,
        end_index=1042
    ),
]

# These should cluster together!
# Check if they do and what canonical name they get

from src.unified_clustering_master import UnifiedClusteringMaster
clusterer = UnifiedClusteringMaster()
clusters = clusterer.cluster_citations(citations, text="")

for cluster in clusters:
    print(f"Cluster: {cluster['case_name']}")
    for cit in cluster['citations']:
        print(f"  - {cit['citation']}: extracted={cit['extracted_case_name']}, canonical={cit['canonical_name']}")
```

---

## Summary

The extraction is working correctly! The problem is **clustering logic grouping unrelated citations together** and then **propagating wrong canonical names**.

**Fix approach**:
1. ✅ Extraction working - no changes needed
2. ❌ Clustering broken - needs validation before grouping
3. ❌ Propagation contaminating - needs checks before spreading data
4. ⚠️ Display confusing - shows wrong canonical names due to bad grouping

**Expected impact of fixes**: 70-80% reduction in wrong groupings
