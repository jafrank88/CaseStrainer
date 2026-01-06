#!/usr/bin/env python3
"""
Test the proprietary format message for WL and Lexis citations
"""

import sys
sys.path.append('src')

from unified_citation_processor_v2 import UnifiedCitationProcessorV2
import asyncio

async def test_proprietary_format():
    """Test that WL and Lexis citations get the proprietary format message"""
    
    processor = UnifiedCitationProcessorV2()
    
    # Test text with WL and Lexis citations
    test_text = """
    This case cites several sources. First, see Doe v. Roe, 123 F.3d 456 (9th Cir. 2021).
    Another important case is Smith v. Jones, No. MC 21-43 (BAH), 2021 WL 3622166, at *3 (D.D.C. June 3, 2021).
    Additionally, see Brown v. Board, 2022 WL 1234567.
    Finally, refer to Lexis 123456 for more details.
    The federal case United States v. Microsoft, 253 F.3d 34 (D.C. Cir. 2021) was also cited.
    """
    
    print("=" * 80)
    print("TESTING PROPRIETARY FORMAT MESSAGE FOR WL/LEXIS CITATIONS")
    print("=" * 80)
    print()
    
    # Process the text
    result = await processor.process_text(test_text)
    
    # Check citations
    citations = result.get("citations", [])
    
    print(f"Found {len(citations)} citations:")
    print()
    
    for i, cit in enumerate(citations, 1):
        citation_text = getattr(cit, "citation", "Unknown")
        is_verified = getattr(cit, "verified", False)
        is_verified_by_parallel = getattr(cit, "true_by_parallel", False)
        verification_status = getattr(cit, "verification_status", None)
        verification_error = getattr(cit, "verification_error", None)
        source = getattr(cit, "source", None)
        
        print(f"{i}. {citation_text}")
        print(f"   Verified: {is_verified}")
        print(f"   Verified by parallel: {is_verified_by_parallel}")
        print(f"   Verification status: {verification_status}")
        print(f"   Verification error: {verification_error}")
        print(f"   Source: {source}")
        
        # Check if it should have proprietary format message
        is_wl = "WL" in citation_text and any(char.isdigit() for char in citation_text)
        is_lexis = "Lexis" in citation_text
        
        if (is_wl or is_lexis) and not is_verified and not is_verified_by_parallel:
            if verification_status == "proprietary_format":
                print(f"   ✅ CORRECTLY marked as proprietary format")
            else:
                print(f"   ❌ SHOULD be marked as proprietary format")
        
        print()
    
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_proprietary_format())
