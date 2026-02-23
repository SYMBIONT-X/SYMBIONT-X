# SYMBIONT-X Technical Decisions

This document explains the reasoning behind key technical choices made during development.

---

## Architecture Decisions

### Decision: Microservices with 4 Specialized Agents
**Choice**: Separate agents for Scanner, Assessment, Remediation, and Orchestration

**Alternatives Considered**:
- Monolithic application
- 2-agent design (Scanner + Remediation)
- Serverless functions

**Why We Chose This**:
1. **Separation of Concerns**: Each agent has a single responsibility
2. **Independent Scaling**: Can scale scanner independently during high load
3. **Fault Isolation**: One agent failure doesn't crash the system
4. **Team Scalability**: Different teams could own different agents
5. **Technology Flexibility**: Each agent could use different tech if needed

**Trade-offs Accepted**:
- More complex deployment
- Network latency between agents
- Need for service discovery

---

### Decision: REST for Agent Communication
**Choice**: HTTP/REST APIs between agents

**Alternatives Considered**:
- gRPC
- Message queues (RabbitMQ, Kafka)
- GraphQL

**Why We Chose This**:
1. **Simplicity**: Easy to debug with curl/Postman
2. **Familiarity**: Team knows REST well
3. **Tooling**: Great tooling (Swagger, OpenAPI)
4. **Hackathon Timeline**: Faster to implement

**Trade-offs Accepted**:
- Less efficient than gRPC for high throughput
- No built-in retry/queue semantics
- Synchronous by default

---

### Decision: Orchestrator as Central Coordinator
**Choice**: Dedicated orchestrator agent managing workflow state

**Alternatives Considered**:
- Choreography (agents communicate directly)
- Workflow engine (Temporal, Airflow)
- Event-driven saga pattern

**Why We Chose This**:
1. **Visibility**: Central place to see workflow state
2. **Control**: Easy to implement approval workflows
3. **Debugging**: Single point to trace issues
4. **Simplicity**: No need for external workflow engine

**Trade-offs Accepted**:
- Single point of failure (mitigated by health checks)
- Potential bottleneck at scale

---

## Technology Choices

### Decision: Python + FastAPI for Backend
**Choice**: Python 3.11 with FastAPI framework

**Alternatives Considered**:
- Node.js + Express
- Go + Gin
- .NET + ASP.NET Core

**Why We Chose This**:
1. **AI/ML Ecosystem**: Best libraries for AI (OpenAI, transformers)
2. **FastAPI Features**: Auto-docs, validation, async support
3. **Development Speed**: Rapid prototyping
4. **Type Hints**: Modern Python with Pydantic validation

**Trade-offs Accepted**:
- Slower than Go/.NET for raw performance
- GIL limitations (mitigated with async)

---

### Decision: React + TypeScript for Frontend
**Choice**: React 18 with TypeScript and Vite

**Alternatives Considered**:
- Vue.js
- Angular
- Next.js
- Plain JavaScript

**Why We Chose This**:
1. **Type Safety**: Catch errors at compile time
2. **Ecosystem**: Huge component library ecosystem
3. **FluentUI**: Microsoft's design system is React-based
4. **Vite**: Fast development experience

**Trade-offs Accepted**:
- More setup than plain JS
- Learning curve for TypeScript

---

### Decision: FluentUI for UI Components
**Choice**: Microsoft FluentUI v9

**Alternatives Considered**:
- Material UI
- Tailwind CSS
- Chakra UI
- shadcn/ui

**Why We Chose This**:
1. **Microsoft Hackathon**: Aligns with Microsoft ecosystem
2. **Enterprise Ready**: Accessibility, RTL, theming built-in
3. **Consistency**: Matches Azure portal aesthetics
4. **Quality**: Well-tested, production-ready

**Trade-offs Accepted**:
- Larger bundle size than Tailwind
- Learning new component library

---

### Decision: In-Memory Storage with Redis Ready
**Choice**: In-memory dictionaries with Redis interface

**Alternatives Considered**:
- PostgreSQL
- MongoDB
- Azure Cosmos DB
- SQLite

**Why We Chose This**:
1. **Hackathon Speed**: No database setup required
2. **Flexibility**: Easy to swap in Redis/Cosmos later
3. **Performance**: Fastest possible for demo
4. **Simplicity**: No ORM, migrations, connections

**Trade-offs Accepted**:
- Data lost on restart
- Not production-ready without persistence

---

## Security Decisions

