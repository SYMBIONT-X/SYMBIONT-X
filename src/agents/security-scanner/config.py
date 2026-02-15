"""Configuration for Security Scanner Agent."""

import os
from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ScannerConfig(BaseModel):
    """Configuration for individual scanners."""
    enabled: bool = True
    timeout_seconds: int = 300
    max_file_size_mb: int = 10


class Settings(BaseSettings):
    """Security Scanner Agent settings."""
    
    # Agent identification
    agent_name: str = "security-scanner"
    agent_version: str = "1.0.0"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8001
    
    # GitHub integration
    github_token: Optional[str] = Field(None, env="GITHUB_TOKEN")
    github_org: str = Field("SYMBIONT-X", env="GITHUB_ORG")
    
    # Azure integration
    azure_keyvault_url: Optional[str] = Field(None, env="AZURE_KEYVAULT_URL")
    cosmos_db_endpoint: Optional[str] = Field(None, env="COSMOS_DB_ENDPOINT")
    cosmos_db_key: Optional[str] = Field(None, env="COSMOS_DB_KEY")
    service_bus_connection: Optional[str] = Field(None, env="SERVICE_BUS_CONNECTION")
    
    # Orchestrator communication
    orchestrator_url: str = Field("http://orchestrator:8000", env="ORCHESTRATOR_URL")
    
    # Scanner configurations
    dependency_scanner: ScannerConfig = ScannerConfig()
    code_scanner: ScannerConfig = ScannerConfig()
    secret_scanner: ScannerConfig = ScannerConfig()
    
    # Scan settings
    scan_on_push: bool = True
    scan_on_pr: bool = True
    scan_schedule_cron: str = "0 */6 * * *"  # Every 6 hours
    
    # Severity thresholds
    fail_on_critical: bool = True
    fail_on_high: bool = False
    min_severity_to_report: str = "low"
    
    # File patterns to exclude
    exclude_patterns: List[str] = [
        "node_modules/",
        "venv/",
        ".git/",
        "__pycache__/",
        "*.min.js",
        "dist/",
        "build/",
    ]
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_json: bool = Field(False, env="LOG_JSON")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
