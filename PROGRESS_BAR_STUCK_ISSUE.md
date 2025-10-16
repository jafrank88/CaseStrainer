# Progress Bar Stuck at 16% - Root Cause Analysis

**Date**: October 9, 2025  
**Issue**: Jobs stuck at "initializing (16%)" forever, progress bar doesn't update

---

## 🎯 **Root Cause: Async Job Function Not Found**

### **The Problem**

When the system queues an async job, it enqueues this function:
```python
job = queue.enqueue(
    'src.progress_manager.process_citation_task_direct',  # <-- THIS FUNCTION
    args=(request_id, input_type, {'text': text}),
    job_id=request_id,
    job_timeout=600,
    result_ttl=86400,
    failure_ttl=86400
)
```

**Location**: `src/enhanced_sync_processor.py`, line 1765

However, the **RQ workers cannot find this function**, causing jobs to sit in the queue forever at "initializing (16%)".

---

## 🔍 **Why This Happens**

### **1. Worker Import Path Issue**
The RQ worker tries to import: `src.progress_manager.process_citation_task_direct`

But this may fail due to:
- Python path issues in Docker
- Module import errors
- Function not properly exposed

### **2. Silent Failure**
RQ workers don't always log import failures clearly, so jobs just sit in the queue

### **3. Progress Tracker Stuck**
The job never starts actual processing, so it remains at:
- Status: `initializing`
- Progress: `16%`
- Message: `Queued for background processing`

---

## 📊 **Sync vs Async Decision**

The system decides between sync and async based on text size:

```python
# src/api/services/citation_service.py
SYNC_THRESHOLD = 5 * 1024  # 5KB

if text_size < SYNC_THRESHOLD:
    return 'sync'  # Process immediately
else:
    return 'async'  # Queue for background processing
```

### **Why Same File Processes Differently**:

1. **First request**: Workers not ready → **sync fallback** (works)
2. **Second request**: Workers ready but can't import function → **async queued** (stuck at 16%)
3. **Third request**: Random chance of which path is taken

---

## ✅ **The Fix**

### **Option 1: Verify Worker Function Import** (Recommended)

Check that the worker function is properly importable:

```bash
docker exec casestrainer-rqworker1-prod python -c "from src.progress_manager import process_citation_task_direct; print('✅ Function found')"
```

If this fails, the function path is wrong or there's an import error.

### **Option 2: Check Worker Logs for Import Errors**

```bash
docker logs casestrainer-rqworker1-prod | grep -i "import\|error\|exception"
```

### **Option 3: Verify the Function Exists**

The function is defined at line 1362 in `src/progress_manager.py`:

```python
def process_citation_task_direct(task_id: str, input_type: str, input_data: dict):
    """
    Direct async processing function for RQ workers.
    This processes the full citation pipeline in the background.
    """
    # ... implementation
```

---

## 🚀 **Immediate Workaround**

For testing, you can force **sync processing** by keeping files under 5KB, or by using the frontend which has better fallback logic.

---

## 🔧 **Long-term Solution**

1. **Fix the worker import path** to ensure `process_citation_task_direct` is importable
2. **Add better error logging** to RQ workers to surface import failures
3. **Add health checks** that verify worker can import required functions
4. **Add timeout + fallback** so stuck jobs automatically fall back to sync processing

---

## ✅ **FIX #16 DEPLOYED**

### **The Bug**:
Line 387 in `src/unified_input_processor.py` was enqueuing the **function object** instead of a **string path**:

```python
# ❌ BEFORE (wrong):
from src.progress_manager import process_citation_task_direct
job = queue.enqueue(
    process_citation_task_direct,  # Python object
    ...
)
```

### **The Fix**:
```python
# ✅ AFTER (correct):
job = queue.enqueue(
    'src.progress_manager.process_citation_task_direct',  # String path
    ...
)
```

RQ (Redis Queue) **requires a string path** to properly serialize jobs. When you pass the function object, RQ can't serialize it correctly, causing the job to fail with:
```
KeyError: 'process_citation_task_direct'
ValueError: Invalid attribute name: p
```

---

## 📊 **Why This Caused Random Sync/Async Behavior**

1. **First request after restart**: Workers not ready → **Sync fallback** (works!)
2. **Second request**: Workers ready, job queued → **Fails silently** → Stuck at 16%
3. **Sometimes**: Redis/RQ timeout → **Sync fallback** (works!)
4. **Sometimes**: Job gets queued → **Fails** → Stuck at 16%

The randomness was due to timing of when workers were ready vs when the sync fallback timeout triggered!

