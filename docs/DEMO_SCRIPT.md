# SYMBIONT-X Demo Video Script

## Video Specifications
- **Duration**: 2:00 minutes (120 seconds)
- **Format**: Screen recording + voiceover
- **Resolution**: 1920x1080 (Full HD)
- **Audio**: Clear voiceover, no background music

---

## Script with Timing

### Opening (0:00 - 0:12) [12 seconds]

**[SCREEN: SYMBIONT-X Logo + Tagline]**

> **VOICEOVER:**
> "Every 39 seconds, a cyberattack occurs. Security teams are overwhelmed, and vulnerabilities slip through.
> 
> Introducing SYMBIONT-X — an AI-powered multi-agent system that autonomously detects, prioritizes, and fixes security vulnerabilities."

---

### Problem Statement (0:12 - 0:22) [10 seconds]

**[SCREEN: Statistics animation]**
- 25,000+ CVEs published in 2025
- Average 287 days to fix a vulnerability
- 60% of breaches involve unpatched vulnerabilities

> **VOICEOVER:**
> "Traditional security is reactive and slow. SYMBIONT-X changes that with four specialized AI agents working together in real-time."

---

### Architecture Overview (0:22 - 0:35) [13 seconds]

**[SCREEN: Animated architecture diagram showing 4 agents]**

> **VOICEOVER:**
> "Our system consists of four intelligent agents:
> - The Security Scanner detects vulnerabilities across your codebase
> - The Risk Assessor prioritizes using AI and business context
> - The Auto-Remediation agent generates fixes automatically
> - And the Orchestrator coordinates everything with human oversight"

---

### Live Demo Start (0:35 - 0:45) [10 seconds]

**[SCREEN: Dashboard - show all agents healthy]**

> **VOICEOVER:**
> "Let me show you SYMBIONT-X in action. Here's our executive dashboard showing all four agents running and healthy."

**[ACTION: Mouse highlights agent status badges showing "healthy"]**

---

### Trigger Scan (0:45 - 0:55) [10 seconds]

**[SCREEN: Click "Start Security Scan" button]**

> **VOICEOVER:**
> "With one click, I'll trigger a comprehensive security scan of our repository. The system scans for dependency vulnerabilities, code issues, exposed secrets, container risks, and infrastructure misconfigurations."

**[ACTION: Click button, show workflow starting]**

---

### Scan Results (0:55 - 1:10) [15 seconds]

**[SCREEN: Vulnerabilities page with results appearing]**

> **VOICEOVER:**
> "In seconds, our AI agents work together. The scanner detected 6 vulnerabilities. The Risk Assessor analyzed each one using CVSS scores and our business context — categorizing them from P0 critical to P4 informational.
>
> Notice the 2 exposed secrets and 4 code issues — all automatically prioritized."

**[ACTION: Show vulnerability cards with P2 badges, severity indicators]**

---

### Auto-Remediation (1:10 - 1:25) [15 seconds]

**[SCREEN: Show remediation in progress]**

> **VOICEOVER:**
> "For lower-priority issues, SYMBIONT-X automatically generates fixes. Our AI creates precise code patches, dependency upgrades, and even opens pull requests on GitHub — all without human intervention.
>
> Higher priority issues go through our human-in-the-loop approval workflow."

**[ACTION: Show auto-remediation status, then switch to Approvals page]**

---

### Human-in-the-Loop (1:25 - 1:40) [15 seconds]

**[SCREEN: Approvals page with pending approval]**

> **VOICEOVER:**
> "For critical vulnerabilities, security teams get notified instantly via Microsoft Teams. They can review the AI's recommended fix, add comments, and approve or reject with full context.
>
> Every decision is logged in our immutable audit trail for compliance."

**[ACTION: Show approval card, click to expand details, show comment section]**

---

### Monitoring & Metrics (1:40 - 1:50) [10 seconds]

**[SCREEN: Monitoring dashboard with charts]**

