#!/usr/bin/env python3
"""
Test script for enhanced extraction improvements.
Demonstrates improved case name extraction, date extraction, and clustering.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_extraction_improvements import EnhancedExtractionProcessor

def create_test_samples():
    """Create various test samples to demonstrate the improvements."""
    samples = [
        {
            'name': 'Standard Washington Citations',
            'text': """
            A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
            """
        },
        {
            'name': 'Complex Citation Patterns',
            'text': """
            The court in Smith v. Jones, 123 Wash. 2d 456, 789 P.2d 123 (1990) held that the statute was constitutional. However, in Brown v. State, 456 Wash. App. 789, 234 P.3d 567 (2015), the court reached a different conclusion. The Supreme Court clarified this in Johnson v. Washington, 789 Wash. 2d 123, 456 P.3d 890 (2020).
            """
        },
        {
            'name': 'Department and Government Cases',
            'text': """
            The Department of Transportation v. State Highway Commission, 123 Wn.2d 456 (1990) established the framework. This was followed by State v. Johnson, 456 Wn. App. 789 (2015), and United States v. Smith, 789 F.3d 123 (2020). In re Estate of Brown, 234 Wn.2d 567 (2018) provided additional guidance.
            """
        },
        {
            'name': 'Corporate and Business Cases',
            'text': """
            Microsoft Corp. v. Department of Revenue, 200 Wn.2d 72 (2022) addressed tax issues. Amazon.com, Inc. v. State, 171 Wn.2d 486 (2011) clarified employment law. Boeing Co. v. Labor & Industries, 146 Wn.2d 1 (2003) established safety standards.
            """
        },
        {
            'name': 'Mixed Citation Types',
            'text': """
            The court considered multiple authorities: RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 514 P.3d 643 (2022); State v. Johnson, 456 Wn. App. 789 (2015); In re Estate of Smith, 234 Wn.2d 567 (2018); and Department of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 43 P.3d 4 (2003).
            """
        }
    ]
    return samples

def print_results(results, sample_name):
    """Print detailed results in a formatted way."""
    print(f"\n{'='*60}")
    print(f"RESULTS FOR: {sample_name}")
    print(f"{'='*60}")
    
    # Statistics
    stats = results['statistics']
    print(f"\n📊 STATISTICS:")
    print(f"   Total citations: {stats['total_citations']}")
    print(f"   Total clusters: {stats['total_clusters']}")
    print(f"   Enhanced case names: {stats['enhanced_case_names']}")
    print(f"   Enhanced dates: {stats['enhanced_dates']}")
    
    # Citations
    print(f"\n📋 CITATIONS:")
    for i, citation in enumerate(results['citations'], 1):
        print(f"   {i}. {citation.citation}")
        print(f"      Case name: {citation.extracted_case_name or 'N/A'}")
        print(f"      Date: {citation.extracted_date or 'N/A'}")
        print(f"      Confidence: {citation.confidence:.2f}")
        print(f"      Method: {citation.method}")
        if hasattr(citation, 'context') and citation.context:
            context_preview = citation.context[:100] + "..." if len(citation.context) > 100 else citation.context
            print(f"      Context: {context_preview}")
        print()
    
    # Clusters
    if results['clusters']:
        print(f"\n🔗 CLUSTERS:")
        for i, cluster in enumerate(results['clusters'], 1):
            print(f"   Cluster {i}:")
            print(f"      Citations: {', '.join(cluster['citations'])}")
            print(f"      Case name: {cluster['canonical_name'] or 'N/A'}")
            print(f"      Date: {cluster['canonical_date'] or 'N/A'}")
            print(f"      Size: {cluster['cluster_size']}")
            print(f"      Confidence: {cluster['confidence']:.2f}")
            if cluster.get('context'):
                context_preview = cluster['context'][:100] + "..." if len(cluster['context']) > 100 else cluster['context']
                print(f"      Context: {context_preview}")
            print()
    
    # Enhanced case names
    if results['enhanced_case_names']:
        print(f"\n🏛️ ENHANCED CASE NAMES:")
        for case_name in results['enhanced_case_names']:
            print(f"   - {case_name['name']}")
            print(f"     Confidence: {case_name['confidence']:.2f}")
            print(f"     Method: {case_name['method']}")
        print()
    
    # Enhanced dates
    if results['enhanced_dates']:
        print(f"\n📅 ENHANCED DATES:")
        for date_info in results['enhanced_dates']:
            print(f"   - {date_info['date']} (year: {date_info['year']})")
            print(f"     Confidence: {date_info['confidence']:.2f}")
            print(f"     Method: {date_info['method']}")
        print()

def compare_with_base_processor(text, sample_name):
    """Compare enhanced processor with base processor."""
    print(f"\n{'='*60}")
    print(f"COMPARISON FOR: {sample_name}")
    print(f"{'='*60}")
    
    # Import base processor
    from unified_citation_processor_v2 import UnifiedCitationProcessorV2
    
    # Initialize processors
    enhanced_processor = EnhancedExtractionProcessor()
    base_processor = UnifiedCitationProcessorV2()
    
    # Process with both
    enhanced_results = enhanced_processor.process_text_enhanced(text)
    base_results = base_processor.process_text(text)
    
    print(f"\n📊 COMPARISON:")
    print(f"   Base processor citations: {len(base_results)}")
    print(f"   Enhanced processor citations: {len(enhanced_results['citations'])}")
    print(f"   Enhanced clusters: {len(enhanced_results['clusters'])}")
    print(f"   Enhanced case names found: {len(enhanced_results['enhanced_case_names'])}")
    print(f"   Enhanced dates found: {len(enhanced_results['enhanced_dates'])}")
    
    # Compare case name extraction
    base_case_names = [r.extracted_case_name for r in base_results if r.extracted_case_name and r.extracted_case_name != 'N/A']
    enhanced_case_names = [r.extracted_case_name for r in enhanced_results['citations'] if r.extracted_case_name and r.extracted_case_name != 'N/A']
    
    print(f"\n🏛️ CASE NAME COMPARISON:")
    print(f"   Base processor case names: {len(base_case_names)}")
    print(f"   Enhanced processor case names: {len(enhanced_case_names)}")
    
    if base_case_names:
        print(f"   Base case names: {base_case_names}")
    if enhanced_case_names:
        print(f"   Enhanced case names: {enhanced_case_names}")
    
    # Compare date extraction
    base_dates = [r.extracted_date for r in base_results if r.extracted_date and r.extracted_date != 'N/A']
    enhanced_dates = [r.extracted_date for r in enhanced_results['citations'] if r.extracted_date and r.extracted_date != 'N/A']
    
    print(f"\n📅 DATE COMPARISON:")
    print(f"   Base processor dates: {len(base_dates)}")
    print(f"   Enhanced processor dates: {len(enhanced_dates)}")
    
    if base_dates:
        print(f"   Base dates: {base_dates}")
    if enhanced_dates:
        print(f"   Enhanced dates: {enhanced_dates}")

def main():
    """Run the enhanced extraction test."""
    print("🚀 ENHANCED EXTRACTION IMPROVEMENTS TEST")
    print("=" * 60)
    
    # Initialize processor
    processor = EnhancedExtractionProcessor()
    
    # Get test samples
    samples = create_test_samples()
    
    print(f"Testing {len(samples)} different sample texts...")
    
    # Process each sample
    for sample in samples:
        print(f"\n{'='*60}")
        print(f"PROCESSING: {sample['name']}")
        print(f"{'='*60}")
        print(f"Text length: {len(sample['text'])} characters")
        print(f"Text preview: {sample['text'][:200]}...")
        
        try:
            # Process with enhanced processor
            results = processor.process_text_enhanced(sample['text'])
            
            # Print results
            print_results(results, sample['name'])
            
            # Compare with base processor
            compare_with_base_processor(sample['text'], sample['name'])
            
        except Exception as e:
            print(f"❌ Error processing sample '{sample['name']}': {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("✅ ENHANCED EXTRACTION TEST COMPLETED")
    print(f"{'='*60}")
    print("\n📈 SUMMARY OF IMPROVEMENTS:")
    print("   • Enhanced case name extraction with multiple strategies")
    print("   • Improved date extraction with citation-adjacent priority")
    print("   • Better clustering with validation and proximity grouping")
    print("   • Confidence scoring for all extractions")
    print("   • Multiple extraction methods for better coverage")
    print("   • Context-aware processing")

if __name__ == "__main__":
    main() 