# CaseStrainer Multi-User Improvements

This document explains the improvements made to CaseStrainer to ensure multiple users can use the tool without having their connections broken or closed prematurely.

## Overview of Changes

The following improvements have been implemented:

1. **Enhanced Server Configuration**
   - Increased default channel timeout from 120s to 300s
   - Increased default connection limit from 1000 to 2000
   - Added worker process support for better isolation and stability
   - Added worker timeout parameter for long-running operations

2. **Robust Client-Side Reconnection**
   - Implemented advanced EventSource reconnection logic in the frontend
   - Added automatic retry mechanism with configurable attempts and delay
   - Added connection timeout handling to prevent hanging connections

3. **Production Deployment Support**
   - Created Nginx configuration for reverse proxy setup
   - Created systemd service file for automatic restarts
   - Added detailed documentation for performance tuning

## How to Use These Improvements

### Running with Improved Settings

To run CaseStrainer with the improved multi-user settings:

```bash
python run_server.py --threads 16 --workers 4 --channel-timeout 300 --connection-limit 2000 --timeout 300
```

Adjust the parameters based on your server's resources:
- `--threads`: Set to 2-4 times the number of CPU cores
- `--workers`: Set to 2-4 for better isolation between user sessions
- `--channel-timeout`: Increase for analyzing large briefs with many citations
- `--connection-limit`: Adjust based on expected concurrent users
- `--timeout`: Set to match or exceed the channel-timeout

#### Multi-Worker Port Assignment

When running with multiple workers, each worker will use a different port to avoid conflicts:
- Worker 0: Uses the base port specified by `--port` (default: 5000)
- Worker 1: Uses base port + 1 (e.g., 5001)
- Worker 2: Uses base port + 2 (e.g., 5002)
- And so on...

For example, with `--workers 4 --port 5000`, the workers will use ports 5000, 5001, 5002, and 5003.

When using Nginx as a reverse proxy, you'll need to configure it to distribute requests across all worker ports. The provided `nginx-casestrainer.conf` includes an example configuration for this setup.

### Production Deployment

For production environments, use the provided configuration files:

1. **Nginx Reverse Proxy**
   - Copy `nginx-casestrainer.conf` to `/etc/nginx/sites-available/`
   - Create a symlink: `ln -s /etc/nginx/sites-available/nginx-casestrainer.conf /etc/nginx/sites-enabled/`
   - Edit the file to update your domain name and SSL certificate paths
   - Test and restart Nginx: `nginx -t && systemctl restart nginx`

2. **Systemd Service**
   - Copy `casestrainer.service` to `/etc/systemd/system/`
   - Edit the file to update paths and user information
   - **Important**: Configure the API keys in the Environment variables section:
     ```ini
     Environment="SSL_CERT_PATH=/path/to/cert.pem"
     Environment="SSL_KEY_PATH=/path/to/key.pem"
     Environment="COURTLISTENER_API_KEY=your_api_key_here"
     Environment="LANGSEARCH_API_KEY=your_api_key_here"
     Environment="SECRET_KEY=your_secret_key_here"
     ```
   - Enable and start the service:
     ```bash
     systemctl daemon-reload
     systemctl enable casestrainer
     systemctl start casestrainer
     ```

3. **API Keys Configuration**
   - Use the provided setup script to configure API keys:
     ```bash
     python setup_api_keys.py
     ```
     This script will:
     - Prompt for your API keys
     - Test the API connections
     - Save the keys to config.json
     - Generate a configured systemd service file
     - Set up environment variables for the current session
   
   - **CourtListener API Key**: Required for citation lookup and case data retrieval
     - Register at https://www.courtlistener.com/help/api/rest/
     - Set the key in the systemd service file or as an environment variable
   - **LangSearch API Key**: Required for advanced case summary generation
     - Contact LangSearch provider for API access
     - Set the key in the systemd service file or as an environment variable
   - Without proper API keys, the application will fall back to rate-limited public access
     which may result in "Authentication credentials were not provided" errors

### Monitoring the Service

Monitor the service status and logs:

```bash
# Check service status
systemctl status casestrainer

# View logs
journalctl -u casestrainer -f
```

## Technical Details

### Server-Side Improvements

The `run_server.py` script has been enhanced to:

1. Support multiple worker processes using Python's multiprocessing module
2. Increase default timeouts to prevent premature connection closures
3. Provide better error handling and recovery
4. Use more flexible SSL certificate paths

### Client-Side Improvements

The frontend JavaScript in `templates/index.html` has been enhanced with:

1. A robust EventSource wrapper with automatic reconnection
2. Connection timeout handling to prevent hanging connections
3. Improved error reporting to users
4. Better cleanup of resources when switching between operations

### Nginx Configuration

The Nginx configuration provides:

1. Special handling for Server-Sent Events (SSE) connections
2. Increased timeouts for long-running operations
3. Disabled buffering for streaming responses
4. HTTP/1.1 protocol support required for SSE
5. Security headers and SSL optimizations

#### Load Balancing Multiple Workers

When using multiple workers, you'll need to update the Nginx configuration to load balance across all worker ports. Here's an example configuration:

```nginx
# Define upstream servers (one for each worker)
upstream casestrainer_workers {
    server localhost:5000;
    server localhost:5001;
    server localhost:5002;
    server localhost:5003;
    # Add more servers if using more workers
}

# Then replace the proxy_pass directives with:
location / {
    proxy_pass http://casestrainer_workers;
    # Other proxy settings remain the same
}
```

This configuration distributes incoming requests across all worker processes, providing better performance and reliability.

## Troubleshooting

### Connection Issues

If users experience connection issues:

1. Check the server logs: `journalctl -u casestrainer -f`
2. Verify Nginx is properly configured for SSE
3. Increase timeouts if operations are taking longer than expected
4. Check browser console for client-side errors

### Performance Issues

If the server is slow or unresponsive:

1. Increase the number of worker processes and threads
2. Monitor CPU and memory usage
3. Consider distributing the load across multiple servers
4. Optimize database queries and API calls

## Further Improvements

Consider these additional improvements for high-traffic deployments:

1. Implement a load balancer for horizontal scaling
2. Use Redis for session management and caching
3. Implement a message queue for processing long-running tasks
4. Set up monitoring and alerting with Prometheus and Grafana
