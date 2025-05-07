# CaseStrainer Deployment Guide

This guide will help you deploy CaseStrainer to wolf.law.uw.edu/casestrainer with Nginx.

## Required Files

The following files are essential for deployment:

1. `app_final.py` - Main application
2. `pdf_handler.py` - PDF processing module
3. `templates/fixed_form_ajax.html` - UI template
4. `config.json` - API keys configuration
5. `run_production.py` - Production deployment script
6. `nginx_casestrainer.conf` - Nginx configuration

## Deployment Steps

### 1. Install Dependencies

```bash
pip install flask python-docx PyPDF2 pdfminer.six requests cheroot
```

### 2. Configure Nginx

There are two ways to configure Nginx with your Flask application:

#### Option 1: TCP Socket (Recommended for simplicity)

1. Copy the provided `nginx_casestrainer.conf` to your Nginx configuration directory:
   ```bash
   sudo cp nginx_casestrainer.conf /etc/nginx/sites-available/casestrainer
   sudo ln -s /etc/nginx/sites-available/casestrainer /etc/nginx/sites-enabled/
   ```

2. Edit the configuration if needed to match your server's setup.

3. Restart Nginx:
   ```bash
   sudo systemctl restart nginx
   ```

4. Run the application on the TCP port:
   ```bash
   python run_production.py --host 127.0.0.1 --port 8000
   ```

#### Option 2: Unix Socket (Better performance)

1. Uncomment the Unix socket section in `nginx_casestrainer.conf` and comment out the TCP socket section.

2. Copy the configuration to Nginx:
   ```bash
   sudo cp nginx_casestrainer.conf /etc/nginx/sites-available/casestrainer
   sudo ln -s /etc/nginx/sites-available/casestrainer /etc/nginx/sites-enabled/
   ```

3. Create a directory for the socket with proper permissions:
   ```bash
   sudo mkdir -p /tmp/casestrainer
   sudo chown www-data:www-data /tmp/casestrainer
   ```

4. Run the application with the Unix socket:
   ```bash
   python run_production.py --unix-socket /tmp/casestrainer/casestrainer.sock
   ```

### 3. Run as a Service (Recommended)

For production, it's best to run the application as a service so it starts automatically:

1. Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/casestrainer.service
   ```

2. Add the following content:
   ```
   [Unit]
   Description=CaseStrainer Application
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/casestrainer
   ExecStart=/usr/bin/python3 run_production.py --host 127.0.0.1 --port 8000
   # Or for Unix socket:
   # ExecStart=/usr/bin/python3 run_production.py --unix-socket /tmp/casestrainer/casestrainer.sock
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl enable casestrainer
   sudo systemctl start casestrainer
   ```

4. Check the status:
   ```bash
   sudo systemctl status casestrainer
   ```

## Troubleshooting

### Nginx Error

If you see an Nginx error, check the following:

1. **Nginx logs**:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

2. **Application logs**:
   ```bash
   sudo journalctl -u casestrainer
   ```

3. **Permissions**:
   - Make sure Nginx can access the socket or port
   - Check that the application has permission to create the socket

4. **Firewall**:
   - Ensure the port is open if using TCP

5. **SELinux** (if applicable):
   - Check SELinux permissions with `sestatus`
   - Allow Nginx to connect to the socket/port

### Common Issues

1. **502 Bad Gateway**: Usually means Nginx can't connect to your application
   - Check if the application is running
   - Verify the socket/port configuration

2. **404 Not Found**: Check URL rewriting in Nginx config
   - Ensure the `location` block is correct
   - Check that the `rewrite` rule is working

3. **Permission Denied**: Check file and socket permissions
   - Make sure the application and Nginx have appropriate permissions

## Testing

After deployment, test the application by:

1. Visiting https://wolf.law.uw.edu/casestrainer in your browser
2. Uploading a test PDF file
3. Testing the problematic "999562 Plaintiff Opening Brief.pdf"

## Maintenance

To update the application:

1. Stop the service:
   ```bash
   sudo systemctl stop casestrainer
   ```

2. Update the files
3. Start the service:
   ```bash
   sudo systemctl start casestrainer
   ```
