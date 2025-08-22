# CaseStrainer TODO List

## Frontend UI Issues

### 🎯 High Priority

#### 1. Progress Indicators Not Working
- **Issue**: Spinner is not spinning and progress bar is not moving during "Extract Names" step
- **Status**: 🔴 OPEN
- **Description**: When processing citations, the frontend shows "Extract Names" but the spinner doesn't animate and progress bar remains static
- **Impact**: Poor user experience - users can't tell if the system is working or stuck
- **Location**: Frontend progress tracking components
- **Notes**: This appears to be related to the backend hanging during enhanced fallback verification

#### 2. Progress Step Stuck at "Extract Names"
- **Issue**: Processing gets stuck at "Extract Names" step with NaN% progress
- **Status**: 🔴 OPEN  
- **Description**: The progress indicator shows "Extract Names" but never advances to the next step
- **Root Cause**: Backend hanging during enhanced fallback verification (now fixed)
- **Frontend Impact**: Progress tracking needs to handle backend timeouts gracefully

## Backend Issues

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
