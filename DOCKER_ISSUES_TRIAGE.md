# Docker Desktop Issues Triage & Prevention Guide

## 🔍 Issue Analysis

Based on our troubleshooting session, here are the **recurring Docker Desktop issues** and their root causes:

### **1. Docker Desktop Port Binding Conflicts**
**Symptoms:**
- `wslrelay` and `com.docker.backend` binding to port 80
- Containers can't bind to their intended ports
- "Docker socket not accessible" errors
- Health checks fail despite containers being "healthy"

**Root Cause:** Docker Desktop's WSL2 integration creates port conflicts where Docker Desktop intercepts ports instead of allowing containers to bind to them.

**Detection:**
```powershell
netstat -ano | findstr ":80" | findstr "LISTENING"
```

**Solution:** Complete restart of Docker Desktop resolves port binding conflicts.

### **2. Docker CLI 500 Internal Server Errors**
**Symptoms:**
- `request returned 500 Internal Server Error for API route`
- Docker CLI commands fail intermittently
- Communication issues between Docker CLI and Docker Desktop

**Root Cause:** Docker Desktop's internal API becomes unresponsive due to resource exhaustion or WSL2 communication issues.

**Detection:**
```powershell
docker ps
# Returns 500 errors instead of container list
```

**Solution:** Restart Docker Desktop processes and wait for proper initialization.

### **3. Container Networking Issues**
**Symptoms:**
- Containers appear to be running but aren't accessible
- Health checks fail despite containers being "healthy"
- Port conflicts between Docker Desktop and containers

**Root Cause:** Docker Desktop's networking stack conflicts with container port mappings.

**Detection:**
```powershell
Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health"
# Returns timeout or connection errors
```

**Solution:** Restart containers and verify proper port mappings.

## 🛠️ Prevention Strategies

### **1. Enhanced Health Check Script**
The updated `docker_health_check.ps1` now includes:

- **Port Conflict Detection:** Automatically detects when Docker Desktop is binding to common ports
- **Enhanced Recovery:** More robust Docker Desktop restart process
- **Better Diagnostics:** Detailed logging of Docker Desktop processes

### **2. Preventive Maintenance Script**
The new `prevent_docker_issues.ps1` provides:

- **Proactive Health Checks:** Runs before issues occur
- **Auto-Fix Capability:** Automatically resolves common issues
- **Resource Optimization:** Clears unused Docker resources
- **Settings Configuration:** Optimizes Docker Desktop settings

### **3. Monitoring and Alerting**
Set up automated monitoring:

```powershell
# Schedule preventive maintenance
.\prevent_docker_issues.ps1 -AutoFix

# Schedule health checks
.\docker_health_check.ps1 -AutoRestart
```

## 📋 Prevention Checklist

### **Daily Checks:**
- [ ] Run `.\prevent_docker_issues.ps1` before starting work
- [ ] Check for port conflicts: `netstat -ano | findstr ":80"`
- [ ] Verify Docker CLI responsiveness: `docker --version`
- [ ] Test application accessibility: `Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health"`

### **Weekly Maintenance:**
- [ ] Clear unused Docker resources: `docker system prune -f`
- [ ] Restart Docker Desktop if issues detected
- [ ] Review Docker Desktop logs for patterns
- [ ] Update Docker Desktop to latest version

### **Monthly Optimization:**
- [ ] Review Docker Desktop resource allocation
- [ ] Clean up old images and containers
- [ ] Verify WSL2 integration settings
- [ ] Check for Docker Desktop updates

## 🚨 Emergency Procedures

### **When Docker CLI Returns 500 Errors:**
1. **Immediate:** Stop all Docker processes
2. **Wait:** 15 seconds for processes to stop
3. **Restart:** Docker Desktop completely
4. **Wait:** 45 seconds for initialization
5. **Test:** `docker ps` to verify functionality

### **When Containers Can't Bind to Ports:**
1. **Check:** Port conflicts with `netstat -ano`
2. **Stop:** Docker Desktop processes
3. **Restart:** Docker Desktop
4. **Verify:** Container port mappings
5. **Test:** Application accessibility

### **When Application Becomes Unresponsive:**
1. **Check:** Container health with `docker ps`
2. **Check:** Port accessibility with `netstat`
3. **Restart:** Containers if needed
4. **Verify:** Application endpoints
5. **Monitor:** Application logs

## 📊 Monitoring Commands

### **Health Check Commands:**
```powershell
# Check Docker CLI
docker --version

# Check container status
docker ps

# Check port conflicts
netstat -ano | findstr ":80"

# Check Docker processes
Get-Process | Where-Object { $_.ProcessName -like "*docker*" }

# Test application
Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health"
```

### **Recovery Commands:**
```powershell
# Stop Docker Desktop
Stop-Process -Name "Docker Desktop" -Force

# Stop Docker backend
Stop-Process -Name "com.docker.backend" -Force

# Restart Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Wait for initialization
Start-Sleep -Seconds 45
```

## 🔧 Configuration Recommendations

### **Docker Desktop Settings:**
- **WSL2 Backend:** Enable WSL2 integration
- **Memory:** Allocate 4GB RAM minimum
- **CPUs:** Allocate 2 CPU cores minimum
- **Disk Image Size:** 64GB minimum
- **File Sharing:** Enable for project directories

### **WSL2 Settings:**
- **Memory:** 4GB minimum
- **Processors:** 2 cores minimum
- **Swap:** 2GB minimum

### **Container Resource Limits:**
```yaml
# docker-compose.yml
services:
  casestrainer:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

## 📈 Performance Monitoring

### **Key Metrics to Monitor:**
- **Docker Desktop CPU Usage:** Should be < 50%
- **Docker Desktop Memory Usage:** Should be < 4GB
- **Container Response Times:** Should be < 5 seconds
- **Port Availability:** Ports 80, 443, 5000 should be accessible
- **WSL2 Performance:** Should be responsive

### **Alert Thresholds:**
- **High CPU Usage:** > 80% for > 5 minutes
- **High Memory Usage:** > 6GB for > 5 minutes
- **Port Conflicts:** Any Docker process binding to ports 80/443
- **Container Failures:** > 3 container restarts in 1 hour
- **API Timeouts:** > 10 second response times

## 🎯 Best Practices

### **Development Workflow:**
1. **Start:** Run `.\prevent_docker_issues.ps1` before development
2. **Monitor:** Use `.\docker_health_check.ps1` during development
3. **Cleanup:** Run `docker system prune` weekly
4. **Restart:** Docker Desktop if issues persist

### **Production Deployment:**
1. **Pre-flight:** Run health checks before deployment
2. **Monitoring:** Set up automated health checks
3. **Alerting:** Configure alerts for critical issues
4. **Recovery:** Automated recovery procedures

### **Troubleshooting Workflow:**
1. **Identify:** Use diagnostic scripts to identify issues
2. **Isolate:** Determine if it's a Docker Desktop or container issue
3. **Resolve:** Apply appropriate fix based on issue type
4. **Verify:** Test that the fix resolved the issue
5. **Document:** Record the issue and solution for future reference

## 📚 Additional Resources

- **Docker Desktop Documentation:** https://docs.docker.com/desktop/
- **WSL2 Integration:** https://docs.docker.com/desktop/wsl/
- **Troubleshooting Guide:** https://docs.docker.com/desktop/troubleshoot/
- **Performance Tuning:** https://docs.docker.com/desktop/settings/windows/

---

**Last Updated:** August 7, 2025  
**Version:** 1.0  
**Maintainer:** CaseStrainer Development Team
