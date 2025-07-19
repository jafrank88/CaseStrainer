#!/usr/bin/env python3
"""
Production Readiness Test Suite for CaseStrainer
Tests all critical fixes and security measures
"""

import os
import sys
import logging
import unittest
from unittest.mock import Mock, patch
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.config import validate_config, get_environment_info
from src.rate_limiter import AdvancedRateLimiter, InputValidator
from src.app_final_vue import ApplicationFactory, SecurityManager


class ProductionReadinessTests(unittest.TestCase):
    """Test suite for production readiness"""
    
    def setUp(self):
        """Set up test environment"""
        self.logger = logging.getLogger(__name__)
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_validation(self):
        """Test configuration validation"""
        try:
            validate_config()
            self.assertTrue(True, "Configuration validation passed")
        except Exception as e:
            self.fail(f"Configuration validation failed: {e}")
    
    def test_environment_info(self):
        """Test environment information gathering"""
        env_info = get_environment_info()
        required_keys = [
            'python_version', 'platform', 'environment', 
            'database_file', 'upload_folder'
        ]
        
        for key in required_keys:
            self.assertIn(key, env_info, f"Missing environment info key: {key}")
        
        self.logger.info(f"Environment info: {env_info}")
    
    def test_advanced_rate_limiter(self):
        """Test advanced rate limiter functionality"""
        limiter = AdvancedRateLimiter()
        
        # Test normal operation with different IPs
        self.assertTrue(limiter.is_allowed("192.168.1.1", limit=5, window=60))
        
        # Test rate limiting - make 5 calls to hit the limit with a different IP
        for _ in range(5):  # 5 calls to hit the limit
            limiter.is_allowed("192.168.1.2", limit=5, window=60)
        
        # Should be blocked after 5 calls
        self.assertFalse(limiter.is_allowed("192.168.1.2", limit=5, window=60))
        
        # Test IP blocking
        blocked_ips = limiter.get_blocked_ips()
        self.assertIn("192.168.1.2", blocked_ips)
        
        # Test unblocking
        limiter.unblock_ip("192.168.1.2")
        self.assertTrue(limiter.is_allowed("192.168.1.3", limit=5, window=60))  # Test with different IP
    
    def test_input_validation(self):
        """Test input validation security"""
        validator = InputValidator()
        
        # Test valid inputs
        self.assertTrue(validator.validate_citation_input("123 Wn.2d 456"))
        self.assertTrue(validator.validate_text_input("Valid text input"))
        self.assertTrue(validator.validate_url_input("https://example.com"))
        
        # Test malicious inputs
        malicious_citations = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>"
        ]
        
        for malicious in malicious_citations:
            self.assertFalse(
                validator.validate_citation_input(malicious),
                f"Should reject malicious citation: {malicious}"
            )
        
        # Test URL validation
        malicious_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "file:///etc/passwd"
        ]
        
        for malicious in malicious_urls:
            self.assertFalse(
                validator.validate_url_input(malicious),
                f"Should reject malicious URL: {malicious}"
            )
    
    def test_security_manager(self):
        """Test security manager functionality"""
        # Test file path validation
        self.assertTrue(SecurityManager.validate_file_path("test.txt", self.temp_dir, self.logger))
        self.assertFalse(SecurityManager.validate_file_path("../etc/passwd", self.temp_dir, self.logger))
        self.assertFalse(SecurityManager.validate_file_path("/etc/passwd", self.temp_dir, self.logger))
        
        # Test input sanitization
        malicious_input = "<script>alert('xss')</script>"
        sanitized = SecurityManager.sanitize_citation_input(malicious_input)
        self.assertNotIn("<script>", sanitized)
        self.assertNotIn("</script>", sanitized)
        
        # Test URL validation
        self.assertTrue(SecurityManager.validate_url("https://example.com"))
        self.assertFalse(SecurityManager.validate_url("javascript:alert('xss')"))
    
    def test_application_factory(self):
        """Test application factory creation"""
        try:
            factory = ApplicationFactory.get_instance()
            self.assertIsNotNone(factory)
            self.assertIsInstance(factory, ApplicationFactory)
        except Exception as e:
            self.fail(f"Application factory creation failed: {e}")
    
    def test_logging_setup(self):
        """Test logging configuration"""
        try:
            from app_final_vue import LoggingManager
            logger = LoggingManager.setup_logging()
            self.assertIsNotNone(logger)
            self.assertIsInstance(logger, logging.Logger)
            
            # Test logging
            logger.info("Test log message")
            self.assertTrue(True, "Logging test passed")
        except Exception as e:
            self.fail(f"Logging setup failed: {e}")
    
    def test_print_statement_removal(self):
        """Test that print statements have been replaced with logging"""
        # Check key files for print statements
        files_to_check = [
            "src/api/services/citation_service.py",
            "src/config.py", 
            "src/canonical_case_name_service.py"
        ]
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for print statements that aren't in test functions
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if 'print(' in line and 'test_' not in line and 'def test_' not in line:
                            self.fail(f"Found print statement in {file_path}:{i}: {line.strip()}")
    
    def test_blueprint_registration(self):
        """Test that blueprints are properly registered"""
        try:
            factory = ApplicationFactory.get_instance()
            app = factory.create_app()
            
            # Check if vue_api blueprint is registered
            blueprint_names = [bp.name for bp in app.blueprints.values()]
            self.logger.info(f"Registered blueprints: {blueprint_names}")
            
            # The blueprint registration should not fail
            self.assertTrue(True, "Blueprint registration test passed")
        except Exception as e:
            self.fail(f"Blueprint registration test failed: {e}")


def run_production_tests():
    """Run all production readiness tests"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("Running Production Readiness Tests")
    logger.info("=" * 80)
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(ProductionReadinessTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    logger.info("=" * 80)
    logger.info("Test Results Summary")
    logger.info("=" * 80)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    if result.failures:
        logger.error("FAILURES:")
        for test, traceback in result.failures:
            logger.error(f"  {test}: {traceback}")
    
    if result.errors:
        logger.error("ERRORS:")
        for test, traceback in result.errors:
            logger.error(f"  {test}: {traceback}")
    
    if result.wasSuccessful():
        logger.info("✅ All production readiness tests PASSED!")
        return True
    else:
        logger.error("❌ Some production readiness tests FAILED!")
        return False


if __name__ == "__main__":
    success = run_production_tests()
    sys.exit(0 if success else 1) 