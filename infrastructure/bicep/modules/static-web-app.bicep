// Azure Static Web App for frontend
@description('Name of the Static Web App')
param staticWebAppName string

@description('Location for the resource (limited locations available)')
param location string = 'eastus2'

@description('SKU (Free or Standard)')
param sku string = 'Free'

@description('GitHub repository URL')
param repositoryUrl string = ''

@description('GitHub branch')
param branch string = 'main'

@description('Tags for the resource')
param tags object = {}

resource staticWebApp 'Microsoft.Web/staticSites@2022-09-01' = {
  name: staticWebAppName
  location: location
  tags: tags
  sku: {
    name: sku
    tier: sku
  }
  properties: {
    repositoryUrl: repositoryUrl
    branch: branch
    buildProperties: {
      appLocation: '/src/frontend'
      apiLocation: ''
      outputLocation: 'dist'
    }
  }
}

output staticWebAppId string = staticWebApp.id
output staticWebAppName string = staticWebApp.name
output staticWebAppUrl string = 'https://${staticWebApp.properties.defaultHostname}'
