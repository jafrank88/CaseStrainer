# Fix #53: Force Sync Mode Not Working

## 📅 Date
October 10, 2025

## 🎯 Problem
API endpoint ignored `force_mode='sync'` parameter when uploading files, always queuing for async processing.

## 🔍 Root Cause
**File:** `src/vue_api_endpoints.py`
**Line:** 124-128

When processing file uploads with form data, the API built the `data` dict from `request.form` but **only extracted** 3 fields:
```python
data = {
    'text': text_content,
    'url': url_content,
    'type': request.form.get('type', 'text')
    # ❌ Missing: 'force_mode'
}
```

Later, line 228 tried to read `force_mode`:
```python
force_mode = data.get('force_mode')  # ❌ Always None!
```

## ✅ Solution
Added `force_mode` extraction from form data:

```python
data = {
    'text': text_content,
    'url': url_content,
    'type': request.form.get('type', 'text'),
    'force_mode': request.form.get('force_mode')  # ✅ FIX #53
}
```

## 📊 Impact
**Before Fix #53:**
- ❌ File uploads always queued for async (even with `force_mode='sync'`)
- ❌ Cannot test sync path via API
- ❌ Users cannot override to sync mode

**After Fix #53:**
- ✅ `force_mode='sync'` will force sync processing
- ✅ Can test sync path via API
- ✅ Users have full control over processing mode

## 🧪 Testing
**Test Command:**
```python
files = {'file': ('1033940.pdf', f, 'application/pdf')}
data = {'force_mode': 'sync'}
response = requests.post(API_URL, files=files, data=data)
```

**Expected Result:**
```json
{
  "metadata": {
    "processing_mode": "immediate",  // Not "queued"!
    "sync_complete": true,
    "force_mode": "sync"
  },
  "citations": [...],  // Immediate results, not empty!
  "clusters": [...]
}
```

## 📋 Files Changed
- `src/vue_api_endpoints.py` (line 128)

## 🔗 Related Issues
- **backend-critical-3:** Force sync mode broken
- **fix52-root-cause:** Cannot test sync path where Fixes #50/#51/#52 live
- **investigate-async-path:** Need to verify fixes exist in async path

## 📝 Next Steps
1. Restart system with Fix #53
2. Test API with `force_mode='sync'`
3. Verify sync processing completes
4. Check if Fixes #50/#51/#52 execute in sync path
5. Compare sync vs async results

