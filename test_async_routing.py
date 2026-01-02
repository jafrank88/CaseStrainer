#!/usr/bin/env python3
"""
Test the should_process_immediately logic
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.api.services.citation_service import CitationService

def test_processing_mode():
    """Test what processing mode is chosen for different text sizes"""
    
    service = CitationService()
    
    # Test small text (should be sync)
    small_text = "Small text with 57 P.3d 273 citation."
    small_input = {'type': 'text', 'text': small_text}
    
    print("🔍 Testing small text (should be SYNC):")
    print(f"Text length: {len(small_text)} characters")
    print(f"should_process_immediately: {service.should_process_immediately(small_input)}")
    print(f"determine_processing_mode: {service.determine_processing_mode(small_text)}")
    print()
    
    # Test large text (should be async)
    large_text = "Large text " * 1000 + " with 57 P.3d 273 citation at the end."
    large_input = {'type': 'text', 'text': large_text}
    
    print("🔍 Testing large text (should be ASYNC):")
    print(f"Text length: {len(large_text)} characters")
    print(f"SYNC_THRESHOLD: {service.SYNC_THRESHOLD} characters")
    print(f"should_process_immediately: {service.should_process_immediately(large_input)}")
    print(f"determine_processing_mode: {service.determine_processing_mode(large_text)}")
    print()
    
    # Test very large text (like user's document)
    very_large_text = "Very large text " * 3000 + " with 57 P.3d 273 citation at the end."
    very_large_input = {'type': 'text', 'text': very_large_text}
    
    print("🔍 Testing very large text (like user's 45KB document - should be ASYNC):")
    print(f"Text length: {len(very_large_text)} characters")
    print(f"should_process_immediately: {service.should_process_immediately(very_large_input)}")
    print(f"determine_processing_mode: {service.determine_processing_mode(very_large_text)}")

if __name__ == "__main__":
    test_processing_mode()
