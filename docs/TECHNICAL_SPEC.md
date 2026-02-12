# SYMBIONT-X Technical Specification

## Azure Resources

### Resource Group
- **Name:** rg-symbiontx-dev
- **Location:** East US
- **Purpose:** Container for all SYMBIONT-X resources

### Container Apps (3 agents)
1. **security-scanner-agent** - Port 8000, 1-5 replicas
2. **risk-assessment-agent** - Port 8001, 0-10 replicas  
3. **orchestrator-agent** - Port 8080, 2-5 replicas (HA)

### Azure Functions
- **Name:** func-symbiontx-dev
- **Runtime:** Python 3.11
- **Plan:** Consumption (Y1)

### Cosmos DB
- **Containers:** vulnerabilities, agents, decisions
- **Mode:** Serverless
- **Consistency:** Session

### Key Vault
- **Name:** kv-symbiontx-dev
- **Purpose:** Store GitHub token, API keys

### Application Insights
- **Purpose:** APM, metrics, tracing
