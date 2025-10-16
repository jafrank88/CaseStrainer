#!/usr/bin/env python3
"""
CaseStrainer Health Monitor

This script monitors the CaseStrainer production server health endpoint and sends alerts
when issues are detected. It can be run as a cron job or service.

Usage:
    python monitor_health.py [--config config.json] [--test]

Configuration:
    Create a config.json file with your settings:
    {
        "health_endpoint": "https://wolf.law.uw.edu/casestrainer/api/health",
        "check_interval": 300,
        "alert_threshold": 3,
        "notifications": {
            "email": {
                "enabled": true,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "your-email@gmail.com",
                "password": "your-app-password",
                "recipients": ["admin@example.com"]
            },
            "slack": {
                "enabled": false,
                "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
            },
            "discord": {
                "enabled": false,
                "webhook_url": "https://discord.com/api/webhooks/YOUR/WEBHOOK/URL"
            }
        }
    }
"""

import json
import time
import logging
import smtplib
import requests
import argparse
import sys
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('health_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self, config_path: str = "config.json"):
        """Initialize the health monitor with configuration."""
        self.config = self.load_config(config_path)
        self.health_endpoint = self.config.get('health_endpoint')
        self.check_interval = self.config.get('check_interval', 300)  # 5 minutes default
        self.alert_threshold = self.config.get('alert_threshold', 3)
        self.notifications = self.config.get('notifications', {})
        
        # Track consecutive failures
        self.consecutive_failures = 0
        self.last_alert_time = None
        self.alert_cooldown = 3600  # 1 hour between alerts
        
        logger.info(f"Health monitor initialized for {self.health_endpoint}")
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file {config_path} not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)
    
    def check_health(self) -> Optional[Dict[str, Any]]:
        """Check the health endpoint and return the response data."""
        try:
            start_time = time.time()
            response = requests.get(self.health_endpoint, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Health check successful (response time: {response_time:.2f}s)")
                return data
            else:
                logger.warning(f"Health check failed with status {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Health check timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Health check connection error")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Health check request error: {e}")
            return None
        except json.JSONDecodeError:
            logger.error("Health check returned invalid JSON")
            return None
    
    def analyze_health_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze health data and return issues found."""
        issues = []
        overall_status = data.get('overall_status', 'unknown')
        
        # Check overall status
        if overall_status != 'healthy':
            issues.append(f"Overall system status: {overall_status}")
        
        # Check individual components
        components = {
            'Flask': data.get('flask_status', {}),
            'Redis': data.get('redis_status', {}),
            'Worker': data.get('worker_status', {}),
            'Database': data.get('database_status', {}),
            'System': data.get('system_status', {})
        }
        
        for component_name, component_data in components.items():
            if not component_data:
                issues.append(f"{component_name}: No data available")
                continue
                
            status = component_data.get('status', 'unknown')
            if status != 'healthy':
                issues.append(f"{component_name}: {status}")
            
            # Check specific metrics
            if component_name == 'System':
                cpu_usage = component_data.get('cpu_usage', 0)
                memory_usage = component_data.get('memory_usage', 0)
                disk_usage = component_data.get('disk_usage', 0)
                
                if cpu_usage > 90:
                    issues.append(f"High CPU usage: {cpu_usage}%")
                if memory_usage > 90:
                    issues.append(f"High memory usage: {memory_usage}%")
                if disk_usage > 90:
                    issues.append(f"High disk usage: {disk_usage}%")
            
            elif component_name == 'Worker':
                queue_size = component_data.get('queue_size', 0)
                active_jobs = component_data.get('active_jobs', 0)
                
                if queue_size > 100:
                    issues.append(f"Large queue size: {queue_size} jobs")
                if active_jobs > 10:
                    issues.append(f"Many active jobs: {active_jobs}")
        
        return {
            'has_issues': len(issues) > 0,
            'issues': issues,
            'overall_status': overall_status,
            'timestamp': data.get('timestamp'),
            'server_uptime': data.get('server_uptime'),
            'response_time': data.get('response_time', 0)
        }
    
    def should_send_alert(self) -> bool:
        """Determine if an alert should be sent based on cooldown and threshold."""
        now = datetime.now()
        
        # Check cooldown period
        if self.last_alert_time:
            time_since_last_alert = (now - self.last_alert_time).total_seconds()
            if time_since_last_alert < self.alert_cooldown:
                return False
        
        # Check threshold
        return self.consecutive_failures >= self.alert_threshold
    
    def send_email_alert(self, analysis: Dict[str, Any]):
        """Send email alert."""
        email_config = self.notifications.get('email', {})
        if not email_config.get('enabled', False):
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['username']
            msg['To'] = ', '.join(email_config['recipients'])
            msg['Subject'] = f"🚨 CaseStrainer Health Alert - {analysis['overall_status']}"
            
            body = self.create_alert_message(analysis)
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info("Email alert sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def send_slack_alert(self, analysis: Dict[str, Any]):
        """Send Slack alert."""
        slack_config = self.notifications.get('slack', {})
        if not slack_config.get('enabled', False):
            return
        
        try:
            message = self.create_alert_message(analysis)
            payload = {
                "text": f"🚨 CaseStrainer Health Alert\n{message}"
            }
            
            response = requests.post(slack_config['webhook_url'], json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Slack alert sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    def send_discord_alert(self, analysis: Dict[str, Any]):
        """Send Discord alert."""
        discord_config = self.notifications.get('discord', {})
        if not discord_config.get('enabled', False):
            return
        
        try:
            message = self.create_alert_message(analysis)
            payload = {
                "content": f"🚨 CaseStrainer Health Alert\n{message}"
            }
            
            response = requests.post(discord_config['webhook_url'], json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Discord alert sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
    
    def create_alert_message(self, analysis: Dict[str, Any]) -> str:
        """Create alert message content."""
        message = f"""
CaseStrainer Health Alert

Status: {analysis['overall_status']}
Time: {datetime.fromtimestamp(analysis['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}
Server Uptime: {analysis['server_uptime']} seconds
Consecutive Failures: {self.consecutive_failures}

Issues Found:
"""
        
        if analysis['issues']:
            for issue in analysis['issues']:
                message += f"• {issue}\n"
        else:
            message += "• No specific issues identified\n"
        
        message += f"\nHealth Endpoint: {self.health_endpoint}"
        return message
    
    def send_alerts(self, analysis: Dict[str, Any]):
        """Send alerts through all configured channels."""
        if not self.should_send_alert():
            return
        
        logger.warning(f"Sending health alert (consecutive failures: {self.consecutive_failures})")
        
        self.send_email_alert(analysis)
        self.send_slack_alert(analysis)
        self.send_discord_alert(analysis)
        
        self.last_alert_time = datetime.now()
    
    def run_check(self):
        """Run a single health check."""
        data = self.check_health()
        
        if data is None:
            self.consecutive_failures += 1
            logger.warning(f"Health check failed (consecutive failures: {self.consecutive_failures})")
            
            # Create analysis for failed check
            analysis = {
                'has_issues': True,
                'issues': ['Health endpoint unreachable'],
                'overall_status': 'unknown',
                'timestamp': time.time(),
                'server_uptime': 0,
                'response_time': 0
            }
            
            if self.should_send_alert():
                self.send_alerts(analysis)
            
            return False
        
        else:
            # Reset consecutive failures on successful check
            if self.consecutive_failures > 0:
                logger.info(f"Health check recovered (was {self.consecutive_failures} consecutive failures)")
                self.consecutive_failures = 0
            
            # Analyze the health data
            analysis = self.analyze_health_data(data)
            
            if analysis['has_issues']:
                self.consecutive_failures += 1
                logger.warning(f"Health issues detected: {analysis['issues']}")
                
                if self.should_send_alert():
                    self.send_alerts(analysis)
            
            return True
    
    def run_continuous(self):
        """Run continuous monitoring."""
        logger.info("Starting continuous health monitoring...")
        
        try:
            while True:
                self.run_check()
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("Health monitoring stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error in monitoring loop: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='CaseStrainer Health Monitor')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--test', action='store_true', help='Run a single test check')
    parser.add_argument('--continuous', action='store_true', help='Run continuous monitoring')
    
    args = parser.parse_args()
    
    monitor = HealthMonitor(args.config)
    
    if args.test:
        logger.info("Running single health check...")
        success = monitor.run_check()
        sys.exit(0 if success else 1)
    
    elif args.continuous:
        monitor.run_continuous()
    
    else:
        # Default: run single check
        success = monitor.run_check()
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 