// Azure Service Bus for messaging between components
@description('Name of the Service Bus namespace')
param serviceBusName string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Tags for the resource')
param tags object = {}

resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: serviceBusName
  location: location
  tags: tags
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  properties: {
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
  }
}

resource remediationQueue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  parent: serviceBusNamespace
  name: 'remediation-requests'
  properties: {
    lockDuration: 'PT5M'
    maxSizeInMegabytes: 1024
    requiresDuplicateDetection: false
    requiresSession: false
    defaultMessageTimeToLive: 'P1D'
    deadLetteringOnMessageExpiration: true
    maxDeliveryCount: 5
    enablePartitioning: false
    enableExpress: false
  }
}

output serviceBusEndpoint string = serviceBusNamespace.properties.serviceBusEndpoint
output serviceBusName string = serviceBusNamespace.name
output serviceBusId string = serviceBusNamespace.id
