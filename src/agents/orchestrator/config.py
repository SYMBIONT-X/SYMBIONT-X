"""Configuration for Orchestrator Agent."""

from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Orchestrator Agent settings."""
    
    # Agent identification
    agent_name: str = "orchestrator"
    agent_version: str = "1.0.0"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Agent URLs
    security_scanner_url: str = Field(
        "http://localhost:8001", 
        env="SECURITY_SCANNER_URL"
    )
    risk_assessment_url: str = Field(
        "http://localhost:8002", 
        env="RISK_ASSESSMENT_URL"
    )
    auto_remediation_url: str = Field(
        "http://localhost:8003", 
        env="AUTO_REMEDIATION_URL"
    )
    
    # Azure Cosmos DB (for state management)
    cosmos_endpoint: Optional[str] = Field(None, env="COSMOS_ENDPOINT")
    cosmos_key: Optional[str] = Field(None, env="COSMOS_KEY")
    cosmos_database: str = Field("symbiontx", env="COSMOS_DATABASE")
    cosmos_container: str = Field("workflows", env="COSMOS_CONTAINER")
    
    # Workflow settings
    auto_remediate_p3_p4: bool = Field(True, env="AUTO_REMEDIATE_P3_P4")
    auto_remediate_p2: bool = Field(False, env="AUTO_REMEDIATE_P2")
    require_approval_p0_p1: bool = Field(True, env="REQUIRE_APPROVAL_P0_P1")
    
    # Timeouts
    agent_timeout_seconds: int = Field(300, env="AGENT_TIMEOUT_SECONDS")
    workflow_timeout_seconds: int = Field(600, env="WORKFLOW_TIMEOUT_SECONDS")
    
    # Notifications
    notify_on_p0: bool = Field(True, env="NOTIFY_ON_P0")
    notify_on_p1: bool = Field(True, env="NOTIFY_ON_P1")
    slack_webhook_url: Optional[str] = Field(None, env="SLACK_WEBHOOK_URL")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_json: bool = Field(False, env="LOG_JSON")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
