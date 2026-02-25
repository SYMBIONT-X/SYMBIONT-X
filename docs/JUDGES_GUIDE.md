# 🏆 SYMBIONT-X - Judges Guide

> Quick reference guide for hackathon judges to evaluate SYMBIONT-X

---

## 📋 Quick Facts

| Item | Value |
|------|-------|
| **Project** | SYMBIONT-X |
| **Category** | AI-Powered DevSecOps |
| **Stack** | Python, FastAPI, React, TypeScript |
| **AI Used** | Multi-Agent Architecture, OpenAI Integration |
| **Tests** | 91 passing |
| **Docs** | 10+ comprehensive documents |

---

## ⚡ Deploy in 5 Minutes

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### Quick Start
```bash
# 1. Clone
git clone https://github.com/SYMBIONT-X/SYMBIONT-X.git
cd SYMBIONT-X

# 2. Setup Python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Start all 4 agents (in separate terminals)
# Terminal 1:
cd src/agents/orchestrator && python main.py

# Terminal 2:
cd src/agents/security-scanner && python main.py

# Terminal 3:
cd src/agents/risk-assessment && python main.py

# Terminal 4:
cd src/agents/auto-remediation && python main.py

# 4. Start Frontend (new terminal)
cd src/frontend
npm install
npm run dev

# 5. Open browser
# http://localhost:5173
```

