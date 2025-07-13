# GitHub Actions Setup for CaseStrainer

This directory contains GitHub Actions workflows for automated testing, building, and deployment of the CaseStrainer application.

## Workflows Overview

### 1. `ci.yml` - Full CI/CD Pipeline
- **Triggers**: Push to `main`/`develop`, Pull Requests
- **Purpose**: Comprehensive testing and deployment
- **Jobs**:
  - Backend testing with Redis
  - Frontend build and testing
  - Docker container testing
  - Integration testing
  - E2E testing with Cypress
  - Security scanning
  - Production deployment (main branch only)

### 2. `pr-check.yml` - Pull Request Checks
- **Triggers**: Pull Requests only
- **Purpose**: Lightweight checks for PRs
- **Jobs**:
  - Quick backend tests
  - Frontend build verification
  - Docker build check

### 3. `deploy.yml` - Production Deployment
- **Triggers**: Push to `main` branch only
- **Purpose**: Production deployment with safety checks
- **Jobs**:
  - Pre-deployment validation
  - Production image building
  - Staging deployment (optional)
  - Production deployment

## Setup Instructions

### 1. Repository Secrets

Set up the following secrets in your GitHub repository (`Settings` → `Secrets and variables` → `Actions`):

#### Required Secrets:
```bash
COURTLISTENER_API_KEY=your_courtlistener_api_key_here
```

#### Optional Secrets (for deployment):
```bash
PRODUCTION_HOST=your_production_server_ip
PRODUCTION_USER=your_ssh_username
PRODUCTION_DEPLOY_KEY=your_private_ssh_key
STAGING_HOST=your_staging_server_ip
STAGING_USER=your_staging_ssh_username
STAGING_DEPLOY_KEY=your_staging_private_ssh_key
SLACK_WEBHOOK_URL=your_slack_webhook_url
NOTIFICATION_EMAIL=your_email@example.com
```

### 2. Branch Protection Rules

Set up branch protection for `main` and `develop`:

1. Go to `Settings` → `Branches`
2. Add rule for `main` and `develop`
3. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Include administrators

### 3. Required Status Checks

Add these status checks to branch protection:
- `Backend Tests`
- `Frontend Build`
- `Docker Build`
- `Integration Tests`
- `E2E Tests`
- `Security Scan`

## Workflow Details

### Backend Testing
- Runs Python 3.11
- Installs dependencies from `requirements.txt`
- Runs pytest with coverage
- Performs security scanning with Bandit
- Tests Redis connectivity

### Frontend Testing
- Runs Node.js 18
- Installs npm dependencies
- Builds Vue.js application
- Runs linting and unit tests
- Generates production build

### Docker Testing
- Builds all Docker images
- Starts services (Redis, Backend, RQ Worker)
- Tests service health endpoints
- Verifies container communication

### Integration Testing
- Tests citation extraction
- Tests clustering algorithms
- Tests API endpoints
- Validates PowerShell scripts

### E2E Testing
- Runs Cypress tests
- Tests user workflows
- Captures screenshots and videos on failure
- Tests full application stack

### Security Scanning
- Bandit for Python security
- Safety for dependency vulnerabilities
- Generates security reports

## Customization

### Adding New Tests

1. **Backend Tests**: Add new test files in the root directory or `src/` directory
2. **Frontend Tests**: Add tests in `casestrainer-vue-new/src/`
3. **E2E Tests**: Add Cypress tests in `casestrainer-vue-new/cypress/e2e/`

### Modifying Deployment

Edit the deployment steps in `deploy.yml`:
```yaml
- name: Deploy to production
  run: |
    # Add your deployment commands here
    ssh user@server "cd /opt/casestrainer && git pull"
    ssh user@server "cd /opt/casestrainer && docker-compose up -d"
```

### Environment Variables

Add new environment variables in `config.yml`:
```yaml
env:
  NEW_VARIABLE: ${{ secrets.NEW_VARIABLE }}
```

## Troubleshooting

### Common Issues

1. **Tests Failing**: Check the workflow logs for specific error messages
2. **Docker Build Failures**: Verify Dockerfile syntax and dependencies
3. **Frontend Build Issues**: Check Node.js version compatibility
4. **Redis Connection Errors**: Verify Redis service configuration

### Debugging

1. **Enable Debug Logging**: Add `ACTIONS_STEP_DEBUG: true` to repository secrets
2. **Check Artifacts**: Download and inspect uploaded artifacts
3. **Local Testing**: Run workflows locally using [act](https://github.com/nektos/act)

### Performance Optimization

1. **Cache Dependencies**: Workflows use caching for pip and npm dependencies
2. **Parallel Jobs**: Jobs run in parallel where possible
3. **Matrix Testing**: Consider adding matrix builds for multiple Python/Node versions

## Monitoring

### Workflow Status
- Check workflow status in the `Actions` tab
- Set up notifications for workflow failures
- Monitor deployment success rates

### Metrics
- Test coverage reports
- Security scan results
- Build times and success rates
- Deployment frequency

## Security Considerations

1. **Secrets Management**: Never commit secrets to the repository
2. **Dependency Scanning**: Regular security scans are automated
3. **Access Control**: Limit who can approve deployments
4. **Audit Logs**: Monitor workflow execution logs

## Support

For issues with GitHub Actions:
1. Check the [GitHub Actions documentation](https://docs.github.com/en/actions)
2. Review workflow logs for error details
3. Test changes locally before pushing
4. Use GitHub's community forums for help 