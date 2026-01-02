#!/usr/bin/env python3
"""
Test the actual PDF content to see why contamination is happening
"""

import sys
import os
import requests
import tempfile
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_pdf_content_directly():
    """Extract PDF content and test contamination directly"""
    
    print("🔍 TESTING PDF CONTENT CONTAMINATION DIRECTLY")
    print("=" * 60)
    
    # Download the PDF
    pdf_url = "http://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"
    
    try:
        print("Downloading PDF...")
        response = requests.get(pdf_url, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # Extract text using PDF processor
        from src.optimized_pdf_processor import OptimizedPDFProcessor
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
        
        try:
            print("Extracting text from PDF...")
            pdf_processor = OptimizedPDFProcessor()
            result = pdf_processor.process_pdf(temp_path)
            pdf_text = result.text if result else ""
            
            print(f"Extracted {len(pdf_text)} characters from PDF")
            print(f"First 500 characters: {pdf_text[:500]}...")
            
            # Test document primary case name detection
            from src.unified_clustering_master import UnifiedClusteringMaster
            clustering_master = UnifiedClusteringMaster()
            primary_case = clustering_master._extract_document_primary_case_name(pdf_text)
            
            print(f"\nDocument primary case detected: '{primary_case}'")
            
            # Test contamination filter
            if primary_case:
                from src.utils.unified_case_name_extractor import _is_document_case_contamination
                
                test_names = [
                    "City of Bellevue v. Lorang",
                    "Berst v. Snohomish County", 
                    "CITY OF BELLEVUE v. LORANG",
                    "State v. Manussier",
                    "Rozner v. Bellevue"
                ]
                
                print(f"\nTesting contamination filter with primary case: '{primary_case}'")
                for name in test_names:
                    is_contaminated = _is_document_case_contamination(name, primary_case)
                    status = "❌ REJECTED" if is_contaminated else "✅ ALLOWED"
                    print(f"  '{name}' → {status}")
            
            # Test a small section of the PDF with the unified pipeline
            print(f"\nTesting first 2000 characters with unified pipeline...")
            test_section = pdf_text[:2000]
            
            import asyncio
            from src.unified_processing_pipeline import process_citations_unified
            
            async def test_section():
                result = await process_citations_unified(
                    test_section,
                    processing_mode="enhanced_sync",
                    enable_parallel_verification=True,
                    enable_verification=True,
                    trace_id="pdf_test"
                )
                
                citations = result.get('citations', [])
                print(f"Found {len(citations)} citations in PDF section:")
                
                for cit in citations:
                    citation_text = cit.get('citation', 'N/A')
                    case_name = cit.get('extracted_case_name', 'N/A')
                    
                    is_contaminated = 'BELLEVUE' in case_name.upper() or 'LORANG' in case_name.upper()
                    status = "❌ CONTAMINATED" if is_contaminated else ("✅ CLEAN" if case_name != 'N/A' else "⚠️  N/A")
                    
                    print(f"  {citation_text} → '{case_name}' ({status})")
                
                return citations
            
            citations = asyncio.run(test_section())
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_content_directly()
