# CaseStrainer TODO List

## Frontend UI Issues

### 🎯 High Priority

#### 1. HomeView Spinner Not Animating
- **Issue**: Processing spinner in HomeView.vue is not spinning/animating
- **Status**: 🔴 OPEN
- **Description**: The spinner shows up during document processing but doesn't rotate - appears static
- **Impact**: Poor user experience - users can't tell if processing is active
- **Location**: `casestrainer-vue-new/src/views/HomeView.vue`
- **Attempted Fixes**: 
  - Added `!important` to CSS animation properties
  - Replaced with simple text indicator "⏳ Processing Your Document..."
- **Current Workaround**: Using text-based indicator instead of animated spinner
- **Notes**: CSS animation may have browser-specific issues or conflicting styles

#### 2. Progress Indicators Not Working (Legacy Issue)
- **Issue**: Progress bar is not moving during "Extract Names" step
- **Status**: 🟡 PARTIALLY RESOLVED
- **Description**: When processing citations, progress bar remains static
- **Impact**: Poor user experience - users can't tell progress
- **Location**: Frontend progress tracking components
- **Notes**: Backend hanging issue was resolved, but frontend animation still needs work

#### 2. Progress Step Stuck at "Extract Names"
- **Issue**: Processing gets stuck at "Extract Names" step with NaN% progress
- **Status**: 🔴 OPEN  
- **Description**: The progress indicator shows "Extract Names" but never advances to the next step
- **Root Cause**: Backend hanging during enhanced fallback verification (now fixed)
- **Frontend Impact**: Progress tracking needs to handle backend timeouts gracefully

## Backend Issues

### 🎯 High Priority

#### 1. Case Name Extraction - Low Verification Rate
- **Issue**: Only 31.7% of citations are being verified (19/60)
- **Status**: 🟡 IN PROGRESS
- **Description**: Case name extraction is capturing contaminated/truncated names
- **Examples of Problems**:
  - "Collateral Order Doctrine Overruling Batzel v. Smith" (includes explanatory text)
  - "Cohen v. Be" (truncated - should be "Cohen v. Beneficial Industrial Loan Corp.")
  - "Gasperini v. Ct" (truncated - should include full defendant name)
- **Recent Improvements**:
  - ✅ Added smart backward-walking algorithm to find case name start
  - ✅ Captures everything between "v." and citation (including commas)
  - ✅ Rejects obviously truncated names (v. Ct, v. Bl, v. Wa, etc.)
  - ✅ Minimum 5-character validation for party names
- **Still Needed**:
  - Remove citation signals and explanatory text before case names
  - Better handling of "In re" and "Ex parte" cases
  - Improve detection of sentence boundaries
- **Test Case**: `D:\dev\casestrainer\24-2626.pdf` (60 citations, 67 clusters)
- **Target**: Increase verification rate from 31.7% to 60%+

### ✅ Completed

#### 1. True by Parallel Logic
- **Issue**: Parallel citations not being marked as `true_by_parallel`
- **Status**: ✅ COMPLETED
- **Solution**: Fixed ultra-fast path to enable clustering for important citations

#### 2. Enhanced Fallback Verification Hanging
- **Issue**: System hanging during fallback verification with multiple timeouts
- **Status**: ✅ COMPLETED
- **Solution**: Added early return for citations with CourtListener data, reduced concurrent load

## Next Steps

1. **Test the Washington citations** to confirm the backend hanging issue is resolved
2. **Investigate frontend progress tracking** to fix spinner and progress bar issues
3. **Add timeout handling** in frontend for better user experience during long operations

---

*Last Updated: 2025-08-22*
*Status: Backend optimizations complete, frontend UI issues pending*
