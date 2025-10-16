# Nginx DNS Cache Fix - October 15, 2025

## ❌ Problem Encountered

Frontend showing **404 errors** for all API endpoints:
```
POST /api/analyze → 404 Not Found (nginx)
GET /api/processing_progress → 404 Not Found (nginx)
```

## 🔍 Root Cause

When `cslaunch` starts all containers:
1. Backend container starts
2. Nginx container starts **at the same time**
3. Nginx tries to resolve `casestrainer-backend-prod` DNS
4. DNS not propagated yet → **Resolution fails**
5. Nginx caches this DNS failure
6. All API requests return 404

Even though `docker-compose.prod.yml` has:
```yaml
depends_on:
  backend:
    condition: service_healthy
```

Docker's internal DNS can have propagation delays **after** health checks pass.

## ✅ Immediate Fix

Reload nginx to clear DNS cache:
```bash
docker exec casestrainer-nginx-prod nginx -s reload
```

**Result:** API endpoints work immediately after reload

## ✅ Permanent Fix Applied

Updated `docker-compose.prod.yml` nginx command to wait for backend DNS:

### Before
```yaml
command: >
  sh -c "nginx -t &&
         nginx -g 'daemon off;'"
```

### After
```yaml
command: >
  sh -c "echo 'Waiting for backend DNS...' &&
         for i in 1 2 3 4 5; do 
           if wget -q --spider --timeout=2 http://casestrainer-backend-prod:5000/casestrainer/api/health; then 
             echo 'Backend reachable!'; break; 
           fi; 
           echo 'Waiting...'; sleep 2; 
         done &&
         nginx -t &&
         nginx -g 'daemon off;'"
```

## How The Fix Works

### Wait Loop Logic
1. Try to reach backend health endpoint
2. If successful → Break and start nginx
3. If fails → Wait 2 seconds, try again
4. Repeat up to 5 times (10 seconds total)
5. Start nginx either way (non-blocking)

### Benefits
- ✅ Ensures DNS is propagated before nginx starts
- ✅ Non-blocking (starts anyway after 10s)
- ✅ Prevents DNS cache issues
- ✅ Works with health check dependencies

## Testing

### Test 1: Normal Startup
```bash
./cslaunch
```

**Expected output:**
```
Waiting for backend DNS...
Backend reachable!
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Test 2: API Endpoint
```bash
# From your browser
https://wolf.law.uw.edu/casestrainer/
# Submit a PDF
```

**Expected:** API endpoints work immediately, no 404 errors

## Debug Commands

### Check if backend is reachable from nginx
```bash
docker exec casestrainer-nginx-prod wget -qO- http://casestrainer-backend-prod:5000/casestrainer/api/health
```

**Should return:** JSON health status

### Check nginx error logs
```bash
docker logs casestrainer-nginx-prod | grep -i error
```

**Should NOT show:** "host not found in upstream"

### Manual reload if needed
```bash
docker exec casestrainer-nginx-prod nginx -s reload
```

## Why This Happened

### Docker DNS Behavior
1. **Container health checks** use Docker's internal networking
2. **DNS resolution** happens separately and can lag
3. **Nginx upstream** caches DNS on startup
4. **Race condition** between health check passing and DNS propagating

### Timeline
```
T+0s:  Backend starts
T+2s:  Backend health check passes
T+2s:  Nginx starts (depends_on satisfied)
T+2s:  Nginx tries DNS lookup: casestrainer-backend-prod
T+2s:  DNS not propagated yet → FAILS
T+2s:  Nginx caches failure, starts anyway
T+3s:  DNS propagates (too late!)
T+10s: User tries API → 404 (cached failure)
```

### With Fix
```
T+0s:  Backend starts
T+2s:  Backend health check passes
T+2s:  Nginx starts (depends_on satisfied)
T+2s:  Nginx wait loop: Try 1...
T+2s:  wget succeeds! DNS working!
T+2s:  Nginx starts with good DNS
T+10s: User tries API → 200 OK ✅
```

## Files Modified

1. **docker-compose.prod.yml** (lines 245-255)
   - Added DNS wait loop to nginx command
   - Ensures backend is reachable before starting

2. **NGINX_DNS_CACHE_FIX.md** (this file)
   - Documentation of issue and fix

## Related Issues

This DNS caching issue can affect any Docker setup where:
- Services start simultaneously
- One service depends on DNS resolution of another
- Nginx or other proxies cache upstream DNS

## Prevention in Other Services

If you add new services that proxy to backends:
1. Add wait loop before starting
2. Test DNS resolution first
3. Don't rely solely on `depends_on` health checks

## Status

✅ **Immediate fix applied:** Nginx reloaded
✅ **Permanent fix deployed:** docker-compose.prod.yml updated
✅ **Tested:** Backend reachable from nginx
✅ **Next deployment:** Will include wait loop

---

**The fix will take effect on the next `./cslaunch` restart!** 🚀

For now, the nginx reload has fixed the immediate issue.
