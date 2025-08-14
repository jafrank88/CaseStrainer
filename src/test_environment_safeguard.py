#!/usr/bin/env python3
"""
Test Environment Safeguard Module
Prevents test code from running in production environment
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TestEnvironmentSafeguard:
    """Safeguard to prevent test code from running in production"""
    
    def __init__(self):
        self.test_patterns = [
            r"smith v\. jones.*123 f\.3d 456",
            r"123 f\.3d 456.*smith v\. jones",
            r"123 f\.\d+d 456",
            r"999 u\.s\. 999",
            r"test citation",
            r"sample citation",
            r"fake citation"
        ]
        
        self.test_user_agents = [
            'casestrainer-production-test',
            'test',
            'pytest',
            'unittest',
            'selenium',
            'cypress',
            'playwright'
        ]
        
        self.test_referers = [
            'localhost',
            '127.0.0.1',
            'test',
            'dev',
            'staging'
        ]
    
    def is_test_environment(self) -> bool:
        """Check if we're running in a test environment
        
        Returns:
            bool: True if running in a test environment, False otherwise
            
        Note:
            In development mode, we're more permissive to allow testing with sample data.
            In production, we're more strict to prevent test data from being processed.
        """
        # Check if we're in development mode
        is_development = os.getenv('FLASK_ENV', '').lower() == 'development' or \
                        os.getenv('FLASK_DEBUG', '').lower() == 'true' or \
                        os.getenv('ENVIRONMENT', '').lower() == 'development'
        
        # In development, be more permissive
        if is_development:
            # Only block if explicitly running tests
            if os.getenv('PYTEST_CURRENT_TEST') or os.getenv('UNITTEST_RUNNING'):
                logger.warning("Test environment detected via test runner")
                return True
            return False
            
        # In production, be more strict
        test_env_vars = [
            'TESTING',
            'PYTEST_CURRENT_TEST',
            'UNITTEST_RUNNING',
            'GITHUB_ACTIONS',
            'CI'
        ]
        
        for var in test_env_vars:
            if os.getenv(var):
                logger.warning(f"Test environment detected via environment variable: {var}")
                return True
        
        # Check if we're running in a test directory
        current_dir = os.getcwd()
        test_indicators = ['test', 'tests', 'pytest', 'unittest']
        for indicator in test_indicators:
            if indicator in current_dir.lower():
                logger.warning(f"Test environment detected via directory: {current_dir}")
                return True
        
        return False
    
    def is_ci_health_check(self, request_data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> bool:
        """Check if this is a legitimate CI health check with real legal content"""
        # Only consider it a CI health check if CI environment variables are present
        if not (os.getenv('CI') or os.getenv('GITHUB_ACTIONS')):
            return False
        
        # Check if the request contains legitimate legal content
        if isinstance(request_data, dict):
            text = request_data.get('text', '')
            if text:
                # Check for legitimate legal cases that are commonly used in health checks
                legitimate_cases = [
                    'roe v. wade',
                    'miranda v. arizona',
                    'brown v. board of education',
                    'marbury v. madison',
                    'gideon v. wainwright'
                ]
                
                text_lower = text.lower()
                for case in legitimate_cases:
                    if case in text_lower:
                        logger.info(f"CI health check detected with legitimate case: {case}")
                        return True
        
        return False
    
    def is_test_request(self, request_data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> bool:
        """Check if a request contains test data
        
        Args:
            request_data: The request data to check
            headers: Optional request headers
            
        Returns:
            bool: True if the request appears to be test data, False otherwise
            
        Note:
            In development mode, we're more permissive to allow testing with sample data.
            In production, we're more strict to prevent test data from being processed.
        """
        # Check if we're in development mode
        is_development = os.getenv('FLASK_ENV', '').lower() == 'development' or \
                        os.getenv('FLASK_DEBUG', '').lower() == 'true' or \
                        os.getenv('ENVIRONMENT', '').lower() == 'development'
                        
        # In development, only block obvious test patterns
        if is_development:
            if not request_data or not isinstance(request_data, dict):
                return False
                
            # Check for test patterns in text input
            if 'text' in request_data and isinstance(request_data['text'], str):
                text = request_data['text'].lower()
                test_phrases = [
                    'test citation',
                    'sample citation',
                    'fake citation',
                    'example citation'
                ]
                
                for phrase in test_phrases:
                    if phrase in text:
                        logger.warning(f"Test data detected in development: {phrase}")
                        return True
            
            return False
        
        # Check for test data in request
        if isinstance(request_data, dict):
            text = request_data.get('text', '')
            if self._contains_test_patterns(text):
                logger.warning(f"Test data detected in request: {text[:100]}...")
                return True
        
        # Check headers for test indicators
        if headers:
            user_agent = headers.get('User-Agent', '').lower()
            referer = headers.get('Referer', '').lower()
            
            for test_ua in self.test_user_agents:
                if test_ua in user_agent:
                    logger.warning(f"Test User-Agent detected: {user_agent}")
                    return True
            
            for test_ref in self.test_referers:
                if test_ref in referer:
                    logger.warning(f"Test Referer detected: {referer}")
                    return True
        
        return False
    
    def _contains_test_patterns(self, text: str) -> bool:
        """Check if text contains test patterns"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Only check for exact test patterns that are clearly test data
        # These are the specific patterns used in our test files
        exact_test_patterns = [
            'smith v. jones, 123 f.3d 456',
            '123 f.3d 456, smith v. jones',
            'smith v. jones 123 f.3d 456',
            '123 f.3d 456 smith v. jones',
            '999 u.s. 999',
            'test citation',
            'sample citation',
            'fake citation'
        ]
        
        # Only flag if the text contains one of these exact patterns
        for pattern in exact_test_patterns:
            if pattern in text_lower:
                return True
        
        # Don't flag real legal documents that happen to contain similar text
        # If the text is longer than 50 characters and contains legal context,
        # it's probably a real document, not test data
        if len(text.strip()) > 50:
            legal_indicators = ['court', 'case', 'legal', 'precedent', 'decision', 'opinion', 'judgment', 'held', 'ruled', 'determined']
            if any(indicator in text_lower for indicator in legal_indicators):
                return False
        
        return False
    
    def block_test_execution(self, reason: str = "Test execution blocked"):
        """Block test execution in production"""
        logger.error(f"Test execution blocked: {reason}")
        raise RuntimeError(f"Test execution not allowed in production: {reason}")

# Global instance
test_safeguard = TestEnvironmentSafeguard()

def check_test_environment():
    """Check if we're in a test environment and block if necessary"""
    if test_safeguard.is_test_environment():
        test_safeguard.block_test_execution("Test environment detected")

def validate_request(request_data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> bool:
    """Validate that a request doesn't contain test data"""
    if test_safeguard.is_test_request(request_data, headers):
        test_safeguard.block_test_execution("Test data detected in request")
    return True 