"""AI-powered vulnerability analysis using Azure OpenAI / Microsoft Foundry."""

import json
from typing import Optional, Dict, Any, List
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_logger
from models import BusinessContext, RiskAssessment
from config import settings

logger = get_logger("ai-analyzer")


class AIAnalyzer:
    """AI-powered vulnerability analysis using GPT-4."""
    
    def __init__(self):
        self.client = None
        self.is_azure = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client (Azure or standard)."""
        
        try:
            # Try Azure OpenAI first
            if settings.azure_openai_endpoint and settings.azure_openai_key:
                from openai import AzureOpenAI
                
                self.client = AzureOpenAI(
                    azure_endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_key,
                    api_version=settings.azure_openai_api_version,
                )
                self.is_azure = True
                self.model = settings.azure_openai_deployment
                logger.info("Initialized Azure OpenAI client")
                
            # Fall back to standard OpenAI
            elif settings.openai_api_key:
                from openai import OpenAI
                
                self.client = OpenAI(api_key=settings.openai_api_key)
                self.is_azure = False
                self.model = settings.openai_model
                logger.info("Initialized OpenAI client")
                
            else:
                logger.warning("No OpenAI credentials configured - AI analysis disabled")
                self.client = None
                
        except ImportError:
            logger.warning("OpenAI package not installed - AI analysis disabled")
            self.client = None
        except Exception as e:
            logger.error("Failed to initialize OpenAI client", error=str(e))
            self.client = None
    
    def is_available(self) -> bool:
        """Check if AI analysis is available."""
        return self.client is not None and settings.enable_ai_analysis
    
    async def analyze_vulnerability(
        self,
        vulnerability: Dict[str, Any],
        business_context: Optional[BusinessContext] = None,
    ) -> Optional[str]:
        """
        Generate AI analysis for a vulnerability.
        
        Returns analysis text or None if unavailable.
        """
        
        if not self.is_available():
            return None
        
        try:
            prompt = self._build_analysis_prompt(vulnerability, business_context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.3,
                max_tokens=500,
            )
            
            analysis = response.choices[0].message.content
            
            logger.info(
                "AI analysis generated",
                vulnerability_id=vulnerability.get("id"),
            )
            
            return analysis
            
        except Exception as e:
            logger.error("AI analysis failed", error=str(e))
            return None
    
    async def analyze_batch(
        self,
        vulnerabilities: List[Dict[str, Any]],
        business_context: Optional[BusinessContext] = None,
    ) -> Dict[str, str]:
        """
        Generate AI analysis for multiple vulnerabilities.
        
        Returns dict mapping vulnerability_id -> analysis.
        """
        
        if not self.is_available():
            return {}
        
        results = {}
        
        # For batch, we prioritize critical/high vulnerabilities
        sorted_vulns = sorted(
            vulnerabilities,
            key=lambda v: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(
                v.get("severity", "medium").lower(), 2
            ),
        )
        
        # Limit to top 10 for API cost management
        for vuln in sorted_vulns[:10]:
            vuln_id = vuln.get("id", "unknown")
            analysis = await self.analyze_vulnerability(vuln, business_context)
            if analysis:
                results[vuln_id] = analysis
        
        return results
    
    async def generate_executive_summary(
        self,
        assessments: List[RiskAssessment],
        business_context: Optional[BusinessContext] = None,
    ) -> Optional[str]:
        """Generate an executive summary of all vulnerabilities."""
        
        if not self.is_available():
            return None
        
        if not assessments:
            return "No vulnerabilities to summarize."
        
        try:
            # Build summary data
            summary_data = {
                "total_vulnerabilities": len(assessments),
                "p0_count": sum(1 for a in assessments if a.risk_score.priority.value == "P0"),
                "p1_count": sum(1 for a in assessments if a.risk_score.priority.value == "P1"),
                "p2_count": sum(1 for a in assessments if a.risk_score.priority.value == "P2"),
                "top_vulnerabilities": [
                    {
                        "id": a.vulnerability_id,
                        "title": a.title,
                        "priority": a.risk_score.priority.value,
                        "score": a.risk_score.total_score,
                    }
                    for a in assessments[:5]
                ],
            }
            
            if business_context:
                summary_data["service"] = business_context.service_name or business_context.repository
                summary_data["is_public_facing"] = business_context.is_public_facing
            
            prompt = f"""Generate a brief executive summary (3-4 sentences) of this security assessment:

