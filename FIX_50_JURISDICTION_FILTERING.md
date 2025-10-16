# Fix #50: Jurisdiction Filtering for API Verification

## 🎯 Goal
Add jurisdiction filtering to prevent wrong API matches (e.g., "9 P.3d 655" matching Mississippi instead of Washington)

## 📚 Reference
Based on [National Reporter System (Wikipedia)](https://en.wikipedia.org/wiki/National_Reporter_System)

## 🔍 Problem
CourtListener API was returning matches from the wrong jurisdiction:
- **'9 P.3d 655'** → Mississippi case (expected: Washington)
- **'182 Wn.2d 342'** → Wrong case (expected: Washington)
- **'509 P.3d 325'** → Wrong case entirely

## ✅ Solution

### New Methods Added

#### 1. `_detect_jurisdiction_from_citation(citation: str) -> Optional[str]`
Detects expected jurisdiction from citation reporter:

**Washington-specific reporters:**
- `Wn.` or `Wash.` → `'washington'`
- These are DEFINITIVE for Washington state

**Federal reporters:**
- `U.S.`, `S. Ct.`, `L. Ed.`, `F.2d`, `F.3d` → `'federal'`

**Pacific Reporter:**
- `P.`, `P.2d`, `P.3d` → `'pacific'`
- **Note:** Pacific Reporter covers **15 western states** (AK, AZ, CA, CO, HI, ID, KS, MT, NV, NM, OK, OR, UT, WA, WY)
- Less specific, but still useful for filtering

**Westlaw:**
- `WL` → `'westlaw'` (unpublished, any jurisdiction)

#### 2. `_validate_jurisdiction_match(cluster, expected_jurisdiction, citation) -> bool`
Validates that a CourtListener cluster matches the expected jurisdiction:

**Washington citations** (`Wn.`, `Wash.`):
- **REQUIRE** at least one WA reporter in the cluster
- **REJECT** if no WA citations found (strict filter)

**Federal citations** (`U.S.`, `F.2d`, etc.):
- **REQUIRE** at least one federal reporter in the cluster
- **REJECT** if no federal citations found (strict filter)

**Pacific Reporter** (`P.2d`, `P.3d`):
- **CHECK** for P. reporter in cluster
- **WARN** but don't reject (lenient - parallel citations may use different reporters)

### Integration Points

#### Both Sync and Async Verification
Jurisdiction filtering is applied in **two methods**:

1. **`_find_best_matching_cluster_sync()`** (line ~711-730)
   - Used by batch verification (sync mode)
   - Filters clusters BEFORE name similarity validation

2. **`_find_matching_cluster()`** (line ~574-593)
   - Used by async verification
   - Filters clusters BEFORE name similarity validation

**Order of validation:**
1. Find clusters with exact citation match
2. **🆕 Filter by jurisdiction** (Fix #50)
3. Validate name similarity (Fix #26)
4. Validate date/year (Fix #26)

## 📊 Expected Impact

### High Confidence Fixes
**Washington-specific reporters** (`Wn.2d`, `Wash.2d`):
- ✅ **'182 Wn.2d 342'** - Will reject non-WA matches
- ✅ **'199 Wn.2d 528'** - Will reject non-WA matches
- ✅ **'183 Wn.2d 649'** - Already correct, will stay correct

### Moderate Confidence Fixes
**Pacific Reporter** (`P.2d`, `P.3d`):
- ⚠️ **'9 P.3d 655'** - Will warn about Mississippi match, but may not reject (Pacific covers 15 states)
- ⚠️ **'509 P.3d 325'** - Depends on whether wrong match has P. citations
- ⚠️ **'495 P.3d 866'** - Depends on cluster citations

**Note:** Pacific Reporter citations still benefit from existing name/year validation (Fix #26)

### Federal Citations
- ✅ **'521 U.S. 811'**, **'117 S. Ct. 2312'** - Will require federal reporters in cluster

## 🧪 Testing

### Test Cases
1. **'182 Wn.2d 342'** - Should only match clusters with WA citations
2. **'9 P.3d 655'** - Should prefer WA over Mississippi if both have P. citations
3. **'521 U.S. 811'** - Should only match clusters with federal citations

### Log Markers
```
[FIX #50] Detected jurisdiction for {citation}: {jurisdiction}
✅ [FIX #50] {n} cluster(s) passed jurisdiction filter
🚫 [FIX #50] Filtered out cluster due to jurisdiction mismatch: {case_name}
❌ [FIX #50] ALL clusters failed jurisdiction filtering for {citation}
```

## 📝 Code Changes

**File:** `src/unified_verification_master.py`

**Lines added:**
- ~813-848: `_detect_jurisdiction_from_citation()` method
- ~850-900: `_validate_jurisdiction_match()` method
- ~711-730: Jurisdiction filtering in sync method
- ~574-593: Jurisdiction filtering in async method

**Total:** ~120 lines added

## ⚠️ Limitations

1. **Pacific Reporter ambiguity:** P.2d/P.3d citations cover 15 states, so jurisdiction filtering is less precise
2. **Unpublished opinions (WL):** Cannot determine jurisdiction from citation alone
3. **Relies on cluster citations:** CourtListener must return complete citation data
4. **Name/year validation still needed:** Jurisdiction filtering is a first-pass filter, not a replacement for similarity checks

## 🔄 Complements Existing Fixes

- **Fix #26:** Name similarity threshold (0.6) - catches wrong names
- **Fix #26:** Year mismatch validation (±2 years) - catches wrong years
- **Fix #50:** Jurisdiction filtering - catches wrong states
- **Together:** Multi-layered validation for accurate verification

## ✅ Status
**DEPLOYED** - Ready for testing with `quick_test.py` and `1033940.pdf`

