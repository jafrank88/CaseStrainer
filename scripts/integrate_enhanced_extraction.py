#!/usr/bin/env python3
"""
Integration script for enhanced extraction improvements.
Demonstrates how to integrate enhanced case name, date extraction, and clustering
with the existing adaptive learning pipeline.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_extraction_improvements import EnhancedExtractionProcessor
from enhanced_adaptive_processor import EnhancedAdaptiveProcessor

class IntegratedExtractionProcessor:
    """
    Integrated processor that combines enhanced extraction with adaptive learning.
    """
    
    def __init__(self, learning_data_dir: str = None):
        self.enhanced_processor = EnhancedExtractionProcessor()
        self.adaptive_processor = EnhancedAdaptiveProcessor(learning_data_dir) if learning_data_dir else None
        
    def process_text_integrated(self, text: str) -> dict:
        """
        Process text using both enhanced extraction and adaptive learning.
        """
        print("🔄 Processing with integrated enhanced extraction...")
        
        # Step 1: Enhanced extraction
        print("   📋 Step 1: Enhanced extraction")
        enhanced_results = self.enhanced_processor.process_text_enhanced(text)
        
        # Step 2: Adaptive learning (if available)
        if self.adaptive_processor:
            print("   🧠 Step 2: Adaptive learning")
            adaptive_results = self.adaptive_processor.extract_with_learned_patterns(text)
            
            # Step 3: Merge results
            print("   🔗 Step 3: Merging results")
            merged_results = self._merge_results(enhanced_results, adaptive_results)
        else:
            print("   ⚠️  Step 2: Adaptive learning not available")
            merged_results = enhanced_results
        
        # Step 4: Apply learning (if adaptive processor available)
        if self.adaptive_processor:
            print("   📚 Step 4: Applying learning")
            self._apply_learning(enhanced_results, text)
        
        return merged_results
    
    def _merge_results(self, enhanced_results: dict, adaptive_results: list) -> dict:
        """
        Merge enhanced extraction results with adaptive learning results.
        """
        merged = enhanced_results.copy()
        
        # Add adaptive learning statistics
        if adaptive_results:
            merged['adaptive_citations'] = len(adaptive_results)
            merged['adaptive_case_names'] = sum(1 for r in adaptive_results if hasattr(r, 'extracted_case_name') and r.extracted_case_name)
            merged['adaptive_dates'] = sum(1 for r in adaptive_results if hasattr(r, 'extracted_date') and r.extracted_date)
        else:
            merged['adaptive_citations'] = 0
            merged['adaptive_case_names'] = 0
            merged['adaptive_dates'] = 0
        
        # Calculate combined statistics
        merged['total_combined_citations'] = merged['statistics']['total_citations'] + merged['adaptive_citations']
        merged['total_combined_case_names'] = merged['statistics']['enhanced_case_names'] + merged['adaptive_case_names']
        merged['total_combined_dates'] = merged['statistics']['enhanced_dates'] + merged['adaptive_dates']
        
        return merged
    
    def _apply_learning(self, enhanced_results: dict, text: str):
        """
        Apply learning from enhanced extraction results.
        """
        try:
            # Learn from enhanced case names
            for case_name_info in enhanced_results['enhanced_case_names']:
                if case_name_info['confidence'] > 0.8:  # High confidence extractions
                    self.adaptive_processor.learn_case_name_pattern(
                        case_name_info['name'],
                        case_name_info['method'],
                        case_name_info['confidence']
                    )
            
            # Learn from enhanced dates
            for date_info in enhanced_results['enhanced_dates']:
                if date_info['confidence'] > 0.8:  # High confidence extractions
                    self.adaptive_processor.learn_date_pattern(
                        date_info['date'],
                        date_info['method'],
                        date_info['confidence']
                    )
            
            print(f"   ✅ Learned from {len(enhanced_results['enhanced_case_names'])} case names and {len(enhanced_results['enhanced_dates'])} dates")
            
        except Exception as e:
            print(f"   ⚠️  Learning failed: {e}")

def create_integration_test_samples():
    """Create test samples for integration testing."""
    samples = [
        {
            'name': 'Complex Legal Document',
            'text': """
            The court's analysis in this matter requires consideration of multiple authorities. 
            First, we examine the framework established in Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 514 P.3d 643 (2022), 
            which addressed similar issues. The Department of Transportation v. State Highway Commission, 123 Wn.2d 456 (1990) 
            provides additional guidance on administrative procedures. 
            
            In Smith v. Jones, 456 Wn. App. 789 (2015), the court clarified the standard of review. 
            This was further refined in Brown v. State, 789 Wn.2d 123 (2020), which established 
            the current framework for such cases.
            
            The Supreme Court's decision in In re Estate of Johnson, 234 Wn.2d 567 (2018) 
            provides important precedent for estate matters, while Microsoft Corp. v. Department of Revenue, 
            171 Wn.2d 486 (2011) addresses corporate tax issues.
            """
        },
        {
            'name': 'Mixed Citation Types with Statutes',
            'text': """
            The statutory framework is established by RCW 2.60.020, which provides for certified questions. 
            This court's interpretation follows the principles set forth in Carlson v. Glob. Client Sols., LLC, 
            171 Wn.2d 486, 256 P.3d 321 (2011). The standard of review is de novo, as established in 
            Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 43 P.3d 4 (2003).
            
            Recent developments in State v. Johnson, 456 Wn. App. 789 (2015) and 
            United States v. Smith, 789 F.3d 123 (2020) provide additional context for this analysis.
            """
        }
    ]
    return samples

def print_integration_results(results, sample_name):
    """Print detailed integration results."""
    print(f"\n{'='*80}")
    print(f"INTEGRATION RESULTS FOR: {sample_name}")
    print(f"{'='*80}")
    
    # Enhanced extraction statistics
    stats = results['statistics']
    print(f"\n📊 ENHANCED EXTRACTION STATISTICS:")
    print(f"   Total citations: {stats['total_citations']}")
    print(f"   Total clusters: {stats['total_clusters']}")
    print(f"   Enhanced case names: {stats['enhanced_case_names']}")
    print(f"   Enhanced dates: {stats['enhanced_dates']}")
    
    # Adaptive learning statistics
    print(f"\n🧠 ADAPTIVE LEARNING STATISTICS:")
    print(f"   Adaptive citations: {results.get('adaptive_citations', 0)}")
    print(f"   Adaptive case names: {results.get('adaptive_case_names', 0)}")
    print(f"   Adaptive dates: {results.get('adaptive_dates', 0)}")
    
    # Combined statistics
    print(f"\n🔗 COMBINED STATISTICS:")
    print(f"   Total combined citations: {results.get('total_combined_citations', 0)}")
    print(f"   Total combined case names: {results.get('total_combined_case_names', 0)}")
    print(f"   Total combined dates: {results.get('total_combined_dates', 0)}")
    
    # Enhanced case names
    if results['enhanced_case_names']:
        print(f"\n🏛️ ENHANCED CASE NAMES:")
        for case_name in results['enhanced_case_names']:
            print(f"   - {case_name['name']} (confidence: {case_name['confidence']:.2f}, method: {case_name['method']})")
    
    # Enhanced dates
    if results['enhanced_dates']:
        print(f"\n📅 ENHANCED DATES:")
        for date_info in results['enhanced_dates']:
            print(f"   - {date_info['date']} (confidence: {date_info['confidence']:.2f}, method: {date_info['method']})")
    
    # Clusters
    if results['clusters']:
        print(f"\n🔗 CLUSTERS:")
        for i, cluster in enumerate(results['clusters'], 1):
            print(f"   Cluster {i}: {', '.join(cluster['citations'])}")
            print(f"     Case name: {cluster['canonical_name']}")
            print(f"     Date: {cluster['canonical_date']}")
            print(f"     Size: {cluster['cluster_size']}")

def main():
    """Run the integration test."""
    print("🚀 ENHANCED EXTRACTION INTEGRATION TEST")
    print("=" * 80)
    
    # Initialize integrated processor
    # Note: Set learning_data_dir to enable adaptive learning
    # processor = IntegratedExtractionProcessor(learning_data_dir="adaptive_results")
    processor = IntegratedExtractionProcessor()  # Without adaptive learning for demo
    
    # Get test samples
    samples = create_integration_test_samples()
    
    print(f"Testing {len(samples)} samples with integrated processing...")
    
    # Process each sample
    for sample in samples:
        print(f"\n{'='*80}")
        print(f"PROCESSING: {sample['name']}")
        print(f"{'='*80}")
        print(f"Text length: {len(sample['text'])} characters")
        print(f"Text preview: {sample['text'][:200]}...")
        
        try:
            # Process with integrated processor
            results = processor.process_text_integrated(sample['text'])
            
            # Print results
            print_integration_results(results, sample['name'])
            
        except Exception as e:
            print(f"❌ Error processing sample '{sample['name']}': {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("✅ INTEGRATION TEST COMPLETED")
    print(f"{'='*80}")
    
    print("\n📈 INTEGRATION BENEFITS:")
    print("   • Enhanced extraction provides better accuracy")
    print("   • Adaptive learning improves over time")
    print("   • Combined approach maximizes coverage")
    print("   • Confidence scoring for quality assessment")
    print("   • Multiple strategies for robust extraction")
    
    print("\n🔧 INTEGRATION OPTIONS:")
    print("   1. Use enhanced extraction only (current demo)")
    print("   2. Use adaptive learning only")
    print("   3. Use both with result merging")
    print("   4. Use enhanced extraction with learning feedback")
    
    print("\n💡 NEXT STEPS:")
    print("   • Enable adaptive learning by setting learning_data_dir")
    print("   • Process real legal documents")
    print("   • Monitor learning progress")
    print("   • Adjust confidence thresholds")
    print("   • Fine-tune extraction patterns")

if __name__ == "__main__":
    main() 