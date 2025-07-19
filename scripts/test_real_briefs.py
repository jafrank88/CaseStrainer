#!/usr/bin/env python3
"""
Real Briefs Test Script
=======================

This script processes real legal briefs from the downloaded_briefs directory
using the enhanced extraction system to evaluate real-world performance.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from enhanced_extraction_improvements import EnhancedExtractionProcessor
from unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.file_utils import extract_text_from_file


class RealBriefsTester:
    """Test the enhanced extraction system on real legal briefs."""
    
    def __init__(self, briefs_dir: str = "downloaded_briefs", max_briefs: int = 10):
        self.briefs_dir = Path(briefs_dir)
        self.max_briefs = max_briefs
        self.results = []
        self.summary_stats = {
            'total_briefs': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'total_citations': 0,
            'total_case_names': 0,
            'total_dates': 0,
            'processing_time': 0,
            'avg_citations_per_brief': 0,
            'avg_case_names_per_brief': 0,
            'avg_dates_per_brief': 0,
        }
        
        # Initialize processors
        self.base_processor = UnifiedCitationProcessorV2()
        self.enhanced_processor = EnhancedExtractionProcessor()
        
    def find_brief_files(self) -> List[Path]:
        """Find PDF brief files to process."""
        if not self.briefs_dir.exists():
            print(f"❌ Briefs directory not found: {self.briefs_dir}")
            return []
            
        pdf_files = list(self.briefs_dir.glob("*.pdf"))
        print(f"📁 Found {len(pdf_files)} PDF files in {self.briefs_dir}")
        
        # Sort by file size (larger files likely have more content)
        pdf_files.sort(key=lambda x: x.stat().st_size, reverse=True)
        
        # Take the first max_briefs files
        selected_files = pdf_files[:self.max_briefs]
        print(f"🎯 Selected {len(selected_files)} files for testing")
        
        return selected_files
    
    def extract_text_from_brief(self, pdf_path: Path) -> Optional[str]:
        """Extract text from a PDF brief."""
        try:
            print(f"   📄 Extracting text from {pdf_path.name}...")
            text = extract_text_from_file(str(pdf_path))
            
            if not text or len(text.strip()) < 100:
                print(f"   ⚠️  Warning: Minimal text extracted ({len(text)} chars)")
                return None
                
            print(f"   ✅ Extracted {len(text)} characters")
            return text
            
        except Exception as e:
            print(f"   ❌ Failed to extract text: {e}")
            return None
    
    def process_brief_with_base(self, text: str, brief_name: str) -> Dict[str, Any]:
        """Process brief with base processor."""
        try:
            print(f"   🔄 Processing with base processor...")
            start_time = time.time()
            
            # Use the correct method name
            result = self.base_processor.process_text(text)
            
            processing_time = time.time() - start_time
            
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            return {
                'citations': len(citations),
                'clusters': len(clusters),
                'processing_time': processing_time,
                'citations_list': citations,
                'clusters_list': clusters
            }
            
        except Exception as e:
            print(f"   ❌ Base processor failed: {e}")
            return {
                'citations': 0,
                'clusters': 0,
                'processing_time': 0,
                'citations_list': [],
                'clusters_list': [],
                'error': str(e)
            }
    
    def process_brief_with_enhanced(self, text: str, brief_name: str) -> Dict[str, Any]:
        """Process brief with enhanced processor."""
        try:
            print(f"   🚀 Processing with enhanced processor...")
            start_time = time.time()
            
            result = self.enhanced_processor.extract_citations_with_enhancements(text)
            
            processing_time = time.time() - start_time
            
            citations = result.get('citations', [])
            case_names = result.get('case_names', [])
            dates = result.get('dates', [])
            clusters = result.get('clusters', [])
            
            return {
                'citations': len(citations),
                'case_names': len(case_names),
                'dates': len(dates),
                'clusters': len(clusters),
                'processing_time': processing_time,
                'citations_list': citations,
                'case_names_list': case_names,
                'dates_list': dates,
                'clusters_list': clusters
            }
            
        except Exception as e:
            print(f"   ❌ Enhanced processor failed: {e}")
            return {
                'citations': 0,
                'case_names': 0,
                'dates': 0,
                'clusters': 0,
                'processing_time': 0,
                'citations_list': [],
                'case_names_list': [],
                'dates_list': [],
                'clusters_list': [],
                'error': str(e)
            }
    
    def process_single_brief(self, pdf_path: Path) -> Dict[str, Any]:
        """Process a single brief and return results."""
        brief_name = pdf_path.stem
        file_size = pdf_path.stat().st_size
        
        print(f"\n{'='*80}")
        print(f"📋 PROCESSING: {brief_name}")
        print(f"📁 File: {pdf_path.name}")
        print(f"📏 Size: {file_size:,} bytes")
        print(f"{'='*80}")
        
        # Extract text
        text = self.extract_text_from_brief(pdf_path)
        if not text:
            return {
                'brief_name': brief_name,
                'file_path': str(pdf_path),
                'file_size': file_size,
                'text_length': 0,
                'success': False,
                'error': 'Failed to extract text'
            }
        
        # Process with base processor
        base_result = self.process_brief_with_base(text, brief_name)
        
        # Process with enhanced processor
        enhanced_result = self.process_brief_with_enhanced(text, brief_name)
        
        # Calculate improvements
        citation_improvement = enhanced_result['citations'] - base_result['citations']
        cluster_improvement = enhanced_result['clusters'] - base_result['clusters']
        
        result = {
            'brief_name': brief_name,
            'file_path': str(pdf_path),
            'file_size': file_size,
            'text_length': len(text),
            'success': True,
            'base_processor': base_result,
            'enhanced_processor': enhanced_result,
            'improvements': {
                'citations': citation_improvement,
                'clusters': cluster_improvement,
                'new_case_names': enhanced_result['case_names'],
                'new_dates': enhanced_result['dates']
            }
        }
        
        # Print summary
        print(f"\n📊 RESULTS FOR: {brief_name}")
        print(f"   Base processor: {base_result['citations']} citations, {base_result['clusters']} clusters")
        print(f"   Enhanced processor: {enhanced_result['citations']} citations, {enhanced_result['clusters']} clusters")
        print(f"   Improvements: +{citation_improvement} citations, +{cluster_improvement} clusters")
        print(f"   New case names: {enhanced_result['case_names']}")
        print(f"   New dates: {enhanced_result['dates']}")
        
        return result
    
    def run_tests(self):
        """Run tests on all selected briefs."""
        print("🚀 REAL BRIEFS TEST SUITE")
        print("=" * 80)
        print(f"📁 Briefs directory: {self.briefs_dir}")
        print(f"🎯 Max briefs to process: {self.max_briefs}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Find brief files
        brief_files = self.find_brief_files()
        if not brief_files:
            print("❌ No brief files found. Exiting.")
            return
        
        # Process each brief
        self.start_time = time.time()
        
        for i, pdf_path in enumerate(brief_files, 1):
            print(f"\n📋 Processing brief {i}/{len(brief_files)}")
            
            try:
                result = self.process_single_brief(pdf_path)
                self.results.append(result)
                
                if result['success']:
                    self.summary_stats['successful_extractions'] += 1
                else:
                    self.summary_stats['failed_extractions'] += 1
                    
            except Exception as e:
                print(f"❌ Unexpected error processing {pdf_path.name}: {e}")
                self.summary_stats['failed_extractions'] += 1
                self.results.append({
                    'brief_name': pdf_path.stem,
                    'file_path': str(pdf_path),
                    'success': False,
                    'error': str(e)
                })
        
        # Calculate summary statistics
        self.calculate_summary_stats()
        
        # Print final results
        self.print_summary()
        
        # Save results
        self.save_results()
    
    def calculate_summary_stats(self):
        """Calculate summary statistics from results."""
        successful_results = [r for r in self.results if r['success']]
        
        self.summary_stats['total_briefs'] = len(self.results)
        self.summary_stats['processing_time'] = time.time() - self.start_time
        
        if successful_results:
            total_citations = sum(r['enhanced_processor']['citations'] for r in successful_results)
            total_case_names = sum(r['enhanced_processor']['case_names'] for r in successful_results)
            total_dates = sum(r['enhanced_processor']['dates'] for r in successful_results)
            
            self.summary_stats['total_citations'] = total_citations
            self.summary_stats['total_case_names'] = total_case_names
            self.summary_stats['total_dates'] = total_dates
            self.summary_stats['avg_citations_per_brief'] = total_citations / len(successful_results)
            self.summary_stats['avg_case_names_per_brief'] = total_case_names / len(successful_results)
            self.summary_stats['avg_dates_per_brief'] = total_dates / len(successful_results)
    
    def print_summary(self):
        """Print summary of test results."""
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        
        print(f"📁 Total briefs processed: {self.summary_stats['total_briefs']}")
        print(f"✅ Successful extractions: {self.summary_stats['successful_extractions']}")
        print(f"❌ Failed extractions: {self.summary_stats['failed_extractions']}")
        print(f"⏱️  Total processing time: {self.summary_stats['processing_time']:.2f} seconds")
        
        if self.summary_stats['successful_extractions'] > 0:
            print(f"\n📈 EXTRACTION STATISTICS:")
            print(f"   Total citations found: {self.summary_stats['total_citations']}")
            print(f"   Total case names found: {self.summary_stats['total_case_names']}")
            print(f"   Total dates found: {self.summary_stats['total_dates']}")
            print(f"   Average citations per brief: {self.summary_stats['avg_citations_per_brief']:.1f}")
            print(f"   Average case names per brief: {self.summary_stats['avg_case_names_per_brief']:.1f}")
            print(f"   Average dates per brief: {self.summary_stats['avg_dates_per_brief']:.1f}")
        
        # Show top performing briefs
        successful_results = [r for r in self.results if r['success']]
        if successful_results:
            print(f"\n🏆 TOP PERFORMING BRIEFS:")
            sorted_results = sorted(successful_results, 
                                  key=lambda x: x['enhanced_processor']['citations'], 
                                  reverse=True)
            
            for i, result in enumerate(sorted_results[:5], 1):
                citations = result['enhanced_processor']['citations']
                case_names = result['enhanced_processor']['case_names']
                dates = result['enhanced_processor']['dates']
                print(f"   {i}. {result['brief_name']}: {citations} citations, {case_names} case names, {dates} dates")
    
    def save_results(self):
        """Save test results to JSON file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"real_briefs_test_results_{timestamp}.json"
        
        output_data = {
            'test_info': {
                'timestamp': datetime.now().isoformat(),
                'briefs_directory': str(self.briefs_dir),
                'max_briefs': self.max_briefs,
                'total_processing_time': self.summary_stats['processing_time']
            },
            'summary_stats': self.summary_stats,
            'detailed_results': self.results
        }
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Results saved to: {results_file}")
        except Exception as e:
            print(f"\n❌ Failed to save results: {e}")


def main():
    """Main function to run the real briefs test."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test enhanced extraction on real briefs')
    parser.add_argument('--briefs-dir', default='downloaded_briefs', 
                       help='Directory containing brief PDFs')
    parser.add_argument('--max-briefs', type=int, default=10,
                       help='Maximum number of briefs to process')
    
    args = parser.parse_args()
    
    # Create and run tester
    tester = RealBriefsTester(
        briefs_dir=args.briefs_dir,
        max_briefs=args.max_briefs
    )
    
    tester.run_tests()


if __name__ == '__main__':
    main() 