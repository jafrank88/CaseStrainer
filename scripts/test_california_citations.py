#!/usr/bin/env python3
"""
Test California Citation Extraction
==================================

This script tests the California citation extraction functionality
with the new citation format: Brandt v. Superior Court (1985) 37 Cal.3d 813 [210 Cal.Rptr. 211, 693 P.2d 796]
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from california_citation_handler import CaliforniaCitationHandler
from enhanced_extraction_improvements import EnhancedExtractionProcessor


def test_california_citations():
    """Test California citation extraction."""
    print("🧪 TESTING CALIFORNIA CITATION EXTRACTION")
    print("=" * 60)
    
    # Initialize handlers
    cal_handler = CaliforniaCitationHandler()
    enhanced_processor = EnhancedExtractionProcessor()
    
    # Test cases with various California citation formats
    test_cases = [
        # Your example
        "Brandt v. Superior Court (1985) 37 Cal.3d 813 [210 Cal.Rptr. 211, 693 P.2d 796]",
        
        # Variations
        "Smith v. Jones (2020) 45 Cal.4th 123 [180 Cal.Rptr.3d 456, 340 P.3d 789]",
        "Doe v. Roe (1995) 12 Cal.App.4th 567 [15 Cal.Rptr.2d 234]",
        "Brown v. Wilson (2010) 25 Cal.3d 456",
        "Johnson v. State (2005) 38 Cal.App.3d 789 [120 Cal.Rptr. 456]",
        
        # More complex examples
        "People v. Superior Court (Smith) (1996) 41 Cal.3d 123 [221 Cal.Rptr. 123, 709 P.2d 837]",
        "Department of Transportation v. Superior Court (1987) 37 Cal.3d 847 [210 Cal.Rptr. 219, 693 P.2d 804]",
        
        # Mixed text with multiple citations
        """
        The court held in Brandt v. Superior Court (1985) 37 Cal.3d 813 [210 Cal.Rptr. 211, 693 P.2d 796] 
        that the plaintiff's claim was valid. This decision was affirmed in Smith v. Jones (2020) 45 Cal.4th 123 
        [180 Cal.Rptr.3d 456, 340 P.3d 789]. The court also considered Doe v. Roe (1995) 12 Cal.App.4th 567 
        [15 Cal.Rptr.2d 234] for additional guidance.
        """
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}:")
        print("-" * 40)
        print(f"Input: {test_case.strip()}")
        
        # Test California handler directly
        print("\n🔍 California Handler Results:")
        cal_citations = cal_handler.extract_california_citations(test_case)
        
        if cal_citations:
            for j, citation in enumerate(cal_citations, 1):
                print(f"  Citation {j}:")
                print(f"    Case Name: {citation.case_name}")
                print(f"    Year: {citation.year}")
                print(f"    Primary: {citation.primary_citation}")
                print(f"    Parallel: {citation.parallel_citations}")
                print(f"    Confidence: {citation.confidence:.2f}")
                print(f"    Full Text: {citation.full_text}")
        else:
            print("  ❌ No California citations found")
        
        # Test enhanced processor
        print("\n🚀 Enhanced Processor Results:")
        enhanced_results = enhanced_processor.process_text_enhanced(test_case)
        enhanced_citations = enhanced_results.get('citations', [])
        
        if enhanced_citations:
            for j, citation in enumerate(enhanced_citations, 1):
                print(f"  Citation {j}:")
                print(f"    Citation: {citation.citation if hasattr(citation, 'citation') else 'N/A'}")
                print(f"    Pattern: {citation.pattern if hasattr(citation, 'pattern') else 'N/A'}")
                print(f"    Method: {citation.method if hasattr(citation, 'method') else 'N/A'}")
                print(f"    Confidence: {citation.confidence if hasattr(citation, 'confidence') else 0:.2f}")
                if hasattr(citation, 'metadata') and citation.metadata and citation.metadata.get('is_california_citation'):
                    print(f"    ⭐ California Citation: {citation.metadata.get('reporter_info', 'N/A')}")
        else:
            print("  ❌ No citations found")
        
        print("\n" + "="*60)
    
    print("\n✅ California citation testing complete!")


def test_integration_with_real_text():
    """Test integration with realistic legal text."""
    print("\n🔗 TESTING INTEGRATION WITH REALISTIC TEXT")
    print("=" * 60)
    
    enhanced_processor = EnhancedExtractionProcessor()
    
    # Realistic legal text with California citations
    realistic_text = """
    The court's analysis begins with the foundational principles established in Brandt v. Superior Court (1985) 37 Cal.3d 813 [210 Cal.Rptr. 211, 693 P.2d 796]. 
    This seminal case established the framework for evaluating administrative procedures in California courts.
    
    The court further considered the more recent decision in Smith v. Jones (2020) 45 Cal.4th 123 [180 Cal.Rptr.3d 456, 340 P.3d 789], 
    which refined the standards set forth in Brandt. Additionally, the appellate court's decision in Doe v. Roe (1995) 12 Cal.App.4th 567 [15 Cal.Rptr.2d 234] 
    provided guidance on procedural matters.
    
    For comparison, the court also examined federal precedent, including the Washington case of Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 514 P.3d 643 (2022).
    """
    
    print("📄 Processing realistic legal text...")
    results = enhanced_processor.process_text_enhanced(realistic_text)
    
    print(f"\n📊 Results Summary:")
    print(f"  Total citations found: {len(results.get('citations', []))}")
    print(f"  California citations: {sum(1 for c in results.get('citations', []) if hasattr(c, 'metadata') and c.metadata and c.metadata.get('is_california_citation', False))}")
    print(f"  Other citations: {sum(1 for c in results.get('citations', []) if not (hasattr(c, 'metadata') and c.metadata and c.metadata.get('is_california_citation', False)))}")
    
    print(f"\n📋 Detailed Results:")
    for i, citation in enumerate(results.get('citations', []), 1):
        print(f"  {i}. {citation.citation if hasattr(citation, 'citation') else 'N/A'}")
        print(f"     Pattern: {citation.pattern if hasattr(citation, 'pattern') else 'N/A'}")
        print(f"     Method: {citation.method if hasattr(citation, 'method') else 'N/A'}")
        print(f"     Confidence: {citation.confidence if hasattr(citation, 'confidence') else 0:.2f}")
        if hasattr(citation, 'metadata') and citation.metadata and citation.metadata.get('is_california_citation'):
            print(f"     ⭐ California Citation: {citation.metadata.get('reporter_info', 'N/A')}")
        print()


if __name__ == '__main__':
    test_california_citations()
    test_integration_with_real_text() 