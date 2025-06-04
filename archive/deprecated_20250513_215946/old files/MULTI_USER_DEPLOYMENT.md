# Multi-User Deployment Guide for CaseStrainer

This guide explains how to deploy CaseStrainer in a multi-user environment, allowing multiple users to use the application simultaneously without connection issues.

## Prerequisites

- Python 3.6 or higher
- pip (Python package manager)
- Waitress and Cheroot (installed automatically by the run script if not present)

## Installation

1. Clone the repository or download the source code
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Multi-User Server

CaseStrainer includes a script that runs the application using Waitress, a production-ready WSGI server that can handle multiple concurrent requests and is compatible with Windows.

### Basic Usage

To start the server with default settings:

```bash
python run_server.py
```

This will start the server with 8 threads, allowing up to 8 concurrent users.

### Advanced Configuration

You can customize the server configuration using command-line arguments:

```bash
python run_server.py --threads 16 --workers 4 --port 8000 --host 0.0.0.0 --channel-timeout 300 --connection-limit 2000 --timeout 300
```

Available options:

- `--threads`: Number of threads per worker (default: 8)
- `--workers`: Number of worker processes (default: 1)
- `--port`: Port to run the server on (default: 5000)
- `--host`: Host to run the server on (default: 0.0.0.0)
- `--channel-timeout`: Channel timeout in seconds (default: 300)
- `--connection-limit`: Maximum number of connections (default: 2000)
- `--timeout`: Worker timeout in seconds (default: 300)

### SSL Configuration

For secure connections (required for Word add-in), place your SSL certificate and key in the `ssl` directory:

- Certificate: `ssl/cert.pem`
- Key: `ssl/key.pem`

The server will automatically detect and use these files if they exist.

You can also specify custom paths using environment variables:

```bash
export SSL_CERT_PATH=/path/to/cert.pem
export SSL_KEY_PATH=/path/to/key.pem
python run_server.py
```

For production environments, always use a valid SSL certificate from a trusted certificate authority.

### Environment Variables

The following environment variables can be used to configure the server:

- `SECRET_KEY`: Secret key for session management (auto-generated if not provided)
- `SSL_CERT_PATH`: Path to SSL certificate (default: ssl/cert.pem)
- `SSL_KEY_PATH`: Path to SSL key (default: ssl/key.pem)
- `COURTLISTENER_API_KEY`: API key for CourtListener
- `LANGSEARCH_API_KEY`: API key for LangSearch

## Performance Tuning

### Worker Processes

The number of worker processes should generally be set to 2-4 times the number of CPU cores available on your server. For example, on a 4-core server, you might use 8-16 worker processes.

```bash
python run_server.py --workers 8
```

The multi-worker mode uses Python's multiprocessing module to create separate processes, each running its own instance of the server. This provides better isolation between user sessions and improves stability.

### Threads per Worker

The number of threads per worker determines how many concurrent requests each worker can handle. A good starting point is 2-4 threads per worker.

```bash
python run_server.py --threads 4
```

### Timeouts for Long-Running Operations

For analyzing large briefs with many citations, increase both the channel timeout and worker timeout:

```bash
python run_server.py --channel-timeout 600 --timeout 600  # 10 minutes
```

This ensures that connections aren't closed prematurely during long-running operations.

## Monitoring

When running in production, you should monitor the server's performance and resource usage. Consider using tools like:

- Prometheus for metrics collection
- Grafana for visualization
- Sentry for error tracking

## Using a Reverse Proxy

For production deployments, it's recommended to run CaseStrainer behind a reverse proxy like Nginx or Apache. This provides additional features like:

- SSL termination
- Load balancing
- Connection buffering
- Request filtering

### Example Nginx Configuration

Create a file named `/etc/nginx/sites-available/casestrainer`:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Increase timeouts for long-running operations
    proxy_read_timeout 600s;
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
    
    # Disable buffering for SSE
    proxy_buffering off;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE specific settings
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

Enable the site and restart Nginx:

```bash
ln -s /etc/nginx/sites-available/casestrainer /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

## Client-Side Reconnection

For the best user experience, implement client-side reconnection logic in your frontend JavaScript. This ensures that if a connection is temporarily lost, the client will automatically reconnect.

Add the following code to your frontend JavaScript:

```javascript
function setupEventSource(url, options) {
    const eventSource = new EventSource(url);
    
    eventSource.onopen = function() {
        console.log('Connection established');
    };
    
    eventSource.onerror = function(event) {
        console.error('EventSource error:', event);
        eventSource.close();
        // Reconnect after a delay
        setTimeout(() => setupEventSource(url, options), 3000);
    };
    
    // Add your event handlers here
    eventSource.addEventListener('message', function(event) {
        const data = JSON.parse(event.data);
        // Process the data
        if (options && options.onMessage) {
            options.onMessage(data);
        }
    });
    
    return eventSource;
}

// Usage
const eventSource = setupEventSource('/analyze', {
    onMessage: function(data) {
        // Handle the data
        console.log('Received data:', data);
    }
});
```

## Systemd Service for Automatic Restart

Create a systemd service file to ensure the server automatically restarts if it crashes:

```bash
sudo nano /etc/systemd/system/casestrainer.service
```

Add the following content:

```ini
[Unit]
Description=CaseStrainer Multi-User Service
After=network.target

[Service]
User=casestrainer
WorkingDirectory=/path/to/casestrainer
ExecStart=/usr/bin/python3 run_server.py --threads 8 --workers 4 --channel-timeout 300 --connection-limit 2000 --timeout 300
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable casestrainer
sudo systemctl start casestrainer
```

## Troubleshooting

### Server Won't Start

- Check if the port is already in use by another application
- Ensure you have the necessary permissions to bind to the specified port
- Verify that all required dependencies are installed

### Connection Errors

- Check if the server is running and accessible from the client's network
- Verify SSL certificate configuration if using HTTPS
- Check firewall settings to ensure the port is open
- Examine server logs for timeout or connection errors
- Verify that proxy settings are correct if using a reverse proxy

### Performance Issues

- Increase the number of workers and/or threads
- Check server resource usage (CPU, memory, disk I/O)
- Consider using a more powerful server or distributing the load across multiple servers
- Monitor connection counts and adjust --connection-limit accordingly
- Increase timeouts if operations are being cut off

## Security Considerations

- Always use HTTPS in production environments
- Set a strong SECRET_KEY for session management
- Keep API keys and other sensitive information secure
- Regularly update dependencies to patch security vulnerabilities
