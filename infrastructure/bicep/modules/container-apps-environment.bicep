// Container Apps Environment for hosting agents
@description('Name of the Container Apps Environment')
param environmentName string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Log Analytics Workspace ID')
param workspaceId string

@description('Log Analytics Customer ID')
param customerId string

@description('Tags for the resource')
param tags object = {}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: environmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: customerId
        sharedKey: listKeys(workspaceId, '2022-10-01').primarySharedKey
      }
    }
    zoneRedundant: false
  }
}

output environmentId string = containerAppsEnvironment.id
output environmentName string = containerAppsEnvironment.name
output defaultDomain string = containerAppsEnvironment.properties.defaultDomain
