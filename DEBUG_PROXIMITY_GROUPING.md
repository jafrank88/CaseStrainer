# Debug Logging for Proximity Grouping

## The Critical Issue

The three Oneida Supreme Court citations are showing as **three separate clusters** instead of one:

```
❌ CURRENT (WRONG):
- Cluster 1: 178 L. Ed. 2d 587 (alone)
- Cluster 2: 562 U.S. 42 (alone)
- Cluster 3: 131 S. Ct. 704 (alone)

✅ EXPECTED (CORRECT):
- Cluster 1: 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (together)
```

## Root Cause Investigation

The clustering process has two stages:
1. **Proximity Grouping** - Group citations that are close together in the text
2. **Parallel Detection** - Within each group, detect which citations refer to the same case

**The Problem:** If Stage 1 fails to group the citations together, Stage 2 never runs (it requires `len(citations) >= 2`).

## What We're Debugging

The text should be:
```
"...vacated and remanded, 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)..."
```

These citations are:
- **Comma-separated** (should be close proximity)
- **No semicolons** between them (should not be boundary-separated)
- **Same sentence** (should be in same context)

So they SHOULD be grouped together in Stage 1.

## Debug Logging Added

Added extensive logging to `_group_by_proximity()` method:

### What We'll See:

**1. Initial State:**
```
[PROXIMITY-DEBUG] Starting proximity grouping for X citations
[PROXIMITY-DEBUG] Proximity threshold: 200 chars
```

**2. For Each Pair of Citations:**
```
[PROXIMITY-DEBUG] Comparing: '562 U.S. 42' → '131 S. Ct. 704'
[PROXIMITY-DEBUG] Distance: X chars (prev_end=Y, curr_start=Z)
[PROXIMITY-DEBUG] Text between: ', '
```

**3. Grouping Decision:**
```
✅ [PROXIMITY-DEBUG] GROUPING citations (distance=2 <= 200)
OR
❌ [PROXIMITY-DEBUG] NEW GROUP (distance=500 > 200 OR semicolon=True)
```

**4. Final Results:**
```
[PROXIMITY-DEBUG] Final result: 1 group(s)
[PROXIMITY-DEBUG] Group 1: 3 citation(s) - 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587
```

## Possible Failure Modes

### Scenario A: Citations Not Found Together
If the citations are extracted from different parts of the document, they might not be close together.

**Evidence:** Distance > 200 chars

### Scenario B: Semicolon Boundary
If there's a semicolon between the citations (even incorrectly detected), they won't group.

**Evidence:** Text between includes ';'

### Scenario C: Wrong Start/End Indices
If the citation positions are incorrect, distance calculation fails.

**Evidence:** Distances don't match expected text layout

### Scenario D: Citations Sorted Incorrectly
If citations aren't sorted by position, grouping logic breaks.

**Evidence:** Citations appear in wrong order

## Testing Instructions

### Step 1: Submit Test Text

Go to http://localhost and submit the Oneida test text:

```
Other cases specifically discussing tribes hold that tribal sovereign immunity is not waived with respect to real property. See Cayuga Indian Nation v. Seneca County, 761 F.3d 218, 221 (2d Cir. 2014) (declining to draw a distinction between in rem and in personam proceedings); Oneida Indian Nation v. Madison County, 605 F.3d 149, 157 (2d Cir. 2010) (a tribe's immunity from suit is independent of its lands), vacated and remanded, 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011); Hamaatsa, Inc. v. Pueblo of San Felipe, 2017-NM-007, 388 P.3d 977, 985 (2016).
```

### Step 2: Check Logs

```bash
docker logs casestrainer-rqworker1-prod --tail 200 | grep "PROXIMITY-DEBUG"
```

### Step 3: Analyze Results

Look for:
1. **How many groups?** Should be 1 group with 3 citations
2. **What's the distance?** Should be very small (2-10 chars for comma+space)
3. **Any semicolons detected?** Should be NO for these three citations
4. **Text between citations?** Should show ", " (comma+space)

### Step 4: Compare with Expected

**Expected Output:**
```
[PROXIMITY-DEBUG] Starting proximity grouping for 3 citations
[PROXIMITY-DEBUG] Proximity threshold: 200 chars
[PROXIMITY-DEBUG] Comparing: '562 U.S. 42' → '131 S. Ct. 704'
[PROXIMITY-DEBUG] Distance: 2 chars (prev_end=X, curr_start=Y)
[PROXIMITY-DEBUG] Text between: ', '
[PROXIMITY-DEBUG] ✅ GROUPING citations (distance=2 <= 200)
[PROXIMITY-DEBUG] Comparing: '131 S. Ct. 704' → '178 L. Ed. 2d 587'
[PROXIMITY-DEBUG] Distance: 2 chars (prev_end=X, curr_start=Y)
[PROXIMITY-DEBUG] Text between: ', '
[PROXIMITY-DEBUG] ✅ GROUPING citations (distance=2 <= 200)
[PROXIMITY-DEBUG] Final result: 1 group(s)
[PROXIMITY-DEBUG] Group 1: 3 citation(s) - 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587
```

**If We See Something Different:**
- Distance > 200? → Citations not in same text location
- Semicolon detected? → False positive boundary detection
- Multiple groups? → Proximity threshold too strict OR wrong distances
- Wrong text between? → Citation positions are incorrect

## Next Steps Based on Findings

### If Proximity Grouping Works (1 group with 3 citations):
→ Problem is in **parallel detection** logic
→ Check case name and year extraction for each citation
→ Debug `_are_parallel_citations()` method

### If Proximity Grouping Fails (3 groups with 1 citation each):
→ Problem is in **citation extraction** or **position tracking**
→ Check start_index and end_index for each citation
→ Verify citations are from the same text location

### If Semicolon Boundary Detected Incorrectly:
→ Problem is in **boundary detection** logic
→ Check what text is between citations
→ May need to refine semicolon detection

## Status

✅ **DEBUG LOGGING ADDED** - Comprehensive proximity grouping diagnostics  
⏱️ **REBUILDING** - Docker build in progress  
🧪 **READY TO TEST** - Will analyze logs after rebuild  
🎯 **GOAL** - Understand why citations aren't grouping together

This debug logging will give us definitive answers about what's happening in the clustering process.
