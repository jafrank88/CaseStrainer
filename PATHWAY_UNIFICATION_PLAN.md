# Pathway Unification Plan

## Executive Summary

**Problem**: CaseStrainer has duplicate sync/async processing pathways that cause bugs (like the citation serialization issue we just fixed) and maintenance overhead.

**Solution**: Consolidate to a single processing pipeline that can run either immediately or queued, but uses the same code path.

---

## Current Architecture (BEFORE)

### Processing Entry Points
1. **Short text (<5000 chars)**: `citation_service.process_immediately()` → Sync
2. **Long text/files**: `unified_input_processor.process_any_input()` → Async via RQ

### Clustering Systems (DUPLICATE CODE!)
1. **Sync**: `unified_clustering_master.py` → `UnifiedClusteringMaster`
2. **Async**: `unified_citation_clustering.py` → `UnifiedCitationClusterer`

### Processing Pipelines
1. **Sync**: `UnifiedCitationProcessorV2.process_text()` called via `asyncio.run()`
2. **Async**: Same `UnifiedCitationProcessorV2.process_text()` called via RQ worker

**ISSUE**: Despite using the same processor, the clustering step diverges!

---

## Target Architecture (AFTER)

```
Input → UnifiedCitationProcessorV2.process_text()
                     ↓
        UnifiedClusteringMaster.cluster_citations()
                     ↓
              Serialized Output
                     ↓
        ┌────────────┴────────────┐
    Immediate                 Queued (RQ)
   (small text)              (large files)
```

**Key Principle**: Same pipeline, different execution context.

---

## Step-by-Step Migration Plan

### Phase 1: Consolidate Clustering (HIGH PRIORITY)

**Goal**: Remove duplicate clustering system

#### 1.1 Verify UnifiedClusteringMaster is Complete
- [x] Check it has all features from UnifiedCitationClusterer
- [x] Verify citation serialization (we just fixed this!)
- [ ] Test parallel citation handling
- [ ] Test verification integration

#### 1.2 Update All Callers
**File**: `unified_citation_processor_v2.py`
- Line 3852: Already uses `cluster_citations_unified_master()` ✅
- Keep this as-is

**File**: `unified_input_processor.py`
- Search for calls to old clustering functions
- Replace with `cluster_citations_unified_master()`

#### 1.3 Remove Old Clustering Code
**File**: `unified_citation_clustering.py`
- Mark as DEPRECATED
- Add warning at top: "⚠️ DEPRECATED: Use unified_clustering_master.py"
- Schedule for deletion after validation

**Validation**: Run full test suite, verify no regressions

---

### Phase 2: Simplify Entry Points (MEDIUM PRIORITY)

**Goal**: Remove artificial sync/async distinction

#### 2.1 Update citation_service.py

**Current**:
```python
def process_immediately(self, input_data):
    # Special "sync" handling
    result = asyncio.run(processor.process_text(text))
    return result
```

**After**:
```python
async def process_text_unified(self, text: str):
    """Single processing method for all text"""
    processor = UnifiedCitationProcessorV2()
    return await processor.process_text(text)

def process_sync(self, text: str):
    """Synchronous wrapper for immediate processing"""
    return asyncio.run(self.process_text_unified(text))

def process_async(self, text: str, request_id: str):
    """Queue for background processing"""
    from src.rq_worker import enqueue_citation_task
    return enqueue_citation_task(text, request_id)
```

#### 2.2 Update vue_api_endpoints_updated.py

**Line 307-321**: Remove duplicate immediate processing branches

**Before**:
```python
if service.should_process_immediately(input_dict):
    logger.info("Processing JSON text immediately")
    result = service.process_immediately(input_dict)
    return _format_response(result, ...)
```

**After**:
```python
# Always use the same processing logic
if len(text) < 5000:  # Immediate threshold
    result = service.process_sync(text)
else:
    task_id = service.process_async(text, request_id)
    return {"task_id": task_id, "status": "queued"}
```

---

### Phase 3: Standardize Serialization (CRITICAL)

**Goal**: Ensure all outputs are consistently serialized

#### 3.1 Create Unified Serialization Function

