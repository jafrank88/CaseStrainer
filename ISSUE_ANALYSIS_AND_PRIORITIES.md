# Issue Analysis and Prioritization

## Results Summary
- **90 Cases Found**
- **124 Citations Verified**
- **Many "N/A" extracted names** (still a major issue)
- **Many wrong extracted names** (new critical issue)

---

## Critical Issues (P0 - Fix Immediately)

### 1. **Case Name Bleeding/Cross-Contamination** ⚠️ CRITICAL

**Problem**: Extracted names are picking up wrong case names from nearby citations or text.

**Examples**:
- `Erickson v. Pharmacia LLC, 1980` → Extracted: `Env't Def. Fund, Inc. v. Env't Prot. Agency, 1980` ❌
- `Rice v. Dow Chemical Co., 1994` → Extracted: `Erickson v. Pharmacia, 1994` ❌
- `State v. Copeland, 1996` → Extracted: `Frye rulings de novo. L.M. v. Hamilton, 1996` ❌ (contains legal text)
- `Bolick v. American Barmag Corp., 1982` → Extracted: `Goad v. Celotex Corp, 1982` ❌
- `Seizer v. Sessions, 1997` → Extracted: `BMW of N. Am., Inc. v. Gore, 1997` ❌
- `L.M. by and Through Dussault v. Hamilton, 2019` → Extracted: `Anderson v. Akzo Nobel Coatings, 2019` ❌
- `Burlington Northern & Santa Fe Railway Co. v. Abc-Naco, 2009` → Extracted: `Marakova v. United States, 2009` ❌
- `ACT I, LLC v. Davis, 2002` → Extracted: `Marakova v. United States, 2002` ❌
- `Department of Ecology v. Campbell & Gwinn, L.L.C., 2002` → Extracted: `Bolick v. Am. Barmag Corp, 2002` ❌
- `Zenaida-Garcia v. Recovery Systems Technology, Inc., 2005` → Extracted: `Bennett v. United States, 2005` ❌
- `Bryant v. Wyeth, 2012` → Extracted: `Kammerer v. W. Gear Corp, 2012` ❌
- `Call v. Heard, 1996` → Extracted: `State Farm Mut. Auto. Ins. Co. v. Campbell, 1996` ❌
- `Goede v. Aerojet General Corp., 2004` → Extracted: `Largent v. Pelikan, 2004` ❌
- `Sanders v. Ahmed, 2012` → Extracted: `Goede v. Aerojet Gen. Corp, 2012` ❌

**Root Cause**: 
- Strict context isolation is failing
- Extraction is picking up case names from nearby citations
- Legal text contamination (e.g., "Frye rulings de novo. L.M. v. Hamilton")

**Impact**: **CRITICAL** - This makes the extracted names unreliable and defeats the purpose of keeping extracted and canonical names separate.

**Priority**: **P0 - Fix Immediately**

**Fix Strategy**:
1. Improve strict context isolation boundaries
2. Better detection of citation boundaries
3. Remove legal analysis text from extracted names
4. Validate that extracted name appears BEFORE the citation (not after or in different sentence)

---

## High Priority Issues (P1 - Fix Soon)

### 2. **Still Too Many "N/A" Extracted Names**

**Problem**: Many citations still show "N/A" as extracted name, even when they're verified.

**Examples**:
- `N/A, N/A` → Citation: `2011 WL 3298912` (Unverified)
- `N/A, 2022` → Citation: `510 P.3d 326` (Unverified)
- `N/A, 1990` → Citation: `498 U.S. 941` (Unverified)
- `N/A, 1987` → Citation: `831 F.2d 508` (Unverified)
- `N/A, N/A` → Citation: `31 Wn. App. 2d 100` (Unverified)
- `N/A, 2021` → Citation: `19 Wn. App. 2d 113` (Unverified)

