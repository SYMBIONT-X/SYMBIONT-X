"""Configuration for Risk Assessment Agent."""

from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Risk Assessment Agent settings."""
    
    # Agent identification
    agent_name: str = "risk-assessment"
    agent_version: str = "1.0.0"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8002
    
    # Azure OpenAI / Microsoft Foundry
    azure_openai_endpoint: Optional[str] = Field(None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: Optional[str] = Field(None, env="AZURE_OPENAI_KEY")
    azure_openai_deployment: str = Field("gpt-4", env="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field("2024-02-15-preview", env="AZURE_OPENAI_API_VERSION")
    
    # OpenAI fallback (for local development)
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4", env="OPENAI_MODEL")
    
    # Security Scanner communication
    security_scanner_url: str = Field("http://localhost:8001", env="SECURITY_SCANNER_URL")
    
    # Orchestrator communication
    orchestrator_url: str = Field("http://localhost:8000", env="ORCHESTRATOR_URL")
    
    # Risk assessment settings
    enable_ai_analysis: bool = Field(True, env="ENABLE_AI_ANALYSIS")
    max_vulnerabilities_per_batch: int = 50
    
    # Priority thresholds
    critical_cvss_threshold: float = 9.0
    high_cvss_threshold: float = 7.0
    medium_cvss_threshold: float = 4.0
    
    # Business context weights
    weight_cvss: float = 0.4
    weight_exploitability: float = 0.25
    weight_business_impact: float = 0.25
    weight_data_sensitivity: float = 0.1
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_json: bool = Field(False, env="LOG_JSON")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
