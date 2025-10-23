# Pathway Unification - Quick Start Guide

## The Problem We Just Discovered

```
User: "Why does the cluster not have the same extracted name as the citation?"
You: "Is it specific to the sync pathway, as this works in async?"
```

**Answer**: YES! And this is exactly why we need to unify.

---

## What's Currently Broken

### Sync Pathway (SHORT TEXT)
- Input: "Carman v. Adventure Bound, 198 Cal.App.3d 449 (1986)"
- Uses: `UnifiedClusteringMaster` → **Was broken** (just fixed)
- Issue: Citations stored as objects, not dicts
- Result: Vue.js couldn't read `extracted_case_name`

### Async Pathway (LONG TEXT/FILES)
- Uses: `UnifiedCitationClusterer` → **Already working**
- Properly serializes citations to dicts
- Result: Vue.js can read `extracted_case_name`

### Why This Happened
**Two separate clustering systems!**
- `unified_clustering_master.py` (sync)
- `unified_citation_clustering.py` (async)

When we fixed one, the other stayed broken.

---

## Immediate Fix (Next 1 Hour)

### Step 1: Create Unified Serialization (20 min)
Create `src/unified_serialization.py` with standardized functions

### Step 2: Update Both Clusterers (20 min)
Replace inline serialization in both files with the shared function

### Step 3: Test Both Pathways (10 min)
- Short text: "Carman v. Adventure Bound, 198 Cal.App.3d 449 (1986)"
- Long text: Any PDF file

### Step 4: Verify Output (10 min)
Both should produce identical JSON structure with `extracted_case_name` visible

---

## Long-Term Fix (Next Sprint)

1. **Delete `unified_citation_clustering.py`** completely
2. **Use only `unified_clustering_master.py`** for everything
3. **Remove sync/async branching** in `citation_service.py`
4. **Single code path** = No more divergence bugs

---

## Want to Start?

I can implement Step 1 right now:
1. Create `unified_serialization.py`
2. Update `unified_clustering_master.py` to use it
3. Test the fix

**Say "implement" and I'll start!**
