# SYMBIONT-X API Documentation

## Overview

SYMBIONT-X exposes REST APIs through 4 microservices (agents). All APIs return JSON and follow RESTful conventions.

## Base URLs

| Agent | Port | Base URL |
|-------|------|----------|
| Orchestrator | 8000 | `http://localhost:8000` |
| Security Scanner | 8001 | `http://localhost:8001` |
| Risk Assessment | 8002 | `http://localhost:8002` |
| Auto-Remediation | 8003 | `http://localhost:8003` |

## Authentication

When enabled (`AUTH_ENABLED=true`), all endpoints require a Bearer token:
```
Authorization: Bearer <jwt_token>
```

### Roles
- `admin`: Full access
- `security_team`: Scans, vulnerabilities, remediation
- `developer`: Scans (create/read), workflows
- `viewer`: Read-only access

---

## Orchestrator API (Port 8000)

### Health & Status

#### GET /health
Check orchestrator and all agent health.

**Response:**
```json
{
  "status": "healthy",
  "agent": "orchestrator",
  "version": "1.0.0",
  "agents": {
    "security-scanner": "healthy",
    "risk-assessment": "healthy",
    "auto-remediation": "healthy"
  },
  "timestamp": "2026-02-28T10:00:00Z"
}
```

#### GET /agents
Get detailed agent status.

**Response:**
```json
{
  "agents": {
    "security-scanner": {
      "status": "healthy",
      "url": "http://localhost:8001",
      "version": "1.0.0",
      "last_check": "2026-02-28T10:00:00Z"
    }
  },
  "all_healthy": true
}
```

### Workflows

#### POST /workflow
Start a new security workflow.

**Request:**
```json
{
  "repository": "owner/repo-name",
  "branch": "main",
  "scan_types": ["dependency", "code", "secret", "container", "iac"],
  "auto_remediate": true,
  "notify": true
}
```

**Response:**
```json
{
  "workflow_id": "wf-uuid-1234",
  "status": "pending",
  "message": "Workflow started",
  "workflow": { ... }
}
```

#### GET /workflow/{workflow_id}
Get workflow status and details.

**Response:**
```json
{
  "workflow_id": "wf-uuid-1234",
  "status": "completed",
  "repository": "owner/repo-name",
  "branch": "main",
  "total_vulnerabilities": 5,
  "critical_count": 0,
  "high_count": 2,
  "auto_remediated": 3,
  "awaiting_approval": 2,
  "steps": [
    {
      "step_id": "scan",
      "status": "completed",
      "started_at": "...",
      "completed_at": "..."
    }
  ]
}
```

#### GET /workflows
List all workflows with optional filters.

**Query Parameters:**
- `status`: Filter by status (pending, scanning, completed, failed)
- `repository`: Filter by repository
- `limit`: Max results (default: 50)

**Response:**
```json
{
  "total": 10,
  "workflows": [ ... ]
}
```

#### POST /workflow/{workflow_id}/cancel
Cancel a running workflow.

### Approvals

#### GET /approvals
Get workflows awaiting approval.

#### POST /approve
Approve or reject pending remediations.

**Request:**
```json
{
  "workflow_id": "wf-uuid-1234",
  "vulnerability_ids": ["vuln-1", "vuln-2"],
  "approved": true,
  "approver": "user@email.com",
  "comment": "Approved after review"
}
```

### Statistics

#### GET /stats
Get orchestrator statistics.

**Response:**
```json
{
  "workflows": {
    "total": 50,
    "by_status": {
      "completed": 40,
      "failed": 5,
      "pending": 5
    }
  }
}
```

---

## Security Scanner API (Port 8001)

### GET /health
Scanner health with available scanners.

**Response:**
```json
{
  "status": "healthy",
  "agent": "security-scanner",
  "version": "1.0.0",
  "scanners": {
    "dependency": true,
    "code": true,
    "secret": true,
    "container": true,
    "iac": true
  }
}
```

### GET /scanners
List available scanners with details.

### POST /scan
Trigger a security scan.

**Request:**
```json
{
  "repository": "owner/repo-name",
  "branch": "main",
  "commit_sha": "abc123",
  "scan_types": ["dependency", "code", "secret"],
  "target_path": "/"
}
```

**Response:**
```json
{
  "scan_id": "scan-uuid-1234",
  "status": "started",
  "message": "Scan initiated"
}
```

### GET /scan/{scan_id}
Get scan results.

**Response:**
```json
{
  "scan_id": "scan-uuid-1234",
  "status": "completed",
  "results": [
    {
      "scan_type": "dependency",
      "vulnerabilities": [
        {
          "id": "vuln-1",
          "cve_id": "CVE-2024-1234",
          "title": "SQL Injection in library-x",
          "severity": "high",
          "cvss_score": 8.5,
          "package_name": "library-x",
          "package_version": "1.0.0",
          "fixed_version": "1.0.1"
        }
      ],
      "total_count": 5
    }
  ]
}
```

### GET /cve/{cve_id}
Lookup CVE details.

---

## Risk Assessment API (Port 8002)

### GET /health
Assessment agent health.

### POST /assess
Assess vulnerabilities with business context.

