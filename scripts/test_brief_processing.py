#!/usr/bin/env python3
"""
Test script to validate citation extraction on a single brief file.
Useful for debugging and testing the extraction pipeline.
"""

import os
import sys
import json
from pathlib import Path
import argparse

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.file_utils import extract_text_from_file

def test_brief_processing(pdf_path: str, output_file: str = None):
    """Test citation extraction on a single brief file."""
    
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return False
    
    print(f"Testing citation extraction on: {pdf_path.name}")
    print("=" * 60)
    
    # Initialize processor
    processor = UnifiedCitationProcessorV2()
    
    # Extract text
    print("1. Extracting text from PDF...")
    try:
        text = extract_text_from_file(str(pdf_path))
        if not text or len(text.strip()) < 100:
            print("Error: Extracted text too short")
            return False
        
        print(f"   Extracted {len(text)} characters")
        print(f"   Text preview: {text[:200]}...")
        
    except Exception as e:
        print(f"Error extracting text: {e}")
        return False
    
    # Extract citations
    print("\n2. Extracting citations...")
    try:
        extraction_result = processor.process_text(text)
        
        if not extraction_result:
            print("   No extraction result returned")
            return False
        
        # process_text returns a list of CitationResult objects
        extracted_citations = [citation.citation_text for citation in extraction_result] if extraction_result else []
        print(f"   Found {len(extracted_citations)} raw citations")
        
        # Show first few citations
        for i, citation in enumerate(extracted_citations[:5]):
            print(f"   Citation {i+1}: {citation}")
        
        if len(extracted_citations) > 5:
            print(f"   ... and {len(extracted_citations) - 5} more")
        
    except Exception as e:
        print(f"Error extracting citations: {e}")
        return False
    
    # Process through clustering
    print("\n3. Processing through clustering...")
    try:
        clusters = processor.group_citations_into_clusters(extraction_result, text)
        print(f"   Created {len(clusters)} clusters")
        
        # Show cluster details
        for i, cluster in enumerate(clusters):
            print(f"\n   Cluster {i+1}:")
            if hasattr(cluster, 'canonical_name'):
                print(f"     Canonical: {cluster.canonical_name}")
            if hasattr(cluster, 'canonical_date'):
                print(f"     Date: {cluster.canonical_date}")
            if hasattr(cluster, 'citations'):
                print(f"     Citations: {len(cluster.citations)}")
                for j, citation in enumerate(cluster.citations[:3]):
                    print(f"       {j+1}. {citation}")
                if len(cluster.citations) > 3:
                    print(f"       ... and {len(cluster.citations) - 3} more")
        
    except Exception as e:
        print(f"Error in clustering: {e}")
        return False
    
    # Save results if output file specified
    if output_file:
        print(f"\n4. Saving results to {output_file}...")
        try:
            result = {
                'filename': pdf_path.name,
                'text_length': len(text),
                'extracted_citations': extracted_citations,
                'clusters': [cluster.to_dict() if hasattr(cluster, 'to_dict') else str(cluster) for cluster in clusters],
                'cluster_count': len(clusters),
                'citation_count': len(extracted_citations)
            }
            
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            print(f"   Results saved successfully")
            
        except Exception as e:
            print(f"Error saving results: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print(f"Summary: {len(extracted_citations)} citations extracted, {len(clusters)} clusters created")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Test citation extraction on a single brief')
    parser.add_argument('pdf_file', help='Path to PDF file to test')
    parser.add_argument('--output', '-o', help='Output JSON file for results')
    
    args = parser.parse_args()
    
    success = test_brief_processing(args.pdf_file, args.output)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 