**But also verified citations with N/A**:
- `Richardson v. Pacific Power & Light Co., 1941` → Extracted: `N/A, 1941` ✅ Verified
- `Baffin Land Corp. v. MONTICELLO MOT. INN., INC., 1967` → Extracted: `N/A, 1967` ✅ Verified
- `Hurtado v. Superior Court, 1974` → Extracted: `N/A, 1974` ✅ Verified
- `Singh v. Edwards Lifesciences Corp., 2009` → Extracted: `N/A, 2009` ✅ Verified
- `Simon v. Philip Morris Inc., 2000` → Extracted: `N/A, 2000` ✅ Verified
- `Natalia Makarova v. United States, 2000` → Extracted: `N/A, 2000` ✅ Verified
- `ACT I, LLC v. Davis, 2002` → Extracted: `Marakova v. United States, 2002` ✅ Verified (but wrong name!)
- `Karpenski v. American General Life Companies, LLC, 2014` → Extracted: `N/A, 2014` ✅ Verified
- `Dailey v. North Coast Life Insurance, 1996` → Extracted: `N/A, 1996` ✅ Verified
- `Poage v. Crane Co., 2017` → Extracted: `N/A, 2017` ✅ Verified
- `Juan Jaurequi v. John Deere Company, 1993` → Extracted: `N/A, 1993` ✅ Verified
- `Christine Mahne v. Ford Motor Company, 1990` → Extracted: `N/A, 1990` ✅ Verified
- `Bradshaw v. Deming, 1992` → Extracted: `N/A, 1992` ✅ Verified
- `Zenaida-Garcia v. RECOVERY SYSTEMS TECH., 2005` → Extracted: `N/A, 2005` ✅ Verified

**Root Cause**:
- Extraction patterns failing
- Context window too small
- Case names not matching regex patterns
- Complex case names (multi-party, long descriptions)

**Impact**: **HIGH** - Users can't see what was extracted from their document.

**Priority**: **P1 - Fix Soon**

**Fix Strategy**:
1. Expand context window adaptively
2. Improve extraction patterns for complex case names
3. Try multiple extraction methods before giving up
4. Better handling of multi-party cases

---

### 3. **Legal Text Contamination in Extracted Names**

**Problem**: Extracted names contain legal analysis text, not just case names.

**Examples**:
- `State v. Copeland, 1996` → Extracted: `Frye rulings de novo. L.M. v. Hamilton, 1996` ❌
- `State v. Cauthron, 1993` → Extracted: `Frye hearing. State v. Copeland, 1993` ❌
- `Stojkovic v. Weller, 1991` → Extracted: `WPLA claim. Call v. Heard, 1991` ❌
- `Erwin v. Cotter Health Centers, Inc., 2007` → Extracted: `We review choice of law questions de novo. Erwin v. Cotter Health Ctrs., 2007` ⚠️ (has legal text but correct case name)
- `State, Dept. of Ecology v. Campbell & Gwinn, 2002` → Extracted: `Washington Legislature intended. Dep't of Ecology v. Campbell, 2002` ⚠️ (has legal text but correct case name)
- `Lakey v. Puget Sound Energy, Inc., 2013` → Extracted: `ER 702. Lakey v. Puget Sound Energy, 2013` ⚠️ (has legal text but correct case name)

**Root Cause**:
- Extraction is picking up text before the case name
- Not properly isolating case name from surrounding legal text
- Signal phrase removal not working correctly

**Impact**: **HIGH** - Extracted names are contaminated with legal analysis.

**Priority**: **P1 - Fix Soon**

**Fix Strategy**:
1. Better signal phrase detection and removal
2. Sentence boundary detection
3. Remove legal analysis phrases before case names
4. Validate extracted names don't contain legal text

---

## Medium Priority Issues (P2 - Fix When Possible)

### 4. **Date Extraction Errors**

**Problem**: Some citations have wrong extracted dates.

