📝 First off, thank you for considering contributing to SYMBIONT-X! 🎉

This document provides guidelines for contributing to this project. Following these guidelines helps communicate that you respect the time of the developers managing and developing this open-source project.

---

## 📋 Table of Contents

- [📋 Table of Contents](#-table-of-contents)
- [📜 Code of Conduct](#-code-of-conduct)
  - [Our Standards](#our-standards)
- [🚧 Current Status](#-current-status)
  - [During Hackathon (Feb 10 - Mar 15, 2026)](#during-hackathon-feb-10---mar-15-2026)
  - [After Hackathon (Post Mar 15, 2026)](#after-hackathon-post-mar-15-2026)
- [🤝 How Can I Contribute?](#-how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Code Contributions](#code-contributions)
    - [First-Time Contributors](#first-time-contributors)
    - [Contribution Workflow](#contribution-workflow)
- [🛠️ Development Setup](#️-development-setup)
  - [Prerequisites](#prerequisites)
  - [Setup Steps](#setup-steps)
  - [Development Tools](#development-tools)
- [🔄 Pull Request Process](#-pull-request-process)
  - [Before Submitting](#before-submitting)
  - [PR Checklist](#pr-checklist)
  - [PR Template](#pr-template)
  - [Review Process](#review-process)
- [💻 Coding Standards](#-coding-standards)
  - [Python](#python)
  - [TypeScript/React](#typescriptreact)
  - [General Guidelines](#general-guidelines)
- [📝 Commit Message Guidelines](#-commit-message-guidelines)
  - [Format](#format)
  - [Types](#types)
  - [Scope (optional)](#scope-optional)
  - [Examples](#examples)
- [📁 Project Structure](#-project-structure)
- [🧪 Testing Guidelines](#-testing-guidelines)
  - [Test Coverage](#test-coverage)
  - [Writing Tests](#writing-tests)
  - [Running Tests](#running-tests)
- [📚 Documentation](#-documentation)
  - [Code Documentation](#code-documentation)
  - [Updating Documentation](#updating-documentation)
- [🏅 Recognition](#-recognition)
- [📞 Questions?](#-questions)

---

## 📜 Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. By participating, you are expected to uphold this code.

### Our Standards

**✅ Positive Behavior:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**❌ Unacceptable Behavior:**
- The use of sexualized language or imagery
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

---

## 🚧 Current Status

**Important:** This project is currently being developed for the **Microsoft AI Dev Days Global Hackathon 2026**.

**Timeline:**
- **Hacking Period:** February 10 - March 15, 2026
- **Submission Deadline:** March 15, 2026, 11:59 PM PST

**Contribution Status:**

| Phase | Dates | Status | Contributions |
|-------|-------|--------|---------------|
| **Hackathon Development** | Feb 10 - Mar 15, 2026 | 🔴 Active | Limited (see below) |
| **Post-Hackathon** | After Mar 15, 2026 | 🟢 Open | Fully open |

### During Hackathon (Feb 10 - Mar 15, 2026)

Due to hackathon rules, we have limited contribution acceptance during this period:

**✅ Welcomed:**
- Bug reports
- Documentation improvements (typos, clarifications)
- Feature suggestions (will be added to roadmap)
- General feedback

**⏸️ Deferred:**
- Major code contributions
- New features
- Architectural changes

### After Hackathon (Post Mar 15, 2026)

Fully open for all types of contributions!

---

## 🤝 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

**When filing a bug report, include:**

- **Title**: Clear, descriptive summary
- **Description**: Detailed description of the problem
- **Steps to Reproduce**: Numbered list of steps
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Screenshots**: If applicable
- **Environment**:
  - OS: [e.g., Ubuntu 24.04, Windows 11]
  - Python version: [e.g., 3.11.7]
  - Node version: [e.g., 20.10.0]
  - Docker version: [e.g., 24.0.7]
- **Additional Context**: Any other relevant information

**Template:**

```markdown
**Bug Description**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

**Expected Behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
- OS: [e.g., Ubuntu 24.04]
- Python: [e.g., 3.11.7]
- Node: [e.g., 20.10.0]

**Additional Context**
Add any other context about the problem here.
```

---

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues.

**When suggesting an enhancement:**

- **Use a clear, descriptive title**
- **Provide detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful**
- **List any alternative solutions** you've considered
- **Include mockups/diagrams** if applicable

**Template:**

```markdown
**Is your feature request related to a problem?**
A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context, mockups, or screenshots about the feature request here.
```

---

### Code Contributions

#### First-Time Contributors

Look for issues labeled:
- `good first issue` - Simple issues perfect for newcomers
- `help wanted` - Issues where we need help
- `documentation` - Documentation improvements

#### Contribution Workflow

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create a branch** from `main`
4. **Make your changes**
5. **Test** your changes thoroughly
6. **Commit** with conventional commit messages
7. **Push** to your fork
8. **Create a Pull Request**

---

## 🛠️ Development Setup

### Prerequisites

Ensure you have the following installed:

- **Python 3.11+** (project uses 3.11.7)
- **Node.js 20+** (LTS)
- **Docker** (latest version)
- **Azure CLI** (latest)
- **GitHub CLI** (optional but recommended)
- **Git**

### Setup Steps

```bash
# 1. Clone your fork
git clone https://github.com/YOUR_USERNAME/SYMBIONT-X.git
cd SYMBIONT-X

# 2. Add upstream remote
git remote add upstream https://github.com/SYMBIONT-X/SYMBIONT-X.git

# 3. Create Python virtual environment
pyenv local 3.11.7  # If using pyenv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 4. Install Python dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt

# 5. Install Node dependencies (frontend)
cd src/frontend
npm install
cd ../..

# 6. Install pre-commit hooks
pre-commit install

# 7. Copy environment template
cp .env.example .env

# 8. Configure environment variables
# Edit .env with your local settings
nano .env

# 9. Run tests to verify setup
pytest tests/
npm test --prefix src/frontend
```

### Development Tools

**Recommended VS Code Extensions:**
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- ESLint (dbaeumer.vscode-eslint)
- Prettier (esbenp.prettier-vscode)
- Docker (ms-azuretools.vscode-docker)
- Azure Tools (ms-vscode.vscode-node-azure-pack)

---

## 🔄 Pull Request Process

### Before Submitting

- ✅ **Run all tests** and ensure they pass
- ✅ **Run linters** (flake8, black, eslint, prettier)
- ✅ **Update documentation** if needed
- ✅ **Add tests** for new features
- ✅ **Update CHANGELOG.md** (if applicable)
- ✅ **Rebase on latest main** to avoid merge conflicts

### PR Checklist

```markdown
- [ ] My code follows the project's coding standards
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
```

### PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Related Issue
Fixes #[issue number]

## How Has This Been Tested?
Describe the tests you ran to verify your changes.

## Screenshots (if applicable)
Add screenshots here.

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

### Review Process

1. **Automated Checks**: GitHub Actions will run automatically
   - Linting (flake8, black, eslint)
   - Type checking (mypy, TypeScript)
   - Unit tests
   - Integration tests
   - Security scanning

2. **Code Review**: At least one maintainer will review
   - Code quality
   - Test coverage
   - Documentation
   - Performance implications

3. **Approval & Merge**: Once approved:
   - Squash and merge for clean history
   - Automatic deployment to staging (for maintainers)

---

## 💻 Coding Standards

### Python

**Style Guide:** [PEP 8](https://pep8.org/)

```python
# Use type hints
def calculate_priority(cvss_score: float, context: dict[str, Any]) -> str:
    """
    Calculate vulnerability priority based on CVSS score and context.

    Args:
        cvss_score: CVSS score (0.0-10.0)
        context: Business context dictionary

    Returns:
        Priority level (P0/P1/P2/P3)

    Raises:
        ValueError: If CVSS score is invalid
    """
    if not 0.0 <= cvss_score <= 10.0:
        raise ValueError(f"Invalid CVSS score: {cvss_score}")

    # Implementation...
    return "P1"
```

**Tools:**
- **Linter**: `flake8` (max line length: 100)
- **Formatter**: `black` (line length: 100)
- **Type Checker**: `mypy` (strict mode)
- **Import Sorter**: `isort`

**Run all checks:**
```bash
flake8 src/
black src/ --check
mypy src/
isort src/ --check-only
```

### TypeScript/React

**Style Guide:** [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)

```typescript
// Use TypeScript strict mode
interface VulnerabilityProps {
  cveId: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  status: VulnerabilityStatus;
  onRemediate?: (id: string) => Promise<void>;
}

// Use functional components with hooks
export const VulnerabilityCard: React.FC<VulnerabilityProps> = ({
  cveId,
  severity,
  status,
  onRemediate,
}) => {
  // Implementation...
};
```

**Tools:**
- **Linter**: `eslint`
- **Formatter**: `prettier`
- **Type Checker**: TypeScript compiler

**Run all checks:**
```bash
npm run lint
npm run type-check
npm run format:check
```

### General Guidelines

- **Write self-documenting code** with clear variable/function names
- **Keep functions small** (< 50 lines ideally)
- **Single Responsibility Principle** - one function, one purpose
- **DRY** - Don't Repeat Yourself
- **KISS** - Keep It Simple, Stupid
- **Test-Driven Development** - write tests first when possible
- **Security first** - never hardcode secrets, sanitize inputs

---

## 📝 Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no code change)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system or dependency changes
- `ci`: CI/CD changes
- `chore`: Other changes that don't modify src or test files

### Scope (optional)

- `scanner`: Security Scanner Agent
- `risk`: Risk Assessment Agent
- `remediation`: Auto-Remediation Agent
- `orchestrator`: Orchestrator Agent
- `frontend`: React frontend
- `infra`: Infrastructure (Bicep)
- `docs`: Documentation
- `deps`: Dependencies

### Examples

```bash
# Feature
feat(scanner): add container image scanning with Trivy

Implements Trivy integration for scanning Docker images.
Detects vulnerabilities in OS packages and application dependencies.

Closes #42

# Bug fix
fix(orchestrator): prevent race condition in state updates

Added mutex lock when updating workflow state in Cosmos DB.

Fixes #56

# Documentation
docs: update deployment guide with Azure CLI commands

Added step-by-step Azure CLI commands for infrastructure deployment.

# Refactoring
refactor(risk): extract priority calculation to separate module

Moved priority calculation logic to dedicated module for reusability.

# Breaking change
feat(api)!: change vulnerability API response format

BREAKING CHANGE: API now returns vulnerabilities in nested structure
for better compatibility with frontend components.

Closes #78
```

---

## 📁 Project Structure

```
SYMBIONT-X/
├── .github/
│   ├── workflows/          # GitHub Actions CI/CD
│   └── ISSUE_TEMPLATE/     # Issue templates
├── docs/
│   ├── diagrams/           # Architecture diagrams
│   ├── assets/             # Images, logos
│   └── *.md                # Documentation files
├── infrastructure/
│   ├── bicep/              # Azure infrastructure as code
│   │   ├── main.bicep
│   │   ├── modules/        # Reusable modules
│   │   └── parameters/     # Environment parameters
│   └── scripts/            # Deployment scripts
├── src/
│   ├── agents/
│   │   ├── security-scanner/
│   │   │   ├── main.py
│   │   │   ├── scanners/
│   │   │   └── tests/
│   │   ├── risk-assessment/
│   │   ├── orchestrator/
│   │   └── shared/         # Shared utilities
│   ├── backend/
│   │   ├── api/            # REST API
│   │   └── functions/      # Azure Functions
│   └── frontend/
│       ├── src/
│       │   ├── components/
│       │   ├── pages/
│       │   └── services/
│       └── tests/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── scripts/                # Utility scripts
├── .env.example            # Environment template
├── .gitignore
├── README.md
├── CONTRIBUTING.md
├── LICENSE
└── requirements.txt
```

---

## 🧪 Testing Guidelines

### Test Coverage

**Minimum Required:** 80% overall coverage

**By Component:**
- Agents: 85%+
- API: 90%+
- Frontend Components: 75%+

### Writing Tests

**Python (pytest):**

```python
import pytest
from agents.risk_assessment.priority import calculate_priority

class TestPriorityCalculation:
    """Test suite for priority calculation."""

    def test_critical_vulnerability_returns_p0(self):
        """Critical vulnerability with active exploits should be P0."""
        # Arrange
        cvss_score = 9.5
        context = {
            "is_public_facing": True,
            "handles_pii": True,
            "active_exploits": True
        }

        # Act
        priority = calculate_priority(cvss_score, context)

        # Assert
        assert priority == "P0"

    def test_invalid_cvss_raises_error(self):
        """Invalid CVSS score should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_priority(11.0, {})
```

**TypeScript/React (Jest + Testing Library):**

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { VulnerabilityCard } from './VulnerabilityCard';

describe('VulnerabilityCard', () => {
  it('displays CVE ID correctly', () => {
    render(
      <VulnerabilityCard
        cveId="CVE-2024-12345"
        severity="CRITICAL"
        status="open"
      />
    );

    expect(screen.getByText('CVE-2024-12345')).toBeInTheDocument();
  });

  it('calls onRemediate when button clicked', async () => {
    const mockRemediate = jest.fn();

    render(
      <VulnerabilityCard
        cveId="CVE-2024-12345"
        severity="CRITICAL"
        status="open"
        onRemediate={mockRemediate}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /remediate/i }));

    expect(mockRemediate).toHaveBeenCalledWith('CVE-2024-12345');
  });
});
```

### Running Tests

```bash
# Python tests
pytest tests/ -v --cov=src --cov-report=html

# JavaScript tests
npm test --prefix src/frontend

# E2E tests
pytest tests/e2e/ -v

# All tests
./scripts/test-all.sh
```

---

## 📚 Documentation

### Code Documentation

**Python:**
- Use **Google-style docstrings**
- Document all public functions/classes
- Include type hints

**TypeScript:**
- Use **TSDoc** comments
- Document props interfaces
- Add inline comments for complex logic

### Updating Documentation

When making changes:

- ✅ Update relevant `.md` files in `docs/`
- ✅ Update API documentation if endpoints change
- ✅ Update architecture diagrams if structure changes
- ✅ Update README if setup process changes

---

## 🏅 Recognition

Contributors will be recognized in:

- `CONTRIBUTORS.md` file
- Release notes
- Project website (post-hackathon)

Thank you for contributing to SYMBIONT-X! 🚀

---

## 📞 Questions?

If you have questions not covered here:

1. **Check existing issues** and discussions
2. **Open a new discussion** on GitHub
3. **Contact maintainers** via the hackathon platform

---

**Last Updated:** February 6, 2026
**For:** Microsoft AI Dev Days Hackathon 2026
