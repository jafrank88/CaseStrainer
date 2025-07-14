#!/usr/bin/env python3
"""
Test script for case.law URL citation extraction
================================================

This script tests the specific case.law URL to diagnose why citations aren't being found.
"""

import os
import sys
import requests
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from enhanced_extraction_improvements import EnhancedExtractionProcessor
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2


def test_case_law_url(url: str = "https://case.law/caselaw/?reporter=cal-4th&volume=11&case=0001-01"):
    """Test citation extraction from the specific case.law URL."""
    
    print(f"🔍 TESTING CASE.LAW URL: {url}")
    print("=" * 60)
    
    # Step 1: Test URL accessibility
    print("📡 Step 1: Testing URL accessibility...")
    try:
        response = requests.get(url, timeout=30)
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Type: {response.headers.get('content-type', 'unknown')}")
        print(f"   Content Length: {len(response.text)} characters")
        
        if response.status_code != 200:
            print(f"   ❌ URL not accessible: {response.status_code}")
            return
        
        print("   ✅ URL accessible")
        
    except Exception as e:
        print(f"   ❌ Error accessing URL: {e}")
        return
    
    # Step 2: Extract text content
    print("\n📄 Step 2: Extracting text content...")
    try:
        from src.document_processing import extract_text_from_url
        text_content = extract_text_from_url(url)
        
        if not text_content:
            print("   ❌ No text content extracted")
            return
        
        print(f"   ✅ Text extracted: {len(text_content)} characters")
        print(f"   📝 First 200 characters: {text_content[:200]}...")
        
    except Exception as e:
        print(f"   ❌ Error extracting text: {e}")
        return
    
    # Step 3: Test with base processor
    print("\n🔧 Step 3: Testing with base processor...")
    try:
        base_processor = UnifiedCitationProcessorV2()
        base_results = base_processor.process_text(text_content)
        
        print(f"   📊 Base processor found: {len(base_results)} citations")
        
        if base_results:
            print("   📋 Sample citations:")
            for i, citation in enumerate(base_results[:5], 1):
                print(f"      {i}. {citation.citation} (confidence: {citation.confidence:.2f})")
        
    except Exception as e:
        print(f"   ❌ Error with base processor: {e}")
    
    # Step 4: Test with enhanced processor
    print("\n🚀 Step 4: Testing with enhanced processor...")
    try:
        enhanced_processor = EnhancedExtractionProcessor()
        enhanced_results = enhanced_processor.process_text_enhanced(text_content)
        
        citations = enhanced_results.get('citations', [])
        case_names = enhanced_results.get('case_names', [])
        dates = enhanced_results.get('dates', [])
        clusters = enhanced_results.get('clusters', [])
        
        print(f"   📊 Enhanced processor found:")
        print(f"      - Citations: {len(citations)}")
        print(f"      - Case names: {len(case_names)}")
        print(f"      - Dates: {len(dates)}")
        print(f"      - Clusters: {len(clusters)}")
        
        if citations:
            print("   📋 Sample citations:")
            for i, citation in enumerate(citations[:5], 1):
                print(f"      {i}. {citation.get('citation', 'N/A')} (confidence: {citation.get('confidence', 0):.2f})")
        
        if clusters:
            print("   📋 Sample clusters:")
            for i, cluster in enumerate(clusters[:3], 1):
                cluster_citations = cluster.get('citations', [])
                print(f"      {i}. Cluster with {len(cluster_citations)} citations: {cluster_citations[:3]}")
        
    except Exception as e:
        print(f"   ❌ Error with enhanced processor: {e}")
    
    # Step 5: Analyze text for citation patterns
    print("\n🔍 Step 5: Analyzing text for citation patterns...")
    try:
        # Look for common citation patterns in the text
        import re
        
        citation_patterns = [
            r'\b\d+\s+Cal\.\s*4th\s+\d+\b',  # California 4th
            r'\b\d+\s+Cal\.\s*App\.\s+\d+\b',  # California App
            r'\b\d+\s+Cal\.\s*3d\s+\d+\b',  # California 3d
            r'\b\d+\s+Cal\.\s*2d\s+\d+\b',  # California 2d
            r'\b\d+\s+Cal\.\s*\d+\b',  # California general
            r'\b\d+\s+P\.\s*3d\s+\d+\b',  # Pacific 3d
            r'\b\d+\s+P\.\s*2d\s+\d+\b',  # Pacific 2d
            r'\b\d+\s+U\.S\.\s+\d+\b',  # US Supreme Court
            r'\b\d+\s+F\.\s*3d\s+\d+\b',  # Federal 3d
            r'\b\d+\s+F\.\s*2d\s+\d+\b',  # Federal 2d
        ]
        
        found_patterns = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                found_patterns.append((pattern, len(matches), matches[:3]))
        
        if found_patterns:
            print("   📋 Found citation patterns:")
            for pattern, count, examples in found_patterns:
                print(f"      - {pattern}: {count} matches (examples: {examples})")
        else:
            print("   ❌ No citation patterns found in text")
            
            # Show some sample text to help debug
            print("   📝 Sample text sections:")
            lines = text_content.split('\n')
            for i, line in enumerate(lines[:10]):
                if line.strip():
                    print(f"      Line {i+1}: {line.strip()[:100]}...")
        
    except Exception as e:
        print(f"   ❌ Error analyzing patterns: {e}")
    
    # Step 6: Test with different text extraction methods
    print("\n🔄 Step 6: Testing alternative text extraction...")
    try:
        # Try different text extraction approaches
        from bs4 import BeautifulSoup
        
        # Method 1: BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        soup_text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in soup_text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        soup_text = ' '.join(chunk for chunk in chunks if chunk)
        
        print(f"   📄 BeautifulSoup extracted: {len(soup_text)} characters")
        
        # Test with enhanced processor on BeautifulSoup text
        enhanced_results_bs = enhanced_processor.process_text_enhanced(soup_text)
        citations_bs = enhanced_results_bs.get('citations', [])
        
        print(f"   📊 BeautifulSoup text yielded: {len(citations_bs)} citations")
        
        if citations_bs:
            print("   📋 Sample citations from BeautifulSoup:")
            for i, citation in enumerate(citations_bs[:3], 1):
                print(f"      {i}. {citation.get('citation', 'N/A')}")
        
    except Exception as e:
        print(f"   ❌ Error with alternative extraction: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY:")
    print("   - URL accessible: ✅" if response.status_code == 200 else "   - URL accessible: ❌")
    print(f"   - Text extracted: ✅ ({len(text_content)} chars)" if text_content else "   - Text extracted: ❌")
    print(f"   - Base processor citations: {len(base_results) if 'base_results' in locals() else 'N/A'}")
    print(f"   - Enhanced processor citations: {len(citations) if 'citations' in locals() else 'N/A'}")
    
    if 'citations' in locals() and citations:
        print("   🎉 Citations found! The system is working.")
    else:
        print("   ❌ No citations found. Possible issues:")
        print("      - Text extraction not working properly")
        print("      - Citation patterns not matching the content")
        print("      - Content format not expected")
        print("      - Need to adjust extraction patterns")


def main():
    """Main function to run the test."""
    url = "https://case.law/caselaw/?reporter=cal-4th&volume=11&case=0001-01"
    test_case_law_url(url)


if __name__ == '__main__':
    main() 