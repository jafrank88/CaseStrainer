# CaseStrainer Session Checklist

This checklist ensures that all necessary steps are followed when starting a new session in Cursor for the CaseStrainer project.

## Prerequisites

- Ensure Cursor is installed and up to date.
- Verify that the project repository is cloned and accessible.

## Environment Setup

1. **Open the Project in Cursor**:
   - Navigate to the project directory in Cursor.

2. **Activate the Virtual Environment**:
   ```bash
   source .venv/bin/activate  # For Unix/Linux
   .venv\Scripts\activate     # For Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Verify Configuration

- Ensure `config.json` is present in the project root with valid API keys for CourtListener and LangSearch.
- Verify that the `.gitignore` file is correctly configured to exclude sensitive files.

## Check for Updates

- Pull the latest changes from the repository:
  ```bash
  git pull origin main
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

Following this checklist will help ensure a smooth session start in Cursor for the CaseStrainer project. If any issues arise, refer to the troubleshooting section or consult the deployment documentation for further guidance. 