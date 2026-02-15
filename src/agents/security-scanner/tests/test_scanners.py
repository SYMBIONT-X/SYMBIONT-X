"""Unit tests for security scanners."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models import ScanResult, ScanType, Severity


class TestDependencyScanner:
    """Tests for DependencyScanner."""
    
    def test_is_available(self):
        """Test scanner availability check."""
        from scanners import DependencyScanner
        scanner = DependencyScanner()
        # Should return True if pip-audit is installed
        result = scanner.is_available()
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_scan_no_requirements(self):
        """Test scanning directory with no requirements files."""
        from scanners import DependencyScanner
        scanner = DependencyScanner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await scanner.scan(
                target_path=Path(tmpdir),
                repository="test/repo",
                branch="main",
            )
            
            assert isinstance(result, ScanResult)
            assert result.scan_type == ScanType.DEPENDENCY
            assert result.total_count == 0
            assert result.success is True
    
    @pytest.mark.asyncio
    async def test_scan_with_requirements(self):
        """Test scanning directory with requirements.txt."""
        from scanners import DependencyScanner
        scanner = DependencyScanner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple requirements.txt
            req_file = Path(tmpdir) / "requirements.txt"
            req_file.write_text("requests==2.28.0\n")
            
            result = await scanner.scan(
                target_path=Path(tmpdir),
                repository="test/repo",
                branch="main",
            )
            
            assert isinstance(result, ScanResult)
            assert result.scan_type == ScanType.DEPENDENCY
            assert result.success is True


class TestCodeScanner:
    """Tests for CodeScanner."""
    
    def test_is_available(self):
        """Test scanner availability check."""
        from scanners import CodeScanner
        scanner = CodeScanner()
        result = scanner.is_available()
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_scan_no_python_files(self):
        """Test scanning directory with no Python files."""
        from scanners import CodeScanner
        scanner = CodeScanner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await scanner.scan(
                target_path=Path(tmpdir),
                repository="test/repo",
                branch="main",
            )
            
            assert isinstance(result, ScanResult)
            assert result.scan_type == ScanType.CODE
            assert result.total_count == 0
    
    @pytest.mark.asyncio
    async def test_scan_with_vulnerable_code(self):
        """Test scanning Python file with security issues."""
        from scanners import CodeScanner
        scanner = CodeScanner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a Python file with a known security issue
            py_file = Path(tmpdir) / "vulnerable.py"
            py_file.write_text('''
import subprocess
user_input = input("Enter command: ")
subprocess.call(user_input, shell=True)  # B602: shell=True is dangerous
''')
            
            result = await scanner.scan(
                target_path=Path(tmpdir),
                repository="test/repo",
                branch="main",
            )
            
            assert isinstance(result, ScanResult)
            assert result.scan_type == ScanType.CODE
            # Should find at least one vulnerability
            if scanner.is_available():
                assert result.total_count >= 1


class TestSecretScanner:
    """Tests for SecretScanner."""
    
    def test_is_available(self):
        """Test scanner availability check."""
        from scanners import SecretScanner
        scanner = SecretScanner()
        result = scanner.is_available()
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_scan_no_secrets(self):
        """Test scanning directory with no secrets."""
        from scanners import SecretScanner
        scanner = SecretScanner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a clean file
            clean_file = Path(tmpdir) / "clean.py"
            clean_file.write_text('print("Hello, World!")\n')
            
            result = await scanner.scan(
                target_path=Path(tmpdir),
                repository="test/repo",
                branch="main",
            )
            
            assert isinstance(result, ScanResult)
            assert result.scan_type == ScanType.SECRET
            assert result.success is True


class TestContainerScanner:
    """Tests for ContainerScanner."""
    
    def test_is_available(self):
        """Test scanner availability check."""
        from scanners import ContainerScanner
        scanner = ContainerScanner()
        result = scanner.is_available()
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_scan_no_dockerfiles(self):
        """Test scanning directory with no Dockerfiles."""
        from scanners import ContainerScanner
        scanner = ContainerScanner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await scanner.scan(
                target_path=Path(tmpdir),
                repository="test/repo",
                branch="main",
            )
            
            assert isinstance(result, ScanResult)
            assert result.scan_type == ScanType.CONTAINER
            assert result.total_count == 0


class TestIaCScanner:
    """Tests for IaCScanner."""
    
    def test_is_available(self):
        """Test scanner availability check."""
        from scanners import IaCScanner
        scanner = IaCScanner()
        result = scanner.is_available()
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_scan_no_iac_files(self):
        """Test scanning directory with no IaC files."""
        from scanners import IaCScanner
        scanner = IaCScanner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await scanner.scan(
                target_path=Path(tmpdir),
                repository="test/repo",
                branch="main",
            )
            
            assert isinstance(result, ScanResult)
            assert result.scan_type == ScanType.IAC
            assert result.total_count == 0
    
    def test_detect_frameworks_terraform(self):
        """Test Terraform framework detection."""
        from scanners import IaCScanner
        scanner = IaCScanner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a Terraform file
            tf_file = Path(tmpdir) / "main.tf"
            tf_file.write_text('resource "aws_instance" "example" {}\n')
            
            frameworks = scanner._detect_frameworks(Path(tmpdir))
            assert "terraform" in frameworks
    
    def test_detect_frameworks_bicep(self):
        """Test Bicep framework detection."""
        from scanners import IaCScanner
        scanner = IaCScanner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a Bicep file
            bicep_file = Path(tmpdir) / "main.bicep"
            bicep_file.write_text('param location string = resourceGroup().location\n')
            
            frameworks = scanner._detect_frameworks(Path(tmpdir))
            assert "bicep" in frameworks


class TestCVELookup:
    """Tests for CVE lookup integration."""
    
    @pytest.mark.asyncio
    async def test_lookup_invalid_cve(self):
        """Test looking up an invalid CVE ID."""
        from integrations import CVELookup
        lookup = CVELookup()
        
        result = await lookup.lookup("not-a-cve")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_lookup_empty_cve(self):
        """Test looking up empty CVE ID."""
        from integrations import CVELookup
        lookup = CVELookup()
        
        result = await lookup.lookup("")
        assert result is None
    
    def test_cvss_to_severity(self):
        """Test CVSS score to severity conversion."""
        from integrations import CVELookup
        lookup = CVELookup()
        
        assert lookup._cvss_to_severity(9.5) == "critical"
        assert lookup._cvss_to_severity(7.5) == "high"
        assert lookup._cvss_to_severity(5.0) == "medium"
        assert lookup._cvss_to_severity(2.0) == "low"
        assert lookup._cvss_to_severity(None) == "unknown"


# Run tests with: pytest tests/test_scanners.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
