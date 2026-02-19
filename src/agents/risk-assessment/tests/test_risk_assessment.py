"""Unit tests for Risk Assessment Agent."""

import pytest
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    BusinessContext,
    Priority,
    ServiceType,
    DataSensitivity,
    ExploitMaturity,
)
from cvss_interpreter import CVSSInterpreter
from business_analyzer import BusinessContextAnalyzer
from priority_calculator import PriorityCalculator


class TestCVSSInterpreter:
    """Tests for CVSS interpretation."""
    
    def setup_method(self):
        self.interpreter = CVSSInterpreter()
    
    def test_get_severity_critical(self):
        assert self.interpreter.get_severity(9.5) == "critical"
        assert self.interpreter.get_severity(10.0) == "critical"
    
    def test_get_severity_high(self):
        assert self.interpreter.get_severity(7.0) == "high"
        assert self.interpreter.get_severity(8.9) == "high"
    
    def test_get_severity_medium(self):
        assert self.interpreter.get_severity(4.0) == "medium"
        assert self.interpreter.get_severity(6.9) == "medium"
    
    def test_get_severity_low(self):
        assert self.interpreter.get_severity(0.1) == "low"
        assert self.interpreter.get_severity(3.9) == "low"
    
    def test_get_severity_unknown(self):
        assert self.interpreter.get_severity(None) == "unknown"
    
    def test_parse_vector_basic(self):
        vector = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
        result = self.interpreter.parse_vector(vector)
        
        assert "attack_vector" in result
        assert result["attack_vector"]["value"] == "N"
        assert result["attack_vector"]["name"] == "Network"
        
        assert "attack_complexity" in result
        assert result["attack_complexity"]["value"] == "L"
        
        assert "privileges_required" in result
        assert result["privileges_required"]["value"] == "N"
    
    def test_parse_vector_empty(self):
        result = self.interpreter.parse_vector("")
        assert result == {}
    
    def test_exploitability_score_critical(self):
        score, factors = self.interpreter.calculate_exploitability_score(
            cvss_score=9.8,
            vector_string="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        )
        
        assert score >= 8.0
        assert len(factors) > 0
    
    def test_exploitability_score_actively_exploited(self):
        score, factors = self.interpreter.calculate_exploitability_score(
            cvss_score=7.0,
            is_actively_exploited=True,
        )
        
        # Actively exploited should boost score significantly
        assert score >= 8.0
        assert "ACTIVELY EXPLOITED" in " ".join(factors)


class TestBusinessContextAnalyzer:
    """Tests for business context analysis."""
    
    def setup_method(self):
        self.analyzer = BusinessContextAnalyzer()
    
    def test_analyze_public_pii_service(self):
        context = BusinessContext(
            repository="user-api",
            service_type=ServiceType.PUBLIC_API,
            is_public_facing=True,
            data_sensitivity=DataSensitivity.PII,
            handles_pii=True,
            business_criticality=8,
        )
        
        score, factors = self.analyzer.analyze(context)
        
        assert score >= 7.0
        assert any("PII" in f for f in factors)
    
    def test_analyze_internal_low_risk_service(self):
        context = BusinessContext(
            repository="internal-tool",
            service_type=ServiceType.INTERNAL_API,
            is_public_facing=False,
            data_sensitivity=DataSensitivity.INTERNAL,
            business_criticality=3,
        )
        
        score, factors = self.analyzer.analyze(context)
        
        assert score < 6.0
    
    def test_infer_context_payment_service(self):
        context = self.analyzer.infer_context_from_repository("payment-gateway-api")
        
        assert context.handles_financial_data is True
        assert context.data_sensitivity == DataSensitivity.PCI
    
    def test_infer_context_health_service(self):
        context = self.analyzer.infer_context_from_repository("patient-records-service")
        
        assert context.handles_health_data is True
        assert context.data_sensitivity == DataSensitivity.PHI
    
    def test_infer_context_user_service(self):
        context = self.analyzer.infer_context_from_repository("user-profile-service")
        
        assert context.handles_pii is True


class TestPriorityCalculator:
    """Tests for priority calculation."""
    
    def setup_method(self):
        self.calculator = PriorityCalculator()
    
    def test_calculate_critical_vulnerability(self):
        vuln = {
            "id": "test-1",
            "title": "Critical RCE",
            "severity": "critical",
            "cvss_score": 9.8,
            "repository": "public-api",
        }
        
        context = BusinessContext(
            repository="public-api",
            service_type=ServiceType.PUBLIC_API,
            is_public_facing=True,
            data_sensitivity=DataSensitivity.PII,
            handles_pii=True,
            business_criticality=9,
        )
        
        assessment = self.calculator.calculate(vuln, context)
        
        assert assessment.risk_score.priority == Priority.P0
        assert assessment.risk_score.total_score >= 9.0
    
    def test_calculate_low_vulnerability(self):
        vuln = {
            "id": "test-2",
            "title": "Minor info disclosure",
            "severity": "low",
            "cvss_score": 2.5,
            "repository": "internal-tool",
        }
        
        context = BusinessContext(
            repository="internal-tool",
            service_type=ServiceType.INTERNAL_API,
            is_public_facing=False,
            data_sensitivity=DataSensitivity.INTERNAL,
            business_criticality=3,
        )
        
        assessment = self.calculator.calculate(vuln, context)
        
        assert assessment.risk_score.priority in [Priority.P3, Priority.P4]
        assert assessment.risk_score.total_score < 5.0
    
    def test_calculate_medium_vulnerability(self):
        vuln = {
            "id": "test-3",
            "title": "XSS vulnerability",
            "severity": "medium",
            "cvss_score": 5.5,
            "repository": "web-app",
        }
        
        assessment = self.calculator.calculate(vuln)
        
        assert assessment.risk_score.priority == Priority.P2
    
    def test_calculate_batch(self):
        vulns = [
            {"id": "v1", "severity": "critical", "cvss_score": 9.5, "repository": "api"},
            {"id": "v2", "severity": "high", "cvss_score": 7.5, "repository": "api"},
            {"id": "v3", "severity": "low", "cvss_score": 2.0, "repository": "api"},
        ]
        
        assessments = self.calculator.calculate_batch(vulns)
        
        assert len(assessments) == 3
        # Should be sorted by priority (highest priority first)
        assert assessments[0].vulnerability_id == "v1"
        # Without high-risk business context, critical CVSS gets P1 (correct behavior)
        assert assessments[0].risk_score.priority in [Priority.P0, Priority.P1]
    
    def test_summary_generation(self):
        vulns = [
            {"id": "v1", "severity": "critical", "cvss_score": 9.5, "repository": "api"},
            {"id": "v2", "severity": "high", "cvss_score": 7.5, "repository": "api"},
            {"id": "v3", "severity": "medium", "cvss_score": 5.0, "repository": "api"},
        ]
        
        assessments = self.calculator.calculate_batch(vulns)
        summary = self.calculator.get_summary(assessments)
        
        assert summary["total"] == 3
        # At least one high priority (P0 or P1)
        assert summary["by_priority"]["P0"] + summary["by_priority"]["P1"] >= 1
        assert "average_score" in summary
    
    def test_actively_exploited_forces_p0(self):
        vuln = {
            "id": "test-4",
            "title": "Exploited vulnerability",
            "severity": "medium",
            "cvss_score": 5.0,
            "repository": "internal-tool",
        }
        
        assessment = self.calculator.calculate(
            vuln,
            is_actively_exploited=True,
        )
        
        assert assessment.risk_score.priority == Priority.P0


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
        assert data["agent"] == "risk-assessment"
        assert "ai_enabled" in data
    
    def test_get_priorities(self, client):
        response = client.get("/priorities")
        
        assert response.status_code == 200
        data = response.json()
        assert "priorities" in data
        assert len(data["priorities"]) == 5
    
    def test_assess_single_vulnerability(self, client):
        response = client.post("/assess/single", json={
            "vulnerability": {
                "id": "test-vuln-1",
                "title": "Test vulnerability",
                "severity": "high",
                "cvss_score": 7.5,
            },
            "repository": "test-repo",
            "use_ai_analysis": False,
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["vulnerability_id"] == "test-vuln-1"
        assert "risk_score" in data
        assert "priority" in data["risk_score"]
    
    def test_assess_batch(self, client):
        response = client.post("/assess", json={
            "vulnerabilities": [
                {"id": "v1", "title": "Vuln 1", "severity": "critical", "cvss_score": 9.5},
                {"id": "v2", "title": "Vuln 2", "severity": "medium", "cvss_score": 5.0},
            ],
            "repository": "test-repo",
            "use_ai_analysis": False,
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_assessed"] == 2
        assert len(data["assessments"]) == 2
        assert "summary" in data
    
    def test_register_context(self, client):
        response = client.post("/context", json={
            "repository": "my-api",
            "service_name": "My API Service",
            "service_type": "public_api",
            "is_public_facing": True,
            "data_sensitivity": "pii",
            "handles_pii": True,
            "business_criticality": 8,
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["repository"] == "my-api"
        assert data["is_public_facing"] is True
    
    def test_get_context(self, client):
        # First register
        client.post("/context", json={
            "repository": "context-test-repo",
            "service_type": "internal_api",
            "business_criticality": 5,
        })
        
        # Then get
        response = client.get("/context/context-test-repo")
        
        assert response.status_code == 200
        data = response.json()
        assert data["repository"] == "context-test-repo"


# Run tests with: pytest tests/test_risk_assessment.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
