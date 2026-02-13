# GitHub Actions Workflows

Automated CI/CD pipelines for SYMBIONT-X.

## Workflows

### 1. CI Build & Test (`ci-build.yml`)
**Triggers:** PR to main/develop, Push to main/develop  
**Purpose:** Quality checks and tests  

**Jobs:**
- Python linting (flake8, black, isort, mypy)
- Python tests (pytest with coverage)
- Frontend linting (ESLint, Prettier, TypeScript)
- Frontend tests (Vitest)
- Docker build validation

**Duration:** ~5 minutes

---

### 2. Deploy to Dev (`deploy-dev.yml`)
**Triggers:** Push to main, Manual  
**Purpose:** Automatic deployment to development environment  

**Jobs:**
- Build & push Docker images to ACR
- Deploy Container Apps (3 agents)
- Deploy Azure Functions
- Deploy frontend to Static Web App
- Smoke tests

**Duration:** ~10 minutes

---

### 3. Deploy to Production (`deploy-prod.yml`)
**Triggers:** Manual only  
**Purpose:** Controlled production deployment  

**Requirements:**
- Manual trigger with version tag (e.g., v1.0.0)
- Type "DEPLOY" to confirm
- Environment approval required

**Jobs:**
- Validation
- Deploy agents, functions, frontend
- Production smoke tests
- Create GitHub release

**Duration:** ~12 minutes

---

### 4. Security Scan (`security-scan.yml`)
**Triggers:** Push, PR, Weekly (Sunday 00:00 UTC), Manual  
**Purpose:** Comprehensive security scanning  

**Scans:**
- Python dependencies (Safety)
- Python code security (Bandit)
- Secrets detection (TruffleHog)
- Container images (Trivy)
- npm audit
- SAST (CodeQL)
- Infrastructure (Checkov)

**Duration:** ~8 minutes

---

## Required Secrets

### Repository Secrets
```
AZURE_SUBSCRIPTION_ID
AZURE_TENANT_ID
AZURE_CLIENT_ID
ACR_NAME
FUNCTION_APP_NAME
DEV_ORCHESTRATOR_URL
DEV_SCANNER_URL
DEV_API_URL
DEV_FRONTEND_URL
AZURE_STATIC_WEB_APPS_API_TOKEN_DEV
```

### Production Secrets (optional)
```
FUNCTION_APP_NAME_PROD
PROD_ORCHESTRATOR_URL
PROD_SCANNER_URL
PROD_API_URL
PROD_FRONTEND_URL
AZURE_STATIC_WEB_APPS_API_TOKEN_PROD
```

---

## Environments

### Development
- No approval required
- Auto-deploys on push to main

### Production
- Requires 1 reviewer approval
- Manual trigger only
- Version tag required

---

## Branch Protection

### `main` branch
- Require PR with 1 approval
- Require status checks:
  - Python Code Quality
  - Python Tests
  - Frontend Code Quality
  - Frontend Tests
  - Docker Build Test
- Require conversation resolution
- Require linear history
- No force pushes
- No deletions

---

## Local Testing

### Test workflow syntax
```bash
# Install act (GitHub Actions local runner)
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run a workflow locally
act -W .github/workflows/ci-build.yml
```

### Validate YAML syntax
```bash
# Using yamllint
yamllint .github/workflows/*.yml

# Using actionlint
actionlint .github/workflows/*.yml
```

---

## Troubleshooting

### Failed deployment
1. Check GitHub Actions logs
2. Verify Azure credentials (secrets)
3. Check resource quotas in Azure
4. Validate Docker images built successfully

### Status checks not running
1. Ensure workflows are in `.github/workflows/`
2. Check trigger conditions match your branch/event
3. Verify YAML syntax is valid

### Secrets not found
1. Go to Settings → Secrets → Actions
2. Verify secret names match exactly (case-sensitive)
3. Re-create Service Principal if expired

---

**Version:** 1.0  
**Last Updated:** February 2026  
**Project:** SYMBIONT-X
