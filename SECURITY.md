# 🔐 Security Policy - SYMBIONT-X

## Overview

SYMBIONT-X takes security seriously. This document outlines our security measures, vulnerability reporting process, and best practices.

---

## 🛡️ Security Measures Implemented

### Authentication & Authorization

| Feature | Implementation | Status |
|---------|---------------|--------|
| JWT Authentication | Bearer tokens with expiration | ✅ Ready |
| Azure AD Integration | OAuth 2.0 / OpenID Connect | ✅ Ready |
| RBAC | 4 roles, 20+ permissions | ✅ Implemented |
| API Key Support | For service-to-service auth | ✅ Ready |

### Roles & Permissions

| Role | Permissions |
|------|-------------|
| `admin` | Full access to all features |
| `security_team` | Scan, assess, approve remediations |
| `developer` | View vulnerabilities, request scans |
| `viewer` | Read-only access |

### Input Validation

- All API inputs validated with Pydantic models
- SQL injection prevention through parameterized queries
- XSS prevention through output encoding
- Path traversal protection

### Rate Limiting

| Endpoint Type | Limit |
|---------------|-------|
| Health checks | 120/min, 2000/hour |
| Read endpoints | 60/min, 1000/hour |
| Write endpoints | 30/min, 500/hour |
| Scan triggers | 5/min, 50/hour |

### Content Safety

The system includes a content safety filter that blocks:
- Shell command execution attempts
- Credential exposure
- SQL injection patterns
- Unsafe deserialization

### Network Security

- CORS configured for specific origins only
- HTTPS enforced in production
- Internal agent communication on private network
- No sensitive data in URLs

### Audit Logging

- All security decisions logged
- Immutable audit trail
- User actions tracked
- Configurable retention (default: 365 days)

---

## 🔍 Security Scan Results

### Bandit (Python Security Linter)
```
Last Scan: February 2026
Total Lines Scanned: 8,046
High Severity Issues: 0
Medium Severity Issues: 6 (intentional 0.0.0.0 bindings for Docker)
```

### Findings

| Issue | Severity | Status | Notes |
|-------|----------|--------|-------|
| Bind to 0.0.0.0 | Medium | Accepted | Required for Docker containers |
| No hardcoded secrets | N/A | ✅ Pass | All secrets via environment |
| No SQL injection | N/A | ✅ Pass | Using parameterized queries |
| No command injection | N/A | ✅ Pass | No shell execution |

---

## 🚫 Secrets Management

### What's NOT in the Repository

- ❌ API keys
- ❌ Database credentials
- ❌ Private keys
- ❌ Access tokens
- ❌ Passwords

### How Secrets Are Managed

1. **Development**: `.env` file (gitignored)
2. **Production**: Azure Key Vault
3. **CI/CD**: GitHub Secrets

### .gitignore Security Rules
```
.env
.env.local
.env.*.local
*.env
secrets/
*.key
*.pem
```

---

## 📋 Security Checklist

### Before Deployment

- [x] No secrets in code
- [x] No secrets in git history
- [x] Environment variables documented
- [x] HTTPS configured
- [x] CORS properly configured
- [x] Rate limiting enabled
- [x] Input validation on all endpoints
- [x] Authentication enabled
- [x] RBAC configured
- [x] Audit logging enabled
- [x] Security headers configured

### Runtime Security

- [x] JWT token validation
- [x] Request size limits
- [x] Timeout configurations
- [x] Error messages don't leak info
- [x] Dependencies up to date

---

## 🐛 Reporting Vulnerabilities

### How to Report

If you discover a security vulnerability, please:

1. **DO NOT** open a public GitHub issue
2. Email: security@symbiontx.io (or use private contact)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

| Phase | Timeline |
|-------|----------|
| Acknowledgment | 24 hours |
| Initial Assessment | 72 hours |
| Fix Development | 7-14 days |
| Public Disclosure | After fix deployed |

### Safe Harbor

We will not pursue legal action against researchers who:
- Act in good faith
- Avoid privacy violations
- Avoid data destruction
- Report responsibly

---

## 🔧 Security Configuration

### Environment Variables
```bash
# Authentication
AUTH_ENABLED=true
JWT_SECRET_KEY=<from-key-vault>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Azure AD
AZURE_AD_TENANT_ID=<your-tenant>
AZURE_AD_CLIENT_ID=<your-client>

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# CORS
CORS_ALLOWED_ORIGINS=https://your-domain.com
```

### Production Recommendations

1. **Use Azure Key Vault** for all secrets
2. **Enable Azure AD** authentication
3. **Deploy behind Azure Front Door** for DDoS protection
4. **Enable Application Insights** for security monitoring
5. **Configure alerts** for suspicious activity
6. **Regular dependency updates** via Dependabot
7. **Enable GitHub Advanced Security** for code scanning

---

## 📦 Dependency Security

### Python Dependencies

- Scanned with `safety` for known vulnerabilities
- Scanned with `bandit` for code security
- Pinned versions in `requirements.txt`

### JavaScript Dependencies

- Scanned with `npm audit`
- Scanned with GitHub Dependabot
- Lock file committed (`package-lock.json`)

### Update Policy

- Critical vulnerabilities: Patch within 24 hours
- High vulnerabilities: Patch within 7 days
- Medium vulnerabilities: Patch within 30 days
- Low vulnerabilities: Next release cycle

---

## 🏗️ Architecture Security

### Agent Communication
```
┌─────────────┐     HTTPS/JWT     ┌─────────────┐
│ Orchestrator│◄──────────────────►│   Scanner   │
│   (8000)    │                    │   (8001)    │
└─────────────┘                    └─────────────┘
       ▲                                  
       │ HTTPS/JWT                        
       ▼                                  
┌─────────────┐     HTTPS/JWT     ┌─────────────┐
│    Risk     │◄──────────────────►│ Remediation │
│   (8002)    │                    │   (8003)    │
└─────────────┘                    └─────────────┘
```

### Data Flow Security

1. All inter-agent communication uses HTTPS in production
2. JWT tokens validate agent identity
3. No sensitive data stored in memory longer than needed
4. Audit logs capture all security decisions

---

## 📚 References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Azure Security Best Practices](https://docs.microsoft.com/en-us/azure/security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [React Security](https://reactjs.org/docs/security.html)

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Feb 2026 | Initial security documentation |

---

*Security is not a feature—it's a foundation.*