{json.dumps(summary_data, indent=2)}

Focus on:
1. Overall risk posture
2. Most critical findings
3. Recommended immediate actions
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a security analyst writing executive summaries. Be concise and actionable.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.3,
                max_tokens=300,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("Executive summary generation failed", error=str(e))
            return None
    
    async def suggest_remediation(
        self,
        vulnerability: Dict[str, Any],
    ) -> Optional[str]:
        """Generate AI-powered remediation suggestions."""
        
        if not self.is_available():
            return None
        
        try:
            prompt = f"""Provide specific remediation steps for this vulnerability:

Title: {vulnerability.get('title', 'Unknown')}
CVE: {vulnerability.get('cve_id', 'N/A')}
Severity: {vulnerability.get('severity', 'Unknown')}
Package: {vulnerability.get('package_name', 'N/A')} @ {vulnerability.get('package_version', 'N/A')}
Fixed Version: {vulnerability.get('fixed_version', 'N/A')}
File: {vulnerability.get('file_path', 'N/A')}

Provide:
1. Immediate mitigation steps
2. Long-term fix
3. Verification steps
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a security engineer providing remediation guidance. Be specific and technical.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.3,
                max_tokens=400,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("Remediation suggestion failed", error=str(e))
            return None
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for vulnerability analysis."""
        
        return """You are an expert security analyst for SYMBIONT-X, an AI-powered DevSecOps platform.

Your role is to analyze vulnerabilities and provide:
1. Clear risk assessment in business terms
2. Potential attack scenarios
3. Impact analysis
4. Prioritization reasoning

Be concise but thorough. Focus on actionable insights.
Use technical terms appropriately but explain impact in business terms.
Always consider the business context when available."""
    
    def _build_analysis_prompt(
        self,
        vulnerability: Dict[str, Any],
        business_context: Optional[BusinessContext] = None,
    ) -> str:
        """Build the analysis prompt for a vulnerability."""
        
        vuln_info = f"""Analyze this security vulnerability:

**Vulnerability Details:**
- ID: {vulnerability.get('id', 'Unknown')}
- CVE: {vulnerability.get('cve_id', 'N/A')}
- Title: {vulnerability.get('title', 'Unknown')}
- Severity: {vulnerability.get('severity', 'Unknown')}
- CVSS Score: {vulnerability.get('cvss_score', 'N/A')}
- Package: {vulnerability.get('package_name', 'N/A')}
- Version: {vulnerability.get('package_version', 'N/A')}
- Fixed Version: {vulnerability.get('fixed_version', 'N/A')}
- File Path: {vulnerability.get('file_path', 'N/A')}
- Description: {vulnerability.get('description', 'N/A')[:500]}
"""
        
        if business_context:
            vuln_info += f"""
**Business Context:**
- Service: {business_context.service_name or business_context.repository}
- Type: {business_context.service_type}
- Public Facing: {business_context.is_public_facing}
- Data Sensitivity: {business_context.data_sensitivity}
- Handles PII: {business_context.handles_pii}
- Handles Financial Data: {business_context.handles_financial_data}
- Business Criticality: {business_context.business_criticality}/10
- Compliance: {', '.join(business_context.compliance_requirements) or 'None specified'}
"""
        
        vuln_info += """
Provide a brief analysis (2-3 sentences) covering:
1. Real-world risk assessment
2. Potential attack scenario
3. Why this priority level is appropriate
"""
        
        return vuln_info
