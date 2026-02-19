"""Configuration for Auto-Remediation Agent."""

from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Auto-Remediation Agent settings."""
    
    # Agent identification
    agent_name: str = "auto-remediation"
    agent_version: str = "1.0.0"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8003
    
    # GitHub integration
    github_token: Optional[str] = Field(None, env="GITHUB_TOKEN")
    github_org: str = Field("SYMBIONT-X", env="GITHUB_ORG")
    github_default_branch: str = Field("main", env="GITHUB_DEFAULT_BRANCH")
    
    # Azure OpenAI for code generation
    azure_openai_endpoint: Optional[str] = Field(None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: Optional[str] = Field(None, env="AZURE_OPENAI_KEY")
    azure_openai_deployment: str = Field("gpt-4", env="AZURE_OPENAI_DEPLOYMENT")
    
    # OpenAI fallback
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    
    # Other agents
    security_scanner_url: str = Field("http://localhost:8001", env="SECURITY_SCANNER_URL")
    risk_assessment_url: str = Field("http://localhost:8002", env="RISK_ASSESSMENT_URL")
    orchestrator_url: str = Field("http://localhost:8000", env="ORCHESTRATOR_URL")
    
    # Auto-remediation settings
    auto_merge_low_risk: bool = Field(False, env="AUTO_MERGE_LOW_RISK")
    require_approval_critical: bool = Field(True, env="REQUIRE_APPROVAL_CRITICAL")
    max_concurrent_prs: int = Field(5, env="MAX_CONCURRENT_PRS")
    
    # PR settings
    pr_branch_prefix: str = "fix/symbiont-x-"
    pr_label_auto: str = "auto-remediation"
    pr_label_security: str = "security"
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_json: bool = Field(False, env="LOG_JSON")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