**Examples**:
- `Neah Bay Fish Co. v. Krummel, 1940` → Extracted: `N/A, 1976` ❌ (wrong date)
- `Barr v. Interbay Citizens Bank of Tampa, 1982` → Extracted: `Barr v. Interbay Citizens Bank, 1981` ⚠️ (1 year off)

**Impact**: **MEDIUM** - Dates are less critical than names, but still important.

**Priority**: **P2 - Fix When Possible**

---

### 5. **Name Formatting Differences (Not Real Issues)**

**Problem**: These are actually OK - just formatting differences between extracted and canonical.

**Examples** (These are fine):
- `Kerry L. Erickson, V. Pharmacia Llc., 2024` → Extracted: `Erickson v. Pharmacia, 2024` ✅ (abbreviation difference)
- `BMW of North America, Inc. v. Gore, 1996` → Extracted: `BMW of N. Am., Inc. v. Gore, 1996` ✅ (abbreviation)
- `State Farm Mutual Automobile Insurance v. Campbell, 2003` → Extracted: `State Farm Mut. Auto. Ins. Co. v. Campbell, 2003` ✅ (abbreviation)
- `FutureSelect Portfolio Management, Inc. v. Tremont Group Holdings, Inc., 2013` → Extracted: `FutureSelect Portfolio Mgmt., Inc. v. Tremont Grp. Holdings, 2013` ✅ (abbreviation)

**Impact**: **LOW** - These are expected differences.

**Priority**: **P3 - Low Priority** (These are working as intended)

---

### 6. **Unverified Citations**

**Problem**: Many citations show "Unverified" status.

**Examples**:
- `205 U.S. App. D.C. 139` - Unverified
- `636 F.2d 1267` - Unverified
- `821 F.2d 1147` - Unverified
- `2019 WL 2066127` - Unverified
- `494 P.3d 1076` - Unverified
- `199 Wn.2d 569` - Unverified
- `510 P.3d 326` - Unverified
- `623 S.W.3d 160` - Unverified
- `498 U.S. 941` - Unverified
- `831 F.2d 508` - Unverified
- `3 Wn.3d 1018` - Unverified
- `31 Wn. App. 2d 100` - Unverified (but verified in another cluster!)
- `19 Wn. App. 2d 113` - Unverified

**Root Cause**:
- Citations not found in CourtListener
- Citation format not recognized
- Network/timeout issues
- Citations too old or from obscure sources

**Impact**: **MEDIUM** - Some citations legitimately can't be verified.

**Priority**: **P2 - Fix When Possible** (Some are expected to be unverified)

---

## Priority Summary

### P0 - Critical (Fix Immediately)
1. **Case Name Bleeding/Cross-Contamination** - Extracted names are picking up wrong case names

### P1 - High Priority (Fix Soon)
2. **Too Many "N/A" Extracted Names** - Extraction failing too often
3. **Legal Text Contamination** - Extracted names contain legal analysis text

### P2 - Medium Priority (Fix When Possible)
4. **Date Extraction Errors** - Some wrong dates
5. **Unverified Citations** - Some expected, some might be fixable

### P3 - Low Priority (Working as Intended)
6. **Name Formatting Differences** - Abbreviation differences are expected

---

## Recommended Fix Order

1. **First**: Fix case name bleeding (P0) - This is the most critical issue
2. **Second**: Fix legal text contamination (P1) - Related to bleeding issue
3. **Third**: Improve extraction success rate (P1) - Reduce "N/A" results
4. **Fourth**: Fix date extraction (P2) - Lower priority
5. **Fifth**: Improve verification rate (P2) - Some are expected to fail

---

## Key Observations

1. **The similarity-based contamination detection is working** - We're not seeing false rejections of legitimate citations anymore.

2. **But extraction is still broken** - Case names are bleeding between citations, and extraction is picking up wrong names.

3. **Strict context isolation needs improvement** - The boundaries aren't working correctly.

4. **Legal text removal needs work** - Signal phrases and legal analysis text are contaminating extracted names.



