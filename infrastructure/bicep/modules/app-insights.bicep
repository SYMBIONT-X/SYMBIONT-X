// Application Insights for APM and monitoring
@description('Name of the Application Insights instance')
param appInsightsName string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Log Analytics Workspace ID')
param workspaceId string

@description('Tags for the resource')
param tags object = {}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspaceId
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

output instrumentationKey string = applicationInsights.properties.InstrumentationKey
output connectionString string = applicationInsights.properties.ConnectionString
output appInsightsId string = applicationInsights.id
