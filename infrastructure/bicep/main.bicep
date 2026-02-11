// SYMBIONT-X Main Infrastructure Deployment
targetScope = 'subscription'

@description('Environment name (dev, staging, prod)')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string = 'dev'

@description('Primary Azure region')
param location string = 'eastus'

@description('Project name prefix')
param projectName string = 'symbiontx'

@description('Your Azure AD Object ID for Key Vault access')
param adminObjectId string

@description('GitHub repository URL for Static Web App')
param githubRepoUrl string = ''

@description('Timestamp for unique naming')
param timestamp string = utcNow('yyyyMMddHHmmss')

// Generate unique names
var uniqueSuffix = substring(uniqueString(subscription().id, projectName, environment), 0, 6)
var resourceGroupName = 'rg-${projectName}-${environment}'
var logAnalyticsName = 'log-${projectName}-${environment}-${uniqueSuffix}'
var appInsightsName = 'appi-${projectName}-${environment}-${uniqueSuffix}'
var cosmosAccountName = 'cosmos-${projectName}-${environment}-${uniqueSuffix}'
var keyVaultName = 'kv-${projectName}-${environment}${uniqueSuffix}'
var containerRegistryName = 'acr${projectName}${environment}${uniqueSuffix}'
var containerAppsEnvName = 'cae-${projectName}-${environment}'
var identityName = 'id-${projectName}-${environment}'
var functionAppName = 'func-${projectName}-${environment}-${uniqueSuffix}'
var storageAccountName = 'st${projectName}${environment}${uniqueSuffix}'
var serviceBusName = 'sb-${projectName}-${environment}-${uniqueSuffix}'
var staticWebAppName = 'swa-${projectName}-${environment}'

// Tags
var commonTags = {
  Environment: environment
  Project: 'SYMBIONT-X'
  ManagedBy: 'Bicep'
  DeployedAt: timestamp
}

// ============================================================================
// RESOURCE GROUP
// ============================================================================
resource resourceGroup 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
  tags: commonTags
}

// ============================================================================
// MANAGED IDENTITY
// ============================================================================
module managedIdentity 'modules/managed-identity.bicep' = {
  scope: resourceGroup
  name: 'deploy-managed-identity'
  params: {
    identityName: identityName
    location: location
    tags: commonTags
  }
}

// ============================================================================
// MONITORING & LOGGING
// ============================================================================
module logAnalytics 'modules/log-analytics.bicep' = {
  scope: resourceGroup
  name: 'deploy-log-analytics'
  params: {
    workspaceName: logAnalyticsName
    location: location
    environment: environment
    tags: commonTags
  }
}

module applicationInsights 'modules/app-insights.bicep' = {
  scope: resourceGroup
  name: 'deploy-app-insights'
  params: {
    appInsightsName: appInsightsName
    location: location
    workspaceId: logAnalytics.outputs.workspaceId
    tags: commonTags
  }
}

// ============================================================================
// DATA LAYER
// ============================================================================
module cosmosDb 'modules/cosmos-db.bicep' = {
  scope: resourceGroup
  name: 'deploy-cosmos-db'
  params: {
    cosmosAccountName: cosmosAccountName
    location: location
    environment: environment
    tags: commonTags
  }
}

module keyVault 'modules/key-vault.bicep' = {
  scope: resourceGroup
  name: 'deploy-key-vault'
  params: {
    keyVaultName: keyVaultName
    location: location
    tags: commonTags
  }
}

// ============================================================================
// MESSAGING
// ============================================================================
module serviceBus 'modules/service-bus.bicep' = {
  scope: resourceGroup
  name: 'deploy-service-bus'
  params: {
    serviceBusName: serviceBusName
    location: location
    tags: commonTags
  }
}

// ============================================================================
// CONTAINER INFRASTRUCTURE
// ============================================================================
module containerRegistry 'modules/container-registry.bicep' = {
  scope: resourceGroup
  name: 'deploy-container-registry'
  params: {
    registryName: containerRegistryName
    location: location
    tags: commonTags
  }
}

module containerAppsEnvironment 'modules/container-apps-environment.bicep' = {
  scope: resourceGroup
  name: 'deploy-container-apps-env'
  params: {
    environmentName: containerAppsEnvName
    location: location
    workspaceId: logAnalytics.outputs.workspaceId
    customerId: logAnalytics.outputs.customerId
    tags: commonTags
  }
}