### Verify Installation
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","agents":{...}}
```

---

## 🎯 Key Features to Evaluate

### 1. Multi-Agent AI Architecture
**Location:** `src/agents/`

| Agent | Port | Purpose |
|-------|------|---------|
| Orchestrator | 8000 | Coordinates all agents |
| Security Scanner | 8001 | Detects vulnerabilities |
| Risk Assessment | 8002 | Prioritizes with AI |
| Auto-Remediation | 8003 | Generates fixes |

**What to look for:**
- Each agent is independent and specialized
- Agents communicate via REST APIs
- Orchestrator manages workflow state

---

### 2. Intelligent Vulnerability Detection
**Location:** `src/agents/security-scanner/scanners/`

**5 Scanner Types:**
- `dependency_scanner.py` - npm/pip vulnerabilities
- `code_scanner.py` - Static analysis (SAST)
- `secret_scanner.py` - Exposed credentials
- `container_scanner.py` - Docker security
- `iac_scanner.py` - Infrastructure-as-Code

**Demo:** Click "Start Security Scan" in Dashboard

---

### 3. AI-Powered Risk Assessment
**Location:** `src/agents/risk-assessment/assessor.py`

**Features:**
- CVSS score interpretation
- Business context analysis
- Priority calculation (P0-P4)
- OpenAI integration for analysis

**What to look for:**
- `PriorityCalculator` class
- `BusinessContextAnalyzer` class
- AI prompt engineering in `_generate_ai_analysis()`

---

### 4. Automated Remediation
**Location:** `src/agents/auto-remediation/`

**Features:**
- 16 fix templates (`templates.py`)
- AI-powered fix generation
- GitHub PR creation ready
- Confidence scoring

**What to look for:**
- `FixGenerator` class
- Template matching logic
- Fix validation

---

### 5. Human-in-the-Loop Workflow
**Location:** `src/agents/orchestrator/hitl_api.py`

**Features:**
- Approval workflow for critical fixes
- Comment system
- Audit logging
- Teams notifications ready

**Demo:** Go to Approvals page, see pending approvals

---

### 6. Real-Time Dashboard
**Location:** `src/frontend/src/pages/`

**Pages:**
- `DashboardPage.tsx` - Executive overview
- `VulnerabilitiesPage.tsx` - Vulnerability list
- `ApprovalsPage.tsx` - HITL approvals
- `MonitoringPage.tsx` - System metrics

---

## 📁 Code Structure
```
SYMBIONT-X/
├── src/
│   ├── agents/
│   │   ├── orchestrator/      # Central coordinator
│   │   ├── security-scanner/  # Detection (25 tests)
│   │   ├── risk-assessment/   # Prioritization (26 tests)
│   │   └── auto-remediation/  # Fix generation (18 tests)
│   ├── shared/
│   │   ├── security/          # Auth, RBAC, rate limiting
│   │   └── performance/       # Caching, pagination
│   └── frontend/              # React + TypeScript
├── docs/                      # Comprehensive documentation
└── scripts/                   # Utilities
```

---

## 🧪 Running Tests
```bash
# All agents (91 tests total)
cd src/agents/security-scanner && python -m pytest tests/ -v
cd src/agents/risk-assessment && python -m pytest tests/ -v
cd src/agents/auto-remediation && python -m pytest tests/ -v
cd src/agents/orchestrator && python -m pytest tests/ -v
```

---

## 📊 Judging Criteria Mapping

### Innovation & Creativity
- ✅ Multi-agent AI architecture (novel approach)
- ✅ 4 specialized AI agents working together
- ✅ Human-in-the-loop for responsible AI
- ✅ Business context-aware prioritization

### Technical Implementation
- ✅ 91 unit tests passing
- ✅ Clean microservices architecture
- ✅ Type-safe frontend (TypeScript)
- ✅ Security hardening (RBAC, rate limiting)
- ✅ Performance optimization (caching, pagination)

### Use of Microsoft Technologies
- ✅ Azure-ready deployment
- ✅ Azure AD authentication ready
- ✅ Teams notifications integration
- ✅ FluentUI React components

### Impact & Practicality
- ✅ Solves real DevSecOps problem
- ✅ Reduces vulnerability response time
- ✅ Automates routine fixes
- ✅ Maintains human oversight for critical decisions

### Documentation & Presentation
- ✅ Comprehensive README
- ✅ Architecture documentation
- ✅ API documentation
- ✅ Deployment guide
- ✅ Demo video

---

## 🔍 Where to Find Key Code

| Feature | File |
|---------|------|
| Agent communication | `src/agents/orchestrator/agent_client.py` |
| Workflow engine | `src/agents/orchestrator/workflow_engine.py` |
| Vulnerability scanning | `src/agents/security-scanner/scanners/` |
| AI risk analysis | `src/agents/risk-assessment/assessor.py` |
| Fix generation | `src/agents/auto-remediation/fix_generator.py` |
| Approval workflow | `src/agents/orchestrator/hitl_api.py` |
| Security middleware | `src/shared/security/` |
| Dashboard | `src/frontend/src/pages/DashboardPage.tsx` |

---

## 📞 Quick Demo Flow

1. **Open Dashboard** → See 4 healthy agents
2. **Click "Start Security Scan"** → Watch scan progress
3. **Go to Vulnerabilities** → See detected issues with priorities
4. **Go to Approvals** → See pending approval request
5. **Approve with comment** → Complete HITL flow
6. **Go to Monitoring** → See system metrics

---

## 💡 Tips for Judges

- All data is in-memory (resets on restart) - this is intentional for demo
- Run `python scripts/setup_demo_data.py` to populate impressive demo data
- The system works end-to-end without any external dependencies
- Check the `/health` endpoints to verify agent status

---

## 📚 Documentation Index

| Document | Description |
|----------|-------------|
| `README.md` | Project overview |
| `docs/ARCHITECTURE.md` | System design |
| `docs/API_DOCUMENTATION.md` | All endpoints |
| `docs/DEPLOYMENT_GUIDE.md` | Setup instructions |
| `docs/DECISIONS.md` | Technical choices |
| `docs/DEVELOPMENT_LOG.md` | Build journey |
| `docs/PERFORMANCE.md` | Optimization details |
| `docs/DEMO_SCRIPT.md` | Video script |

---

**Thank you for evaluating SYMBIONT-X!** 🚀
