# Multi-User Deployment Guide for CaseStrainer

This guide explains how to deploy CaseStrainer in a multi-user environment, allowing multiple users to use the application simultaneously.

## Prerequisites

- Python 3.6 or higher
- pip (Python package manager)
- Waitress (installed automatically by the run script if not present)

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
python run_server.py --threads 16 --port 8000 --host 0.0.0.0 --channel-timeout 180 --connection-limit 2000
```

Available options:

- `--threads`: Number of threads (default: 8)
- `--port`: Port to run the server on (default: 5000)
- `--host`: Host to run the server on (default: 0.0.0.0)
- `--channel-timeout`: Channel timeout in seconds (default: 120)
- `--connection-limit`: Maximum number of connections (default: 1000)

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

### Threads per Worker

The number of threads per worker determines how many concurrent requests each worker can handle. A good starting point is 2-4 threads per worker.

```bash
python run_server.py --threads 4
```

### Worker Timeout

For long-running analyses with many citations, you may need to increase the worker timeout:

```bash
python run_server.py --timeout 300  # 5 minutes
```

## Monitoring

When running in production, you should monitor the server's performance and resource usage. Consider using tools like:

- Prometheus for metrics collection
- Grafana for visualization
- Sentry for error tracking

## Troubleshooting

### Server Won't Start

- Check if the port is already in use by another application
- Ensure you have the necessary permissions to bind to the specified port
- Verify that all required dependencies are installed

### Connection Errors

- Check if the server is running and accessible from the client's network
- Verify SSL certificate configuration if using HTTPS
- Check firewall settings to ensure the port is open

### Performance Issues

- Increase the number of workers and/or threads
- Check server resource usage (CPU, memory, disk I/O)
- Consider using a more powerful server or distributing the load across multiple servers

## Security Considerations

- Always use HTTPS in production environments
- Set a strong SECRET_KEY for session management
- Keep API keys and other sensitive information secure
- Regularly update dependencies to patch security vulnerabilities