> **VOICEOVER:**
> "Our monitoring dashboard shows real-time metrics: vulnerabilities detected per hour, remediation success rates, and time saved compared to manual processes. Teams gain complete visibility into their security posture."

**[ACTION: Highlight key metrics - success rate, time saved]**

---

### Closing (1:50 - 2:00) [10 seconds]

**[SCREEN: Return to Dashboard, then fade to logo + call to action]**

> **VOICEOVER:**
> "SYMBIONT-X transforms security from reactive to proactive. Built with Microsoft AI technologies, it's the future of DevSecOps.
>
> SYMBIONT-X — Secure smarter, not harder."

**[SCREEN: Logo + GitHub URL + "Microsoft AI Dev Days 2026"]**

---

## Storyboard

### Frame-by-Frame Visual Guide

| Time | Frame | Visual | Action |
|------|-------|--------|--------|
| 0:00 | 1 | Logo animation | Fade in |
| 0:05 | 2 | Tagline appears | Text animation |
| 0:12 | 3 | Statistics (3 numbers) | Count-up animation |
| 0:22 | 4 | Architecture diagram | Agents appear one by one |
| 0:35 | 5 | Dashboard full view | Pan across |
| 0:40 | 6 | Agent status section | Highlight badges |
| 0:45 | 7 | "Start Scan" button | Mouse cursor clicks |
| 0:48 | 8 | Workflow started toast | Brief notification |
| 0:55 | 9 | Vulnerabilities page | Results loading |
| 1:00 | 10 | Vulnerability cards | Scroll through list |
| 1:10 | 11 | Remediation status | Show progress |
| 1:18 | 12 | GitHub PR preview | Quick glimpse |
| 1:25 | 13 | Approvals page | Pending items |
| 1:30 | 14 | Approval detail | Expanded view |
| 1:35 | 15 | Comment section | Show comments |
| 1:40 | 16 | Monitoring dashboard | Full charts view |
| 1:45 | 17 | Key metrics highlighted | Zoom on numbers |
| 1:50 | 18 | Dashboard return | Quick transition |
| 1:55 | 19 | Logo + URL | Fade in |
| 2:00 | 20 | End card | Hold |

---

## Demo Data Setup

### Pre-configured Vulnerabilities (for impressive demo)
```json
{
  "vulnerabilities": [
    {
      "id": "vuln-001",
      "title": "SQL Injection in User Authentication",
      "severity": "critical",
      "priority": "P0",
      "cve_id": "CVE-2026-1234",
      "cvss_score": 9.8,
      "file": "src/auth/login.py",
      "status": "awaiting_approval"
    },
    {
      "id": "vuln-002", 
      "title": "Exposed AWS Secret Key in Config",
      "severity": "high",
      "priority": "P1",
      "file": "config/settings.py",
      "status": "awaiting_approval"
    },
    {
      "id": "vuln-003",
      "title": "Hardcoded Database Password",
      "severity": "high",
      "priority": "P2",
      "file": "src/db/connection.py",
      "status": "auto_remediated"
    },
    {
      "id": "vuln-004",
      "title": "Outdated lodash with Prototype Pollution",
      "severity": "medium",
      "priority": "P2",
      "package": "lodash@4.17.15",
      "fixed_version": "4.17.21",
      "status": "auto_remediated"
    },
    {
      "id": "vuln-005",
      "title": "Insecure Bind to 0.0.0.0",
      "severity": "medium",
      "priority": "P3",
      "file": "src/server/config.py",
      "status": "auto_remediated"
    },
    {
      "id": "vuln-006",
      "title": "Missing HTTPS Redirect",
      "severity": "low",
      "priority": "P4",
      "file": "src/middleware/security.py",
      "status": "auto_remediated"
    }
  ]
}
```

### Dashboard Metrics (pre-populated)
```json
{
  "metrics": {
    "total_vulnerabilities": 47,
    "critical_high": 8,
    "auto_remediated": 39,
    "success_rate": 94.5,
    "avg_fix_time_minutes": 3.2,
    "time_saved_hours": 156,
    "workflows_completed": 23,
    "agents_healthy": 4
  }
}
```

