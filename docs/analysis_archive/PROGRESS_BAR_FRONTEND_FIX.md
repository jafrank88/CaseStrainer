# Progress Bar Frontend Integration Fix

## Current Status

✅ **Backend**: Progress tracking is working correctly
- Progress callback wired up in sync processing
- Progress updates stored in global `SSEProgressManager`
- API endpoint updated to check global progress manager

❌ **Frontend**: Not polling for progress during sync processing

## The Problem

The frontend only polls for progress when it receives a `task_id` in the response (async mode), but for sync processing, it receives `request_id` and doesn't poll.

### Backend Response Structure

**Sync Processing:**
```json
{
  "success": true,
  "citations": [...],
  "clusters": [...],
  "request_id": "abc-123",
  "metadata": {
    "processing_mode": "immediate"
  }
}
```

**Async Processing:**
```json
{
  "success": true,
  "task_id": "abc-123",
  "status": "processing",
  "metadata": {
    "processing_mode": "queued"
  }
}
```

### Frontend Logic (HomeView.vue)

**Line 1453:** Frontend checks for `task_id` to start polling:
```javascript
if (response && response.task_id) {
  console.log('🔄 Async task started with task_id:', response.task_id);
  // Start polling...
}
```

**Issue:** Sync responses have `request_id` not `task_id`, so polling never starts!

## Solution Options

### Option 1: Frontend Polls During Sync (Recommended)

Update the frontend to poll for progress even during sync processing:

**File: `casestrainer-vue-new/src/views/HomeView.vue`**

```javascript
// Around line 1420-1450
const handleResponse = (response) => {
  // Check for both task_id (async) and request_id (sync)
  const trackingId = response.task_id || response.request_id;
  
  if (trackingId && response.metadata?.processing_mode !== 'immediate') {
    // Start polling for progress
    startProgressPolling(trackingId);
  }
  
  // For immediate mode, still poll briefly to show progress
  if (response.metadata?.processing_mode === 'immediate' && response.request_id) {
    startBriefProgressPolling(response.request_id);
  }
};

const startBriefProgressPolling = (requestId) => {
  // Poll for 2-3 seconds to catch progress updates
  let attempts = 0;
  const maxAttempts = 6; // 6 attempts * 500ms = 3 seconds
  
  const pollInterval = setInterval(async () => {
    attempts++;
    
    try {
      const progressResponse = await axios.get(
        `/casestrainer/api/processing_progress?request_id=${requestId}`
      );
      
      if (progressResponse.data) {
        updateProgressDisplay(progressResponse.data);
      }
      
      if (attempts >= maxAttempts || progressResponse.data?.is_complete) {
        clearInterval(pollInterval);
      }
    } catch (error) {
      console.error('Progress polling error:', error);
      clearInterval(pollInterval);
    }
  }, 500);
};
```

### Option 2: Backend Returns task_id for Both Modes

Standardize the backend to always return `task_id`:

**File: `src/unified_input_processor.py` (Line 383)**

```python
return {
    'success': True,
    'citations': converted_citations,
    'clusters': result.get('clusters', []),
    'request_id': request_id,
    'task_id': request_id,  # ADD THIS - frontend expects task_id
    'metadata': {
        **input_metadata,
        'processing_mode': 'immediate',
        'source': source_name,
        'processing_strategy': 'unified_v2_direct'
    }
}
```

### Option 3: Show Progress Immediately (No Polling)

Since sync is fast, show progress bar that fills quickly:

```javascript
if (response.metadata?.processing_mode === 'immediate') {
  // Show animated progress bar that fills in 1-2 seconds
  animateProgressBar(0, 100, 2000); // 0 to 100% in 2 seconds
}
```

## Recommended Implementation

**Use Option 1 + Option 2 Combined:**

1. **Backend**: Add `task_id` to sync responses (backward compatible)
2. **Frontend**: Poll for progress using `task_id || request_id`

This ensures:
- ✅ Backward compatibility
- ✅ Progress visible for both sync and async
- ✅ Minimal code changes

## API Endpoint Status

✅ **Already Fixed:** `/api/processing_progress` now checks global progress manager

```python
# Line 882-902 in vue_api_endpoints_updated.py
from src.unified_input_processor import get_progress_manager
global_progress_mgr = get_progress_manager()

if request_id in global_progress_mgr.active_tasks:
    progress_data = global_progress_mgr.get_progress(request_id)
    # Returns progress data...
```

## Testing

After implementing the fix:

1. **Upload a PDF** (sync mode)
2. **Check browser console** for progress polling logs
3. **Verify progress bar** shows 10% → 30% → 60% → 100%
4. **Check Network tab** for `/processing_progress?request_id=...` calls

Expected console output:
```
📊 Progress update: {progress_percent: 10, current_message: "Extracting citations"}
📊 Progress update: {progress_percent: 30, current_message: "Enhancing citation data"}
📊 Progress update: {progress_percent: 100, current_message: "Processing complete"}
```

## Files to Modify

### Backend (Already Done ✅)
1. ✅ `src/unified_input_processor.py` - Progress callback wired up
2. ✅ `src/vue_api_endpoints_updated.py` - API endpoint checks global manager

### Backend (Quick Fix Needed)
3. ⚠️ `src/unified_input_processor.py` (Line 383) - Add `task_id` field

### Frontend (Needs Update)
4. ❌ `casestrainer-vue-new/src/views/HomeView.vue` - Add progress polling for sync
5. ❌ `casestrainer-vue-new/src/stores/progressStore.js` - Handle request_id

## Quick Backend Fix

Add this one line to make frontend work immediately:

```python
# File: src/unified_input_processor.py, Line 383
return {
    'success': True,
    'citations': converted_citations,
    'clusters': result.get('clusters', []),
    'request_id': request_id,
    'task_id': request_id,  # ADD THIS LINE
    'metadata': {
        **input_metadata,
        'processing_mode': 'immediate',
        'source': source_name,
        'processing_strategy': 'unified_v2_direct'
    }
}
```

This single change will make the frontend start polling for progress!

## Current State

- ✅ Backend progress tracking: **Working**
- ✅ Backend API endpoint: **Working**  
- ⚠️ Backend response format: **Needs `task_id` field**
- ❌ Frontend polling: **Not polling for sync mode**

**Next Step:** Add `task_id` field to backend sync response, then test!
