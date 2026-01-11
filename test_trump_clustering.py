#!/usr/bin/env python3
"""
Test script to process Trump v. Barbara PDF and check clustering behavior.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import extract_and_verify_citations_unified

def test_trump_pdf():
    """Process the Trump PDF and analyze clustering."""
    pdf_path = "D:/dev/casestrainer/trumpvbarbaracertpet.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found at {pdf_path}")
        return
    
    print("=" * 80)
    print("PROCESSING TRUMP V. BARBARA PDF")
    print("=" * 80)
    
    # Read PDF
    import PyPDF2
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    
    print(f"\nExtracted {len(text)} characters from PDF")
    
    # Process citations
    print("\nProcessing citations...")
    result = extract_and_verify_citations_unified(
        text=text,
        enable_verification=False,  # Skip verification to focus on clustering
        request_id="test_trump_clustering"
    )
    
    print(f"\nFound {len(result.get('citations', []))} citations")
    print(f"Found {len(result.get('clusters', []))} clusters")
    
    # Find Trump v. CASA cluster
    print("\n" + "=" * 80)
    print("LOOKING FOR TRUMP V. CASA CLUSTER")
    print("=" * 80)
    
    for cluster in result.get('clusters', []):
        case_name = cluster.get('case_name', '')
        if 'Trump v. CASA' in case_name or 'CASA' in case_name:
            citations = cluster.get('citations', [])
            print(f"\nFound cluster: {case_name}")
            print(f"Number of citations: {len(citations)}")
            print("\nCitations in cluster:")
            for i, cit in enumerate(citations, 1):
                if isinstance(cit, dict):
                    cit_text = cit.get('citation', 'N/A')
                else:
                    cit_text = getattr(cit, 'citation', 'N/A')
                print(f"  {i}. {cit_text}")
    
    # Also check for individual citations
    print("\n" + "=" * 80)
    print("ALL CITATIONS CONTAINING 'U.S. 831' OR 'F. Supp. 3d 1142' OR 'F. Supp. 3d 1050'")
    print("=" * 80)
    
    for cit in result.get('citations', []):
        if isinstance(cit, dict):
            cit_text = cit.get('citation', '')
            cluster_id = cit.get('cluster_id', 'N/A')
        else:
            cit_text = getattr(cit, 'citation', '')
            cluster_id = getattr(cit, 'cluster_id', 'N/A')
        
        if '606 U.S. 831' in cit_text or '765 F. Supp. 3d 1142' in cit_text or '764 F. Supp. 3d 1050' in cit_text:
            print(f"\nCitation: {cit_text}")
            print(f"  Cluster ID: {cluster_id}")

if __name__ == '__main__':
    test_trump_pdf()
