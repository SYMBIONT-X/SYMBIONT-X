"""Azure Security Center / Microsoft Defender for Cloud integration."""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

import httpx

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.utils import get_logger
from shared.models import Vulnerability, Severity


class AzureSecurityClient:
    """Client for Azure Security Center / Microsoft Defender for Cloud APIs."""
    
    def __init__(
        self,
        subscription_id: str,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
    ):
        self.subscription_id = subscription_id
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = access_token
        self._token_expires_at: Optional[datetime] = None
        
        self.base_url = "https://management.azure.com"
        self.api_version = "2023-01-01"
        self.logger = get_logger("azure-security")
    
    async def _get_access_token(self) -> str:
        """Get or refresh Azure access token."""
        
        # Use provided token if available
        if self._access_token:
            return self._access_token
        
        # Check if we have a valid cached token
        if self._token_expires_at and datetime.utcnow() < self._token_expires_at:
            return self._access_token
        
        # Get new token using client credentials
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("Azure credentials not configured")
        
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "https://management.azure.com/.default",
                },
            )
            
            if response.status_code == 200:
                data = response.json()
                self._access_token = data["access_token"]
                expires_in = data.get("expires_in", 3600)
                self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                return self._access_token
            else:
                raise Exception(f"Failed to get Azure token: {response.status_code}")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> Optional[Dict[str, Any]]:
        """Make an authenticated request to Azure API."""
        
        try:
            token = await self._get_access_token()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            
            url = f"{self.base_url}{endpoint}"
            
            # Add API version to params
            params = params or {}
            params["api-version"] = self.api_version
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json_data,
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(
                        "Azure API error",
                        status=response.status_code,
                        endpoint=endpoint,
                    )
                    return None
                    
        except Exception as e:
            self.logger.error("Azure API request failed", error=str(e))
            return None
    
    async def get_security_alerts(self) -> List[Dict[str, Any]]:
        """Get security alerts from Microsoft Defender for Cloud."""
        
        endpoint = f"/subscriptions/{self.subscription_id}/providers/Microsoft.Security/alerts"
        
        self.logger.info("Fetching security alerts")
        
        result = await self._make_request("GET", endpoint)
        
        if result:
            return result.get("value", [])
        return []
    
    async def get_security_recommendations(self) -> List[Dict[str, Any]]:
        """Get security recommendations from Microsoft Defender for Cloud."""
        
        endpoint = f"/subscriptions/{self.subscription_id}/providers/Microsoft.Security/assessments"
        
        self.logger.info("Fetching security recommendations")
        
        result = await self._make_request("GET", endpoint)
        
        if result:
            return result.get("value", [])
        return []
    
    async def get_secure_score(self) -> Optional[Dict[str, Any]]:
        """Get the secure score for the subscription."""
        
        endpoint = f"/subscriptions/{self.subscription_id}/providers/Microsoft.Security/secureScores/ascScore"
        
        self.logger.info("Fetching secure score")
        
        return await self._make_request("GET", endpoint)
    
    async def get_container_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Get container vulnerabilities from Defender for Containers."""
        
        endpoint = f"/subscriptions/{self.subscription_id}/providers/Microsoft.Security/subAssessments"
        
        self.logger.info("Fetching container vulnerabilities")
        
        result = await self._make_request("GET", endpoint)
        
        if result:
            return result.get("value", [])
        return []
    
    def convert_alert_to_vulnerability(
        self,
        alert: Dict[str, Any],
        repository: str,
    ) -> Vulnerability:
        """Convert an Azure Security alert to our Vulnerability model."""
        
        properties = alert.get("properties", {})
        
        # Map Azure severity to our severity
        azure_severity = properties.get("severity", "Medium")
        severity_map = {
            "High": Severity.HIGH,
            "Medium": Severity.MEDIUM,
            "Low": Severity.LOW,
        }
        severity = severity_map.get(azure_severity, Severity.MEDIUM)
        
        # Check if it's a critical alert
        if "Critical" in properties.get("alertDisplayName", ""):
            severity = Severity.CRITICAL
        
        return Vulnerability(
            id=f"azure-{alert.get('name', 'unknown')}",
            title=properties.get("alertDisplayName", "Azure Security Alert"),
            description=properties.get("description", "")[:500],
            severity=severity,
            fix_recommendation=properties.get("remediationSteps", "Review alert in Azure Portal"),
            source="azure-security-center",
            repository=repository,
            detected_at=datetime.fromisoformat(
                properties.get("timeGeneratedUtc", datetime.utcnow().isoformat()).replace("Z", "+00:00")
            ),
        )
    
    def convert_recommendation_to_vulnerability(
        self,
        recommendation: Dict[str, Any],
        repository: str,
    ) -> Optional[Vulnerability]:
        """Convert an Azure Security recommendation to our Vulnerability model."""
        
        properties = recommendation.get("properties", {})
        status = properties.get("status", {})
        
        # Only include unhealthy recommendations
        if status.get("code") == "Healthy":
            return None
        
        # Map severity
        metadata = properties.get("metadata", {})
        severity_str = metadata.get("severity", "Medium")
        severity_map = {
            "High": Severity.HIGH,
            "Medium": Severity.MEDIUM,
            "Low": Severity.LOW,
        }
        severity = severity_map.get(severity_str, Severity.MEDIUM)
        
        return Vulnerability(
            id=f"azure-rec-{recommendation.get('name', 'unknown')}",
            title=metadata.get("displayName", "Azure Security Recommendation"),
            description=metadata.get("description", "")[:500],
            severity=severity,
            fix_recommendation=metadata.get("remediationDescription", "Review recommendation in Azure Portal"),
            source="azure-security-center",
            repository=repository,
        )


# Need to import timedelta
from datetime import timedelta
