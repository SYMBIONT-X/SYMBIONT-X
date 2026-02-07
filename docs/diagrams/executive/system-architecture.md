# SYMBIONT-X - System Architecture (Executive View)

**Purpose:** High-level overview for README.md  
**Audience:** Judges, general audience  
**Complexity:** Simplified for 30-second understanding  

---

## Architecture Diagram
```mermaid
graph TB
    subgraph External["🌐 External Systems"]
        GH[("GitHub<br/>Source Control<br/>Webhooks & PRs")]
        GHC[("GitHub Copilot<br/>Agent Mode<br/>AI Code Gen")]
        MF[("Microsoft Foundry<br/>GPT-4 Models<br/>AI Analysis")]
        CVE[("CVE Database<br/>NVD<br/>Vulnerability Data")]
    end

    subgraph Azure["☁️ Azure Cloud Platform"]
        subgraph Compute["Compute Layer"]
            subgraph CAE["Container Apps Environment"]
                SSA["🔍 Security Scanner<br/>Agent"]
                RAA["🧠 Risk Assessment<br/>Agent"]
                ORC["🎯 Orchestrator<br/>Agent"]
            end
            subgraph FUNC["Azure Functions"]
                ARM["🔧 Auto-Remediation<br/>Function"]
                EVT["📡 Event Processor<br/>Function"]
            end
        end

        subgraph Data["Data & State Layer"]
            CDB[("🗄️ Cosmos DB<br/>NoSQL<br/>Vulnerabilities<br/>Agents<br/>Decisions")]
            KV[("🔐 Key Vault<br/>Secrets<br/>API Keys")]
        end

        subgraph Observability["Observability Layer"]
            AI["📊 Application<br/>Insights<br/>Metrics/Logs/Traces"]
            ACR["📦 Container<br/>Registry<br/>Docker Images")]
        end
    end

    subgraph Frontend["💻 User Interface"]
        SWA["Azure Static Web App<br/>React Dashboard<br/>TypeScript + Fluent UI"]
    end

    %% External to Azure Flows
    GH -->|"①<br/>Webhook:<br/>Push Event"| SSA
    SSA -->|"②<br/>Vulnerability<br/>Detected<br/>(MCP)"| ORC
    ORC -.->|"③<br/>Assess Risk<br/>(A2A)"| RAA
    RAA -->|"④<br/>AI Context<br/>Analysis"| MF
    RAA -.->|"④<br/>Priority:<br/>P1"| ORC
    ORC -.->|"⑤<br/>Trigger Fix<br/>(A2A)"| ARM
    ARM -->|"⑥<br/>Generate<br/>Fix Code"| GHC
    ARM -->|"⑦<br/>Create<br/>Pull Request"| GH

    %% Data Persistence
    ORC <-->|"State &<br/>Decisions"| CDB
    SSA -.->|"Secrets"| KV
    RAA -.->|"Secrets"| KV
    ARM -.->|"Secrets"| KV

    %% Observability
    SSA -.->|"Telemetry"| AI
    RAA -.->|"Telemetry"| AI
    ORC -.->|"Telemetry"| AI
    ARM -.->|"Telemetry"| AI

    %% Frontend Connection
    SWA <-->|"REST API<br/>WebSocket"| ORC

    %% Styling
    classDef azure fill:#0078D4,stroke:#0078D4,color:#fff,stroke-width:2px
    classDef external fill:#505050,stroke:#505050,color:#fff,stroke-width:2px
    classDef agent fill:#4DB6AC,stroke:#00796B,color:#fff,stroke-width:2px
    classDef data fill:#FFA726,stroke:#F57C00,color:#fff,stroke-width:2px
    classDef success fill:#107C10,stroke:#107C10,color:#fff,stroke-width:2px

    class SSA,RAA,ORC,ARM agent
    class CDB,KV data
    class GH,GHC,MF,CVE external
    class SWA success
```

---

## Legend

| Symbol | Meaning |
|--------|---------|
| **━━━▶** | Synchronous Call |
| **╌╌╌▶** | A2A Protocol (Agent-to-Agent) |
| **┄┄┄▶** | Telemetry / Async |

---

**Version**: 1.0 | **Date**: February 2026 | **Project**: SYMBIONT-X
