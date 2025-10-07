"""
Test the verification fix for 521 U.S. 811
This tests that the verification system now returns the correct canonical name.
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
import PyPDF2

async def test_521_verification():
    """Test that 521 U.S. 811 gets correct verification."""
    
    print("=" * 80)
    print("TESTING: 521 U.S. 811 Verification Fix")
    print("=" * 80)
    
    # Get the PDF
    pdf_path = Path('1033940.pdf')
    if not pdf_path.exists():
        print(" Error: 1033940.pdf not found")
        return
    
    # Extract text
    print("\n1. Extracting text from PDF...")
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''.join([page.extract_text() or "" for page in reader.pages])
    print(f"   [OK] Extracted {len(text)} characters")
    
    # Process with full pipeline (extraction + verification + clustering)
    print("\n2. Processing with UnifiedCitationProcessorV2...")
    processor = UnifiedCitationProcessorV2()
    result = await processor.process_text(text)
    
    # Find 521 U.S. 811 in the results
    print("\n3. Looking for 521 U.S. 811 in results...")
    target_citation = None
    
    if hasattr(result, 'citations'):
        citations = result.citations
    else:
        citations = result.get('citations', [])
    
    for cit in citations:
        if isinstance(cit, dict):
            citation_text = cit.get('citation', '')
        else:
            citation_text = getattr(cit, 'citation', '')
        
        if '521 U.S. 811' in citation_text:
            target_citation = cit if isinstance(cit, dict) else {
                k: getattr(cit, k, None) for k in dir(cit) if not k.startswith('_')
            }
            break
    
    if not target_citation:
        print("    521 U.S. 811 not found in results!")
        print(f"   Found {len(citations)} total citations")
        return
    
    print(f"    Found 521 U.S. 811")
    
    # Check the verification results
    print("\n4. Checking verification results...")
    print("=" * 80)
    
    extracted_name = target_citation.get('extracted_case_name', 'N/A')
    canonical_name = target_citation.get('canonical_name', 'N/A')
    canonical_date = target_citation.get('canonical_date', 'N/A')
    canonical_url = target_citation.get('canonical_url', 'N/A')
    is_verified = target_citation.get('is_verified', False)
    cluster_case_name = target_citation.get('cluster_case_name', 'N/A')
    cluster_id = target_citation.get('cluster_id', 'N/A')
    
    print(f"Citation:           521 U.S. 811")
    print(f"Extracted Name:     {extracted_name}")
    print(f"Canonical Name:     {canonical_name}")
    print(f"Canonical Date:     {canonical_date}")
    print(f"Canonical URL:      {canonical_url}")
    print(f"Is Verified:        {is_verified}")
    print(f"Cluster Case Name:  {cluster_case_name}")
    print(f"Cluster ID:         {cluster_id}")
    print("=" * 80)
    
    # Validate the fix
    print("\n5. Validating the fix...")
    errors = []
    warnings = []
    
    # Check if verified
    if not is_verified:
        errors.append(" Citation is not verified")
    else:
        print("    Citation is verified")
    
    # Check canonical name
    if canonical_name == 'N/A' or not canonical_name:
        errors.append(" No canonical name found")
    elif 'Raines' in canonical_name and 'Byrd' in canonical_name:
        print(f"    Canonical name is correct: '{canonical_name}'")
    else:
        errors.append(f" Canonical name is wrong: '{canonical_name}' (should contain 'Raines' and 'Byrd')")
    
    # Check canonical date
    if canonical_date == '1997':
        print(f"    Canonical date is correct: {canonical_date}")
    else:
        warnings.append(f"  Canonical date is '{canonical_date}' (expected '1997')")
    
    # Check extracted name (we know this will be wrong due to PDF formatting)
    if extracted_name != canonical_name:
        warnings.append(f"  Extracted name '{extracted_name}' differs from canonical (expected due to PDF formatting)")
    
    # Check if it's NOT clustered with Spokeo
    print("\n6. Checking clustering...")
    spokeo_citation = None
    for cit in citations:
        if isinstance(cit, dict):
            citation_text = cit.get('citation', '')
        else:
            citation_text = getattr(cit, 'citation', '')
        
        if '136 S. Ct. 1540' in citation_text:
            spokeo_citation = cit if isinstance(cit, dict) else {
                k: getattr(cit, k, None) for k in dir(cit) if not k.startswith('_')
            }
            break
    
    if spokeo_citation:
        spokeo_cluster = spokeo_citation.get('cluster_id', 'N/A')
        print(f"   Spokeo (136 S. Ct. 1540) cluster: {spokeo_cluster}")
        print(f"   Raines (521 U.S. 811) cluster:    {cluster_id}")
        
        if cluster_id == spokeo_cluster:
            errors.append(f" Raines and Spokeo are in SAME cluster: {cluster_id}")
        else:
            print(f"    Raines and Spokeo are in DIFFERENT clusters")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if errors:
        print("\n ERRORS:")
        for error in errors:
            print(f"   {error}")
    
    if warnings:
        print("\n  WARNINGS:")
        for warning in warnings:
            print(f"   {warning}")
    
    if not errors:
        print("\n   ALL CHECKS PASSED!   ")
        print("\nThe verification fix is working correctly!")
        print("521 U.S. 811 now has the correct canonical name: Raines v. Byrd")
    else:
        print("\n VERIFICATION FIX NOT WORKING YET")
        print("\nPossible reasons:")
        print("1. System hasn't been restarted yet (run: .\\cslaunch.ps1)")
        print("2. Verification is disabled")
        print("3. CourtListener API issue")
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_521_verification())
