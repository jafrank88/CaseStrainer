# CaseStrainer Development Guide

This guide provides comprehensive information for developers working on the CaseStrainer project.

## Development Environment Setup

### Prerequisites

1. **Python Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   .\venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Node.js Environment**
   ```bash
   # Install Node.js dependencies
   cd casestrainer-vue-new
   npm install
   ```

3. **Docker**
   - Install Docker Desktop for Windows
   - Enable WSL 2 backend
   - Configure resource limits

### Development Tools

1. **IDE Setup**
   - VS Code with extensions:
     - Python
     - Vue.js
     - Docker
     - ESLint
     - Prettier

2. **Git Configuration**
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

## Project Structure

```
CaseStrainer/
├── src/                    # Backend source code
│   ├── app_final_vue.py    # Main Flask application
│   ├── vue_api_endpoints.py # Vue.js API endpoints
│   ├── citation_api.py     # Citation API endpoints
│   ├── config.py           # Configuration management
│   └── static/             # Static files
├── casestrainer-vue-new/   # Frontend Vue.js application
│   ├── src/               # Vue.js source code
│   ├── public/            # Static assets
│   └── package.json       # Node.js dependencies
├── docker-compose.prod.yml # Production Docker configuration
├── docker-compose.dev.yml  # Development Docker configuration
├── launcher.ps1           # PowerShell launcher with auto-restart
├── docs/                  # Documentation
├── logs/                  # Application logs
└── tests/                 # Test files
```

## Development Modes

### Local Development

```powershell
.\launcher.ps1 -Environment Development
```

- Backend: Flask development server on port 5000
- Frontend: Vue.js dev server on port 5173
- Redis: Local or Docker container
- Hot reload enabled

### Docker Development

```powershell
.\launcher.ps1 -Environment DockerDevelopment
```

- Backend: Containerized Flask development server
- Frontend: Containerized Vue.js dev server
- Redis: Dedicated container
- Volume mounts for live code changes

### Docker Production

```powershell
.\launcher.ps1 -Environment DockerProduction
```

- Full production stack with health checks
- Waitress WSGI server
- Nginx reverse proxy
- Multiple RQ workers
- Redis persistence

## Coding Standards

### Python

1. **Style Guide**
   - Follow PEP 8
   - Use type hints
   - Document all functions and classes
   - Maximum line length: 88 characters

2. **Code Organization**
   ```python
   # Imports
   import os
   import sys
   from typing import List, Dict
   
   # Constants
   MAX_RETRIES = 5
   
   # Classes
   class CitationVerifier:
       """Class for verifying legal citations."""
       
       def __init__(self, api_key: str) -> None:
           """Initialize the verifier with API key."""
           self.api_key = api_key
   
       def verify_citation(self, citation: str) -> Dict:
           """Verify a single citation."""
           pass
   
   # Functions
   def process_document(file_path: str) -> List[Dict]:
       """Process a document for citations."""
       pass
   ```

3. **Configuration Management**
   - Use `src/config.py` for all configuration
   - Environment variables take precedence
   - Fallback to `config.json` for defaults
   - Never hardcode sensitive values

### Vue.js

1. **Component Structure**
   ```vue
   <template>
     <div class="component-name">
       <!-- Template content -->
     </div>
   </template>
   
   <script setup>
   import { ref, computed } from 'vue'
   
   // Component logic
   const props = defineProps({
     propName: {
       type: String,
       required: true
     }
   })
   
   const data = ref({})
   
   const computedValue = computed(() => {
     return data.value.someProperty
   })
   </script>
   
   <style scoped>
   /* Component styles */
   </style>
   ```

2. **State Management**
   - Use Pinia for global state
   - Keep components focused
   - Use computed properties
   - Implement proper error handling

## API Development

### Endpoint Structure

All API endpoints are under `/casestrainer/api/`:

```python
@vue_api.route('/analyze', methods=['POST'])
def analyze():
    """Analyze and validate citations."""
    pass

@vue_api.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    """Check processing status."""
    pass

@vue_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    pass
```

### Response Format

```python
def make_response(data=None, status="success", message="", status_code=200):
    """Standard API response format."""
    response = {
        "status": status,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(response), status_code
```

### Error Handling

```python
@vue_api.errorhandler(Exception)
def handle_error(error):
    """Global error handler."""
    logger.error(f"Unhandled error: {str(error)}")
    return make_response(
        status="error",
        message="Internal server error",
        status_code=500
    )
```

## Testing

### Backend Testing

1. **Unit Tests**
   ```python
   import unittest
   
   class TestCitationVerifier(unittest.TestCase):
       def setUp(self):
           self.verifier = CitationVerifier("test_key")
   
       def test_verify_citation(self):
           result = self.verifier.verify_citation("test citation")
           self.assertIsNotNone(result)
   ```

2. **Integration Tests**
   ```python
   class TestAPIEndpoints(unittest.TestCase):
       def setUp(self):
           self.app = create_test_app()
           self.client = self.app.test_client()
   
       def test_verify_citation_endpoint(self):
           response = self.client.post('/casestrainer/api/analyze',
               json={'text': 'test citation'})
           self.assertEqual(response.status_code, 200)
   ```

### Frontend Testing

