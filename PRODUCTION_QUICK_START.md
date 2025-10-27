# CaseStrainer - Production Quick Start Guide

**Status**: ✅ **PRODUCTION READY**  
**Last Updated**: October 10, 2025

---

## 🚀 Quick Commands

### Start the System
```bash
./cslaunch
```

### Check System Health
```bash
# API health check
curl -k https://wolf.law.uw.edu/casestrainer/api/health

# Docker status
docker ps --filter "name=casestrainer"
```

### View Logs
```bash
# Backend logs
docker logs casestrainer-backend-prod --tail 50

# Nginx logs
Get-Content logs/nginx/error.log -Tail 50

# Application logs
Get-Content logs/casestrainer.log -Tail 100
```

### Restart Services
```bash
# Full restart (if needed)
./cslaunch

# Restart individual services
docker restart casestrainer-nginx-prod
docker restart casestrainer-backend-prod
```

### Clear Cache (If Needed)
```bash
docker exec casestrainer-redis-prod redis-cli FLUSHALL
```

---

## 📊 System Capabilities

### Supported Document Types
- ✅ PDF briefs (up to 1.9 MB tested)
- ✅ Legal opinions
- ✅ Documents with Tables of Authorities
- ✅ Documents with 200+ citations

### Processing Times
- **Small documents** (< 500 KB): ~180 seconds
- **Medium documents** (500 KB - 1 MB): ~300 seconds
- **Large documents** (1-2 MB): ~550 seconds
- **Maximum timeout**: 600 seconds (10 minutes)

### Quality Metrics
- **Clustering Accuracy**: 100% (0% mixed clusters)
- **Header Contamination**: 1%
- **Case Name Extraction**: 96% accuracy
- **N/A Extraction Rate**: 4% (edge cases)

---

## 🔧 Key Configuration Files

### Nginx Timeout Configuration
**File**: `nginx/conf.d/casestrainer.conf`
```nginx
proxy_read_timeout 600s;  # 10 minutes for large briefs
proxy_connect_timeout 60s;
proxy_send_timeout 600s;
```

### Backend API Timeouts
**File**: `src/unified_verification_master.py`
- CourtListener API timeout: **20 seconds**
- Search API timeout: **20 seconds**

### Clustering Configuration
**File**: `src/unified_clustering_master.py`
- Similarity threshold: **0.95**
- Proximity threshold: **200 characters**

---

## ⚠️ Troubleshooting

### Issue: Large files returning 404
**Cause**: Nginx timeout too short  
**Solution**: Verify `proxy_read_timeout 600s` in nginx config, restart nginx

### Issue: Header contamination in extractions
**Cause**: Fix #67 not applied  
**Solution**: Verify `_filter_header_contamination()` is in `src/unified_case_extraction_master.py`

### Issue: Citations from different cases in same cluster
**Cause**: Fix #58 not applied  
**Solution**: Verify `src/unified_clustering_master.py` uses extracted names only

### Issue: Wrong jurisdiction verifications
**Cause**: Fix #60 not applied  
**Solution**: Verify `_validate_jurisdiction_match()` in `src/unified_verification_master.py`

### Issue: Slow processing
**Cause**: CourtListener API latency (normal)  
**Check**: View backend logs for API response times  
**Note**: Processing times of 5-10 minutes for large documents are expected

---

## 📈 Testing

### Test with Sample Brief
```bash
python test_wa_briefs.py
```

### Manual API Test
```bash
python -c "import requests; filepath = r'D:\dev\casestrainer\wa_briefs\018_Plaintiff Opening Brief.pdf'; files = {'file': ('test.pdf', open(filepath, 'rb'), 'application/pdf')}; data = {'force_mode': 'sync'}; r = requests.post('https://wolf.law.uw.edu/casestrainer/api/analyze', files=files, data=data, verify=False, timeout=600); print(f'Status: {r.status_code}')"
```

---

## 📚 Documentation

### Comprehensive Documentation
- **FINAL_SESSION_SUMMARY.md**: Complete session summary with all fixes
- **QUALITY_ASSESSMENT_018.md**: Detailed quality analysis
- **FEATURE_EXTRACTION_COMPLETE.md**: Feature extraction documentation
- **FINAL_FIX_SUMMARY.md**: Previous fix documentation

### Key Code Files
- **Extraction**: `src/unified_case_extraction_master.py`
- **Clustering**: `src/unified_clustering_master.py`
- **Verification**: `src/unified_verification_master.py`
- **Processing**: `src/unified_citation_processor_v2.py`
- **API Endpoints**: `src/vue_api_endpoints.py`

---

## ✅ Production Checklist

Before deploying updates:
- [ ] Test with `test_wa_briefs.py`
- [ ] Check logs for errors
- [ ] Verify Docker containers healthy
- [ ] Test API health endpoint
- [ ] Clear Redis cache if needed
- [ ] Monitor processing times
- [ ] Check nginx error logs

---

## 🎯 Performance Expectations

### Normal Operations
- **Response Time**: 180-600 seconds depending on document size
- **Memory Usage**: ~200 MB per request
- **Error Rate**: < 1%
- **Clustering Accuracy**: 100%

### When to Investigate
- ⚠️ Response times > 600 seconds
- ⚠️ 404 errors on uploads
- ⚠️ Memory usage > 500 MB per container
- ⚠️ Mixed clusters in results
- ⚠️ Header contamination > 5%

---

## 🏆 Success Criteria Met

- ✅ 100% clustering accuracy (0% mixed clusters)
- ✅ 99% header contamination prevention
- ✅ 96% case name extraction accuracy
- ✅ 100% test suite success (4/4 WA briefs)
- ✅ Timeout handling for large documents
- ✅ Multi-source verification working
- ✅ Jurisdiction filtering operational

---

**System Status**: ✅ **PRODUCTION READY**

**Support**: See `FINAL_SESSION_SUMMARY.md` for detailed troubleshooting








