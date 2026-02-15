"""CVE Database lookup using NVD API."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

import httpx

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.utils import get_logger
from shared.models import Severity


class CVELookup:
    """Client for looking up CVE details from the NVD database."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.logger = get_logger("cve-lookup")
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(hours=24)
    
    async def lookup(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Look up CVE details from NVD.
        
        Args:
            cve_id: CVE identifier (e.g., 'CVE-2024-12345')
            
        Returns:
            CVE details dict or None if not found
        """
        
        if not cve_id or not cve_id.startswith("CVE-"):
            return None
        
        # Check cache first
        if cve_id in self._cache:
            cached = self._cache[cve_id]
            if datetime.utcnow() - cached["cached_at"] < self._cache_ttl:
                self.logger.debug("CVE cache hit", cve_id=cve_id)
                return cached["data"]
        
        self.logger.info("Looking up CVE", cve_id=cve_id)
        
        try:
            headers = {"Accept": "application/json"}
            if self.api_key:
                headers["apiKey"] = self.api_key
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.base_url,
                    params={"cveId": cve_id},
                    headers=headers,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    vulnerabilities = data.get("vulnerabilities", [])
                    
                    if vulnerabilities:
                        cve_data = self._parse_cve_response(vulnerabilities[0])
                        
                        # Cache the result
                        self._cache[cve_id] = {
                            "data": cve_data,
                            "cached_at": datetime.utcnow(),
                        }
                        
                        return cve_data
                elif response.status_code == 404:
                    self.logger.warning("CVE not found", cve_id=cve_id)
                else:
                    self.logger.warning(
                        "NVD API error",
                        cve_id=cve_id,
                        status=response.status_code,
                    )
                    
        except httpx.TimeoutException:
            self.logger.error("NVD API timeout", cve_id=cve_id)
        except Exception as e:
            self.logger.error("CVE lookup failed", cve_id=cve_id, error=str(e))
        
        return None
    
    async def lookup_batch(self, cve_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Look up multiple CVEs.
        
        Args:
            cve_ids: List of CVE identifiers
            
        Returns:
            Dict mapping CVE IDs to their details
        """
        
        results = {}
        
        # NVD has rate limits, so we batch requests
        for cve_id in cve_ids:
            result = await self.lookup(cve_id)
            if result:
                results[cve_id] = result
            
            # Rate limiting: NVD allows ~5 requests per 30 seconds without API key
            if not self.api_key:
                await asyncio.sleep(6)
            else:
                await asyncio.sleep(0.6)
        
        return results
    
    def _parse_cve_response(self, vuln_data: dict) -> Dict[str, Any]:
        """Parse NVD CVE response into a simplified format."""
        
        cve = vuln_data.get("cve", {})
        
        # Extract CVSS scores (prefer v3.1, then v3.0, then v2.0)
        cvss_data = self._extract_cvss(cve)
        
        # Extract description
        descriptions = cve.get("descriptions", [])
        description = ""
        for desc in descriptions:
            if desc.get("lang") == "en":
                description = desc.get("value", "")
                break
        
        # Extract references
        references = []
        for ref in cve.get("references", []):
            references.append({
                "url": ref.get("url"),
                "source": ref.get("source"),
            })
        
        # Extract affected products (CPE)
        affected_products = self._extract_affected_products(cve)
        
        return {
            "cve_id": cve.get("id"),
            "description": description,
            "published": cve.get("published"),
            "last_modified": cve.get("lastModified"),
            "cvss_v3_score": cvss_data.get("v3_score"),
            "cvss_v3_vector": cvss_data.get("v3_vector"),
            "cvss_v2_score": cvss_data.get("v2_score"),
            "severity": cvss_data.get("severity"),
            "references": references[:5],  # Limit to first 5
            "affected_products": affected_products[:10],  # Limit to first 10
            "weaknesses": self._extract_weaknesses(cve),
        }
    
    def _extract_cvss(self, cve: dict) -> Dict[str, Any]:
        """Extract CVSS scores from CVE data."""
        
        metrics = cve.get("metrics", {})
        
        result = {
            "v3_score": None,
            "v3_vector": None,
            "v2_score": None,
            "severity": Severity.UNKNOWN.value,
        }
        
        # Try CVSS v3.1
        cvss_v31 = metrics.get("cvssMetricV31", [])
        if cvss_v31:
            cvss_data = cvss_v31[0].get("cvssData", {})
            result["v3_score"] = cvss_data.get("baseScore")
            result["v3_vector"] = cvss_data.get("vectorString")
            result["severity"] = self._cvss_to_severity(result["v3_score"])
            return result
        
        # Try CVSS v3.0
        cvss_v30 = metrics.get("cvssMetricV30", [])
        if cvss_v30:
            cvss_data = cvss_v30[0].get("cvssData", {})
            result["v3_score"] = cvss_data.get("baseScore")
            result["v3_vector"] = cvss_data.get("vectorString")
            result["severity"] = self._cvss_to_severity(result["v3_score"])
            return result
        
        # Try CVSS v2.0
        cvss_v2 = metrics.get("cvssMetricV2", [])
        if cvss_v2:
            cvss_data = cvss_v2[0].get("cvssData", {})
            result["v2_score"] = cvss_data.get("baseScore")
            result["severity"] = self._cvss_to_severity(result["v2_score"])
            return result
        
        return result
    
    def _cvss_to_severity(self, score: Optional[float]) -> str:
        """Convert CVSS score to severity level."""
        
        if score is None:
            return Severity.UNKNOWN.value
        
        if score >= 9.0:
            return Severity.CRITICAL.value
        elif score >= 7.0:
            return Severity.HIGH.value
        elif score >= 4.0:
            return Severity.MEDIUM.value
        else:
            return Severity.LOW.value
    
    def _extract_affected_products(self, cve: dict) -> List[str]:
        """Extract affected products from CPE data."""
        
        products = []
        
        configurations = cve.get("configurations", [])
        for config in configurations:
            nodes = config.get("nodes", [])
            for node in nodes:
                cpe_matches = node.get("cpeMatch", [])
                for cpe in cpe_matches:
                    if cpe.get("vulnerable"):
                        criteria = cpe.get("criteria", "")
                        # Extract product name from CPE string
                        parts = criteria.split(":")
                        if len(parts) >= 5:
                            vendor = parts[3]
                            product = parts[4]
                            products.append(f"{vendor}/{product}")
        
        return list(set(products))
    
    def _extract_weaknesses(self, cve: dict) -> List[str]:
        """Extract CWE weaknesses from CVE data."""
        
        weaknesses = []
        
        for weakness in cve.get("weaknesses", []):
            for desc in weakness.get("description", []):
                if desc.get("lang") == "en":
                    weaknesses.append(desc.get("value", ""))
        
        return weaknesses


# Convenience function
async def enrich_vulnerability_with_cve(
    vulnerability: dict,
    cve_lookup: CVELookup,
) -> dict:
    """
    Enrich a vulnerability with additional CVE data from NVD.
    
    Args:
        vulnerability: Vulnerability dict with cve_id field
        cve_lookup: CVELookup instance
        
    Returns:
        Enriched vulnerability dict
    """
    
    cve_id = vulnerability.get("cve_id")
    if not cve_id:
        return vulnerability
    
    cve_data = await cve_lookup.lookup(cve_id)
    if not cve_data:
        return vulnerability
    
    # Enrich with NVD data
    enriched = vulnerability.copy()
    
    if cve_data.get("cvss_v3_score") and not enriched.get("cvss_score"):
        enriched["cvss_score"] = cve_data["cvss_v3_score"]
    
    if cve_data.get("severity") and enriched.get("severity") == "unknown":
        enriched["severity"] = cve_data["severity"]
    
    if cve_data.get("description") and len(enriched.get("description", "")) < 100:
        enriched["description"] = cve_data["description"][:500]
    
    # Add NVD metadata
    enriched["nvd_data"] = {
        "published": cve_data.get("published"),
        "references": cve_data.get("references", []),
        "weaknesses": cve_data.get("weaknesses", []),
    }
    
    return enriched
