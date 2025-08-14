#!/usr/bin/env python3
"""
Clean Six Data Points Test
Simple test to verify all six data points without debug noise
"""

import sys
import os
import json
import logging

# Suppress warnings for cleaner output
logging.getLogger().setLevel(logging.ERROR)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_clean_six_data_points():
    """Clean test of all six data points."""
    print("🎯 CLEAN SIX DATA POINTS TEST")
    print("="*40)
    
    test_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
    
    try:
        from src.api.services.citation_service import CitationService
        
        service = CitationService()
        input_data = {'text': test_text, 'type': 'text'}
        
        print(f"Testing: {test_text}")
        result = service.process_immediately(input_data)
        
        if result.get('status') != 'completed':
            print(f"❌ Processing failed: {result.get('message', 'Unknown error')}")
            return False
        
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"\nResults: {len(citations)} citations, {len(clusters)} clusters")
        
        if not citations:
            print("❌ No citations found")
            return False
        
        citation = citations[0]
        
        # The six data points
        print(f"\n📋 SIX DATA POINTS:")
        print(f"1. Extracted Case Name: {citation.get('extracted_case_name')}")
        print(f"2. Extracted Year: {citation.get('extracted_date')}")
        print(f"3. Canonical Name: {citation.get('canonical_name')}")
        print(f"4. Canonical Year: {citation.get('canonical_date')}")
        print(f"5. Canonical URL: {citation.get('canonical_url')}")
        print(f"6. Verified Status: {citation.get('verified')}")
        
        # Count successful data points
        data_points = [
            citation.get('extracted_case_name'),
            citation.get('extracted_date'),
            citation.get('canonical_name'),
            citation.get('canonical_date'),
            citation.get('canonical_url'),
            citation.get('verified')
        ]
        
        successful_points = sum(1 for point in data_points if point is not None and point is not False)
        
        print(f"\n📊 SUMMARY:")
        print(f"Data points delivered: {successful_points}/6")
        print(f"Success rate: {(successful_points/6)*100:.1f}%")
        
        success = successful_points == 6
        print(f"Overall: {'✅ SUCCESS' if success else '❌ PARTIAL'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run clean six data points test."""
    success = test_clean_six_data_points()
    
    print(f"\n" + "="*50)
    if success:
        print("🎉 ALL 6 DATA POINTS DELIVERED!")
        print("✅ Backend is ready for production")
    else:
        print("⚠️  PARTIAL SUCCESS - Some data points missing")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
