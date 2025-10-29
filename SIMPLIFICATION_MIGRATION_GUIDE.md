# CaseStrainer Simplification Migration Guide

## Overview
This guide provides a step-by-step approach to migrate from the current complex citation processing system to the simplified unified processor.

## Current State Analysis

### Issues Identified
1. **7 different locations** calling `extract_citations_with_clustering()`
2. **3 different processors** (UnifiedInputProcessor, CitationProcessor, ChunkedCitationProcessor)
3. **Duplicate code paths** for sync/async processing
4. **Hardcoded verification flag** in multiple files
5. **Complex routing** through multiple layers

### Files Requiring Changes
- `src/vue_api_endpoints.py` - API endpoints
- `src/unified_input_processor.py` - Main processor
- `src/rq_worker.py` - Worker logic
- `src/progress_manager.py` - Alternative worker logic
- `src/services/citation_service.py` - Service layer

## Migration Strategy

### Phase 1: Implementation (Week 1)
1. ✅ Create `SimplifiedCitationProcessor` class
2. ✅ Implement unified entry point
3. ✅ Add configuration-driven behavior
4. ⭕ Create comprehensive tests

### Phase 2: Parallel Deployment (Week 2)
1. Deploy new processor alongside existing
2. Add feature flag to control routing
3. Monitor performance and accuracy
4. Collect feedback

### Phase 3: Gradual Migration (Week 3-4)
1. Route 10% of traffic to new processor
2. Route 50% of traffic to new processor
3. Route 100% of traffic to new processor
4. Remove old code paths

### Phase 4: Cleanup (Week 5)
1. Remove deprecated processors
2. Clean up unused imports
3. Update documentation
4. Archive old code

## Implementation Steps

### Step 1: Add Feature Flag
```python
# In src/config.py
USE_SIMPLIFIED_PROCESSOR = os.getenv('USE_SIMPLIFIED_PROCESSOR', 'false').lower() == 'true'
SIMPLIFIED_PROCESSOR_PERCENTAGE = float(os.getenv('SIMPLIFIED_PROCESSOR_PERCENTAGE', '0'))
```

### Step 2: Update API Endpoints
```python
# In src/vue_api_endpoints.py
from src.simplified_citation_processor import create_processor
from src.config import USE_SIMPLIFIED_PROCESSOR, SIMPLIFIED_PROCESSOR_PERCENTAGE
import random

@vue_api.route('/analyze', methods=['POST'])
def analyze_text():
    # Check if we should use simplified processor
    if USE_SIMPLIFIED_PROCESSOR or random.random() < SIMPLIFIED_PROCESSOR_PERCENTAGE:
        return _analyze_with_simplified_processor()
    else:
        return _analyze_with_legacy_processor()

def _analyze_with_simplified_processor():
    processor = create_processor(
        enable_verification=request.json.get('enable_verification', True),
        cache_results=True,
        async_threshold_kb=5
    )
    
    input_data = {
        'type': 'text',
        'text': request.json.get('text', '')
    }
    
    result = processor.process(input_data, request_id)
    
    if result.mode == ProcessingMode.ASYNCHRONOUS:
        return jsonify({
            'status': 'processing',
            'task_id': result.task_id,
            'message': 'Processing started asynchronously'
        })
    else:
        return jsonify({
            'status': 'completed',
            'result': {
                'citations': result.citations,
                'clusters': result.clusters
            }
        })
```

### Step 3: Update Worker
```python
# In src/rq_worker.py
from src.simplified_citation_processor import _process_async_task

def process_citation_task_direct(task_id: str, input_type: str, input_data: dict):
    """Simplified worker function."""
    # Extract configuration from input_data
    config = ProcessingConfig(
        enable_verification=input_data.get('enable_verification', True),
        timeout_seconds=600
    )
    
    # Process using simplified task function
    result = _process_async_task(
        text=input_data.get('text', ''),
        config=config,
        request_id=task_id
    )
    
    return result
```

### Step 4: Update Progress Tracking
```python
# In src/simplified_citation_processor.py
def _create_progress_callback(request_id: str):
    """Create a progress callback that updates Redis."""
    def progress_callback(percent: int, message: str):
        from src.progress_manager import sync_progress_to_redis
        sync_progress_to_redis(
            status='processing',
            progress_pct=percent,
            message=message
        )
    return progress_callback
```