---

## Recording Checklist

### Before Recording

- [ ] All 4 agents running and healthy
- [ ] Frontend running on localhost:5173
- [ ] Demo data pre-loaded
- [ ] Browser zoom at 100%
- [ ] Clear browser cache
- [ ] Close unnecessary tabs
- [ ] Hide bookmarks bar
- [ ] Disable notifications
- [ ] Test microphone levels
- [ ] Practice script 3 times

### Screen Recording Settings

- Resolution: 1920x1080
- Frame rate: 30 FPS
- Format: MP4 (H.264)
- Audio: Mono, 44.1kHz

### Post-Recording

- [ ] Trim dead space
- [ ] Add transitions between sections
- [ ] Add logo intro/outro
- [ ] Verify audio levels consistent
- [ ] Add subtle background music (optional)
- [ ] Export at high quality
- [ ] Verify final duration: 2:00

---

## Key Messages to Emphasize

1. **Speed**: "In seconds" - AI works faster than humans
2. **Intelligence**: "AI prioritizes" - Not just detection, smart triage
3. **Automation**: "Without human intervention" - Saves time
4. **Safety**: "Human-in-the-loop" - Responsible AI for critical decisions
5. **Visibility**: "Complete visibility" - Dashboards and metrics
6. **Microsoft**: "Built with Microsoft AI" - Hackathon alignment

---

## Backup Plans

### If agents crash during demo
- Use pre-recorded clips for that section
- Have screenshots ready as fallback

### If scan takes too long
- Cut to pre-loaded results
- "Let me show you results from a previous scan"

### If network issues
- All services run locally
- No external dependencies needed for demo

---

## Script Word Count

- Total words: ~380
- Speaking rate: ~190 words/minute
- Estimated duration: 2:00 ✓

---

## Final Script (Clean Version for Teleprompter)
```
[0:00] Every 39 seconds, a cyberattack occurs. Security teams are overwhelmed, and vulnerabilities slip through. Introducing SYMBIONT-X — an AI-powered multi-agent system that autonomously detects, prioritizes, and fixes security vulnerabilities.

[0:12] Traditional security is reactive and slow. SYMBIONT-X changes that with four specialized AI agents working together in real-time.

[0:22] Our system consists of four intelligent agents: The Security Scanner detects vulnerabilities across your codebase. The Risk Assessor prioritizes using AI and business context. The Auto-Remediation agent generates fixes automatically. And the Orchestrator coordinates everything with human oversight.

[0:35] Let me show you SYMBIONT-X in action. Here's our executive dashboard showing all four agents running and healthy.

[0:45] With one click, I'll trigger a comprehensive security scan. The system scans for dependency vulnerabilities, code issues, exposed secrets, container risks, and infrastructure misconfigurations.

[0:55] In seconds, our AI agents work together. The scanner detected 6 vulnerabilities. The Risk Assessor analyzed each one using CVSS scores and our business context — categorizing them from P0 critical to P4 informational. Notice the 2 exposed secrets and 4 code issues — all automatically prioritized.

[1:10] For lower-priority issues, SYMBIONT-X automatically generates fixes. Our AI creates precise code patches, dependency upgrades, and even opens pull requests on GitHub — all without human intervention. Higher priority issues go through our human-in-the-loop approval workflow.

[1:25] For critical vulnerabilities, security teams get notified instantly via Microsoft Teams. They can review the AI's recommended fix, add comments, and approve or reject with full context. Every decision is logged in our immutable audit trail for compliance.

[1:40] Our monitoring dashboard shows real-time metrics: vulnerabilities detected per hour, remediation success rates, and time saved compared to manual processes. Teams gain complete visibility into their security posture.

[1:50] SYMBIONT-X transforms security from reactive to proactive. Built with Microsoft AI technologies, it's the future of DevSecOps. SYMBIONT-X — Secure smarter, not harder.
```
