# Troubleshooting 404 Error on /casestrainer/api/analyze

## Issue
Frontend is getting 404 Not Found when calling:
- `POST /casestrainer/api/analyze`
- `GET /casestrainer/api/analyze/progress/<request_id>`

## Root Cause
The blueprint should be registered at `/casestrainer/api`, but nginx is returning 404, suggesting:
1. Backend container is not running
2. Blueprint registration is failing
3. Nginx routing is misconfigured

## Steps to Diagnose

### 1. Check Backend Container Status
```bash
docker ps | grep backend
docker logs casestrainer-backend-prod --tail 100
```

Look for:
- Blueprint registration messages
- Any import errors
- Flask app startup messages

### 2. Check Blueprint Registration
In the backend logs, look for:
```
=== REGISTERING BLUEPRINTS ===
✅ Vue API blueprint registered successfully
=== REGISTERED ROUTES ===
```

If you see errors like:
```
❌ Error registering blueprints: ...
ImportError: Could not import Vue API blueprint
```

Then the blueprint import is failing.

### 3. Check Nginx Configuration
The nginx config should route `/casestrainer/api/*` to the backend container.

### 4. Quick Fix: Restart Backend
If the container is running but endpoints aren't working:
```bash
docker restart casestrainer-backend-prod
```

Then check logs again to see if blueprint registers.

## Expected Log Output
When working correctly, you should see:
```
=== REGISTERING BLUEPRINTS ===
✅ Successfully imported Vue API blueprint from UPDATED endpoints
✅ Vue API blueprint registered successfully
=== REGISTERED ROUTES ===
- vue_api.analyze: /casestrainer/api/analyze (POST)
- vue_api.analyze_progress: /casestrainer/api/analyze/progress/<request_id> (GET)
```

## If Blueprint Import Fails
The code tries to import from `vue_api_endpoints_updated.py` first, then falls back to `vue_api_endpoints.py`. If both fail, check:
1. File exists: `src/vue_api_endpoints_updated.py`
2. File has `vue_api` blueprint defined
3. No syntax errors in the file


