# SYMBIONT-X Infrastructure as Code

Complete Azure infrastructure for SYMBIONT-X platform.

## Structure
```
bicep/
├── main.bicep                 # Main orchestration file
├── modules/                   # Reusable Bicep modules
│   ├── log-analytics.bicep
│   ├── app-insights.bicep
│   ├── cosmos-db.bicep
│   ├── key-vault.bicep
│   ├── container-registry.bicep
│   ├── container-apps-environment.bicep
│   ├── managed-identity.bicep
│   ├── container-app.bicep
│   ├── azure-functions.bicep
│   ├── service-bus.bicep
│   └── static-web-app.bicep
└── parameters/
    ├── dev.parameters.json    # Development environment
    └── prod.parameters.json   # Production environment
```

## Prerequisites

- Azure CLI (`az`) installed
- Azure subscription
- Contributor or Owner role on subscription

## Deployment

### 1. Get your Azure AD Object ID
```bash
az ad signed-in-user show --query id -o tsv
```

### 2. Update parameters file

Edit `parameters/dev.parameters.json` and replace `adminObjectId` with your Object ID.

### 3. Validate
```bash
az bicep build --file main.bicep
```

### 4. Preview changes (What-If)
```bash
az deployment sub what-if \
  --location eastus \
  --template-file main.bicep \
  --parameters parameters/dev.parameters.json
```

### 5. Deploy
```bash
az deployment sub create \
  --name symbiontx-infra-$(date +%Y%m%d-%H%M%S) \
  --location eastus \
  --template-file main.bicep \
  --parameters parameters/dev.parameters.json
```

## Resources Created

| Resource | Type | Purpose |
|----------|------|---------|
| Resource Group | Microsoft.Resources | Container for all resources |
| Log Analytics | Microsoft.OperationalInsights | Centralized logging |
| Application Insights | Microsoft.Insights | APM and monitoring |
| Cosmos DB | Microsoft.DocumentDB | NoSQL database for state |
| Key Vault | Microsoft.KeyVault | Secrets management |
| Container Registry | Microsoft.ContainerRegistry | Docker images |
| Container Apps Env | Microsoft.App | Hosting environment |
| Security Scanner | Microsoft.App/containerApps | Vulnerability detection |
| Risk Assessment | Microsoft.App/containerApps | AI risk analysis |
| Orchestrator | Microsoft.App/containerApps | Agent coordination |
| Function App | Microsoft.Web/sites | Event processing |
| Service Bus | Microsoft.ServiceBus | Messaging queue |
| Static Web App | Microsoft.Web/staticSites | Frontend hosting |
| Managed Identity | Microsoft.ManagedIdentity | Secure authentication |

## Outputs

After deployment, you'll get:

- Container Registry login server
- Cosmos DB endpoint
- Key Vault URI
- Agent URLs (security-scanner, risk-assessment, orchestrator)
- Function App name
- Static Web App URL
- Managed Identity Client ID
- Application Insights connection string

## Cost Estimation

**Development Environment (~$50/month):**
- Container Apps: ~$15
- Cosmos DB (Serverless): ~$10
- Functions (Consumption): ~$5
- Other services: ~$20

**Production Environment (~$200/month):**
- Container Apps: ~$75
- Cosmos DB: ~$50
- Functions: ~$20
- Other services: ~$55

## Cleanup

To delete all resources:
```bash
az group delete --name rg-symbiontx-dev --yes --no-wait
```

## Troubleshooting

### Error: "Location not available"

Some resources have limited region availability. Ensure `location` is set to a supported region (e.g., `eastus`, `westus2`).

### Error: "Quota exceeded"

Check your subscription quotas:
```bash
az vm list-usage --location eastus --output table
```

### Error: "Name already exists"

Bicep uses unique suffixes, but if deployment fails and you retry, you may need to delete the resource group first.

## Next Steps

1. Build and push Docker images to Container Registry
2. Update Container Apps with actual images
3. Configure secrets in Key Vault
4. Deploy Functions code
5. Deploy frontend to Static Web App

---

**Version:** 1.0  
**Last Updated:** February 2026  
**Project:** SYMBIONT-X
