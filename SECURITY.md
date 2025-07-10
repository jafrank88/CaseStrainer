# Security Guide

This document outlines security best practices for CaseStrainer deployment and operation.

## API Key Security

### Critical Security Requirements

**Never store API keys in version-controlled files.** All API keys must be stored as environment variables.

### Required API Keys

1. **CourtListener API Key**
   - Purpose: Citation verification and canonical data lookup
   - Get your key: https://www.courtlistener.com/help/api/rest/
   - Environment variable: `COURTLISTENER_API_KEY`

2. **LangSearch API Key** (optional)
   - Purpose: Advanced text analysis features
   - Environment variable: `LANGSEARCH_API_KEY`

### Secure Setup Instructions

#### Development Environment

**Windows (PowerShell):**
```powershell
$env:COURTLISTENER_API_KEY="your_courtlistener_api_key_here"
$env:LANGSEARCH_API_KEY="your_langsearch_api_key_here"
```

**Linux/macOS (bash):**
```bash
export COURTLISTENER_API_KEY="your_courtlistener_api_key_here"
export LANGSEARCH_API_KEY="your_langsearch_api_key_here"
```

#### Production Docker Deployment

```powershell
# Set environment variables for Docker containers
docker-compose -f docker-compose.prod.yml up -d --build \
  -e COURTLISTENER_API_KEY="your_courtlistener_api_key_here" \
  -e LANGSEARCH_API_KEY="your_langsearch_api_key_here"
```

#### Docker Compose Environment File (Recommended)

Create a `.env` file (not committed to version control):

```bash
# .env file
COURTLISTENER_API_KEY=your_courtlistener_api_key_here
LANGSEARCH_API_KEY=your_langsearch_api_key_here
```

Then reference it in docker-compose.yml:
```yaml
services:
  backend-prod:
    environment:
      - COURTLISTENER_API_KEY=${COURTLISTENER_API_KEY}
      - LANGSEARCH_API_KEY=${LANGSEARCH_API_KEY}
```

### Security Best Practices

#### ✅ Do This
- Store API keys as environment variables
- Use different keys for development and production
- Rotate API keys regularly
- Use Docker secrets for production deployments
- Monitor API key usage and set rate limits
- Use HTTPS for all API communications

#### ❌ Don't Do This
- Store API keys in config files
- Commit API keys to version control
- Hardcode API keys in source code
- Share API keys in logs or error messages
- Use the same key across multiple environments

### Key Rotation

1. **Generate new API key** from the service provider
2. **Update environment variables** with the new key
3. **Restart services** to pick up the new key
4. **Verify functionality** with the new key
5. **Revoke old key** after confirming everything works

### Monitoring and Alerts

- Monitor API key usage for unusual patterns
- Set up alerts for failed API calls
- Log API call success/failure rates
- Monitor rate limit usage

### Emergency Procedures

If an API key is compromised:

1. **Immediately revoke the key** from the service provider
2. **Generate a new key**
3. **Update all environment variables**
4. **Restart all services**
5. **Audit logs** for unauthorized usage
6. **Update documentation** with new key information

## Network Security

### HTTPS/TLS
- All external communications use HTTPS
- SSL certificates are properly configured
- TLS 1.2+ is enforced

### Firewall Configuration
- Only necessary ports are exposed
- Internal services are not directly accessible
- API endpoints are properly rate-limited

### Container Security
- Containers run with minimal privileges
- Base images are regularly updated
- Security patches are applied promptly

## Data Security

### File Uploads
- All uploaded files are scanned for malware
- File size limits are enforced
- Only allowed file types are processed

### Data Storage
- Sensitive data is not logged
- Temporary files are properly cleaned up
- Database connections use encryption

## Compliance

### Logging
- No sensitive data in logs
- Log rotation is configured
- Access logs are monitored

### Access Control
- API endpoints are properly authenticated
- Rate limiting is enforced
- Failed access attempts are logged

---

**Last Updated**: January 2025  
**Version**: 1.0 