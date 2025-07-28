# CaseStrainer Startup Checklist

This checklist ensures that all necessary steps are followed when starting the CaseStrainer system.

## Prerequisites

- Ensure Python 3.8 or higher is installed.
- Verify that pip is available and up to date.
- Ensure Docker is installed and running.
- Verify that Nginx is installed and configured correctly.

## API Keys

- Ensure `config.json` is present in the project root with valid API keys for CourtListener and LangSearch.

## Environment Setup

1. **Activate the Virtual Environment**:
   ```bash
   source .venv/bin/activate  # For Unix/Linux
   .venv\Scripts\activate     # For Windows
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Start the Application

1. **Stop Any Running Instances**:
   - Stop any running Python instances:
     ```powershell
     taskkill /f /im python.exe
     ```
   - Stop any running Nginx instances:
     ```powershell
     Stop-Process -Name nginx -Force
     ```

2. **Start the CaseStrainer Application**:
   ```powershell
   cd "d:\dev\casestrainer"
   .\cslaunch.ps1
   ```
   Select option 1 for quick production start.

3. **Verify Docker Nginx is Running**:
   ```powershell
   docker ps | findstr nginx
   ```

4. **Access the Application**:
   - Open a web browser and navigate to https://wolf.law.uw.edu/casestrainer/

## Troubleshooting

- If you encounter a 502 Bad Gateway error, ensure the application is listening on all interfaces (0.0.0.0) and not just localhost (127.0.0.1).
- Check application logs for any errors or warnings.
- Verify that the Docker Nginx container is running and correctly configured.

## Security

- Ensure `config.json` is not committed to version control.
- Verify that SSL/TLS certificates are up to date and correctly configured in Nginx.

## Monitoring

- Monitor application logs for any issues or performance concerns.
- Check Nginx logs for any proxy or SSL-related issues.

## Conclusion

Following this checklist will help ensure a smooth startup of the CaseStrainer system. If any issues arise, refer to the troubleshooting section or consult the deployment documentation for further guidance. 