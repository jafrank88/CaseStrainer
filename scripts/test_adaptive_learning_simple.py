#!/usr/bin/env python3
"""
Simple test of the adaptive learning pipeline with sample data.
This avoids Unicode encoding issues and scraping dependencies.
"""

import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_adaptive_processor import EnhancedAdaptiveProcessor

def create_sample_data():
    """Create sample legal texts for testing."""
    sample_texts = [
        # Test case 1: Standard Washington citations
        """
        A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
        """,
        
        # Test case 2: Citations with variations
        """
        The court in Smith v. Jones, 123 Wash. 2d 456, 789 P.2d 123 (1990) held that the statute was constitutional. However, in Brown v. State, 456 Wash. App. 789, 234 P.3d 567 (2015), the court reached a different conclusion. The Supreme Court clarified this in Johnson v. Washington, 789 Wash. 2d 123, 456 P.3d 890 (2020).
        """,
        
        # Test case 3: Complex citations
        """
        As established in Washington v. State, 123 Wn.2d 456, 789 P.2d 123, 125 (1990), and reaffirmed in State v. Washington, 456 Wn. App. 789, 234 P.3d 567, 570 (2015), the standard of review is de novo. This was further clarified in Washington State v. Johnson, 789 Wn. 2d 123, 456 P.3d 890, 892 (2020).
        """
    ]
    
    return sample_texts

def main():
    """Run the adaptive learning test with sample data."""
    print("=== ADAPTIVE LEARNING TEST WITH SAMPLE DATA ===")
    
    # Create directories
    results_dir = Path("adaptive_results")
    learning_dir = Path("learning_data")
    results_dir.mkdir(exist_ok=True)
    learning_dir.mkdir(exist_ok=True)
    
    # Initialize processor
    print("Initializing enhanced adaptive processor...")
    processor = EnhancedAdaptiveProcessor(
        learning_data_dir=str(learning_dir)
    )
    
    # Get sample texts
    sample_texts = create_sample_data()
    
    print(f"\nProcessing {len(sample_texts)} sample texts...")
    
    all_results = []
    
    for i, text in enumerate(sample_texts, 1):
        print(f"\n--- Processing Sample Text {i} ---")
        print(f"Text length: {len(text)} characters")
        
        try:
            # Process with learned patterns
            results = processor.extract_with_learned_patterns(text)
            
            print(f"Extracted {len(results)} citations:")
            for j, citation in enumerate(results, 1):
                print(f"  {j}. {citation.citation} (confidence: {getattr(citation, 'confidence', 'N/A')})")
                if hasattr(citation, 'method'):
                    print(f"     Method: {citation.method}")
                if hasattr(citation, 'start_index') and hasattr(citation, 'end_index'):
                    print(f"     Position: {citation.start_index}-{citation.end_index}")
                if hasattr(citation, 'pattern'):
                    print(f"     Pattern: {citation.pattern}")
            
            all_results.append({
                'sample_id': i,
                'text_length': len(text),
                'citations_count': len(results),
                'citations': [citation.citation for citation in results]
            })
            
        except Exception as e:
            print(f"Error processing sample {i}: {e}")
            all_results.append({
                'sample_id': i,
                'error': str(e)
            })
    
    # Save results
    results_file = results_dir / "sample_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Show learning summary
    print(f"\n=== LEARNING SUMMARY ===")
    learning_summary_file = results_dir / "learning_summary.json"
    if learning_summary_file.exists():
        with open(learning_summary_file, 'r') as f:
            summary = json.load(f)
        
        print(f"Patterns learned: {len(summary.get('learned_patterns', []))}")
        print(f"Confidence adjustments: {len(summary.get('confidence_adjustments', []))}")
        print(f"Case name database entries: {len(summary.get('case_name_database', {}))}")
    else:
        print("No learning summary found yet.")
    
    # Show final results
    print(f"\n=== FINAL RESULTS ===")
    print(f"Results saved to: {results_file}")
    print(f"Total samples processed: {len(all_results)}")
    
    successful = sum(1 for r in all_results if 'error' not in r)
    print(f"Successful extractions: {successful}")
    print(f"Failed extractions: {len(all_results) - successful}")
    
    if successful > 0:
        total_citations = sum(r.get('citations_count', 0) for r in all_results if 'error' not in r)
        print(f"Total citations extracted: {total_citations}")
    
    print("\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    main() 