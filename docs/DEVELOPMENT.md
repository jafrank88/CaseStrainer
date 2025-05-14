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
   cd casestrainer-vue
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
│   ├── citation_api.py     # Citation API endpoints
│   ├── vue_api.py         # Vue.js API endpoints
│   └── static/            # Static files
├── casestrainer-vue/      # Frontend Vue.js application
│   ├── src/              # Vue.js source code
│   ├── public/           # Static assets
│   └── package.json      # Node.js dependencies
├── conf/                 # Configuration files
│   └── nginx.conf.new   # Nginx configuration
├── docs/                # Documentation
├── logs/               # Application logs
└── tests/             # Test files
```

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

### Vue.js

1. **Component Structure**
   ```vue
   <template>
     <div class="component-name">
       <!-- Template content -->
     </div>
   </template>
   
   <script>
   export default {
     name: 'ComponentName',
     props: {
       propName: {
         type: String,
         required: true
       }
     },
     data() {
       return {
         // Component data
       }
     },
     methods: {
       // Component methods
     }
   }
   </script>
   
   <style scoped>
   /* Component styles */
   </style>
   ```

2. **State Management**
   - Use Vuex for global state
   - Keep components focused
   - Use computed properties
   - Implement proper error handling

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
           response = self.client.post('/api/verify_citation',
               json={'citation': 'test citation'})
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

## API Development

### Adding New Endpoints

1. **Backend API**
   ```python
   @api_blueprint.route('/new-endpoint', methods=['POST'])
   def new_endpoint():
       """Document the endpoint purpose."""
       try:
           data = request.get_json()
           # Process request
           return jsonify({
               'success': True,
               'data': result
           })
       except Exception as e:
           return jsonify({
               'error': str(e)
           }), 500
   ```

2. **Frontend API Service**
   ```javascript
   // src/api/citations.js
   export default {
     newEndpoint(data) {
       return axios.post(`${API_URL}/new-endpoint`, data)
     }
   }
   ```

## Database Development

### Schema Changes

1. **Create Migration**
   ```python
   def create_migration():
       """Create a new database migration."""
       conn = get_db_connection()
       cursor = conn.cursor()
       
       # Add new table
       cursor.execute('''
           CREATE TABLE new_table (
               id INTEGER PRIMARY KEY,
               name TEXT NOT NULL
           )
       ''')
       
       conn.commit()
       conn.close()
   ```

2. **Update Models**
   ```python
   class NewModel:
       """Model for new table."""
       
       def __init__(self, name: str):
           self.name = name
       
       def save(self):
           """Save model to database."""
           conn = get_db_connection()
           cursor = conn.cursor()
           cursor.execute(
               'INSERT INTO new_table (name) VALUES (?)',
               (self.name,)
           )
           conn.commit()
           conn.close()
   ```

## Deployment

### Development Deployment

1. **Start Development Server**
   ```bash
   # Start Flask development server
   python src/app_final_vue.py --host 0.0.0.0 --port 5000
   
   # Start Vue.js development server
   cd casestrainer-vue
   npm run serve
   ```

2. **Start Nginx Container**
   ```bash
   docker run -d --name casestrainer-nginx-dev \
     --network casestrainer_default \
     -p 443:443 \
     -v "$(pwd)/ssl:/etc/nginx/ssl" \
     -v "$(pwd)/conf/nginx.conf.new:/etc/nginx/nginx.conf" \
     -v "$(pwd)/src/static:/etc/nginx/static" \
     -v "$(pwd)/logs:/var/log/nginx" \
     nginx:latest
   ```

### Production Deployment

1. **Build Frontend**
   ```bash
   cd casestrainer-vue
   npm run build
   ```

2. **Deploy Backend**
   ```bash
   # Stop existing processes
   taskkill /f /im python.exe
   
   # Start production server
   python src/app_final_vue.py --host 0.0.0.0 --port 5000
   ```

## Contributing

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Make Changes**
   - Follow coding standards
   - Add tests
   - Update documentation

3. **Submit Pull Request**
   - Describe changes
   - Link related issues
   - Request review

### Code Review

1. **Review Checklist**
   - Code follows standards
   - Tests are included
   - Documentation is updated
   - No security issues
   - Performance is considered

2. **Review Process**
   - At least one approval required
   - All tests must pass
   - No merge conflicts
   - Documentation is complete

## Security

### Best Practices

1. **API Security**
   - Validate all input
   - Use parameterized queries
   - Implement rate limiting
   - Secure API keys

2. **Frontend Security**
   - Sanitize user input
   - Use HTTPS
   - Implement CSP
   - Handle errors gracefully

3. **Database Security**
   - Use prepared statements
   - Encrypt sensitive data
   - Implement access control
   - Regular backups

## Performance

### Optimization

1. **Backend**
   - Use connection pooling
   - Implement caching
   - Optimize database queries
   - Use async operations

2. **Frontend**
   - Lazy load components
   - Optimize assets
   - Use service workers
   - Implement caching

## Monitoring

### Logging

1. **Application Logs**
   ```python
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           RotatingFileHandler('logs/app.log', maxBytes=10000000, backupCount=5),
           StreamHandler()
       ]
   )
   ```

2. **Error Tracking**
   ```python
   try:
       # Operation
   except Exception as e:
       logger.error(f"Error in operation: {str(e)}", exc_info=True)
       # Handle error
   ```

## Support

### Getting Help

1. **Documentation**
   - Check existing docs
   - Review API documentation
   - Read deployment guides

2. **Communication**
   - Use GitHub issues
   - Join development chat
   - Contact maintainers

### Reporting Issues

1. **Issue Template**
   - Describe the problem
   - Provide reproduction steps
   - Include error messages
   - Specify environment

2. **Feature Requests**
   - Describe the feature
   - Explain the benefit
   - Provide examples
   - Consider implementation 