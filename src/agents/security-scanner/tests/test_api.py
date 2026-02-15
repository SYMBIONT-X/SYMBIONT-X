"""Integration tests for Security Scanner API."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns correct structure."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["agent"] == "security-scanner"
        assert "version" in data
        assert "scanners" in data
        assert "timestamp" in data
    
    def test_health_scanners_structure(self, client):
        """Test health check includes all scanners."""
        response = client.get("/health")
        data = response.json()
        
        scanners = data["scanners"]
        assert "dependency" in scanners
        assert "code" in scanners
        assert "secret" in scanners
        assert "container" in scanners
        assert "iac" in scanners


class TestScannersEndpoint:
    """Tests for /scanners endpoint."""
    
    def test_list_scanners(self, client):
        """Test listing available scanners."""
        response = client.get("/scanners")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "scanners" in data
        assert len(data["scanners"]) == 5
        
        scanner_names = [s["name"] for s in data["scanners"]]
        assert "dependency-scanner" in scanner_names
        assert "code-scanner" in scanner_names
        assert "secret-scanner" in scanner_names
        assert "container-scanner" in scanner_names
        assert "iac-scanner" in scanner_names


class TestScanEndpoint:
    """Tests for /scan endpoint."""
    
    def test_scan_missing_repository(self, client):
        """Test scan request without repository."""
        response = client.post("/scan", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_scan_invalid_path(self, client):
        """Test scan request with invalid path."""
        response = client.post("/scan", json={
            "repository": "test/repo",
            "target_path": "/nonexistent/path/12345",
        })
        
        assert response.status_code == 400
    
    def test_scan_request_accepted(self, client):
        """Test valid scan request is accepted."""
        response = client.post("/scan", json={
            "repository": "test/repo",
            "branch": "main",
            "target_path": "/tmp",
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "scan_id" in data
        assert data["status"] == "started"


class TestScanResultsEndpoint:
    """Tests for /scan/{scan_id} endpoint."""
    
    def test_get_nonexistent_scan(self, client):
        """Test getting results for non-existent scan."""
        response = client.get("/scan/nonexistent-scan-id")
        
        assert response.status_code == 404


class TestCVEEndpoint:
    """Tests for /cve/{cve_id} endpoint."""
    
    def test_lookup_invalid_cve(self, client):
        """Test looking up invalid CVE ID."""
        response = client.get("/cve/invalid-cve")
        
        # Should return 404 since it's not a valid CVE format
        assert response.status_code == 404


# Run tests with: pytest tests/test_api.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
