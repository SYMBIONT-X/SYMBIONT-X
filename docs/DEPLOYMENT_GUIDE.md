# SYMBIONT-X Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Azure Deployment](#azure-deployment)
5. [Configuration](#configuration)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (for containerized deployment)
- Git
- Azure CLI (for Azure deployment)

### Required Accounts
- GitHub account with repo access
- Azure subscription (for cloud deployment)
- OpenAI API key (optional, for AI features)

---

## Local Development

### 1. Clone Repository
```bash
git clone https://github.com/SYMBIONT-X/SYMBIONT-X.git
cd SYMBIONT-X
```

### 2. Setup Python Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 3. Setup Frontend
```bash
cd src/frontend
npm install
cd ../..
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Start All Agents

Open 4 terminal windows:

**Terminal 1 - Orchestrator:**
```bash
cd src/agents/orchestrator
source ../../venv/bin/activate
python main.py
# Runs on http://localhost:8000
```

**Terminal 2 - Security Scanner:**
```bash
cd src/agents/security-scanner
source ../../venv/bin/activate
python main.py
# Runs on http://localhost:8001
```

**Terminal 3 - Risk Assessment:**
```bash
cd src/agents/risk-assessment
source ../../venv/bin/activate
python main.py
# Runs on http://localhost:8002
```

**Terminal 4 - Auto-Remediation:**
```bash
cd src/agents/auto-remediation
source ../../venv/bin/activate
python main.py
# Runs on http://localhost:8003
```

### 6. Start Frontend
```bash
cd src/frontend
npm run dev
# Runs on http://localhost:5173
```

### 7. Verify Installation
```bash
curl http://localhost:8000/health
```

---

## Docker Deployment

### 1. Build Images
```bash
docker-compose build
```

### 2. Start Services
```bash
docker-compose up -d
```

### 3. Check Status
```bash
docker-compose ps
docker-compose logs -f
```

### 4. Stop Services
```bash
docker-compose down
```

### Docker Compose File
```yaml
version: '3.8'

services:
  orchestrator:
    build:
      context: .
      dockerfile: src/agents/orchestrator/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - SCANNER_URL=http://scanner:8001
      - ASSESSMENT_URL=http://assessment:8002
      - REMEDIATION_URL=http://remediation:8003
    depends_on:
      - scanner
      - assessment
      - remediation

  scanner:
    build:
      context: .
      dockerfile: src/agents/security-scanner/Dockerfile
    ports:
      - "8001:8001"

  assessment:
    build:
      context: .
      dockerfile: src/agents/risk-assessment/Dockerfile
    ports:
      - "8002:8002"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}

  remediation:
    build:
      context: .
      dockerfile: src/agents/auto-remediation/Dockerfile
    ports:
      - "8003:8003"
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}

  frontend:
    build:
      context: ./src/frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - orchestrator

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

---

## Azure Deployment

### 1. Login to Azure
```bash
az login
az account set --subscription "Your Subscription"
```

### 2. Create Resource Group
```bash
az group create \
  --name rg-symbiontx-prod \
  --location eastus
```

### 3. Create Container Registry
```bash
az acr create \
  --resource-group rg-symbiontx-prod \
  --name symbiontxacr \
  --sku Basic

az acr login --name symbiontxacr
```

### 4. Build and Push Images
```bash
# Build and tag
docker build -t symbiontxacr.azurecr.io/orchestrator:latest ./src/agents/orchestrator
docker build -t symbiontxacr.azurecr.io/scanner:latest ./src/agents/security-scanner
docker build -t symbiontxacr.azurecr.io/assessment:latest ./src/agents/risk-assessment
docker build -t symbiontxacr.azurecr.io/remediation:latest ./src/agents/auto-remediation

# Push
docker push symbiontxacr.azurecr.io/orchestrator:latest
docker push symbiontxacr.azurecr.io/scanner:latest
docker push symbiontxacr.azurecr.io/assessment:latest
docker push symbiontxacr.azurecr.io/remediation:latest
```

### 5. Create Azure Container Apps Environment
```bash
az containerapp env create \
  --name symbiontx-env \
  --resource-group rg-symbiontx-prod \
  --location eastus
```

### 6. Deploy Container Apps
```bash
# Deploy each agent
az containerapp create \
  --name orchestrator \
  --resource-group rg-symbiontx-prod \
  --environment symbiontx-env \
  --image symbiontxacr.azurecr.io/orchestrator:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server symbiontxacr.azurecr.io

# Repeat for other agents...
```

### 7. Configure Secrets
```bash
az containerapp secret set \
  --name orchestrator \
  --resource-group rg-symbiontx-prod \
  --secrets "github-token=${GITHUB_TOKEN}" "openai-key=${OPENAI_API_KEY}"
```

### 8. Setup Application Insights
```bash
az monitor app-insights component create \
  --app symbiontx-insights \
  --location eastus \
  --resource-group rg-symbiontx-prod
```

---

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub API token for repo access | Yes |
| `OPENAI_API_KEY` | OpenAI API key for AI features | No |
| `AZURE_AD_TENANT_ID` | Azure AD tenant for auth | No |
| `AZURE_AD_CLIENT_ID` | Azure AD client ID | No |
| `REDIS_URL` | Redis connection URL | No |
| `AUTH_ENABLED` | Enable authentication | No |
| `TEAMS_WEBHOOK_URL` | Teams notification webhook | No |

### Agent URLs (for Orchestrator)
```
SCANNER_URL=http://localhost:8001
ASSESSMENT_URL=http://localhost:8002
REMEDIATION_URL=http://localhost:8003
```

---

## Monitoring

### Health Checks
```bash
# All agents
curl http://localhost:8000/health

# Individual agents
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

### Performance Stats
```bash
curl http://localhost:8000/performance/stats
```

### Logs
```bash
# Docker
docker-compose logs -f orchestrator

# Azure
az containerapp logs show --name orchestrator -g rg-symbiontx-prod
```

---

## Troubleshooting

### Agent Not Starting
1. Check port availability: `lsof -i :8000`
2. Verify Python environment: `which python`
3. Check logs for errors

### Connection Refused Between Agents
1. Verify all agents are running
2. Check firewall rules
3. Verify URLs in configuration

### Frontend Can't Connect
1. Check CORS settings
2. Verify backend URLs in frontend config
3. Check browser console for errors

### Rate Limiting Issues
1. Check `X-RateLimit-*` headers
2. Wait for rate limit window reset
3. Increase limits if needed

### Memory Issues
1. Increase container memory limits
2. Check for memory leaks
3. Reduce cache size

---

## Scaling

### Horizontal Scaling
```bash
# Docker Compose
docker-compose up -d --scale scanner=3

# Azure Container Apps
az containerapp update \
  --name scanner \
  --resource-group rg-symbiontx-prod \
  --min-replicas 2 \
  --max-replicas 10
```

### Load Balancing
- Use Azure Front Door or Application Gateway
- Configure health probes on `/health` endpoints
- Enable session affinity if needed

---

## Security Checklist

- [ ] Change default JWT secret
- [ ] Enable HTTPS everywhere
- [ ] Configure Azure AD authentication
- [ ] Set up network security groups
- [ ] Enable audit logging
- [ ] Rotate secrets regularly
- [ ] Enable rate limiting
- [ ] Configure WAF rules