**Request:**
```json
{
  "vulnerabilities": [ ... ],
  "repository": "owner/repo-name",
  "business_context": {
    "service_type": "api",
    "is_public_facing": true,
    "data_sensitivity": "high",
    "handles_pii": true,
    "business_criticality": 9
  },
  "use_ai_analysis": true
}
```

**Response:**
```json
{
  "assessment_id": "assess-uuid-1234",
  "repository": "owner/repo-name",
  "total_assessed": 5,
  "assessments": [
    {
      "vulnerability_id": "vuln-1",
      "risk_score": {
        "cvss_score": 8.5,
        "business_impact_score": 9.0,
        "total_score": 8.75,
        "priority": "P0"
      },
      "remediation_urgency": "immediate",
      "recommended_action": "Patch immediately"
    }
  ],
  "summary": {
    "P0": 1,
    "P1": 2,
    "P2": 2
  }
}
```

### POST /assess/single
Assess a single vulnerability.

### GET /assessment/{assessment_id}
Get assessment by ID.

### POST /context
Register business context for a repository.

### GET /context/{repository}
Get business context.

### GET /priorities
Get priority definitions and thresholds.

---

## Auto-Remediation API (Port 8003)

### GET /health
Remediation agent health.

**Response:**
```json
{
  "status": "healthy",
  "agent": "auto-remediation",
  "version": "1.0.0",
  "github_enabled": true,
  "ai_enabled": true,
  "templates_count": 16
}
```

### POST /remediate
Remediate a single vulnerability.

**Request:**
```json
{
  "vulnerability": { ... },
  "repository": "owner/repo-name",
  "branch": "main",
  "priority": "P1",
  "auto_create_pr": true,
  "require_approval": false
}
```

**Response:**
```json
{
  "remediation_id": "rem-uuid-1234",
  "vulnerability_id": "vuln-1",
  "status": "completed",
  "fix": {
    "fix_type": "dependency_upgrade",
    "title": "Upgrade library-x to 1.0.1",
    "changes": [ ... ],
    "confidence": "high"
  },
  "pr_info": {
    "pr_number": 42,
    "pr_url": "https://github.com/owner/repo/pull/42"
  }
}
```

### POST /remediate/batch
Remediate multiple vulnerabilities.

### POST /preview
Preview fix without creating PR.

### GET /remediation/{remediation_id}
Get remediation status.

### GET /templates
List available fix templates.

### GET /templates/{template_id}
Get template details.

### GET /stats
Remediation statistics.

---

## Monitoring API (Port 8000/monitoring)

### GET /monitoring/health
Monitoring system health.

### GET /monitoring/metrics/summary
Get metrics summary.

**Response:**
```json
{
  "vulnerabilities_per_hour": { "2026-02-28-10": 5 },
  "remediation_success_rate": 85.5,
  "average_fix_time_seconds": 120,
  "total_remediation_attempts": 100,
  "total_remediation_successes": 85
}
```

### GET /monitoring/dashboard/overview
System overview dashboard.

### GET /monitoring/dashboard/vulnerabilities
Vulnerability dashboard.

### GET /monitoring/dashboard/remediation
Remediation dashboard.

### GET /monitoring/dashboard/agents
Agent health dashboard.

### GET /monitoring/alerts
Get active alerts.

### POST /monitoring/alerts/{alert_id}/resolve
Resolve an alert.

---

## HITL API (Port 8000/hitl)

### POST /hitl/approvals
Create approval request.

**Request:**
```json
{
  "workflow_id": "wf-uuid-1234",
  "title": "Critical vulnerability remediation",
  "description": "Requires approval for P0 fixes",
  "vulnerability_ids": ["vuln-1"],
  "priority": "P0",
  "risk_summary": "High risk SQL injection",
  "expires_in_hours": 24
}
```

### GET /hitl/approvals
List all approvals.

### GET /hitl/approvals/pending
Get pending approvals.

### GET /hitl/approvals/{approval_id}
Get approval details with comments.

### POST /hitl/approvals/{approval_id}/decide
Approve or reject.

**Request:**
```json
{
  "approved": true,
  "resolver": "admin@company.com",
  "comment": "Verified and approved"
}
```

### POST /hitl/comments
Add comment to any entity.

### GET /hitl/comments/{target_id}
Get comments for entity.

### GET /hitl/audit
Query audit log.

### GET /hitl/audit/workflow/{workflow_id}/timeline
Get workflow timeline.

### GET /hitl/audit/stats
Audit statistics.

---

## Error Responses

All APIs return consistent error responses:
```json
{
  "detail": "Error message here"
}
```

### Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation error)
- `401`: Unauthorized
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `429`: Rate Limited
- `500`: Internal Server Error

---

## Rate Limits

| Endpoint Type | Requests/Min | Requests/Hour |
|---------------|--------------|---------------|
| Health checks | 120 | 2000 |
| Read endpoints | 60 | 1000 |
| Write endpoints | 30 | 500 |
| Scan triggers | 5 | 50 |

Rate limit headers:
- `X-RateLimit-Limit`: Max requests per window
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Window reset timestamp

---

## Webhooks

### POST /webhook/scan-complete
Webhook for scan completion notifications.

**Payload:**
```json
{
  "event": "scan_complete",
  "scan_id": "scan-uuid-1234",
  "workflow_id": "wf-uuid-1234",
  "status": "completed",
  "vulnerabilities_found": 5
}
```
