// Generic Container App for agents
@description('Name of the Container App')
param appName string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Container Apps Environment ID')
param environmentId string

@description('Container image')
param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Container port')
param containerPort int = 8080

@description('CPU cores (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0)')
param cpu string = '0.5'

@description('Memory in Gi (0.5, 1.0, 1.5, 2.0, 3.0, 3.5, 4.0)')
param memory string = '1Gi'

@description('Minimum replicas')
param minReplicas int = 1

@description('Maximum replicas')
param maxReplicas int = 5

@description('Managed Identity ID')
param identityId string

@description('Environment variables')
param environmentVariables array = []

@description('Tags for the resource')
param tags object = {}

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: appName
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      ingress: {
        external: true
        targetPort: containerPort
        transport: 'http'
        allowInsecure: false
      }
      registries: []
    }
    template: {
      containers: [
        {
          name: appName
          image: containerImage
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: environmentVariables
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: containerPort
              }
              initialDelaySeconds: 10
              periodSeconds: 30
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

output appFqdn string = containerApp.properties.configuration.ingress.fqdn
output appName string = containerApp.name
output appId string = containerApp.id