**New File**: `unified_serialization.py`
```python
def serialize_citation(citation) -> dict:
    """Single source of truth for citation serialization"""
    if isinstance(citation, dict):
        return citation
    
    return {
        'citation': getattr(citation, 'citation', ''),
        'extracted_case_name': getattr(citation, 'extracted_case_name', None),
        'extracted_date': getattr(citation, 'extracted_date', None),
        'canonical_name': getattr(citation, 'canonical_name', None),
        'canonical_date': getattr(citation, 'canonical_date', None),
        'canonical_url': getattr(citation, 'canonical_url', None),
        'verified': getattr(citation, 'verified', False),
        'true_by_parallel': getattr(citation, 'true_by_parallel', False),
        'verification_source': getattr(citation, 'verification_source', None),
        'confidence': getattr(citation, 'confidence', None),
        'method': getattr(citation, 'method', None),
        'source': getattr(citation, 'source', None),
        'cluster_id': getattr(citation, 'cluster_id', None),
        'cluster_case_name': getattr(citation, 'cluster_case_name', None),
        'is_cluster': getattr(citation, 'is_cluster', False),
        'start_index': getattr(citation, 'start_index', None),
        'end_index': getattr(citation, 'end_index', None),
    }

def serialize_cluster(cluster) -> dict:
    """Single source of truth for cluster serialization"""
    citations = cluster.get('citations', [])
    return {
        'cluster_id': cluster.get('cluster_id'),
        'case_name': cluster.get('case_name', 'N/A'),
        'extracted_case_name': cluster.get('extracted_case_name'),
        'extracted_date': cluster.get('extracted_date'),
        'year': cluster.get('year'),
        'canonical_name': cluster.get('canonical_name'),
        'canonical_date': cluster.get('canonical_date'),
        'canonical_url': cluster.get('canonical_url'),
        'size': len(citations),
        'citations': [serialize_citation(c) for c in citations],
        'verified': cluster.get('verified', False),
    }
```

#### 3.2 Update All Serialization Points

**File**: `unified_clustering_master.py` (line 2454-2476)
- Replace inline serialization with `serialize_citation()`

**File**: `unified_citation_clustering.py` (if kept temporarily)
- Replace inline serialization with `serialize_citation()`

**File**: `unified_citation_processor_v2.py`
- Add final serialization before return

---

### Phase 4: Remove Redundant Code (LOW PRIORITY)

**Goal**: Delete deprecated code after validation

#### Files to Remove (After Phase 1-3 Complete)
- [ ] `unified_citation_clustering.py` (replaced by unified_clustering_master.py)
- [ ] Old clustering helper functions scattered across codebase
- [ ] Duplicate serialization code

#### Files to Keep & Enhance
- [x] `unified_citation_processor_v2.py` - Main processing pipeline
- [x] `unified_clustering_master.py` - Single clustering system
- [x] `unified_case_extraction_master.py` - Case name extraction
- [ ] `unified_serialization.py` - NEW: Standardized output formatting

---

## Testing Strategy

### Unit Tests
- [ ] Test `serialize_citation()` with objects and dicts
- [ ] Test `serialize_cluster()` with various cluster types
- [ ] Test UnifiedClusteringMaster with sync pathway
- [ ] Test UnifiedClusteringMaster with async pathway

### Integration Tests
- [ ] Submit short text (sync): "Carman v. Adventure Bound, 198 Cal.App.3d 449 (1986)"
- [ ] Submit long text (async): Large PDF or multi-page document
- [ ] Verify both produce identical output structure
- [ ] Check logs: Both should show same pipeline steps

### Validation Criteria
✅ **Success** = Both pathways produce identical JSON structure  
✅ **Success** = `extracted_case_name` appears in cluster citations array  
✅ **Success** = No serialization errors in logs  
✅ **Success** = Frontend displays correctly for both pathways  

---

## Implementation Order

### Week 1: Quick Wins
1. ✅ Fix sync clustering serialization (DONE!)
2. ✅ Fix validation to handle both dicts and objects (DONE!)
3. [ ] Create `unified_serialization.py`
4. [ ] Update `unified_clustering_master.py` to use it

### Week 2: Consolidation
5. [ ] Deprecate `unified_citation_clustering.py`
6. [ ] Update all callers to use `UnifiedClusteringMaster`
7. [ ] Test sync and async pathways produce identical output

### Week 3: Cleanup
8. [ ] Remove deprecated code
9. [ ] Simplify `citation_service.py` and `vue_api_endpoints_updated.py`
10. [ ] Update documentation

---

## Risk Mitigation

### Risks
1. **Breaking existing functionality**: Async pathway might have edge cases
2. **Performance regression**: Unified code might be slower
3. **Frontend compatibility**: Changes to output structure

### Mitigations
1. **Feature flags**: Keep old code path behind flag during migration
2. **A/B testing**: Run both pathways in parallel, compare outputs
3. **Gradual rollout**: Migrate one endpoint at a time
4. **Comprehensive logging**: Log everything during transition

---

## Success Metrics

- [ ] **Code reduction**: Delete 500+ lines of duplicate code
- [ ] **Bug reduction**: Zero sync/async divergence bugs
- [ ] **Maintenance**: Single code path to maintain
- [ ] **Performance**: No regression in processing speed
- [ ] **Correctness**: 100% output structure consistency

---

## Next Immediate Actions

1. **Create `unified_serialization.py`** (30 minutes)
2. **Update `unified_clustering_master.py` to use it** (15 minutes)
3. **Test with "Carman v. Adventure Bound"** (5 minutes)
4. **Commit checkpoint**: "Standardize citation serialization"

Ready to start? 🚀
