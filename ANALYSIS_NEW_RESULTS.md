# Analysis of New Results After Fixes

## Improvements ✅

1. **Legal text removal working**:
   - `State v. Cauthron, 1993` → Extracted: `State v. Cauthron, 1993` ✅ (was "Frye hearing. State v. Copeland" before)
   - `Erwin v. Cotter Health Centers, Inc., 2007` → Extracted: `N/A, 2007` (was "We review choice of law questions de novo. Erwin v. Cotter Health Ctrs., 2007" before - legal text removed, but now N/A)

2. **Some correct extractions**:
   - Many verified citations now have correct extracted names

## Remaining Issues ❌

### 1. Still Wrong Extracted Names (Case Name Bleeding)

**Examples**:
- `Erickson v. Pharmacia LLC, 1980` → Extracted: `Env't Def. Fund, Inc. v. Env't Prot. Agency, 1980` ❌
- `Rice v. Dow Chemical Co., 1994` → Extracted: `Erickson v. Pharmacia, 1994` ❌
- `Burlington Northern & Santa Fe Railway Co. v. Abc-Naco, 2009` → Extracted: `Marakova v. United States, 2009` ❌
- `ACT I, LLC v. Davis, 2002` → Extracted: `Marakova v. United States, 2002` ❌
- `Department of Ecology v. Campbell & Gwinn, L.L.C., 2002` → Extracted: `Bolick v. Am. Barmag Corp, 2002` ❌
- `Zenaida-Garcia v. Recovery Systems Technology, Inc., 2005` → Extracted: `Bennett v. United States, 2005` ❌
- `Bryant v. Wyeth, 2012` → Extracted: `Kammerer v. W. Gear Corp, 2012` ❌
- `Call v. Heard, 1996` → Extracted: `State Farm Mut. Auto. Ins. Co. v. Campbell, 1996` ❌
- `Goede v. Aerojet General Corp., 2004` → Extracted: `Largent v. Pelikan, 2004` ❌
- `Sanders v. Ahmed, 2012` → Extracted: `Goede v. Aerojet Gen. Corp, 2012` ❌

**Root Cause**: The boundary validation I added should be catching these, but they're still getting through. This suggests:
1. The wrong case names ARE appearing in the text before the citation (but from a different citation)
2. The boundary validation isn't strict enough
3. The context isolation is still including text from other citations

### 2. Still Legal Text Contamination

**Examples**:
- `Stojkovic v. Weller, 1991` → Extracted: `WPLA claim. Call v. Heard, 1991` ❌
- `State, Dept. of Ecology v. Campbell & Gwinn, 2002` → Extracted: `Washington Legislature intended. Dep't of Ecology v. Campbell, 2002` ❌

**Root Cause**: The legal text removal patterns aren't catching all variations. "WPLA claim" and "Washington Legislature intended" aren't being removed.

### 3. Still Many "N/A" Results

**Examples**:
- Many verified citations still show "N/A" as extracted name
- This is expected for some cases, but too many are failing

---

## Why Boundary Validation Isn't Working

The boundary validation I added checks if the extracted case name appears before the citation. But the problem is:

1. **Wrong case names ARE appearing before the citation** - they're just from a different citation that appears earlier in the text
2. **The validation needs to be stricter** - it should check that the case name appears in the ISOLATED context, not just anywhere before the citation

---

## Additional Fixes Needed

### 1. Stricter Boundary Validation

**Current**: Checks if case name appears anywhere in 500-char window before citation
**Problem**: Wrong case names from earlier citations can still pass this check

**Fix**: Check that case name appears in the ISOLATED context (between previous citation and current citation), not just anywhere before

### 2. Better Legal Text Removal

**Current**: Removes some patterns, but misses "WPLA claim", "Washington Legislature intended"

**Fix**: Add more patterns and better sentence boundary detection

### 3. Improve Context Isolation

**Current**: Uses citation END positions, but may still include too much text

**Fix**: 
- Stricter sentence boundary detection
- Better handling of parentheticals
- Ensure context doesn't include any citation text


