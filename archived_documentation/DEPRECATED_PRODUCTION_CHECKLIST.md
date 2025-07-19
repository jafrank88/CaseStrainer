# ⚠️ DEPRECATED - auto_deprecate_markdown.py

> **This file has been deprecated and moved to the archived documentation.**

## Deprecation Information
- **Date Deprecated**: 2025-07-19 15:12:58
- **Reason**: Superseded by CONSOLIDATED_DOCUMENTATION.md
- **Replacement**: See `CONSOLIDATED_DOCUMENTATION.md` for current documentation

## Original Content
The original content has been preserved below for reference:

---

# CaseStrainer Production Readiness Checklist

## ✅ **Already Fixed**
- [x] Removed obsolete Docker Compose version warning
- [x] Dockerfile casing is correct (no issues found)
- [x] RQ worker and Redis setup working correctly
- [x] Async task processing functional
- [x] Frontend polling and result display working

## 🚨 **Critical Issues (Must Fix Before Production)**

### 1. **SECURITY: Hardcoded API Keys and Secrets** ⚠️ **CRITICAL**
**Issue**: API keys and secrets were hardcoded in config files
**Impact**: Major security vulnerability - exposed API keys
**Status**: ✅ **FIXED** - Removed hardcoded secrets from config.json files
**Action Required**: 
- Update `.env.production` with your actual API keys
- Never commit API keys to version control
- Consider rotating the exposed API keys

### 2. **SSL Certificate Configuration**
**Issue**: SSL certificates referenced but may not exist in `/ssl/` directory
**Impact**: HTTPS won't work, security risk
**Solution**: 
```bash
# Check if certificates exist
ls -la ssl/
# If missing, obtain proper SSL certificates for wolf.law.uw.edu
# Place them in ssl/ directory:
# - ssl/WolfCertBundle.crt
# - ssl/wolf.law.uw.edu.key
```

### 3. **Environment Variables**
**Issue**: Production environment variables need proper configuration
**Solution**: Create `.env.production` file:
```bash
FLASK_ENV=production
FLASK_APP=src/app_final_vue.py
SECRET_KEY=your-secure-secret-key-here
COURTLISTENER_API_KEY=your-courtlistener-api-key
REDIS_URL=redis://casestrainer-redis-prod:6379/0
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
LOG_LEVEL=INFO
SECRET_KEY
COURTLISTENER_API_KEY
LANGSEARCH_API_KEY
MAIL_USERNAME
MAIL_PASSWORD
MAIL_DEFAULT_SENDER
SECURITY_PASSWORD_SALT
```

### 4. **Database Configuration**
**Issue**: SQLite database path may not be production-ready
**Solution**: Ensure database directory exists and is writable:
```bash
mkdir -p data/
chmod 755 data/
```

## ⚠️ **Important Issues (Should Fix)**

### 5. **Nginx Configuration Paths**
**Issue**: Multiple nginx configs with different SSL certificate paths
**Solution**: Standardize SSL certificate paths in all nginx configs:
```nginx
ssl_certificate /etc/nginx/ssl/WolfCertBundle.crt;
ssl_certificate_key /etc/nginx/ssl/wolf.law.uw.edu.key;
```

### 6. **Security Headers**
**Issue**: Inconsistent security headers across configurations
**Solution**: Standardize security headers in nginx configs

### 7. **Logging Configuration**
**Issue**: Log directories may not exist
**Solution**: Create log directories:
```bash
mkdir -p logs/
chmod 755 logs/
```

## 🔧 **Recommended Fixes**

### 8. **Docker Production Setup**
**Issue**: Docker Compose production file needs environment variables
**Solution**: Add environment file support:
```yaml
# In docker-compose.prod.yml
services:
  backend:
    env_file:
      - .env.production
```

### 9. **Health Checks**
**Issue**: Health check endpoints need proper configuration
**Solution**: Ensure health check endpoints are accessible and working

### 10. **Rate Limiting**
**Issue**: Rate limiting configuration may need adjustment
**Solution**: Review and adjust rate limiting settings for production load

## 🔒 **Security Checklist**

- [x] **CRITICAL**: Removed hardcoded API keys from config files
- [ ] Rotate exposed API keys (CourtListener, LangSearch)
- [ ] Update `.env.production` with secure API keys
- [ ] Ensure SSL certificates are valid and secure
- [ ] Verify security headers are properly configured
- [ ] Check file upload security (file type validation)
- [ ] Review session security settings
- [ ] Ensure no secrets in version control
- [ ] Configure proper file permissions
- [ ] Set up secure logging (no sensitive data in logs)

## 📋 **Pre-Production Testing Checklist**

- [ ] SSL certificates are valid and accessible
- [ ] All environment variables are set correctly
- [ ] Database is accessible and writable
- [ ] Redis is running and accessible
- [ ] RQ worker is processing tasks correctly
- [ ] Frontend builds successfully
- [ ] Nginx configuration is valid
- [ ] Health checks are passing
- [ ] Rate limiting is configured appropriately
- [ ] Logging is working correctly
- [ ] File uploads are working
- [ ] Citation verification is functional

## 🚀 **Production Deployment Steps**

1. **Environment Setup**:
   ```bash
   # Create production environment
   cp .env.template .env.production
   # Edit .env.production with production values
   ```

2. **SSL Certificate Setup**:
   ```bash
   # Place SSL certificates in ssl/ directory
   # Ensure proper permissions (600 for key, 644 for cert)
   ```

3. **Database Setup**:
   ```bash
   # Create data directory
   mkdir -p data/
   # Initialize database if needed
   python src/init_db.py
   ```

4. **Build and Deploy**:
   ```bash
   # Build frontend
   cd casestrainer-vue-new && npm run build
   
   # Start production services
   docker-compose -f docker-compose.prod.yml up -d
   ```

5. **Verify Deployment**:
   ```bash
   # Check all services are running
   docker-compose -f docker-compose.prod.yml ps
   
   # Test health endpoints
   curl https://wolf.law.uw.edu/casestrainer/api/health
   ```

## 🔍 **Monitoring and Maintenance**

- [ ] Set up log rotation
- [ ] Configure monitoring alerts
- [ ] Set up backup strategy
- [ ] Plan for SSL certificate renewal
- [ ] Monitor Redis memory usage
- [ ] Track API rate limits
- [ ] Monitor file upload sizes

## 📞 **Emergency Contacts**

- **System Administrator**: [Contact Info]
- **SSL Certificate Provider**: [Contact Info]
- **Hosting Provider**: [Contact Info] 