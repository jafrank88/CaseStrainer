# CaseStrainer Troubleshooting Guide

This guide covers common issues encountered when deploying and running CaseStrainer, along with their solutions.

## Quick Diagnostic Commands

```powershell
# Check all container status
docker ps

# Check Docker Compose services
docker-compose -f docker-compose.prod.yml ps

# Check backend health
curl http://localhost:5001/casestrainer/api/health

# Check Redis connection
docker exec casestrainer-redis-prod redis-cli ping

# Check frontend accessibility
curl http://localhost:8080/casestrainer/
```

## Common Issues and Solutions

### 1. Frontend 404 Errors

**Symptoms:**
- Browser shows 404 error when accessing `https://localhost/casestrainer/`
- Console shows "Failed to load resource: the server responded with a status of 404"

**Causes:**
- Frontend container not running
- Nginx configuration routing issues
- Frontend assets not built correctly
- Container networking problems

**Solutions:**

#### A. Check Container Status
```powershell
docker ps | findstr frontend
```

#### B. Rebuild Frontend Container
```powershell
docker-compose -f docker-compose.prod.yml build frontend-prod
docker-compose -f docker-compose.prod.yml up -d frontend-prod
```

#### C. Check Nginx Configuration
```powershell
docker logs casestrainer-nginx-prod --tail 20
```

#### D. Restart Nginx
```powershell
docker restart casestrainer-nginx-prod
```

### 2. Assets Not Loading (JS/CSS 404)

**Symptoms:**
- Main page loads but JavaScript and CSS files fail to load
- Console shows 404 errors for files like `index-BKS0pzKA.js`

**Causes:**
- Nginx not routing `/assets/` requests to frontend container
- Frontend build not configured for correct base path
- Asset paths in HTML don't match Nginx routing

**Solutions:**

#### A. Check Nginx Asset Routing
Verify that `nginx/conf.d/ssl.conf` includes:
```nginx
location /assets/ {
    proxy_pass http://casestrainer-frontend-prod:80;
    # ... other settings
}
```

#### B. Rebuild Frontend with Correct Base Path
```powershell
cd casestrainer-vue-new
$env:VITE_APP_ENV = "production"
npm run build
cd ..
docker-compose -f docker-compose.prod.yml build frontend-prod
```

#### C. Restart Nginx
```powershell
docker restart casestrainer-nginx-prod
```

### 3. Backend 500 Errors

**Symptoms:**
- API calls return 500 Internal Server Error
- Citation analysis fails
- Console shows "Request failed with status code 500"

**Causes:**
- Redis container stopped
- Backend can't connect to Redis
- Missing dependencies in backend container
- Environment variable issues

**Solutions:**

#### A. Check Redis Status
```powershell
docker ps | findstr redis
```

#### B. Start Redis Container
```powershell
docker start casestrainer-redis-prod
```

#### C. Check Backend Logs
```powershell
docker logs casestrainer-backend-prod --tail 50
```

#### D. Rebuild Backend Container
```powershell
docker-compose -f docker-compose.prod.yml build backend
docker-compose -f docker-compose.prod.yml up -d backend
```

### 4. Frontend Stuck on "Waiting for backend"

**Symptoms:**
- Frontend container logs show "Waiting for backend to be resolvable..."
- Frontend never starts serving content
- Infinite loop in container startup

**Causes:**
- Container networking issues
- Incorrect backend hostname in wait script
- Backend container not accessible from frontend

**Solutions:**

#### A. Check Wait Script Configuration
Verify that `casestrainer-vue-new/wait-for-backend.sh` contains:
```bash
until getent hosts casestrainer-backend-prod; do
  echo "Waiting for backend to be resolvable..."
  sleep 2
done
```

#### B. Rebuild Frontend Container
```powershell
docker-compose -f docker-compose.prod.yml build frontend-prod
docker-compose -f docker-compose.prod.yml up -d frontend-prod
```

#### C. Alternative: Remove Wait Script
Edit `casestrainer-vue-new/Dockerfile.prod` and change:
```dockerfile
CMD ["/wait-for-backend.sh"]
```
To:
```dockerfile
CMD ["nginx", "-g", "daemon off;"]
```

### 5. Parallel Citations Not Appearing

**Symptoms:**
- Citation analysis works but parallel citations don't display
- Only primary citations show, no parallel citations like "302 P.3d 156"
- Backend returns parallel citations in `parallels` array but frontend doesn't show them

**Causes:**
- Frontend not processing the `parallels` arrays within citation objects
- Backend container using old code without parallel citations fix
- Frontend container using old code without parallel citations processing

**Solutions:**

#### A. Rebuild Frontend Container (Fixed in v1.2.0)
```powershell
docker-compose -f docker-compose.prod.yml build frontend-prod
docker-compose -f docker-compose.prod.yml up -d frontend-prod
```

