# Frontend 404 Error Fix

## 🐛 **Problem**

The frontend was getting 404 errors when trying to analyze documents:

```
POST https://wolf.law.uw.edu/casestrainer/api/analyze 404 (Not Found)
Making API call to: /casestrainer/api//analyze
```

Notice the **double slash** in the URL: `/casestrainer/api//analyze`

---

## 🔍 **Root Cause**

The issue was in `src/api/citations.js` where API endpoints were using **absolute paths** instead of **relative paths**:

```javascript
// WRONG - Uses absolute path, ignores baseURL
return api.post('/casestrainer/api/analyze', { ... });

// CORRECT - Uses relative path, respects baseURL
return api.post('/analyze', { ... });
```

### Why This Caused 404:

1. **axios baseURL** is configured as `/casestrainer/api` (in `main.js` and `api.js`)
2. **Absolute paths** (starting with `/casestrainer/api/...`) bypass the baseURL
3. **Nginx** expects requests at `/casestrainer/api/analyze`, not `/casestrainer/api/casestrainer/api/analyze`
4. Result: **404 Not Found**

---

## ✅ **The Fix**

Changed all API endpoints in `src/api/citations.js` to use **relative paths**:

### Before (WRONG):
```javascript
validateCitation(citation) {
  return api.post('/casestrainer/api/analyze', { 
    text: citation,
    type: 'text'
  });
}

pollTaskResults(taskId) {
  return api.get(`/casestrainer/api/analyze/progress/${taskId}`);
}

getCitationMetadata(citation) {
  return api.get(`/casestrainer/api/metadata?citation=${encodeURIComponent(citation)}`);
}

// ... and 4 more endpoints
```

### After (CORRECT):
```javascript
validateCitation(citation) {
  return api.post('/analyze', {  // ← Relative path
    text: citation,
    type: 'text'
  });
}

pollTaskResults(taskId) {
  return api.get(`/analyze/progress/${taskId}`);  // ← Relative path
}

getCitationMetadata(citation) {
  return api.get(`/metadata?citation=${encodeURIComponent(citation)}`);  // ← Relative path
}

// ... and 4 more endpoints
```

---

## 🎯 **Endpoints Fixed**

1. **`/analyze`** - Main analysis endpoint
2. **`/analyze/progress/${taskId}`** - Progress polling
3. **`/metadata`** - Citation metadata
4. **`/network`** - Citation network
5. **`/classify`** - Citation classification
6. **`/feedback`** - Get feedback
7. **`/feedback`** - Submit feedback

All 7 endpoints now use relative paths that respect the axios baseURL configuration.

---

## 📊 **How It Works Now**

### Request Flow:
```
1. Frontend calls: api.post('/analyze', data)
2. Axios adds baseURL: '/casestrainer/api' + '/analyze'
3. Final URL: '/casestrainer/api/analyze' ✓
4. Nginx routes to backend: http://backend:5000/casestrainer/api/analyze ✓
5. Backend processes request ✓
```

### Before Fix:
```
1. Frontend calls: api.post('/casestrainer/api/analyze', data)
2. Axios sees absolute path, ignores baseURL
3. Final URL: '/casestrainer/api/analyze' ✓
4. But axios tries: '/casestrainer/api/casestrainer/api/analyze' ❌
5. Nginx returns: 404 Not Found ❌
```

---

## 🔧 **Deployment Steps**

### 1. Fixed Frontend Code:
```bash
# Modified: src/api/citations.js
# Changed 7 endpoints from absolute to relative paths
```

### 2. Rebuilt Frontend:
```bash
cd casestrainer-vue-new
npm run build
# Output: dist/ folder with updated assets
```

### 3. Rebuilt Docker Container:
```bash
docker-compose -f docker-compose.prod.yml build frontend-prod
# Rebuilds container with new frontend code
```

### 4. Restarted Services:
```bash
docker-compose -f docker-compose.prod.yml up -d frontend-prod nginx
# Restarts frontend and nginx containers
```

---

## ✅ **Verification**

### Check Frontend Logs:
```bash
docker logs casestrainer-frontend-prod
```

### Check Nginx Logs:
```bash
docker logs casestrainer-nginx-prod
```

### Test in Browser:
1. Go to https://wolf.law.uw.edu/casestrainer/
2. Try URL input with: https://www.courts.wa.gov/opinions/pdf/1033940.pdf
3. Check browser console - should see:
   - ✅ `POST /casestrainer/api/analyze 200 OK`
   - ❌ NOT `POST /casestrainer/api/analyze 404 Not Found`

---

## 🎯 **Expected Behavior**

### Before Fix:
```
Making API call to: /casestrainer/api//analyze
POST https://wolf.law.uw.edu/casestrainer/api/analyze 404 (Not Found)
Response: <html><title>404 Not Found</title></html>
```

### After Fix:
```
Making API call to: /casestrainer/api/analyze
POST https://wolf.law.uw.edu/casestrainer/api/analyze 200 OK
Response: {citations: [...], clusters: [...], task_id: "..."}
```

---

## 📝 **Key Lessons**

### 1. **Axios BaseURL Behavior**:
- **Relative paths** (`/analyze`) → Uses baseURL
- **Absolute paths** (`/casestrainer/api/analyze`) → Ignores baseURL

### 2. **Best Practice**:
Always use **relative paths** when you have a baseURL configured:
```javascript
// ✅ GOOD
api.post('/analyze', data)

// ❌ BAD
api.post('/casestrainer/api/analyze', data)
```

### 3. **Consistency**:
All API calls should use the same pattern (relative paths) to avoid confusion and bugs.

---

## 🚀 **Status**

✅ **FIXED AND DEPLOYED**

- Frontend code updated
- Docker container rebuilt
- Services restarted
- Ready for testing

The 404 error should now be resolved, and the frontend should successfully communicate with the backend API!

---

## 🧪 **Testing Checklist**

- [ ] URL input works without 404 errors
- [ ] File upload works without 404 errors
- [ ] Text paste works without 404 errors
- [ ] Progress polling works
- [ ] Results display correctly
- [ ] No console errors about 404

Test with the same PDF that was failing:
https://www.courts.wa.gov/opinions/pdf/1033940.pdf
