// Azure Container Registry for Docker images
@description('Name of the Container Registry')
param registryName string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Tags for the resource')
param tags object = {}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: registryName
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    zoneRedundancy: 'Disabled'
  }
}

output registryName string = containerRegistry.name
output registryLoginServer string = containerRegistry.properties.loginServer
output registryId string = containerRegistry.id
