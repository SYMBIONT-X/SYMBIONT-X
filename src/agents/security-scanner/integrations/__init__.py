"""External integrations for Security Scanner Agent."""

from .github import GitHubClient
from .cve_lookup import CVELookup, enrich_vulnerability_with_cve
from .azure_security import AzureSecurityClient

__all__ = [
    "GitHubClient",
    "CVELookup",
    "enrich_vulnerability_with_cve",
    "AzureSecurityClient",
]