#### B. Rebuild Backend Container (Fixed in v1.2.0)
```powershell
docker-compose -f docker-compose.prod.yml build backend
docker-compose -f docker-compose.prod.yml up -d backend
```

#### C. Verify Backend Code
Check that `src/vue_api_endpoints.py` contains the parallel citations fix (lines 825-835).

#### D. Verify Frontend Code
Check that `casestrainer-vue-new/src/components/CitationResults.vue` contains the parallel citations processing logic (lines 613-640).

### 6. Missing Extracted Case Names and Dates

**Symptoms:**
- Citation analysis works but `extracted_case_name` and `extracted_date` fields are empty
- No `hinted_case_name` values in the results
- Backend not using enhanced extraction logic

**Causes:**
- Backend using `ComplexCitationIntegrator` instead of enhanced extraction
- Missing case name and date extraction parameters in verification calls
- Frontend not displaying extracted information correctly

**Solutions:**

#### A. Rebuild Backend Container (Fixed in v1.2.0)
```powershell
docker-compose -f docker-compose.prod.yml build backend
docker-compose -f docker-compose.prod.yml up -d backend
```

#### B. Verify Backend Code
Check that `src/document_processing.py` uses the enhanced extraction logic instead of `ComplexCitationIntegrator`.

#### C. Check Extraction Parameters
Verify that `verify_citation_unified_workflow` is called with `extracted_case_name` and `extracted_date` parameters.

### 7. SSL Certificate Issues

**Symptoms:**
- Browser shows SSL certificate warnings
- HTTPS redirects not working
- Mixed content warnings

**Causes:**
- SSL certificates not found or expired
- Incorrect certificate paths in Nginx configuration

**Solutions:**

#### A. Check Certificate Files
```powershell
ls ssl/
ls nginx/ssl/
```

#### B. Verify Nginx SSL Configuration
Check that `nginx/conf.d/ssl.conf` has correct certificate paths:
```nginx
ssl_certificate /etc/nginx/ssl/WolfCertBundle.crt;
ssl_certificate_key /etc/nginx/ssl/wolf.law.uw.edu.key;
```

#### C. Restart Nginx
```powershell
docker restart casestrainer-nginx-prod
```

## Container-Specific Issues

### Redis Container Issues

```powershell
# Check Redis logs
docker logs casestrainer-redis-prod

# Test Redis connection
docker exec casestrainer-redis-prod redis-cli ping

# Restart Redis
docker restart casestrainer-redis-prod
```

### Backend Container Issues

```powershell
# Check backend logs
docker logs casestrainer-backend-prod

# Test backend health
curl http://localhost:5001/casestrainer/api/health

# Restart backend
docker restart casestrainer-backend-prod
```

### Frontend Container Issues

```powershell
# Check frontend logs
docker logs casestrainer-frontend-prod

# Test frontend directly
curl http://localhost:8080/casestrainer/

# Restart frontend
docker restart casestrainer-frontend-prod
```

### Nginx Container Issues

```powershell
# Check Nginx logs
docker logs casestrainer-nginx-prod

# Test Nginx configuration
docker exec casestrainer-nginx-prod nginx -t

# Restart Nginx
docker restart casestrainer-nginx-prod
```

## Complete Reset Procedure

If all else fails, perform a complete reset:

```powershell
# Stop all containers
docker-compose -f docker-compose.prod.yml down

# Remove all containers and volumes
docker-compose -f docker-compose.prod.yml down -v

# Rebuild everything
docker-compose -f docker-compose.prod.yml up -d --build

# Or use the launcher
.\launcher.ps1 -Environment DockerProduction
```

## Recent Fixes (v1.2.0)

### Parallel Citations Fix
- **Issue**: Frontend not displaying parallel citations from backend `parallels` arrays
- **Fix**: Updated `CitationResults.vue` to process `parallels` arrays within citation objects
- **Files**: `casestrainer-vue-new/src/components/CitationResults.vue`

### Case Name and Date Extraction Fix
- **Issue**: Backend not using enhanced extraction logic for case names and dates
- **Fix**: Replaced `ComplexCitationIntegrator` with proper `CitationExtractor` and `EnhancedMultiSourceVerifier`
- **Files**: `src/document_processing.py`

### Nginx Asset Routing Fix
- **Issue**: Frontend assets (JS/CSS) returning 404 errors
- **Fix**: Added proper `/assets/` routing in Nginx configuration
- **Files**: `nginx/conf.d/ssl.conf`

## Getting Help

If you encounter issues not covered in this guide:

1. **Check the logs** for specific error messages
2. **Verify container status** with `docker ps`
3. **Test individual components** using the diagnostic commands above
4. **Check the main deployment guide** for additional information
5. **Contact the system administrator** with specific error messages and logs 