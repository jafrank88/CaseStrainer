# Final Fixes Plan - Issues #19, #20, #21

**Date**: October 9, 2025  
**Goal**: Address remaining quality issues

---

## 🎯 **Fix #19: Improve Extraction Quality**

### **Current Issues**:
1. Returns `None` (becomes "N/A") when no patterns match
2. Search context may be too narrow or patterns too strict
3. Extraction from wrong parts of document

### **Solutions**:
1. **Expand pattern matching**: Add more flexible patterns
2. **Increase search radius**: From 200 to 300 characters
3. **Add fallback extraction**: Use simple "X v. Y" pattern as last resort
4. **Better validation**: Check if extracted name makes sense

### **Implementation**:
```python
# In _extract_case_name_from_context():

# 1. Increase search radius
start_search = max(0, citation.start_index - 300)  # Was 200

# 2. Add fallback simple pattern as last resort
if not candidates:
    # Try simple "Word v. Word" pattern
    simple_match = re.search(r'([A-Z][\w\s&,.\']+?)\s+v\.\s+([A-Z][\w\s&,.\']+?)(?=\s*,|\s*\d)', search_text_no_parens)
    if simple_match:
        return f"{simple_match.group(1).strip()} v. {simple_match.group(2).strip()}"

# 3. Better scoring - penalize very distant matches
score = distance_from_citation
if distance_from_citation > 150:  # Case name very far from citation
    score += 100  # Heavy penalty
```

---

## 🎯 **Fix #20: Improve API Matching**

### **Current Issues**:
1. CourtListener sometimes returns wrong cases
2. No reporter/jurisdiction validation
3. No date proximity checking
4. Still 100% verification (too high, indicates low standards)

### **Solutions**:
1. **Add reporter validation**: Check if API reporter matches extracted reporter
2. **Add jurisdiction validation**: Ensure courts match
3. **Add date proximity**: Reject if dates are >5 years apart
4. **Improve scoring**: Multiple factors, not just name similarity

### **Implementation**:
```python
# In _find_best_matching_cluster_sync():

def _validate_api_match(self, cluster, citation, extracted_name, extracted_date):
    """Validate API match quality before accepting."""
    
    # 1. Reporter validation
    citation_reporter = self._extract_reporter(citation)
    cluster_reporter = cluster.get('citations', [{}])[0].get('reporter', '')
    if citation_reporter and cluster_reporter:
        if citation_reporter.lower() != cluster_reporter.lower():
            logger.warning(f"Reporter mismatch: {citation_reporter} vs {cluster_reporter}")
            return False
    
    # 2. Date proximity validation
    if extracted_date:
        cluster_date = cluster.get('date_filed', '')
        date_diff = self._calculate_year_difference(extracted_date, cluster_date)
        if date_diff > 5:
            logger.warning(f"Date too far apart: {date_diff} years")
            return False
    
    # 3. Name similarity (existing check, keep it)
    canonical_name = cluster.get('case_name', '')
    similarity = self._calculate_name_similarity(canonical_name, extracted_name)
    if similarity < 0.6:
        return False
    
    return True
```

---

## 🎯 **Fix #21: Fix Progress Bar**

### **Current Issue**:
Progress updates in async worker don't sync to Redis, so API endpoint never sees them.

### **Root Cause**:
The `progress_tracker` in `process_citation_task_direct` is a local object, not synced to Redis.

### **Solution**:
Update progress using the same Redis key that the API endpoint reads from.

### **Implementation**:
```python
# In src/progress_manager.py, process_citation_task_direct():

def update_progress_to_redis(task_id, status, progress, message):
    """Update progress directly to Redis for API consumption."""
    try:
        from redis import Redis
        redis_conn = Redis.from_url(config.REDIS_URL)
        
        progress_key = f"task_progress:{task_id}"
        progress_data = {
            'status': status,
            'overall_progress': progress,
            'current_message': message,
            'updated_at': datetime.now().isoformat()
        }
        
        redis_conn.setex(
            progress_key,
            86400,  # 24 hour expiry
            json.dumps(progress_data)
        )
        logger.info(f"Progress synced to Redis: {status} ({progress}%)")
    except Exception as e:
        logger.error(f"Failed to sync progress: {e}")

# Then call this throughout processing:
update_progress_to_redis(task_id, 'extracting', 30, 'Extracting citations...')
update_progress_to_redis(task_id, 'clustering', 50, 'Clustering citations...')
update_progress_to_redis(task_id, 'verifying', 70, 'Verifying with CourtListener...')
update_progress_to_redis(task_id, 'finalizing', 90, 'Finalizing results...')
update_progress_to_redis(task_id, 'completed', 100, 'Processing complete')
```

---

## 📊 **Expected Impact**

### **Before Fixes**:
| Metric | Current |
|--------|---------|
| "N/A" extracted names | ~15% |
| Wrong API matches | ~20% |
| Verification rate | 100% (too high) |
| Progress bar updates | 0% (stuck at 16%) |

### **After Fixes (Expected)**:
| Metric | Target |
|--------|--------|
| "N/A" extracted names | **<5%** ✅ |
| Wrong API matches | **<10%** ✅ |
| Verification rate | **70-80%** ✅ (more realistic) |
| Progress bar updates | **100%** ✅ (working) |

---

## 🚀 **Implementation Order**

1. **Fix #21 First** (Progress Bar) - Easiest, immediate user experience improvement
2. **Fix #19 Second** (Extraction) - Improves data quality for Fix #20
3. **Fix #20 Last** (API Matching) - Depends on better extraction from Fix #19

---

## ⚠️ **Risks**

- **Fix #19**: May extract more wrong names if patterns too loose
- **Fix #20**: Will reduce verification rate (this is good! but user may notice)
- **Fix #21**: Low risk, purely cosmetic

---

## ✅ **Success Criteria**

1. **Fix #19**: <5% "N/A" results, extracted names look reasonable
2. **Fix #20**: Verification rate 70-80%, fewer obviously wrong matches
3. **Fix #21**: Progress bar moves from 16% → 100%

**Let's implement these now!**


