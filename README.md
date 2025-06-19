# CaseStrainer

A web application for extracting, analyzing, and validating legal citations from legal documents.

## 📁 Project Structure

- `casestrainer-vue-new/` - Current Vue.js frontend (Vite + Vue 3)
  - Uses modern tooling and best practices
  - Active development happens here
- `casestrainer-vue/` - Legacy Vue.js frontend (deprecated)
  - Kept for reference only
  - See [DEPRECATED.md](casestrainer-vue/DEPRECATED.md) for more info
- `api/` - Backend API server
- `docs/` - Documentation

## ✨ Features

### Modern Web Interface

- Built with Vue 3 Composition API and Vite
- Responsive design for all devices
- Real-time citation verification

### Document Processing

- Extract citations from PDF, DOCX, and text files
- Process multiple document formats
- Clean and normalize extracted text

### Citation Analysis

- Validate citations against CourtListener API v4
- Cross-reference with legal databases
- Generate citation networks

### User Experience

- Intuitive drag-and-drop interface
- Real-time feedback and progress tracking
- Exportable results in multiple formats

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** (LTS recommended)
- **Windows 10/11** or **Windows Server 2019/2022**
- **Nginx 1.27.5** (included in repository)
- **Git** for version control

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/jafrank88/CaseStrainer.git
   cd CaseStrainer
   ```

2. **Set up Python environment**

   ```bash
   # Create and activate virtual environment
   python -m venv venv
   .\venv\Scripts\activate
   
   # Install Python dependencies
   pip install -r requirements.txt
   ```

3. **Set up Vue.js frontend**

   ```bash
   # Navigate to frontend directory
   cd casestrainer-vue-new
   
   # Install Node.js dependencies
   npm install
   
   # Build for production
   npm run build
   
   # Return to project root
   cd ..
   ```

4. **Configure environment**

   ```bash
   # Copy example environment file
   copy .env.example .env
   ```

   Edit `.env` and set your configuration:

   ```ini
   FLASK_APP=app_vue.py
   FLASK_ENV=production
   SECRET_KEY=your-secret-key-here
   COURTLISTENER_API_KEY=your-api-key
   ```

## 🚀 Quick Start

### Development Mode

1. **Start the development server**

   ```bash
   # In one terminal (backend)
   flask run --debug
   
   # In another terminal (frontend)
   cd casestrainer-vue-new
   npm run dev
   ```

2. **Access the application**
   - Frontend: `http://localhost:3000`
   - API: `http://localhost:5000/api`

### Production Deployment

1. **Build the frontend**

   ```bash
   cd casestrainer-vue-new
   npm run build
   cd ..
   ```

2. **Start the production server**

   ```bash
   # Using the production script (includes Nginx)
   .\start_casestrainer.bat
   ```

3. **Access the application**
   - Main URL: `https://your-domain.com/casestrainer`
   - API: `https://your-domain.com/casestrainer/api`

## ⚙️ Configuration

### Environment Variables

Key environment variables (set in `.env`):

| Variable | Required | Description |
|----------|----------|-------------|
| `FLASK_APP` | Yes | Set to `app_vue.py` |
| `FLASK_ENV` | Yes | `development` or `production` |
| `SECRET_KEY` | Yes | Secret key for session encryption |
| `COURTLISTENER_API_KEY` | Yes | API key for CourtListener v4 |
| `DATABASE_URL` | No | Database connection string (default: SQLite) |
| `UPLOAD_FOLDER` | No | Path for file uploads (default: `./uploads`) |
| `MAX_CONTENT_LENGTH` | No | Max file upload size (default: 16MB) |

### Setting Up API Keys

