# Frontend Caching Troubleshooting Guide

## Issue: Frontend Shows Incorrect Results Despite Correct Backend API

### Symptoms
- Frontend displays `extracted_case_name: "N/A"` or incorrect clustering
- Backend API returns correct data when tested directly
- Case names appear truncated or wrong in the web interface
- Results look identical to previous incorrect behavior

### Root Cause
The nginx configuration in `casestrainer-vue-new/nginx.conf` sets **`expires 1y`** (1 year) for JavaScript files, causing browsers to cache old JavaScript files for an entire year. Even though the backend is returning correct data, the frontend is using stale JavaScript that calls old backend APIs.

### Solution Steps

1. **Update nginx configuration**:
   ```nginx
   # In casestrainer-vue-new/nginx.conf, change:
   expires 1y;  # OLD - too aggressive
   
   # To:
   expires 1h;  # NEW - reasonable for development
   add_header Cache-Control "public, no-transform, must-revalidate";
   ```

2. **Rebuild frontend container**:
   ```powershell
   docker compose -f docker-compose.prod.yml build --no-cache frontend-prod
   ```

3. **Restart frontend container**:
   ```powershell
   docker compose -f docker-compose.prod.yml up -d frontend-prod
   ```

4. **Clear browser cache**:
   - Press `Ctrl+Shift+Delete` (Windows) or `Cmd+Shift+Delete` (Mac)
   - Or hard refresh with `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac)

### Verification
Test the API directly to confirm backend is working:
```powershell
$payload = '{"type":"text","text":"Your test text here"}'
$response = Invoke-RestMethod -Uri "https://wolf.law.uw.edu/casestrainer/api/analyze" -Method POST -Body $payload -ContentType "application/json"
$response.result.citations | ForEach-Object { Write-Host "Case: '$($_.extracted_case_name)' | Date: '$($_.extracted_date)'" }
```

### Prevention
- Use shorter cache times (`1h` instead of `1y`) for development
- Add `must-revalidate` to force cache validation
- Consider implementing cache-busting with versioned filenames for production

### Related Files
- `casestrainer-vue-new/nginx.conf` - nginx configuration
- `docker-compose.prod.yml` - container definitions
- `cslaunch.ps1` - deployment script

---
*Created: September 12, 2025*
*Issue: Frontend caching preventing latest JavaScript from loading*