## Testing Strategy

### Unit Tests
```python
# tests/test_simplified_processor.py
import pytest
from src.simplified_citation_processor import SimplifiedCitationProcessor, ProcessingConfig

def test_synchronous_processing():
    processor = SimplifiedCitationProcessor(
        ProcessingConfig(enable_verification=False)
    )
    
    input_data = {
        'type': 'text',
        'text': 'In Smith v. Jones, 123 U.S. 456 (2020), the court ruled.'
    }
    
    result = processor.process(input_data, 'test-123')
    
    assert result.mode == ProcessingMode.SYNCHRONOUS
    assert len(result.citations) > 0
    assert result.verification_results is None

def test_asynchronous_processing():
    processor = SimplifiedCitationProcessor(
        ProcessingConfig(async_threshold_kb=1)  # Low threshold for testing
    )
    
    large_text = "In Smith v. Jones, 123 U.S. 456 (2020), " * 1000  # Large text
    input_data = {
        'type': 'text',
        'text': large_text
    }
    
    result = processor.process(input_data, 'test-456')
    
    assert result.mode == ProcessingMode.ASYNCHRONOUS
    assert result.task_id is not None
```

### Integration Tests
```python
# tests/test_integration.py
def test_api_compatibility():
    """Test that the new API produces the same results as the old API."""
    # Send same request to both endpoints
    # Compare results
    pass

def test_performance_comparison():
    """Compare performance between old and new processors."""
    import time
    
    # Test with various document sizes
    # Measure processing time
    # Verify accuracy is maintained
    pass
```

### Load Testing
```python
# tests/test_load.py
def test_concurrent_requests():
    """Test system under load."""
    import concurrent.futures
    
    def make_request():
        # Simulate API request
        pass
    
    # Run 100 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [f.result() for f in futures]
    
    # Verify all requests completed successfully
    assert all(r['status'] == 'completed' for r in results)
```

## Rollback Plan

### Immediate Rollback
1. Set environment variable: `USE_SIMPLIFIED_PROCESSOR=false`
2. Restart services
3. System reverts to legacy processor

### Monitoring During Migration
```python
# Add monitoring to track metrics
class MigrationMonitor:
    def __init__(self):
        self.metrics = {
            'requests_processed': 0,
            'errors': 0,
            'avg_processing_time': 0,
            'accuracy_score': 0
        }
    
    def record_request(self, processor_type: str, success: bool, duration: float):
        self.metrics['requests_processed'] += 1
        if not success:
            self.metrics['errors'] += 1
        # Update other metrics
```

## Benefits Realization

### Expected Improvements
1. **50% reduction in code complexity** - Single processor instead of 3
2. **30% faster development** - Changes in one place
3. **25% better performance** - Eliminate duplicate processing
4. **90% easier testing** - Single entry point
5. **100% configuration clarity** - All options documented

### Success Metrics
- [ ] Code coverage > 90%
- [ ] Processing time reduced by 20%
- [ ] Error rate reduced by 50%
- [ ] Developer satisfaction score > 8/10

## Timeline

| Week | Milestone | Status |
|------|----------|--------|
| 1 | Core implementation | ✅ Complete |
| 2 | Parallel deployment | 🔄 In Progress |
| 3 | 50% traffic migration | ⏳ Pending |
| 4 | 100% traffic migration | ⏳ Pending |
| 5 | Cleanup and documentation | ⏳ Pending |

## Next Steps

1. **Review and approve** the simplified processor design
2. **Set up feature flags** in production
3. **Create comprehensive test suite**
4. **Deploy to staging** for testing
5. **Begin gradual migration** with 10% traffic
6. **Monitor and iterate** based on feedback

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance regression | Low | High | Comprehensive benchmarking |
| Accuracy loss | Low | High | A/B testing with known documents |
| Deployment issues | Medium | Medium | Feature flags and rollback plan |
| User resistance | Low | Medium | Clear communication and training |

This migration plan ensures a smooth transition from the complex current system to a simplified, maintainable solution.
