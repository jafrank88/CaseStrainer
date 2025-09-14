# CaseStrainer Deployment Checklist

This checklist ensures all components are properly updated and working after code changes.

## Pre-Deployment

- [ ] **Code Review**: All changes reviewed and approved
- [ ] **Tests Pass**: All unit tests and integration tests pass
- [ ] **Git Status**: No uncommitted changes (or intentionally committing changes)
- [ ] **Backup**: Current working state backed up

## Deployment Steps

### 1. Backend Changes
- [ ] **Detect Changes**: Check if backend files changed (`src/`, `requirements.txt`, `Dockerfile`, `docker-compose.prod.yml`)
- [ ] **Build Backend**: `docker compose -f docker-compose.prod.yml build backend`
- [ ] **Restart Backend**: `docker compose -f docker-compose.prod.yml restart backend`
- [ ] **Wait**: Allow 5 seconds for backend to start

### 2. Frontend Changes  
- [ ] **Detect Changes**: Check if frontend files changed (`casestrainer-vue-new/`, `nginx.conf`)
- [ ] **Build Frontend**: `docker compose -f docker-compose.prod.yml build frontend-prod`
- [ ] **Restart Frontend**: `docker compose -f docker-compose.prod.yml restart frontend-prod`
- [ ] **Wait**: Allow 10 seconds for frontend to start

### 3. Verification
- [ ] **API Health**: Test `/api/health_check` endpoint
- [ ] **Case Name Extraction**: Test with standard paragraph
- [ ] **Clustering**: Verify correct clustering (2 clusters, 2 citations each)
- [ ] **No N/A Values**: Ensure no extracted case names are "N/A"
- [ ] **Frontend Display**: Test web interface shows correct results

## Automated Tools

### Quick Verification
```powershell
.\scripts\verify_deployment.ps1
```

### Auto Deployment
```powershell
.\scripts\auto_deploy.ps1
```

### Integration Tests
```bash
python tests/integration_test.py
```

## Common Issues & Solutions

### Issue: Frontend shows old results
**Solution**: Rebuild and restart frontend container
```powershell
docker compose -f docker-compose.prod.yml build frontend-prod
docker compose -f docker-compose.prod.yml restart frontend-prod
```

### Issue: Backend not using latest code
**Solution**: Restart backend container
```powershell
docker compose -f docker-compose.prod.yml restart backend
```

### Issue: Case names showing as "N/A"
**Solution**: Check context window and regex patterns in `unified_extraction_architecture.py`

### Issue: Wrong clustering
**Solution**: Check `_ensure_full_names_from_master` method in `enhanced_sync_processor.py`

## Verification Test Data

Use this standard test paragraph:
```
Certified questions are questions of law that this court reviews de novo and in light
of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183
Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we
review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430 P.3d 655 (2018).
```

Expected results:
- **4 citations** with correct case names
- **2 clusters** with 2 citations each
- **No "N/A" values** in extracted case names
- **Correct clustering**: Lopez Demetrio cluster and Spokane County cluster

## Post-Deployment

- [ ] **Monitor Logs**: Check backend logs for errors
- [ ] **User Testing**: Have users test the web interface
- [ ] **Performance**: Monitor response times
- [ ] **Documentation**: Update any relevant documentation

## Emergency Rollback

If issues are detected:
1. **Stop containers**: `docker compose -f docker-compose.prod.yml down`
2. **Revert code**: `git revert <commit-hash>`
3. **Rebuild**: `docker compose -f docker-compose.prod.yml up -d`
4. **Verify**: Run verification tests
