# ⚠️ DEPRECATED - auto_deprecate_markdown.py

> **This file has been deprecated and moved to the archived documentation.**

## Deprecation Information
- **Date Deprecated**: 2025-07-19 15:12:58
- **Reason**: Superseded by CONSOLIDATED_DOCUMENTATION.md
- **Replacement**: See `CONSOLIDATED_DOCUMENTATION.md` for current documentation

## Original Content
The original content has been preserved below for reference:

---

# Docker Configuration Disabled

## Important Notice

As of May 16, 2025, Docker is **NOT** being used for the CaseStrainer deployment. All Docker-related files in this repository are currently inactive and should not be used.

## Current Deployment Configuration

The current deployment uses:
- Native Flask application running directly on the host
- Nginx for reverse proxy and SSL termination
- Windows batch scripts for application management

## Docker-Related Files (Inactive)

The following Docker-related files are present in the repository but are not in use:
- `Dockerfile`
- `docker-compose.yml`
- `docker/` directory and its contents
- `scripts/run_hyperscan_docker.bat`

## Restart Instructions

To restart the CaseStrainer application:
1. Run `restart_casestrainer.bat` from the main directory
2. For development mode, run `restart_casestrainer.bat dev`

## Nginx Configuration

The Nginx configuration has been updated to work without Docker:
- Proxy passes to `127.0.0.1:5000` instead of Docker-specific hostnames
- To reload Nginx configuration, run `scripts/reload_nginx.bat`
