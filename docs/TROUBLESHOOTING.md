# CaseStrainer Troubleshooting Guide

This guide provides solutions for common issues that may arise when using or deploying CaseStrainer.

## Application Issues

### 1. Application Won't Start

**Symptoms:**

- Application fails to start
- Error messages in console
- Port already in use errors

**Solutions:**

1. Check if another instance is running:

   ```powershell
   tasklist | findstr python
   ```text

2. Kill any existing Python processes:

   ```powershell
   taskkill /f /im python.exe
   ```text

3. Verify port 5000 is available:

   ```powershell
   netstat -ano | findstr :5000
   ```text

4. Check Python version:

   ```powershell
   python --version
   ```text

   Ensure it's Python 3.8 or higher.

### 2. Nginx Container Issues

**Symptoms:**

- 502 Bad Gateway errors
- Nginx container won't start
- SSL certificate errors

**Solutions:**

1. Check Nginx container status:

   ```powershell
   docker ps | findstr nginx
   ```text

2. View Nginx logs:

   ```powershell
   docker logs casestrainer-nginx
   ```text

3. Verify SSL certificates:
   - Check `ssl` directory for certificate files
   - Ensure certificate names match configuration
   - Verify certificate permissions

4. Restart Nginx container:

   ```powershell
   docker stop casestrainer-nginx
   docker rm casestrainer-nginx
   docker run -d --name casestrainer-nginx --network casestrainer_default -p 443:443 -v "C:/Users/jafrank/OneDrive - UW/Documents/GitHub/CaseStrainer/ssl:/etc/nginx/ssl" -v "C:/Users/jafrank/OneDrive - UW/Documents/GitHub/CaseStrainer/conf/nginx.conf.new:/etc/nginx/nginx.conf" -v "C:/Users/jafrank/OneDrive - UW/Documents/GitHub/CaseStrainer/src/static:/etc/nginx/static" -v "C:/Users/jafrank/OneDrive - UW/Documents/GitHub/CaseStrainer/logs:/var/log/nginx" nginx:latest
   ```text

### 3. API Connection Issues

**Symptoms:**

- Citation verification fails
- API timeout errors
- Rate limit exceeded errors

**Solutions:**

1. Check API keys in `config.json`:

   ```json
   {
     "courtlistener_api_key": "your_key_here",
     "langsearch_api_key": "your_key_here"
   }
   ```text

2. Verify API endpoints are accessible:

   ```powershell
   curl https://www.courtlistener.com/api/rest/v4/citation-lookup/
   ```text

3. Check rate limits:
   - Monitor API usage
   - Implement exponential backoff
   - Cache frequently used results

### 4. Database Issues

**Symptoms:**

- Database connection errors
- Missing or corrupted data
- Slow query performance

**Solutions:**

1. Check database file:

   ```powershell
   dir casestrainer.db
   ```text

2. Verify database integrity:

   ```powershell
   sqlite3 casestrainer.db "PRAGMA integrity_check;"
   ```text

3. Check database logs:

   ```powershell
   type logs\database.log
   ```text

4. Rebuild indexes if needed:

   ```powershell
   sqlite3 casestrainer.db "REINDEX;"
   ```text

### 5. Vue.js Frontend Issues

**Symptoms:**

- Frontend won't load
- API calls fail
- UI components not rendering

**Solutions:**

1. Check browser console for errors
2. Verify API endpoint configuration:

   ```javascript
   const API_URL = process.env.NODE_ENV === 'production'
     ? '/casestrainer/api'
     : '/api';
   ```text

3. Rebuild frontend:

   ```bash
   cd casestrainer-vue
   npm install
   npm run build
   ```text

## Deployment Issues

### 1. Docker Network Issues

**Symptoms:**

- Containers can't communicate
- Network not found errors
- Connection refused errors

**Solutions:**

1. Check Docker network:

   ```powershell
   docker network ls | findstr casestrainer
   ```text

2. Create network if missing:

   ```powershell
   docker network create casestrainer_default
   ```text