### Decision: JWT with Azure AD Ready
**Choice**: JWT tokens locally, Azure AD integration ready

**Alternatives Considered**:
- Session-based auth
- OAuth2 only
- API keys

**Why We Chose This**:
1. **Stateless**: No session storage needed
2. **Azure Integration**: Easy to add Azure AD later
3. **Flexibility**: Works in dev without Azure
4. **Standards**: Well-understood, library support

---

### Decision: Role-Based Access Control (RBAC)
**Choice**: 4 roles with granular permissions

**Alternatives Considered**:
- Simple admin/user roles
- Attribute-based (ABAC)
- No access control (trust network)

**Why We Chose This**:
1. **Real-World Alignment**: Matches enterprise security models
2. **Granularity**: Can restrict specific operations
3. **Simplicity**: Easier than ABAC to understand
4. **Extensibility**: Easy to add new roles/permissions

**Roles Defined**:
- `admin`: Full access (DevOps, Security leads)
- `security_team`: Manage vulnerabilities, approve fixes
- `developer`: Run scans, view results
- `viewer`: Read-only access

---

### Decision: Content Safety Filter for AI Code
**Choice**: Pattern-based dangerous code detection

**Alternatives Considered**:
- External code scanning service
- No filtering (trust AI)
- Sandboxed execution

**Why We Chose This**:
1. **Responsible AI**: Prevent AI from generating dangerous code
2. **Performance**: Fast pattern matching
3. **Transparency**: Clear rules, auditable
4. **Safety**: Block known dangerous patterns

**Patterns Blocked**:
- Shell execution (os.system, eval, exec)
- Hardcoded credentials
- SQL injection vectors
- Unsafe deserialization

---

## Performance Decisions

### Decision: Token Bucket Rate Limiting
**Choice**: In-memory token bucket algorithm

**Alternatives Considered**:
- Fixed window
- Sliding window
- External rate limiter (Redis)

**Why We Chose This**:
1. **Burst Handling**: Allows short bursts
2. **Memory Efficient**: O(1) per key
3. **Industry Standard**: Well-understood algorithm
4. **No Dependencies**: Works without Redis

---

### Decision: Frontend Code Splitting
**Choice**: Vendor chunk separation (react, charts)

**Alternatives Considered**:
- Single bundle
- Route-based splitting
- Dynamic imports everywhere

**Why We Chose This**:
1. **Cache Efficiency**: Vendors change rarely
2. **Parallel Loading**: Multiple chunks load in parallel
3. **Simplicity**: Easy to configure in Vite
4. **Balance**: Good split without complexity

**Result**: 1100KB → 3 chunks (160KB + 411KB + 527KB)

---

## Integration Decisions

### Decision: Webhook for Scan Completion
**Choice**: POST webhook from scanner to orchestrator

**Alternatives Considered**:
- Polling from orchestrator
- WebSocket connection
- Message queue

**Why We Chose This**:
1. **Simplicity**: Standard HTTP POST
2. **Decoupling**: Scanner doesn't need to know orchestrator details
3. **Reliability**: HTTP is well-understood
4. **Flexibility**: Easy to add more subscribers

---

### Decision: Teams Webhook for Notifications
**Choice**: Microsoft Teams incoming webhooks

**Alternatives Considered**:
- Email (SMTP)
- Slack
- PagerDuty
- Custom notification service

**Why We Chose This**:
1. **Microsoft Hackathon**: Natural fit
2. **No Auth Complexity**: Webhook URL is all that's needed
3. **Rich Cards**: Adaptive cards look professional
4. **Free**: No additional service costs

---

## What We'd Do Differently

### With More Time
1. **Database**: Use PostgreSQL with proper migrations
2. **Message Queue**: Add RabbitMQ for async workflows
3. **Kubernetes**: Full K8s deployment with Helm charts
4. **CI/CD**: GitHub Actions with automated testing
5. **Monitoring**: Full Prometheus + Grafana stack

### If Starting Over
1. **Consider gRPC**: For agent-to-agent communication
2. **Workflow Engine**: Evaluate Temporal for complex workflows
3. **GraphQL**: For flexible frontend data fetching
4. **Monorepo Tools**: Use Nx or Turborepo for better DX

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [FluentUI React](https://react.fluentui.dev/)
- [Microsoft AI Agent Framework](https://microsoft.github.io/autogen/)
- [OWASP Vulnerability Scoring](https://owasp.org/www-community/vulnerability-scoring)