1. **Unit Tests**
   ```javascript
   import { mount } from '@vue/test-utils'
   import CitationVerifier from '@/components/CitationVerifier.vue'
   
   describe('CitationVerifier', () => {
     test('verifies citation correctly', async () => {
       const wrapper = mount(CitationVerifier)
       await wrapper.setData({ citation: 'test citation' })
       await wrapper.find('button').trigger('click')
       expect(wrapper.text()).toContain('Verified')
     })
   })
   ```

2. **E2E Tests**
   ```javascript
   describe('Citation Verification', () => {
     it('verifies citation from home page', () => {
       cy.visit('/')
       cy.get('[data-test="citation-input"]').type('test citation')
       cy.get('[data-test="verify-button"]').click()
       cy.get('[data-test="result"]').should('be.visible')
     })
   })
   ```

## Docker Development

### Development Container

```yaml
# docker-compose.dev.yml
services:
  backend-dev:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./src:/app/src
      - ./logs:/app/logs
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
```

### Production Container

```yaml
# docker-compose.prod.yml
services:
  backend:
    build: .
    command: waitress-serve --port=5000 --threads=2 src.app_final_vue:app
    ports:
      - "5001:5000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/casestrainer/api/health"]
      interval: 60s
      timeout: 30s
      retries: 8
```

## Health Checks

### Backend Health Check

```python
def check_redis():
    """Check Redis connection."""
    try:
        redis_conn.ping()
        return "ok"
    except Exception as e:
        logger.warning(f"Redis check failed: {e}")
        return "down"

def check_db():
    """Check database connection."""
    try:
        conn = sqlite3.connect(DATABASE_FILE, timeout=3)
        conn.execute('SELECT 1')
        conn.close()
        return "ok"
    except Exception as e:
        logger.warning(f"Database check failed: {e}")
        return "down"
```

### Docker Health Checks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/casestrainer/api/health"]
  interval: 60s
  timeout: 30s
  retries: 8
  start_period: 180s
```

## Logging

### Configuration

```python
def configure_logging(log_level: int = logging.INFO) -> None:
    """Configure logging for the application."""
    from concurrent_log_handler import ConcurrentRotatingFileHandler
    
    logs_dir = os.path.join(project_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    file_handler = ConcurrentRotatingFileHandler(
        os.path.join(logs_dir, "casestrainer.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5
    )
```

### Usage

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Application started")
logger.warning("Deprecated function called")
logger.error("Failed to process request", exc_info=True)
```

## Background Tasks

### RQ Worker Setup

```python
from rq import Queue
from redis import Redis

redis_conn = Redis(host='localhost', port=6379, db=0)
task_queue = Queue('casestrainer', connection=redis_conn)

def process_citation_task(task_id, task_type, task_data):
    """Process citation verification task."""
    try:
        # Task processing logic
        result = process_citations(task_data)
        set_task_result(task_id, result)
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        set_task_status(task_id, "failed", str(e))
```

### Worker Management

```bash
# Start RQ worker
python src/rq_worker.py worker casestrainer

# Monitor workers
rq info

# Clear failed jobs
rq requeue --all
```

## Performance Optimization

### Database Optimization

```python
# Use connection pooling
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_citation_metadata(citation_id):
    """Cache citation metadata."""
    pass
```

### Rate Limiting

```python
from backoff import on_exception, expo
import requests

@on_exception(expo, requests.exceptions.RequestException, max_tries=3)
def api_call_with_retry(url, headers, data):
    """Make API call with exponential backoff."""
    return requests.post(url, headers=headers, data=data)
```

## Security

### Input Validation

```python
def validate_file_upload(file):
    """Validate uploaded file."""
    if not file:
        raise ValueError("No file provided")
    
    if file.filename == '':
        raise ValueError("No file selected")
    
    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")
    
    return True
```

### Environment Variables

```python
# Never hardcode sensitive values
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key')
API_KEY = os.environ.get('COURTLISTENER_API_KEY')
```

### CORS Configuration

```python
from flask_cors import CORS

CORS(app, resources={
    r"/casestrainer/api/*": {
        "origins": ["http://localhost:5173", "https://your-domain.com"],
        "methods": ["GET", "POST", "OPTIONS"]
    }
})
```

## Deployment

### Production Checklist

- [ ] Environment variables configured
- [ ] Frontend built for production
- [ ] Health checks implemented
- [ ] Logging configured
- [ ] Security headers set
- [ ] SSL certificates installed
- [ ] Database migrations run
- [ ] Background workers started

### Monitoring

```python
@app.route('/casestrainer/api/server_stats')
def server_stats():
    """Get server statistics."""
    return jsonify({
        "uptime": time.time() - start_time,
        "memory_usage": psutil.virtual_memory().percent,
        "cpu_usage": psutil.cpu_percent(),
        "active_requests": len(active_requests)
    })
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Check if ports are in use
2. **Redis connection**: Ensure Redis is running
3. **File permissions**: Check upload directory permissions
4. **API rate limits**: Monitor CourtListener API usage
5. **Memory issues**: Check Docker resource limits

### Debug Mode

```python
# Enable debug mode for development
FLASK_DEBUG = True
FLASK_ENV = 'development'
```

### Log Analysis

```bash
# View recent logs
tail -f logs/casestrainer.log

# Search for errors
grep -i error logs/casestrainer.log

# Monitor health checks
grep -i health logs/casestrainer.log
``` 