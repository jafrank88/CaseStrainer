# Production Health Check Integration Guide

## For: wolf.law.uw.edu/casestrainer

The health check endpoint at `wolf.law.uw.edu/casestrainer/api/health` needs to include the new v2 clean pipeline status.

## Quick Integration

Add these endpoints to your Flask app (likely in `app.py` or `app_final.py`):

```python
from src.health_check_endpoint import create_health_endpoint

# Add this after creating your Flask app
create_health_endpoint(app)
```

This creates three endpoints:

### 1. Basic Health Check
**URL**: `GET /api/health`

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-13T06:21:00.000Z",
  "version": "2.0.0"
}
```

### 2. Detailed Health Check
**URL**: `GET /api/health/detailed`

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-13T06:21:00.000Z",
  "version": "2.0.0",
  "components": {
    "clean_pipeline": {
      "status": "healthy",
      "version": "v1.0.0",
      "accuracy": "87-93%"
    },
    "strict_isolator": {
      "status": "healthy",
      "version": "v1.0.0",
      "accuracy": "100% (isolation)"
    },
    "production_endpoint": {
      "status": "healthy",
      "version": "v1.0.0",
      "method": "clean_pipeline_v1"
    },
    "functional_test": {
      "status": "healthy",
      "test": "extraction",
      "citations_found": 1
    }
  }
}
```

### 3. V2 Endpoint Health
**URL**: `GET /api/v2/health`

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "version": "v2.0.0",
  "accuracy": "87-93%",
  "method": "clean_pipeline_v1",
  "case_name_bleeding": "zero",
  "test_passed": true,
  "timestamp": "2025-10-13T06:21:00.000Z"
}
```

## Docker Integration

If using Docker, add this to your Dockerfile health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/api/health || exit 1
```

## Testing Locally

Before deploying to production:

```bash
# Test health check
python test_health_endpoint.py

# Or test via HTTP (if running locally)
curl http://localhost:5000/api/health
curl http://localhost:5000/api/health/detailed
curl http://localhost:5000/api/v2/health
```

## Production Deployment Steps

1. **Add health check to your Flask app**:
   ```python
   # In app.py or app_final.py
   from src.health_check_endpoint import create_health_endpoint
   
   app = Flask(__name__)
   # ... your existing setup ...
   
   # Add health checks
   create_health_endpoint(app)
   ```

2. **Test locally**:
   ```bash
   python test_health_endpoint.py
   ```

3. **Deploy to production**:
   - Push changes to repository
   - Restart Docker container
   - Verify: `curl https://wolf.law.uw.edu/casestrainer/api/health`

4. **Verify all endpoints**:
   ```bash
   curl https://wolf.law.uw.edu/casestrainer/api/health
   curl https://wolf.law.uw.edu/casestrainer/api/health/detailed
   curl https://wolf.law.uw.edu/casestrainer/api/v2/health
   ```

## Expected Results

- **Status 200**: System is healthy or degraded but operational
- **Status 503**: System is unhealthy (service unavailable)

**Healthy response**: All components show "status": "healthy"
**Degraded response**: Some components degraded but core functionality working
**Unhealthy response**: Critical components failed

## Monitoring

Use the detailed endpoint to monitor:
- Clean pipeline status
- Strict isolator availability
- Production endpoint functionality
- Functional test results (live extraction test)

## Troubleshooting

If health check fails:

1. Check component status in `/api/health/detailed`
2. Look for specific component errors
3. Check logs for detailed error messages
4. Verify all source files are deployed:
   - `src/clean_extraction_pipeline.py`
   - `src/utils/strict_context_isolator.py`
   - `src/citation_extraction_endpoint.py`
   - `src/health_check_endpoint.py`

## Status Codes

- **healthy**: All systems operational (87-93% accuracy)
- **degraded**: Some components down but extraction still works
- **unhealthy**: Critical failure, extraction unavailable

## Integration with cslaunch

The health check is compatible with cslaunch monitoring. It will:
- Return 200 OK when healthy/degraded
- Return 503 Service Unavailable when unhealthy
- Provide JSON response with detailed status

This follows standard health check conventions for Docker and Kubernetes deployments.
