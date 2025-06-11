# CaseStrainer Deployment Guide

This guide provides instructions for deploying CaseStrainer in a production environment.

## Prerequisites

- Windows Server 2016 or later
- Python 3.8 or higher
- Node.js 16.x or higher
- Nginx for Windows
- SSL certificates (for production)

## Installation

1. **Clone the repository**
   ```
   git clone https://github.com/yourusername/CaseStrainer.git
   cd CaseStrainer
   ```

2. **Set up Python virtual environment**
   ```
   python -m venv venv
   call venv\Scripts\activate
   pip install -r src\requirements.txt
   ```

3. **Install frontend dependencies**
   ```
   cd casestrainer-vue-new
   npm install
   cd ..
   ```

## Configuration

1. **Environment Variables**
   Create a `.env.production` file in the project root with the following variables:
   ```
   FLASK_APP=src/app_final_vue.py
   FLASK_ENV=production
   SECRET_KEY=your-secret-key
   PROD_BACKEND_PORT=5000
   ```

2. **SSL Certificates**
   Place your SSL certificate and key in `D:/CaseStrainer/ssl/`:
   - `WolfCertBundle.crt`
   - `wolf.law.uw.edu.key`

## Deployment

### Starting the Application

1. **Run as Administrator**
   Right-click on `start_casestrainer.bat` and select "Run as administrator"

   This will:
   - Stop any running instances
   - Build the frontend
   - Configure Nginx
   - Start Nginx and the Flask backend

2. **Verify the deployment**
   - Frontend: https://wolf.law.uw.edu/casestrainer
   - Backend API: http://localhost:5000

### Stopping the Application

1. **Run the stop script**
   ```
   stop_casestrainer.bat
   ```

## Logs

- Application logs: `logs/casestrainer_*.log`
- Nginx access logs: `nginx-1.27.5/logs/casestrainer_access.log`
- Nginx error logs: `nginx-1.27.5/logs/casestrainer_error.log`

## Troubleshooting

### Common Issues

1. **Port in use**
   - Error: `[ERROR] Port 5000 is in use`
   - Solution: The script will attempt to free the port automatically. If it fails, manually stop the process using the port:
     ```
     netstat -ano | find ":5000"
     taskkill /F /PID <PID>
     ```

2. **Nginx fails to start**
   - Check the Nginx error log: `nginx-1.27.5/logs/error.log`
   - Common causes:
     - Invalid configuration
     - Port 80 or 443 already in use
     - Missing SSL certificates

3. **Frontend not updating**
   - Clear browser cache
   - Check the browser's developer console for errors
   - Verify the frontend built successfully (check the log file)

## Maintenance

### Updating the Application

1. Pull the latest changes
   ```
   git pull
   ```

2. Rebuild the frontend
   ```
   cd casestrainer-vue-new
   npm install
   npm run build
   cd ..
   ```

3. Restart the application
   ```
   stop_casestrainer.bat
   start_casestrainer.bat
   ```

## Security Considerations

- Always run the application with a non-administrator account
- Keep all dependencies up to date
- Use strong, unique passwords for all accounts
- Regularly review logs for suspicious activity
- Configure a firewall to restrict access to the application ports

## Backup and Recovery

### Backup

1. **Database**
   - Back up the SQLite database file: `src/instance/casestrainer.db`

2. **Uploads**
   - Back up the uploads directory: `src/uploads`

3. **Configuration**
   - Back up the `.env.production` file

### Recovery

1. **Restore from backup**
   - Copy the backup files to their respective locations
   - Run the start script

## Support

For assistance, please contact [Your Support Email] or open an issue on GitHub.