1. **CourtListener API**
   - Get your API key from [CourtListener](https://www.courtlistener.com/api/)
   - Only v4 of the API is supported

2. **Other Services**
   - LangSearch (optional): Set `LANGSEARCH_API_KEY`
   - Other integrations: Refer to respective documentation

## 🛠 Development

### Project Structure

```text
CaseStrainer/
├── casestrainer-vue-new/  # Vue 3 frontend
│   ├── src/               # Source files
│   ├── public/            # Static files
│   └── package.json       # Frontend dependencies
├── app/                   # Flask application
├── static/                # Static files (served by Flask)
├── templates/             # Server-side templates
├── migrations/            # Database migrations
├── scripts/               # Utility scripts
└── tests/                 # Test suite
```

### Common Tasks

```bash
# Run tests
pytest

# Lint code
flake8 .

# Format code
black .

# Update dependencies
pip freeze > requirements.txt
```

## 📚 Documentation

- [Deployment Guide](./DEPLOYMENT.md) - Production deployment instructions
- [API Documentation](./docs/API.md) - API endpoints and usage
- [Frontend Guide](./casestrainer-vue-new/README.md) - Vue.js development guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Getting Started

### Starting and Restarting CaseStrainer

- Use the unified script `start_casestrainer.bat` to start or restart both the backend and Nginx.
- For production (default):
  ```
  start_casestrainer.bat
  ```
- For test/minimal Nginx config:
  ```
  start_casestrainer.bat test
  ```
- To build and deploy the Vue.js frontend after frontend changes:
  ```
  scripts\build_and_deploy_vue.bat
  ```
- **All other batch files are deprecated and should not be used for regular workflow.**

## Running the Application

### Dual Interface Structure

- **Modern Vue.js Frontend:**
  - Accessible at: https://wolf.law.uw.edu/casestrainer/
  - Features modern UI, supports file upload, text, and URL input
- **Legacy Interface:**
  - Accessible at: https://wolf.law.uw.edu/casestrainer/api/
  - Will eventually be replaced by the full Vue.js implementation

---

## For New Contributors

**Start Here:**

- **Scripts:**
  - Use only `start_casestrainer.bat` to start/restart backend and Nginx.
  - Use `build_and_deploy_vue.bat` to build and deploy the Vue.js frontend.
  - All other batch files are deprecated and archived.
- **API Path:**
  - All frontend and backend API calls must use the `/casestrainer/api/` prefix.
- **Docs:**
  - See `DEPLOYMENT.md` and `docs/DEPLOYMENT_VUE.md` for deployment, troubleshooting, and rollback procedures.
- **Environment & Security:**
  - Copy `.env.example` to `.env` and fill in your secrets. Never commit real secrets.
  - `.env` is already in `.gitignore`.
  - Use pre-commit hooks for secret scanning and code linting. Install with:
    ```bash
    pip install pre-commit
    pre-commit install
    pre-commit run --all-files
    ```
- **Testing:**
  - Use `test_api.py` to verify backend endpoints. See comments in the script for usage.
- **Code Quality:**
  - Code is formatted with `black` and checked with `flake8` (see `.pre-commit-config.yaml`).
  - Type hints and docstrings are encouraged for Python code.
- **Troubleshooting:**
  - Check the logs in the `logs/` directory if issues arise.
  - Ensure all dependencies are installed and your `.env` is configured.

---

### API Path and Troubleshooting
- All API endpoints are available under `/casestrainer/api/`.

### API Base Path

All API endpoints are accessed under the `/casestrainer/api/` prefix. For example:
- `https://wolf.law.uw.edu/casestrainer/api/verify_citation`
- `http://localhost:5000/casestrainer/api/verify_citation`

**Troubleshooting:**
If you receive 404 or path errors, ensure that both the frontend and backend are using the `/casestrainer/api/` prefix and that your Nginx or proxy configuration matches this path.

### Startup Script

Always use `start_casestrainer.bat` to start or restart the application. All other batch files are archived and unsupported.
- If you encounter 404s or path errors, ensure the frontend and Nginx proxy are configured to use the `/casestrainer` prefix.
- See `DEPLOYMENT.md` and `DEPLOYMENT_VUE.md` for Nginx and proxy configuration details.

### Security Practices
- All sensitive information (API keys, database paths, etc.) must be stored in the `.env` file and referenced via `config.py`.
- `.env` and other sensitive files are included in `.gitignore` and must never be committed.
- It is recommended to use pre-commit hooks to scan for secrets before pushing code.

### Running Backend Tests
- (To be filled in after test script is added)

### Windows

The application can be started in two modes:

#### Development Mode (Default)
```bash
start_casestrainer.bat
```
This will:
- Stop any running Python processes on port 5000
- Install/update Python dependencies
- Start the Flask development server on http://localhost:5000/
  - API endpoints are available at http://localhost:5000/api/...

#### Production Mode
```bash
start_casestrainer.bat production
```
This will:
- Stop any running Python processes on port 5000
- Install/update Python dependencies
- Start the Waitress WSGI server on http://localhost:5000/
  - API endpoints are available at http://localhost:5000/api/...

### Manual Start

#### Development Mode
1. Set environment variables:
```bash
set FLASK_ENV=development
set FLASK_APP=src/app_final_vue.py
set FLASK_DEBUG=1
```

2. Run the development server:
```bash
python -m flask run --host=0.0.0.0 --port=5000
```

#### Production Mode
1. Set environment variables:
```bash
set FLASK_ENV=production
set FLASK_APP=src/app_final_vue.py
```

2. Run the production server:
```bash
python run_production.py
```

The application will be available at:
- Local: http://localhost:5000
- Network: http://your-ip-address:5000

## Development vs Production

CaseStrainer provides PowerShell-based launchers for both development and production environments:

### Development Environment
- **Ports**:
  - Backend: 5001
  - Frontend: 5173
- **Features**:
  - Hot module replacement (HMR)
  - Debug logging
  - Detailed error messages
  - Source maps for debugging
  - Automatic process management

To start in development mode:
```powershell
# Using PowerShell (recommended)
.\launch.ps1

# Or using the batch file (legacy)
start_development.bat
```

### Production Environment
- **Ports**:
  - Backend: 5000
  - Frontend: 80/443 (via Nginx)
- **Features**:
  - Optimized builds
  - Minified assets
  - Production-grade security
  - Process monitoring
  - Automatic health checks

To start in production mode:
```powershell
# Using PowerShell (recommended)
.\launch-production.ps1

# Or using the batch file (legacy)
start_casestrainer.bat
```

### Key Differences

| Feature          | Development (`launch.ps1`) | Production (`launch-production.ps1`) |
|-----------------|---------------------------|-------------------------------------|
| Backend Server  | Flask dev server          | Waitress WSGI server               |
| Debug Mode      | Enabled                   | Disabled                           |
| Logging         | Verbose                  | Production-optimized               |
| Ports           | 5001 (BE), 5173 (FE)     | 5000 (BE), 80/443 (FE)             |
| Process Manager | PowerShell               | Systemd/PM2 (in production)        |


### Environment Variables

Key environment variables:
- `NODE_ENV`: Set to 'development' or 'production'
- `VITE_API_BASE_URL`: Base URL for API requests
- `FLASK_ENV`: Flask environment ('development' or 'production')
- `FLASK_DEBUG`: Enable/disable Flask debug mode

### Configuration Files
- `.env.development`: Development environment variables
- `.env.production`: Production environment variables (not committed to version control)
- `vite.config.js`: Development server and build configuration
- `nginx.conf`: Production web server configuration

### Switching Between Environments

1. **Development to Production**:
   ```powershell
   # Stop development servers (Ctrl+C in the terminal)
   # Build frontend for production
   cd casestrainer-vue-new
   npm run build
   
   # Start production environment
   cd ..
   .\launch-production.ps1
   ```

2. **Production to Development**:
   ```powershell
   # Stop production servers (Ctrl+C in the terminal)
   # Start development environment
   .\launch.ps1
   ```

### Advanced Usage

#### Custom Ports
You can modify the ports in the respective launcher scripts or use environment variables:

```powershell
# Launch development environment on custom ports
$env:FLASK_RUN_PORT=5002
$env:VITE_DEV_SERVER_PORT=3000
.\launch.ps1
```

#### Process Management
Both launchers include process management features:
- Automatic cleanup on exit
- Port conflict detection
- Process monitoring
- Graceful shutdown

### Development Mode
- Uses Flask's built-in development server
- Enables debug mode for detailed error messages
- Auto-reloads on code changes
- Not suitable for production use

### Production Mode
- Uses Waitress WSGI server
- Disables debug mode for security
- Handles multiple users efficiently
- Includes proper logging and error handling
- Suitable for production deployment

## Configuration

The application can be configured through environment variables:

- `FLASK_ENV`: Set to 'production' or 'development'
- `FLASK_APP`: Path to the main application file (src/app_final_vue.py)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 5000)
- `THREADS`: Number of worker threads (default: 10)
- `COURTLISTENER_API_KEY`: Your CourtListener API key

