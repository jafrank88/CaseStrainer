# CaseStrainer

A web application for extracting and validating legal citations from documents.

## Features

- Extract citations from PDF, DOCX, and text files
- Validate citations against CourtListener API
- Support for multiple users
- Real-time citation verification
- Modern Vue.js frontend

## Requirements

- Python 3.8 or higher
- Windows 10 or higher
- Internet connection for API access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/CaseStrainer.git
cd CaseStrainer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Environment Variables

CaseStrainer uses environment variables for configuration. You can set them up in two ways:

### Option 1: Using the Setup Script (Recommended)

Run the interactive setup script:

```bash
scripts\setup_env.bat
```

This will guide you through the process of creating a `.env` file with the required configuration.

### Option 2: Manual Setup

1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```

2. Edit the `.env` file and update the following variables:
   - `COURTLISTENER_API_KEY`: Your CourtListener API key (required for citation validation). Note: Only v4 of the CourtListener API is supported. The application will automatically use the v4 endpoints.
   - `LANGSEARCH_API_KEY`: Your LangSearch API key (if using LangSearch features)
   - `SECRET_KEY`: A secret key for Flask session encryption
   - Other settings can be left as default for local development

### Important Security Notes
- Never commit the `.env` file to version control (it's already in `.gitignore`)
- Keep your API keys secure and never share them publicly
- The setup script generates a secure random `SECRET_KEY` for you

### Verifying Your Configuration

After setting up your environment, you can verify your configuration by running:

```bash
scripts\test_env.bat
```

This will check that all required environment variables are properly set and display their values (without showing sensitive information).

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