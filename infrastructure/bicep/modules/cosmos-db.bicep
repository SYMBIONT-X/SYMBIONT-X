// Cosmos DB for state management and data storage
@description('Name of the Cosmos DB account')
param cosmosAccountName string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Database name')
param databaseName string = 'symbiontx'

@description('Environment (dev, staging, prod)')
param environment string

@description('Tags for the resource')
param tags object = {}

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: cosmosAccountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
      maxIntervalInSeconds: 5
      maxStalenessPrefix: 100
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    backupPolicy: {
      type: 'Continuous'
      continuousModeProperties: {
        tier: 'Continuous7Days'
      }
    }
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosAccount
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
  }
}

resource vulnerabilitiesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: database
  name: 'vulnerabilities'
  properties: {
    resource: {
      id: 'vulnerabilities'
      partitionKey: {
        paths: [
          '/cve_id'
        ]
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
      defaultTtl: 7776000 // 90 days
    }
  }
}

resource agentsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: database
  name: 'agents'
  properties: {
    resource: {
      id: 'agents'
      partitionKey: {
        paths: [
          '/type'
        ]
        kind: 'Hash'
      }
    }
  }
}

resource decisionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: database
  name: 'decisions'
  properties: {
    resource: {
      id: 'decisions'
      partitionKey: {
        paths: [
          '/vulnerability_id'
        ]
        kind: 'Hash'
      }
      defaultTtl: 31536000 // 365 days
    }
  }
}

output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
output cosmosAccountName string = cosmosAccount.name
output databaseName string = database.name
