"""Security Scanner Agent - Main entry point."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import uuid

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from shared.models import ScanResult, ScanType
from shared.utils import setup_logging, get_logger
from config import settings
from scanners import (
    DependencyScanner,
    CodeScanner,
    SecretScanner,
    ContainerScanner,
    IaCScanner,
)
from integrations import CVELookup


# Setup logging
setup_logging(level=settings.log_level, json_format=settings.log_json)
logger = get_logger("security-scanner")


# Initialize FastAPI app
app = FastAPI(
    title="SYMBIONT-X Security Scanner Agent",
    description="Continuous vulnerability detection for DevSecOps",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scanners
dependency_scanner = DependencyScanner()
code_scanner = CodeScanner()
secret_scanner = SecretScanner()
container_scanner = ContainerScanner()
iac_scanner = IaCScanner()

# Initialize CVE lookup
cve_lookup = CVELookup()


# ----- Request/Response Models -----

class ScanRequest(BaseModel):
    """Request to trigger a scan."""
    repository: str = Field(..., description="Repository to scan (e.g., 'SYMBIONT-X/SYMBIONT-X')")
    branch: str = Field(default="main", description="Branch to scan")
    commit_sha: Optional[str] = Field(None, description="Specific commit to scan")
    scan_types: List[ScanType] = Field(
        default=[ScanType.DEPENDENCY, ScanType.CODE, ScanType.SECRET, ScanType.CONTAINER, ScanType.IAC],
        description="Types of scans to run"
    )
    target_path: Optional[str] = Field(None, description="Path to scan (defaults to current directory)")
    enrich_cve: bool = Field(default=False, description="Enrich vulnerabilities with NVD CVE data")


class ImageScanRequest(BaseModel):
    """Request to scan a container image."""
    image: str = Field(..., description="Container image to scan (e.g., 'nginx:latest')")
    repository: str = Field(default="", description="Repository name for tracking")


class ScanResponse(BaseModel):
    """Response with scan results."""
    scan_id: str
    status: str
    message: str
    results: Optional[List[ScanResult]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    agent: str
    version: str
    scanners: dict
    timestamp: str


class WebhookPayload(BaseModel):
    """GitHub webhook payload (simplified)."""
    ref: Optional[str] = None
    repository: Optional[dict] = None
    commits: Optional[List[dict]] = None
    pull_request: Optional[dict] = None
    action: Optional[str] = None


# ----- In-memory scan storage (would be Cosmos DB in production) -----

scan_results_store: dict = {}


# ----- API Endpoints -----

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check agent health and scanner availability."""
    return HealthResponse(
        status="healthy",
        agent=settings.agent_name,
        version=settings.agent_version,
        scanners={
            "dependency": dependency_scanner.is_available(),
            "code": code_scanner.is_available(),
            "secret": secret_scanner.is_available(),
            "container": container_scanner.is_available(),
            "iac": iac_scanner.is_available(),
        },
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post("/scan", response_model=ScanResponse)
async def trigger_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Trigger a security scan."""
    
    scan_id = str(uuid.uuid4())
    
    logger.info(
        "Scan requested",
        scan_id=scan_id,
        repository=request.repository,
        branch=request.branch,
        scan_types=[st.value for st in request.scan_types],
    )
    
    # Determine target path
    target_path = Path(request.target_path) if request.target_path else Path.cwd()
    
    if not target_path.exists():
        raise HTTPException(status_code=400, detail=f"Target path does not exist: {target_path}")
    
    # Run scan in background
    background_tasks.add_task(
        run_scan,
        scan_id=scan_id,
        request=request,
        target_path=target_path,
    )
    
    return ScanResponse(
        scan_id=scan_id,
        status="started",
        message=f"Scan started for {request.repository}",
    )


@app.post("/scan/image", response_model=ScanResponse)
async def scan_container_image(request: ImageScanRequest, background_tasks: BackgroundTasks):
    """Scan a container image for vulnerabilities."""
    
    if not container_scanner.is_available():
        raise HTTPException(status_code=503, detail="Container scanner (Trivy) not available")
    
    scan_id = str(uuid.uuid4())
    
    logger.info("Image scan requested", scan_id=scan_id, image=request.image)
    
    # Run scan in background
    background_tasks.add_task(
        run_image_scan,
        scan_id=scan_id,
        image=request.image,
        repository=request.repository,
    )
    
    return ScanResponse(
        scan_id=scan_id,
        status="started",
        message=f"Image scan started for {request.image}",
    )


@app.get("/scan/{scan_id}", response_model=ScanResponse)
async def get_scan_results(scan_id: str):
    """Get results for a specific scan."""
    
    if scan_id not in scan_results_store:
        raise HTTPException(status_code=404, detail=f"Scan not found: {scan_id}")
    
    stored = scan_results_store[scan_id]
    
    return ScanResponse(
        scan_id=scan_id,
        status=stored["status"],
        message=stored["message"],
        results=stored.get("results"),
    )


@app.post("/webhook/github")
async def github_webhook(payload: WebhookPayload, background_tasks: BackgroundTasks):
    """Handle GitHub webhook events."""
    
    logger.info("Received GitHub webhook", action=payload.action)
    
    # Extract repository info
    repo_info = payload.repository or {}
    repo_name = repo_info.get("full_name", "unknown/unknown")
    
    # Determine branch from ref
    branch = "main"
    if payload.ref:
        branch = payload.ref.replace("refs/heads/", "")
    
    # For PRs, get the head branch
    if payload.pull_request:
        branch = payload.pull_request.get("head", {}).get("ref", branch)
    
    # Create scan request
    scan_request = ScanRequest(
        repository=repo_name,
        branch=branch,
        scan_types=[ScanType.DEPENDENCY, ScanType.CODE, ScanType.SECRET, ScanType.CONTAINER, ScanType.IAC],
    )
    
    scan_id = str(uuid.uuid4())
    
    # Run scan in background
    background_tasks.add_task(
        run_scan,
        scan_id=scan_id,
        request=scan_request,
        target_path=Path.cwd(),
    )
    
    return {"status": "accepted", "scan_id": scan_id}


@app.get("/scanners")
async def list_scanners():
    """List available scanners and their status."""
    return {
        "scanners": [
            {
                "name": "dependency-scanner",
                "type": ScanType.DEPENDENCY,
                "available": dependency_scanner.is_available(),
                "description": "Scans Python dependencies for known vulnerabilities using pip-audit",
            },
            {
                "name": "code-scanner",
                "type": ScanType.CODE,
                "available": code_scanner.is_available(),
                "description": "Scans Python code for security issues using Bandit",
            },
            {
                "name": "secret-scanner",
                "type": ScanType.SECRET,
                "available": secret_scanner.is_available(),
                "description": "Detects leaked secrets and credentials using detect-secrets",
            },
            {
                "name": "container-scanner",
                "type": ScanType.CONTAINER,
                "available": container_scanner.is_available(),
                "description": "Scans container images and Dockerfiles using Trivy",
            },
            {
                "name": "iac-scanner",
                "type": ScanType.IAC,
                "available": iac_scanner.is_available(),
                "description": "Scans Infrastructure as Code (Bicep, Terraform) using Checkov",
            },
        ]
    }


@app.get("/cve/{cve_id}")
async def lookup_cve(cve_id: str):
    """Look up CVE details from NVD."""
    
    result = await cve_lookup.lookup(cve_id)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"CVE not found: {cve_id}")
    
    return result


# ----- Background Tasks -----

async def run_scan(scan_id: str, request: ScanRequest, target_path: Path):
    """Run the actual scan (background task)."""
    
    scan_results_store[scan_id] = {
        "status": "running",
        "message": "Scan in progress...",
        "results": [],
    }
    
    results = []
    
    try:
        # Run each requested scanner
        if ScanType.DEPENDENCY in request.scan_types and dependency_scanner.is_available():
            logger.info("Running dependency scan", scan_id=scan_id)
            result = await dependency_scanner.scan(
                target_path=target_path,
                repository=request.repository,
                branch=request.branch,
                commit_sha=request.commit_sha,
            )
            results.append(result)
        
        if ScanType.CODE in request.scan_types and code_scanner.is_available():
            logger.info("Running code scan", scan_id=scan_id)
            result = await code_scanner.scan(
                target_path=target_path,
                repository=request.repository,
                branch=request.branch,
                commit_sha=request.commit_sha,
            )
            results.append(result)
        
        if ScanType.SECRET in request.scan_types and secret_scanner.is_available():
            logger.info("Running secret scan", scan_id=scan_id)
            result = await secret_scanner.scan(
                target_path=target_path,
                repository=request.repository,
                branch=request.branch,
                commit_sha=request.commit_sha,
            )
            results.append(result)
        
        if ScanType.CONTAINER in request.scan_types and container_scanner.is_available():
            logger.info("Running container scan", scan_id=scan_id)
            result = await container_scanner.scan(
                target_path=target_path,
                repository=request.repository,
                branch=request.branch,
                commit_sha=request.commit_sha,
            )
            results.append(result)
        
        if ScanType.IAC in request.scan_types and iac_scanner.is_available():
            logger.info("Running IaC scan", scan_id=scan_id)
            result = await iac_scanner.scan(
                target_path=target_path,
                repository=request.repository,
                branch=request.branch,
                commit_sha=request.commit_sha,
            )
            results.append(result)
        
        # Calculate totals
        total_vulns = sum(r.total_count for r in results)
        critical_count = sum(r.critical_count for r in results)
        
        scan_results_store[scan_id] = {
            "status": "completed",
            "message": f"Scan completed. Found {total_vulns} vulnerabilities ({critical_count} critical).",
            "results": results,
        }
        
        logger.info(
            "Scan completed",
            scan_id=scan_id,
            total_vulnerabilities=total_vulns,
            critical=critical_count,
        )
        
    except Exception as e:
        logger.error("Scan failed", scan_id=scan_id, error=str(e))
        scan_results_store[scan_id] = {
            "status": "failed",
            "message": f"Scan failed: {str(e)}",
            "results": results,
        }


async def run_image_scan(scan_id: str, image: str, repository: str):
    """Run container image scan (background task)."""
    
    scan_results_store[scan_id] = {
        "status": "running",
        "message": f"Scanning image {image}...",
        "results": [],
    }
    
    try:
        result = await container_scanner.scan_image(
            image_name=image,
            repository=repository,
        )
        
        scan_results_store[scan_id] = {
            "status": "completed",
            "message": f"Image scan completed. Found {result.total_count} vulnerabilities.",
            "results": [result],
        }
        
    except Exception as e:
        logger.error("Image scan failed", scan_id=scan_id, error=str(e))
        scan_results_store[scan_id] = {
            "status": "failed",
            "message": f"Image scan failed: {str(e)}",
            "results": [],
        }


# ----- Main Entry Point -----

def main():
    """Start the Security Scanner Agent."""
    logger.info(
        "Starting Security Scanner Agent",
        host=settings.host,
        port=settings.port,
    )
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
