"""Unit tests for Auto-Remediation Agent."""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import FixType, FixStatus, FixConfidence
from templates import TemplateEngine
from fix_generator import FixGenerator


class TestTemplateEngine:
    """Tests for template engine."""
    
    def setup_method(self):
        self.engine = TemplateEngine()
    
    def test_get_all_templates(self):
        templates = self.engine.get_all_templates()
        assert len(templates) > 0
        assert "python_requirements_update" in templates
    
    def test_get_template_by_id(self):
        template = self.engine.get_template_by_id("python_requirements_update")
        assert template is not None
        assert template["fix_type"] == "dependency_update"
    
    def test_get_template_not_found(self):
        template = self.engine.get_template_by_id("nonexistent")
        assert template is None
    
    def test_find_matching_template_requirements(self):
        vuln = {
            "file_path": "requirements.txt",
            "package_name": "requests",
            "source": "dependency-scanner",
        }
        
        template = self.engine.find_matching_template(vuln)
        assert template is not None
    
    def test_find_matching_template_dockerfile(self):
        vuln = {
            "file_path": "Dockerfile",
            "title": "Using latest tag",
            "source": "container-scanner",
        }
        
        template = self.engine.find_matching_template(vuln)
        assert template is not None
    
    def test_generate_dependency_fix(self):
        fix = self.engine.generate_dependency_fix(
            package_name="requests",
            old_version="2.28.0",
            new_version="2.31.0",
            file_type="requirements.txt",
        )
        
        assert fix["template_id"] == "python_requirements_update"
        assert fix["variables"]["package_name"] == "requests"
        assert fix["replacement"] == "requests==2.31.0"
    
    def test_apply_template_replacement(self):
        template = {
            "patterns": [
                ("DEBUG = True", "DEBUG = False"),
            ],
        }
        
        content = "DEBUG = True\nOTHER = True"
        fixed, changes = self.engine.apply_template(template, content, {})
        
        assert "DEBUG = False" in fixed
        assert "OTHER = True" in fixed
        assert len(changes) > 0


class TestFixGenerator:
    """Tests for fix generator."""
    
    def setup_method(self):
        self.generator = FixGenerator()
    
    def test_generate_dependency_fix(self):
        vuln = {
            "id": "CVE-2024-1234",
            "cve_id": "CVE-2024-1234",
            "title": "Vulnerability in requests",
            "severity": "high",
            "package_name": "requests",
            "package_version": "2.28.0",
            "fixed_version": "2.31.0",
            "file_path": "requirements.txt",
        }
        
        fix = self.generator.generate_fix(vuln, use_ai=False)
        
        assert fix is not None
        assert fix.fix_type == FixType.DEPENDENCY_UPDATE
        assert fix.confidence == FixConfidence.HIGH
        assert fix.status == FixStatus.READY
        assert "2.31.0" in fix.title
    
    def test_generate_fix_no_fixed_version(self):
        vuln = {
            "id": "TEST-001",
            "title": "Some vulnerability",
            "severity": "medium",
            "file_path": "config.py",
        }
        
        fix = self.generator.generate_fix(vuln, use_ai=False)
        
        assert fix is not None
        # Without fixed_version and no matching template, should be manual
        assert fix.fix_type in [FixType.MANUAL_REQUIRED, FixType.CONFIG_CHANGE]
    
    def test_get_fix_stats(self):
        stats = self.generator.get_fix_stats()
        
        assert "total_templates" in stats
        assert stats["total_templates"] > 0
        assert "by_type" in stats
        assert "ai_enabled" in stats


class TestAPIEndpoints:
    """Tests for API endpoints."""
    
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)
    
    def test_health_check(self, client):
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["agent"] == "auto-remediation"
        assert "templates_count" in data
        assert data["templates_count"] > 0
    
    def test_list_templates(self, client):
        response = client.get("/templates")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        assert len(data["templates"]) > 0
    
    def test_get_template(self, client):
        response = client.get("/templates/python_requirements_update")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "python_requirements_update"
    
    def test_get_template_not_found(self, client):
        response = client.get("/templates/nonexistent")
        
        assert response.status_code == 404
    
    def test_preview_fix(self, client):
        response = client.post("/preview", json={
            "vulnerability": {
                "id": "CVE-2024-1234",
                "title": "Test vulnerability",
                "severity": "high",
                "package_name": "requests",
                "package_version": "2.28.0",
                "fixed_version": "2.31.0",
                "file_path": "requirements.txt",
            },
            "repository": "test/repo",
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["preview_only"] is True
        assert data["fix"] is not None
    
    def test_remediate_single(self, client):
        response = client.post("/remediate", json={
            "vulnerability": {
                "id": "CVE-2024-5678",
                "title": "SQL Injection",
                "severity": "critical",
                "package_name": "django",
                "package_version": "3.0.0",
                "fixed_version": "3.2.0",
                "file_path": "requirements.txt",
            },
            "repository": "test/repo",
            "auto_create_pr": False,
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "remediation_id" in data
        assert data["fix"] is not None
    
    def test_remediate_batch(self, client):
        response = client.post("/remediate/batch", json={
            "vulnerabilities": [
                {
                    "id": "V1",
                    "title": "Vuln 1",
                    "severity": "high",
                    "package_name": "pkg1",
                    "package_version": "1.0.0",
                    "fixed_version": "1.1.0",
                    "file_path": "requirements.txt",
                },
                {
                    "id": "V2",
                    "title": "Vuln 2",
                    "severity": "medium",
                    "package_name": "pkg2",
                    "package_version": "2.0.0",
                    "fixed_version": "2.1.0",
                    "file_path": "requirements.txt",
                },
            ],
            "repository": "test/repo",
            "auto_create_pr": False,
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_vulnerabilities"] == 2
        assert data["fixes_generated"] == 2
    
    def test_get_stats(self, client):
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "fix_generator" in data
        assert "remediations" in data
        assert "github" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
