"""
Simple test script for parallel citation handling.
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.models import CitationResult

class SimpleProcessingConfig:
    debug_mode = True

class SimpleCitationClusterer:
    def __init__(self):
        self.config = SimpleProcessingConfig()
    
    def detect_parallel_citations(self, citations, text):
        """Simple parallel citation detection for testing."""
        if len(citations) < 2:
            return citations
            
        # Sort by position
        citations = sorted(citations, key=lambda c: c.start_index if c.start_index is not None else 0)
        
        # Simple proximity-based grouping (within 150 chars)
        groups = []
        current_group = [citations[0]]
        
        for i in range(1, len(citations)):
            prev = citations[i-1]
            curr = citations[i]
            
            # Calculate distance
            distance = (curr.start_index or 0) - (prev.end_index or 0)
            
            # Simple grouping
            if distance <= 150:
                current_group.append(curr)
            else:
                groups.append(current_group)
                current_group = [curr]
        
        if current_group:
            groups.append(current_group)
        
        # Mark parallel citations within groups
        for group in groups:
            if len(group) > 1:
                for i, cite1 in enumerate(group):
                    for j, cite2 in enumerate(group):
                        if i != j:
                            if not hasattr(cite1, 'parallel_citations') or cite1.parallel_citations is None:
                                cite1.parallel_citations = []
                            if cite2.citation not in cite1.parallel_citations:
                                cite1.parallel_citations.append(cite2.citation)
        
        # Simple metadata propagation
        for group in groups:
            if len(group) > 1:
                # Find first citation with extracted data
                source = None
                for cite in group:
                    if hasattr(cite, 'extracted_case_name') and cite.extracted_case_name:
                        source = cite
                        break
                
                # Propagate to others
                if source:
                    for cite in group:
                        if cite != source:
                            if not hasattr(cite, 'extracted_case_name') or not cite.extracted_case_name:
                                cite.extracted_case_name = source.extracted_case_name
                            if not hasattr(cite, 'extracted_date') or not cite.extracted_date:
                                cite.extracted_date = source.extracted_date
        
        return citations

def test_parallel_citation():
    """Test parallel citation handling."""
    # Test case: "In re Marriage of Chandola, 180 Wn.2d 632, 642, 327 P.3d 644 (2014)"
    text = "In re Marriage of Chandola, 180 Wn.2d 632, 642, 327 P.3d 644 (2014)"
    
    # Create citations
    cite1 = CitationResult(
        citation="180 Wn.2d 632",
        extracted_case_name="In re Marriage of Chandola",
        extracted_date="2014",
        start_index=text.find("180 Wn.2d 632"),
        end_index=text.find("180 Wn.2d 632") + len("180 Wn.2d 632")
    )
    
    cite2 = CitationResult(
        citation="327 P.3d 644",
        start_index=text.find("327 P.3d 644"),
        end_index=text.find("327 P.3d 644") + len("327 P.3d 644")
    )
    
    # Process citations
    clusterer = SimpleCitationClusterer()
    result = clusterer.detect_parallel_citations([cite1, cite2], text)
    
    # Verify results
    print("\nTest 1: Parallel Citations")
    print("-" * 50)
    print(f"Citation 1: {cite1.citation}")
    print(f"  Extracted name: {getattr(cite1, 'extracted_case_name', 'N/A')}")
    print(f"  Parallels: {getattr(cite1, 'parallel_citations', [])}")
    
    print(f"\nCitation 2: {cite2.citation}")
    print(f"  Extracted name: {getattr(cite2, 'extracted_case_name', 'N/A')}")
    print(f"  Parallels: {getattr(cite2, 'parallel_citations', [])}")
    
    # Assertions
    assert hasattr(cite1, 'parallel_citations'), "cite1 should have parallel_citations"
    assert hasattr(cite2, 'parallel_citations'), "cite2 should have parallel_citations"
    assert cite2.citation in cite1.parallel_citations, "cite2 should be in cite1's parallels"
    assert hasattr(cite2, 'extracted_case_name'), "cite2 should have extracted_case_name"
    assert cite2.extracted_case_name == "In re Marriage of Chandola", "cite2 should have same case name as cite1"
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_parallel_citation()