3. Verify container network settings:

   ```powershell
   docker inspect casestrainer-nginx
   ```text

### 2. File Permission Issues

**Symptoms:**

- Can't access files
- Permission denied errors
- File not found errors

**Solutions:**

1. Check file permissions:

   ```powershell
   icacls "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\ssl"
   ```text

2. Verify directory structure:

   ```powershell
   dir "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer"
   ```text

3. Ensure proper ownership:

   ```powershell
   takeown /f "path\to\file" /r
   ```text

### 3. SSL Certificate Issues

**Symptoms:**

- SSL handshake failures
- Certificate not trusted
- Mixed content warnings

**Solutions:**

1. Verify certificate chain:

   ```powershell
   openssl verify -CAfile ssl/WolfCertBundle.crt ssl/wolf.law.uw.edu.crt
   ```text

2. Check certificate dates:

   ```powershell
   openssl x509 -in ssl/wolf.law.uw.edu.crt -text -noout | findstr "Not Before Not After"
   ```text

3. Update Nginx SSL configuration:

   ```nginx
   ssl_certificate /etc/nginx/ssl/wolf.law.uw.edu.crt;
   ssl_certificate_key /etc/nginx/ssl/wolf.law.uw.edu.key;
   ```text

## Performance Issues

### 1. Slow Citation Verification

**Symptoms:**

- Long verification times
- High CPU usage
- Timeout errors

**Solutions:**

1. Implement caching:
   - Use Redis for caching
   - Cache verification results
   - Set appropriate TTL

2. Optimize database queries:
   - Add missing indexes
   - Use prepared statements
   - Implement connection pooling

3. Scale horizontally:
   - Add more worker processes
   - Use load balancing
   - Implement request queuing

### 2. High Memory Usage

**Symptoms:**

- Out of memory errors
- Slow response times
- System instability

**Solutions:**

1. Monitor memory usage:

   ```powershell
   Get-Process python | Select-Object WorkingSet
   ```text

2. Optimize Python memory:
   - Use generators
   - Implement garbage collection
   - Limit batch sizes

3. Adjust Nginx settings:

   ```nginx
   worker_processes auto;
   worker_rlimit_nofile 65535;
   ```text

## Security Issues

### 1. API Key Exposure

**Symptoms:**

- Unauthorized API access
- Rate limit exceeded
- Suspicious activity

**Solutions:**

1. Rotate API keys
2. Implement key validation
3. Add request signing
4. Monitor API usage

### 2. SSL/TLS Issues

**Symptoms:**

- SSL handshake failures
- Certificate warnings
- Security vulnerabilities

**Solutions:**

1. Update SSL configuration:

   ```nginx
   ssl_protocols TLSv1.2 TLSv1.3;
   ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
   ```text

2. Enable HSTS:

   ```nginx
   add_header Strict-Transport-Security "max-age=31536000" always;
   ```text

3. Regular certificate updates

## Monitoring and Logging

### 1. Log Analysis

**Symptoms:**

- Missing logs
- Incomplete information
- Log rotation issues

**Solutions:**

1. Check log configuration:

   ```python
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('logs/app.log'),
           logging.StreamHandler()
       ]
   )
   ```text

2. Implement log rotation:

   ```python
   from logging.handlers import RotatingFileHandler
   handler = RotatingFileHandler('logs/app.log', maxBytes=10000000, backupCount=5)
   ```text

### 2. Performance Monitoring

**Symptoms:**

- Unresponsive application
- High resource usage
- Slow response times

**Solutions:**

1. Implement monitoring:
   - Use Prometheus for metrics
   - Set up Grafana dashboards
   - Configure alerts

2. Monitor key metrics:
   - Response times
   - Error rates
   - Resource usage
   - API latency

## Getting Help

If you encounter issues not covered in this guide:

1. Check the application logs:

   ```powershell
   type logs\app.log
   ```text

2. Review Nginx logs:

   ```powershell
   docker logs casestrainer-nginx
   ```text

3. Contact support:
   - Create a GitHub issue
   - Include relevant logs
   - Provide reproduction steps
   - Specify environment details
