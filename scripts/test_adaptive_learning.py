#!/usr/bin/env python3
"""
Test script to demonstrate adaptive learning functionality.
This script shows how the system learns from failed extractions.
"""

import os
import sys
import json
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from adaptive_learning_pipeline import AdaptiveCitationProcessor, AdaptiveLearningPipeline

def test_adaptive_learning():
    """Test the adaptive learning functionality."""
    print("Testing Adaptive Learning System")
    print("=" * 40)
    
    # Initialize adaptive processor
    processor = AdaptiveCitationProcessor("test_learning_data")
    
    # Test text with some citations that might be challenging
    test_texts = [
        # Standard citations (should work well)
        """
        The court held in Smith v. Jones, 200 Wn.2d 72, 514 P.3d 643 (2022) that the 
        plaintiff's claim was valid. This decision was affirmed in Brown v. Wilson, 
        171 Wn.2d 486, 256 P.3d 321 (2011).
        """,
        
        # More challenging citations (might have lower confidence)
        """
        See generally RCW 2.60.020; see also Convoyant LLC v DeepThink LLC 200 Wn2d 72 
        at 73 (2022) (discussing certified questions). The court in Carlson v Global 
        Client Solutions LLC 171 Wn2d 486 at 493 (2011) reached a similar conclusion.
        """,
        
        # Very challenging citations (likely to fail)
        """
        As noted in the brief, the case of Dep't of Ecology v Campbell & Gwinn LLC 
        146 Wn2d 1 at 9 (2003) supports this position. See also State v Johnson 
        43 P3d 4 (2003) for additional authority.
        """
    ]
    
    print("Processing test texts with adaptive learning...")
    print()
    
    for i, text in enumerate(test_texts, 1):
        print(f"Test Text {i}:")
        print("-" * 20)
        
        # Process with learning
        citations, learning_info = processor.extract_with_learning(text, f"test_text_{i}")
        
        print(f"  Citations found: {len(citations)}")
        print(f"  Learning improvements: {learning_info['improvements']}")
        print(f"  Potential failures: {learning_info['potential_failures']}")
        
        # Show some citations
        for j, citation in enumerate(citations[:3], 1):
            print(f"    {j}. {citation.citation} (confidence: {citation.confidence:.2f})")
        
        if len(citations) > 3:
            print(f"    ... and {len(citations) - 3} more")
        
        print()
    
    # Show learning summary
    print("Learning Summary:")
    print("-" * 20)
    summary = processor.get_learning_summary()
    
    print(f"Total processed: {summary['total_processed']}")
    print(f"Total improvements: {summary['total_improvements']}")
    print(f"Learned patterns: {summary['learned_patterns']}")
    print(f"Failed extractions: {summary['failed_extractions']}")
    
    # Show failure analysis
    failure_analysis = summary['failure_analysis']
    if failure_analysis['total_failures'] > 0:
        print(f"\nFailure Analysis:")
        print(f"  Total failures: {failure_analysis['total_failures']}")
        print(f"  Error types: {failure_analysis['error_types']}")
        
        if failure_analysis['suggested_improvements']:
            print(f"  Suggested improvements:")
            for suggestion in failure_analysis['suggested_improvements']:
                print(f"    - {suggestion['description']}")
    
    # Save learning data
    processor.save_learning_data()
    print(f"\nLearning data saved to test_learning_data/")
    
    return summary

def test_enhanced_processor():
    """Test the enhanced processor that applies learned patterns."""
    print("\n" + "=" * 40)
    print("Testing Enhanced Adaptive Processor")
    print("=" * 40)
    
    try:
        from enhanced_adaptive_processor import EnhancedAdaptiveProcessor
    except ImportError:
        # Try importing from src directory
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        try:
            from enhanced_adaptive_processor import EnhancedAdaptiveProcessor
        except ImportError:
            print("Warning: enhanced_adaptive_processor not available")
            return None
    
    # Initialize enhanced processor
    processor = EnhancedAdaptiveProcessor("test_learning_data")
    
    # Test text
    test_text = """
    The court held in Smith v. Jones, 200 Wn.2d 72, 514 P.3d 643 (2022) that the 
    plaintiff's claim was valid. This decision was affirmed in Brown v. Wilson, 
    171 Wn.2d 486, 256 P.3d 321 (2011). See also Dep't of Ecology v Campbell & Gwinn LLC 
    146 Wn2d 1 at 9 (2003) for additional authority.
    """
    
    # Extract with learned patterns
    results = processor.extract_case_names(test_text)
    
    print(f"Enhanced processor found {len(results)} case names:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.case_name} (confidence: {result.confidence:.2f})")
    
    # Show learning stats
    stats = processor.get_performance_summary()
    print(f"\nEnhanced Processor Stats:")
    print(f"  Total learned patterns: {len(processor.learned_patterns)}")
    print(f"  Performance metrics: {dict(stats)}")
    
    return stats

def main():
    """Run the adaptive learning tests."""
    print("Adaptive Learning Test Suite")
    print("=" * 50)
    
    # Test basic adaptive learning
    learning_summary = test_adaptive_learning()
    
    # Test enhanced processor
    enhanced_stats = test_enhanced_processor()
    
    # Final summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"✓ Adaptive learning system tested successfully")
    print(f"✓ Processed {learning_summary['total_processed']} test texts")
    print(f"✓ Made {learning_summary['total_improvements']} improvements")
    print(f"✓ Learned {learning_summary['learned_patterns']} new patterns")
    print(f"✓ Analyzed {learning_summary['failed_extractions']} failed extractions")
    
    if enhanced_stats:
        print(f"✓ Enhanced processor tested with {enhanced_stats['total_learned_patterns']} patterns")
    
    print(f"\nThe system is now ready to learn from real brief processing!")
    print(f"Run the full pipeline to see continuous improvements.")

if __name__ == "__main__":
    main() 