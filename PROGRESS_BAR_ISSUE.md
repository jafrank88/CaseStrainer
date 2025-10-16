# Progress Bar Issue - "NaN%" Display

## Problem

The progress bar shows:
```
Initializing
0s elapsed
NaN%        <-- Invalid value
Extract
Analyze
Extract Names
Verify
Cluster
```

## Root Cause

The `UnifiedCitationProcessorV2` is being instantiated **without a progress_callback**, so progress updates are being called but not transmitted to the frontend.

### Code Evidence

**File: `src/unified_input_processor.py` (Line 317)**
```python
processor = UnifiedCitationProcessorV2()  # ❌ No progress_callback!
result = asyncio.run(processor.process_text(input_data.get('text', '')))
```

**File: `src/unified_citation_processor_v2.py` (Line 172)**
```python
def __init__(self, config: Optional[ProcessingConfig] = None, 
             progress_callback: Optional[callable] = None):
    self.progress_callback = progress_callback  # ✓ Accepts callback
```

**File: `src/unified_citation_processor_v2.py` (Line 209-215)**
```python
def _update_progress(self, progress: int, step: str, message: str):
    """Update progress if callback is available."""
    if self.progress_callback and callable(self.progress_callback):
        try:
            self.progress_callback(progress, step, message)
        except Exception as e:
            logger.warning(f"Progress callback failed: {e}")
```

The progress updates are being called (lines 3589, 3593, 3756, etc.) but since `progress_callback` is `None`, they do nothing.

## Progress System Architecture

The system uses **two different progress mechanisms**:

### 1. Sync Processing (Current - Broken)
```
Frontend → API → UnifiedInputProcessor → UnifiedCitationProcessorV2(no callback) ❌
                                          ↓
                                     _update_progress() called but ignored
```

### 2. Async Processing (SSE-based)
```
Frontend → API → RQ Queue → process_citation_task_direct → progress_manager (SSE)
                                                             ↓
                                                        Redis pub/sub
                                                             ↓
                                                        Frontend SSE
```

## Why NaN%?

The frontend is expecting numeric progress values (0-100) but receiving:
- `undefined` or `null` from the sync path
- JavaScript: `undefined / 100 = NaN`

## Solution Options

### Option 1: Wire Up Progress Callback (Recommended for Sync)

Modify `unified_input_processor.py` to create and pass a progress callback:

```python
# Create progress callback that updates via SSE or API
def progress_callback(progress, step, message):
    # Send progress update to frontend
    # Could use SSE, Redis, or direct response
    pass

processor = UnifiedCitationProcessorV2(progress_callback=progress_callback)
result = asyncio.run(processor.process_text(input_data.get('text', '')))
```

### Option 2: Use Existing SSE Progress Manager

Integrate with the existing `progress_manager` module:

```python
from src.progress_manager import SSEProgressManager

progress_mgr = SSEProgressManager()

def progress_callback(progress, step, message):
    progress_mgr.update_progress(request_id, progress, step, message)

processor = UnifiedCitationProcessorV2(progress_callback=progress_callback)
```

### Option 3: Disable Progress Bar for Sync (Quick Fix)

If sync processing is fast enough, just hide the progress bar for immediate processing:

```javascript
// Frontend
if (processingMode === 'immediate') {
    // Don't show progress bar
} else {
    // Show SSE-based progress for async
}
```

## Current Behavior by Mode

### Sync Mode (< 66KB)
- ❌ Progress: No updates (NaN%)
- ✓ Speed: Fast (< 1 second typically)
- ✓ Results: Working correctly

### Async Mode (>= 66KB)
- ✓ Progress: SSE updates work
- ✓ Speed: Slower but with progress
- ✓ Results: Working correctly

## Recommendation

**For sync processing**: Since it's typically very fast (< 1 second), the simplest fix is:

1. **Frontend**: Don't show progress bar for `processing_mode: 'immediate'`
2. **Backend**: Keep current implementation (no callback needed for fast operations)

**For async processing**: Current SSE-based progress works fine.

## Implementation

### Quick Fix (Frontend Only)

```javascript
// In Vue component
if (response.metadata.processing_mode === 'immediate') {
    // Hide progress bar, show results immediately
    this.showProgress = false;
    this.results = response.citations;
} else {
    // Show SSE progress for async/queued
    this.showProgress = true;
    this.connectToSSE(response.request_id);
}
```

### Full Fix (Backend + Frontend)

If you want progress even for sync:

**Backend (`unified_input_processor.py`):**
```python
# Import progress manager
from src.progress_manager import get_progress_manager

# Create callback
progress_mgr = get_progress_manager()

def progress_callback(progress, step, message):
    progress_mgr.update_progress(request_id, progress, step, message)

# Pass to processor
processor = UnifiedCitationProcessorV2(progress_callback=progress_callback)
```

**Frontend:** No changes needed if using existing SSE connection.

## Files Involved

1. **`src/unified_input_processor.py`** - Instantiates processor without callback
2. **`src/unified_citation_processor_v2.py`** - Has progress support but callback is None
3. **`src/progress_manager.py`** - SSE-based progress system (async only)
4. **Frontend Vue component** - Displays progress bar

## Testing

After implementing fix:

```python
# Test sync with progress
result = processor.process_any_input(
    input_data={'type': 'text', 'text': 'short text'},
    input_type='text',
    request_id='test-123',
    force_mode='sync'
)
# Should see progress updates: 10%, 30%, 60%, 70%, 100%
```

## Current Status

- ✅ Citation extraction: Working
- ✅ Sync processing: Working (but no progress)
- ✅ Async processing: Working (with progress)
- ❌ Sync progress bar: Shows NaN%

**Impact**: Low - sync is fast enough that progress isn't critical, but UX could be improved.
