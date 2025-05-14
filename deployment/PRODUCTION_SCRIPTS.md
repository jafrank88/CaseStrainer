# CaseStrainer Production Scripts

## Main Production Script
The primary production script is `src/run_vue_production.py`. This script:
- Builds and deploys the Vue.js frontend
- Configures the Cheroot production server
- Handles port availability and process management
- Sets up proper environment variables
- Includes comprehensive error handling and logging

### Usage
```bash
# Basic usage (defaults to port 5000)
python src/run_vue_production.py

# Specify custom port
python src/run_vue_production.py --port 5001

# Specify custom host
python src/run_vue_production.py --host 0.0.0.0 --port 5001

# Skip Vue.js frontend build
python src/run_vue_production.py --skip-build
```

## Development Server
For development and testing, use `src/app_final_vue.py`:
```bash
# Start with debug mode
python src/app_final_vue.py --debug --port 5001
```

## Legacy Scripts
The following scripts are maintained for reference but should not be used in production:
- `deployment/run_production.py` - Older version without Vue.js support
- `src/deploy_vue_frontend_updated.py` - Vue.js deployment only
- `src/deploy_to_production.py` - Basic deployment script

## Production Checklist
1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Verify configuration in `config.json`:
   - CourtListener API key
   - Base URL
   - Upload folder permissions
   - Session configuration

3. Check port availability:
   ```bash
   # Windows
   netstat -ano | findstr :5000
   
   # Linux/Mac
   lsof -i :5000
   ```

4. Start the production server:
   ```bash
   python src/run_vue_production.py --port 5001
   ```

5. Verify the server is running:
   - Check logs in `logs/casestrainer.log`
   - Access the application at `http://localhost:5001`
   - Test citation validation endpoints

## Troubleshooting
- If port is in use, the script will attempt to kill existing Python processes
- If Vue.js build fails, check Node.js installation and run `npm install` in the Vue project directory
- For API key issues, verify `config.json` contains valid CourtListener API key
- Check logs for detailed error messages

## Logging
Logs are stored in `logs/casestrainer.log` with the following levels:
- INFO: Normal operation messages
- WARNING: Non-critical issues
- ERROR: Critical issues requiring attention
- DEBUG: Detailed debugging information (when --debug is enabled) 