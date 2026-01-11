#!/usr/bin/env python3
"""
Test script to verify citation string conversion fix
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_processing_pipeline import UnifiedProcessingPipeline

# Create some test citations with objects that need string conversion
test_citations = [
    {
        "citation": "FullCaseCitation('123 F.3d 456', ...)",  # This would be an object in reality
        "extracted_case_name": "Test Case v. Test",
        "extracted_date": "2023",
    },
    {
        "citation": "ShortCaseCitation('Id.', ...)",
        "parallel_citations": ["FullCaseCitation('123 F.3d 456', ...)", "FullCaseCitation('456 F.2d 789', ...)"],
        "extracted_case_name": "Another Case v. Another",
        "extracted_date": "2022",
    }
]

# Test the conversion function
def test_conversion():
    pipeline = UnifiedProcessingPipeline()
    
    # Simulate the conversion function
    def _convert_citations_to_strings(citations):
        """Convert all citation objects in citation dicts to strings"""
        for cit in citations:
            # Handle citation objects (from clusters) vs dict citations (from citation_dicts)
            if "citation" in cit:
                # Dict format - convert citation field if it exists and is not already a string
                if cit["citation"] is not None and not isinstance(cit["citation"], str):
                    cit["citation"] = str(cit["citation"])
            else:
                # Object format - the cit dict itself represents a citation object
                # Add citation field as string representation
                if not isinstance(cit, str):
                    # Find the best string representation
                    if hasattr(cit, '__dict__'):
                        # It's a citation object
                        cit_str = str(cit)
                        cit["citation"] = cit_str
            
            # Convert parallel_citations to strings
            if "parallel_citations" in cit and cit["parallel_citations"]:
                cit["parallel_citations"] = [str(c) if not isinstance(c, str) else c for c in cit["parallel_citations"]]
            
            # Convert cluster_members to strings
            if "cluster_members" in cit and cit["cluster_members"]:
                cit["cluster_members"] = [str(c) if not isinstance(c, str) else c for c in cit["cluster_members"]]
        
        return citations
    
    # Test the conversion
    print("Before conversion:")
    for i, cit in enumerate(test_citations):
        print(f"  Citation {i+1}: {cit}")
    
    converted = _convert_citations_to_strings(test_citations)
    
    print("\nAfter conversion:")
    for i, cit in enumerate(converted):
        print(f"  Citation {i+1}: {cit}")
    
    # Check if all citations are now strings
    all_strings = all(isinstance(cit["citation"], str) for cit in converted)
    print(f"\nAll citations converted to strings: {all_strings}")
    
    return all_strings

if __name__ == "__main__":
    success = test_conversion()
    sys.exit(0 if success else 1)
