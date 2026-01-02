#!/usr/bin/env python3
"""
Test if the unified pipeline fix is working for document primary case detection
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_unified_pipeline_contamination():
    """Test the unified pipeline with contamination fix"""
    
    print("🔍 TESTING UNIFIED PIPELINE CONTAMINATION FIX")
    print("=" * 55)
    
    from src.unified_processing_pipeline import process_citations_unified
    
    # Test the problematic document
    test_document = """
    IN THE COURT OF APPEALS OF THE STATE OF WASHINGTON
    DIVISION II
    
    CITY OF BELLEVUE v. LORANG
    
    No. 59366-1-II
    
    Filed: November 4, 2002
    
    In this case involving municipal liability, the court considered 
    precedent from Berst v. Snohomish County, 114 Wn. App. 245 and 
    related cases like 57 P.3d 273. Additionally, the court referenced 
    State v. Manussier, 129 Wn.2d 652 in its analysis.
    
    The court also considered federal precedent including 161 F.3d 584 
    in its environmental law analysis.
    """
    
    print("Testing unified pipeline with document primary case detection...")
    
    try:
        result = await process_citations_unified(
            test_document, 
            processing_mode="enhanced_sync",
            enable_parallel_verification=True,
            enable_verification=True,
            trace_id="test123"
        )
        
        citations = result.get('citations', [])
        print(f"Found {len(citations)} citations:")
        
        contaminated_count = 0
        for i, cit in enumerate(citations, 1):
            citation_text = cit.get('citation', 'N/A')
            case_name = cit.get('extracted_case_name', 'N/A')
            
            is_contaminated = 'BELLEVUE' in case_name.upper() or 'LORANG' in case_name.upper()
            if is_contaminated:
                contaminated_count += 1
                print(f"  ❌ {citation_text} → '{case_name}' (CONTAMINATED)")
            elif case_name == 'N/A':
                print(f"  ⚠️  {citation_text} → '{case_name}' (no extraction)")
            else:
                print(f"  ✅ {citation_text} → '{case_name}' (clean)")
        
        contamination_rate = (contaminated_count / len(citations) * 100) if citations else 0
        print(f"\nContamination rate: {contamination_rate:.1f}% ({contaminated_count}/{len(citations)})")
        
        if contamination_rate == 0:
            print("🎉 UNIFIED PIPELINE CONTAMINATION FIX IS WORKING!")
        else:
            print("❌ UNIFIED PIPELINE STILL HAS CONTAMINATION")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_unified_pipeline_contamination())
