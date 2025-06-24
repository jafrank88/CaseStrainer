# CaseStrainer Production Monitoring

This directory contains tools for monitoring the CaseStrainer production server's health and performance.

## Components

### 1. Web Dashboard (`monitoring_dashboard.html`)
A beautiful, responsive web interface that displays real-time system health information.

**Features:**
- Real-time status monitoring of all components
- Visual indicators (green/yellow/red) for component health
- Auto-refresh capability (30-second intervals)
- Uptime tracking and performance metrics
- Mobile-responsive design
- Error handling and connection status

### 2. Health Monitor Script (`monitor_health.py`)
A Python script that continuously monitors the health endpoint and sends alerts when issues are detected.

**Features:**
- Configurable check intervals and alert thresholds
- Multiple notification channels (email, Slack, Discord)
- Consecutive failure tracking
- Alert cooldown periods to prevent spam
- Comprehensive logging

### 3. Windows Service Management (`monitor_service.ps1`)
PowerShell script to install and manage the health monitor as a Windows service.

**Features:**
- Easy service installation/uninstallation
- Automatic startup configuration
- Service status monitoring
- Administrator privilege handling

## Setup Instructions

### Prerequisites

1. **Python 3.7+** with the following packages:
   ```bash
   pip install requests
   ```

2. **Production Server Health Endpoint**
   - Ensure your production server has the enhanced `/health` endpoint
   - The endpoint should return JSON with component status information

### Configuration

1. **Update the Health Endpoint URL**
   
   Edit `config.json` and update the `health_endpoint` URL:
   ```json
   {
       "health_endpoint": "https://your-production-domain.com/health"
   }
   ```

2. **Configure Notifications (Optional)**

   **Email Alerts:**
   ```json
   {
       "email": {
           "enabled": true,
           "smtp_server": "smtp.gmail.com",
           "smtp_port": 587,
           "username": "your-email@gmail.com",
           "password": "your-app-password",
           "recipients": ["admin@example.com"]
       }
   }
   ```

   **Slack Alerts:**
   ```json
   {
       "slack": {
           "enabled": true,
           "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
       }
   }
   ```

   **Discord Alerts:**
   ```json
   {
       "discord": {
           "enabled": true,
           "webhook_url": "https://discord.com/api/webhooks/YOUR/WEBHOOK/URL"
       }
   }
   ```

### Installation Options

#### Option 1: Web Dashboard Only
1. Open `monitoring_dashboard.html` in a web browser
2. Update the `HEALTH_ENDPOINT` variable in the JavaScript section
3. The dashboard will automatically start monitoring

#### Option 2: Command Line Monitoring
1. Test the monitor:
   ```bash
   python monitor_health.py --test
   ```

2. Run continuous monitoring:
   ```bash
   python monitor_health.py --continuous
   ```

#### Option 3: Windows Service (Recommended for Production)
1. **Install the service** (run PowerShell as Administrator):
   ```powershell
   .\monitor_service.ps1 -Action install
   ```

2. **Start the service**:
   ```powershell
   .\monitor_service.ps1 -Action start
   ```

3. **Check service status**:
   ```powershell
   .\monitor_service.ps1 -Action status
   ```

4. **Stop the service**:
   ```powershell
   .\monitor_service.ps1 -Action stop
   ```

5. **Uninstall the service** (run PowerShell as Administrator):
   ```powershell
   .\monitor_service.ps1 -Action uninstall
   ```

### Cron Job Setup (Linux/Mac)

For Linux or Mac systems, you can set up a cron job:

1. **Edit crontab**:
   ```bash
   crontab -e
   ```

2. **Add monitoring job** (runs every 5 minutes):
   ```bash
   */5 * * * * cd /path/to/casestrainer && python monitor_health.py --config config.json
   ```

3. **Add continuous monitoring** (runs on startup):
   ```bash
   @reboot cd /path/to/casestrainer && nohup python monitor_health.py --config config.json --continuous > monitor.log 2>&1 &
   ```

## Usage

### Web Dashboard
- Open `monitoring_dashboard.html` in any modern web browser
- The dashboard automatically refreshes every 30 seconds
- Use the control buttons to:
  - Manually refresh data
  - Toggle auto-refresh
  - View raw health endpoint data

### Health Monitor Script
```bash
# Single health check
python monitor_health.py --test

# Continuous monitoring
python monitor_health.py --continuous

# Custom configuration
python monitor_health.py --config my_config.json
```

### Service Management
```powershell
# Check service status
.\monitor_service.ps1

# Start service
.\monitor_service.ps1 -Action start

# Stop service
.\monitor_service.ps1 -Action stop
```

## Monitoring Metrics

The system monitors the following components:

### Flask Application
- Application status
- Version information
- Environment configuration

### Redis Database
- Connection status
- Memory usage
- Response time

### RQ Worker
- Worker status
- Active job count
- Queue size

### SQLite Database
- Connection status
- File size
- Database health

### System Resources
- CPU usage
- Memory usage
- Disk usage

### Overall Health
- Combined system status
- Number of healthy components
- Last error information

## Alert Thresholds

The monitoring system uses configurable thresholds:

- **Alert Threshold**: Number of consecutive failures before sending alerts (default: 3)
- **Check Interval**: Time between health checks in seconds (default: 300)
- **Alert Cooldown**: Minimum time between alerts in seconds (default: 3600)

## Logging

- **Web Dashboard**: Browser console for debugging
- **Health Monitor**: `health_monitor.log` file
- **Windows Service**: Windows Event Log

## Troubleshooting

### Common Issues

1. **Health endpoint unreachable**
   - Check the URL in `config.json`
   - Verify the production server is running
   - Check firewall settings

2. **Email alerts not working**
   - Verify SMTP settings
   - Check app password for Gmail
   - Ensure recipient emails are correct

3. **Service won't start**
   - Run PowerShell as Administrator
   - Check Python path in service configuration
   - Verify config.json exists and is valid

4. **Dashboard shows no data**
   - Check browser console for errors
   - Verify CORS settings on the health endpoint
   - Update the `HEALTH_ENDPOINT` URL in the HTML file

### Debug Mode

Enable debug logging by modifying the Python script:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Testing

Test the health endpoint manually:
```bash
curl https://your-production-domain.com/health
```

## Security Considerations

1. **HTTPS**: Always use HTTPS for production health endpoints
2. **Authentication**: Consider adding authentication to the health endpoint
3. **Firewall**: Restrict access to monitoring tools
4. **Credentials**: Store sensitive credentials securely (consider environment variables)

## Customization

### Adding New Metrics
1. Update the health endpoint to include new metrics
2. Modify the dashboard HTML to display new data
3. Update the monitor script to check new thresholds

### Custom Alert Channels
1. Add new notification methods to `monitor_health.py`
2. Update `config.json` with new channel settings
3. Implement the notification logic

### Dashboard Styling
- Modify the CSS in `monitoring_dashboard.html`
- Add new status indicators or metrics
- Customize the color scheme and layout

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify configuration settings
3. Test individual components
4. Review the troubleshooting section above 