## Directory Structure

- `src/`: Source code
  - `app_final_vue.py`: Main application file
  - `run_production.py`: Production server script
- `logs/`: Application logs
- `uploads/`: Temporary file storage
- `casestrainer_sessions/`: User session data

## Troubleshooting

1. If you get a "port already in use" error:
   - Change the PORT environment variable
   - Or close the application using the port

2. If the application doesn't start:
   - Check the logs in the `logs` directory
   - Ensure all dependencies are installed
   - Verify your CourtListener API key

3. Development Mode Issues:
   - Make sure FLASK_DEBUG=1 is set
   - Check for syntax errors in the code
   - Verify all imports are working

4. Production Mode Issues:
   - Check the production logs
   - Verify all environment variables are set
   - Ensure proper permissions on directories

## Support

For issues and feature requests, please create an issue in the GitHub repository.

## Citation Extraction and Verification (2024+)

**All citation extraction and verification should now use the [CourtListener citation-lookup API](https://www.courtlistener.com/api/rest/v4/citation-lookup/) by sending the full text blob.**

- Do NOT use local extraction functions like `extract_all_citations` or `extract_citations_from_text`—these are deprecated and will raise errors.
- For any input (pasted text, file upload, URL), extract the text, then send it to the CourtListener API as the `text` parameter.
- The API will return a list of all found citations with metadata.

**Example (Python):**
```python
import requests
headers = {"Authorization": f"Token <your-token-here>"}
data = {"text": your_full_text_blob}
response = requests.post(
    "https://www.courtlistener.com/api/rest/v4/citation-lookup/",
    headers=headers,
    data=data
)
citations = response.json()  # List of citation objects
```

## Deprecated Functions
- `extract_all_citations` (Python): Deprecated. Use the CourtListener API instead.
- `extract_citations_from_text` (Python): Deprecated. Use the CourtListener API instead. 