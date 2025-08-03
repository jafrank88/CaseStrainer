#!/usr/bin/env python3
"""
Test Environment Safeguard Module
Prevents test code from running in production environment
"""

import os
import sys
import logging
from typing import List, Dict, Any

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
        """Check if we're running in a test environment"""
        # Check environment variables
        env_vars = [
            'TESTING',
            'PYTEST_CURRENT_TEST',
            'UNITTEST_RUNNING',
            'CI',
            'TRAVIS',
            'GITHUB_ACTIONS'
        ]
        
        for var in env_vars:
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
    
    def is_test_request(self, request_data: Dict[str, Any], headers: Dict[str, str] = None) -> bool:
        """Check if a request contains test data"""
        
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
        
        # Check for exact test strings
        test_strings = [
            'smith v. jones',
            '123 f.3d 456',
            '999 u.s. 999',
            'test citation',
            'sample citation',
            'fake citation'
        ]
        
        for test_string in test_strings:
            if test_string in text_lower:
                return True
        
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

def validate_request(request_data: Dict[str, Any], headers: Dict[str, str] = None) -> bool:
    """Validate that a request doesn't contain test data"""
    if test_safeguard.is_test_request(request_data, headers):
        test_safeguard.block_test_execution("Test data detected in request")
    return True 