// ============================================================================
// CONTAINER APPS - AGENTS
// ============================================================================
/* module securityScannerAgent 'modules/container-app.bicep' = {
  scope: resourceGroup
  name: 'deploy-security-scanner'
  params: {
    appName: 'security-scanner-agent'
    location: location
    environmentId: containerAppsEnvironment.outputs.environmentId
    containerImage: '${containerRegistry.outputs.registryLoginServer}/security-scanner:latest'
    containerPort: 8000
    cpu: '0.5'
    memory: '1Gi'
    minReplicas: 1
    maxReplicas: 5
    identityId: managedIdentity.outputs.identityId
    environmentVariables: [
      {
        name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
        value: applicationInsights.outputs.connectionString
      }
      {
        name: 'COSMOS_ENDPOINT'
        value: cosmosDb.outputs.cosmosEndpoint
      }
    ]
    tags: commonTags
  }
}

module riskAssessmentAgent 'modules/container-app.bicep' = {
  scope: resourceGroup
  name: 'deploy-risk-assessment'
  params: {
    appName: 'risk-assessment-agent'
    location: location
    environmentId: containerAppsEnvironment.outputs.environmentId
    containerImage: '${containerRegistry.outputs.registryLoginServer}/risk-assessment:latest'
    containerPort: 8001
    cpu: '1.0'
    memory: '2Gi'
    minReplicas: 0
    maxReplicas: 10
    identityId: managedIdentity.outputs.identityId
    environmentVariables: [
      {
        name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
        value: applicationInsights.outputs.connectionString
      }
      {
        name: 'COSMOS_ENDPOINT'
        value: cosmosDb.outputs.cosmosEndpoint
      }
    ]
    tags: commonTags
  }
}

module orchestratorAgent 'modules/container-app.bicep' = {
  scope: resourceGroup
  name: 'deploy-orchestrator'
  params: {
    appName: 'orchestrator-agent'
    location: location
    environmentId: containerAppsEnvironment.outputs.environmentId
    containerImage: '${containerRegistry.outputs.registryLoginServer}/orchestrator:latest'
    containerPort: 8080
    cpu: '1.0'
    memory: '2Gi'
    minReplicas: 2
    maxReplicas: 5
    identityId: managedIdentity.outputs.identityId
    environmentVariables: [
      {
        name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
        value: applicationInsights.outputs.connectionString
      }
      {
        name: 'COSMOS_ENDPOINT'
        value: cosmosDb.outputs.cosmosEndpoint
      }
    ]
    tags: commonTags
  }
} */

// ============================================================================
// AZURE FUNCTIONS
// ============================================================================
/* module azureFunctions 'modules/azure-functions.bicep' = {
  scope: resourceGroup
  name: 'deploy-azure-functions'
  params: {
    functionAppName: functionAppName
    location: location
    appInsightsConnectionString: applicationInsights.outputs.connectionString
    storageAccountName: storageAccountName
    identityId: managedIdentity.outputs.identityId
    tags: commonTags
  }
} */

// ============================================================================
// FRONTEND
// ============================================================================
module staticWebApp 'modules/static-web-app.bicep' = {
  scope: resourceGroup
  name: 'deploy-static-web-app'
  params: {
    staticWebAppName: staticWebAppName
    location: 'eastus2'
    sku: environment == 'prod' ? 'Standard' : 'Free'
    repositoryUrl: githubRepoUrl
    branch: 'main'
    tags: commonTags
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================
output resourceGroupName string = resourceGroup.name
output location string = location
output containerRegistryLoginServer string = containerRegistry.outputs.registryLoginServer
output cosmosEndpoint string = cosmosDb.outputs.cosmosEndpoint
output keyVaultUri string = keyVault.outputs.keyVaultUri
// MÓDULOS COMENTADOS:
// output securityScannerUrl string = 'https://${securityScannerAgent.outputs.appFqdn}'
// output riskAssessmentUrl string = 'https://${riskAssessmentAgent.outputs.appFqdn}'
// output orchestratorUrl string = 'https://${orchestratorAgent.outputs.appFqdn}'
// output functionAppName string = azureFunctions.outputs.functionAppName
output staticWebAppUrl string = staticWebApp.outputs.staticWebAppUrl
output managedIdentityClientId string = managedIdentity.outputs.clientId
output appInsightsConnectionString string = applicationInsights.outputs.connectionString
