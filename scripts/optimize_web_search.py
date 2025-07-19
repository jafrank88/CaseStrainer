#!/usr/bin/env python3
"""
Web Search Optimization Script

This script tests and optimizes web search strategies for legal citations
that are not found in CourtListener. It analyzes success rates, response times,
and method effectiveness to create the most efficient search strategy.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Tuple
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from optimized_web_searcher import OptimizedWebSearcher
    from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
    from src.websearch_utils import LegalWebsearchEngine
except ImportError:
    # Try alternative import paths
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from src.optimized_web_searcher import OptimizedWebSearcher
    from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
    from src.websearch_utils import LegalWebsearchEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebSearchOptimizer:
    """Optimizes web search strategies for legal citations."""
    
    def __init__(self):
        self.searcher = None
        self.verifier = EnhancedMultiSourceVerifier()
        self.test_results = []
        
    async def initialize(self):
        """Initialize the web searcher."""
        self.searcher = LegalWebsearchEngine()
        await self.searcher.__aenter__()
        
    async def cleanup(self):
        """Clean up resources."""
        if self.searcher:
            await self.searcher.__aexit__(None, None, None)
    
    def load_test_citations(self, file_path: str = None) -> List[Dict]:
        """Load test citations from file or use sample data."""
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Sample test citations covering different types
        return [
            # Federal citations
            {"citation": "410 U.S. 113", "name": "Roe v. Wade", "type": "federal"},
            {"citation": "347 U.S. 483", "name": "Brown v. Board of Education", "type": "federal"},
            {"citation": "123 F.3d 456", "name": "Sample Federal Case", "type": "federal"},
            {"citation": "456 F.Supp.2d 789", "name": "Sample Federal Supplement", "type": "federal"},
            
            # State citations
            {"citation": "123 OK 456", "name": "Sample Oklahoma Case", "type": "state"},
            {"citation": "456 Cal.App.4th 789", "name": "Sample California Case", "type": "state"},
            {"citation": "789 N.Y.App.Div. 123", "name": "Sample New York Case", "type": "state"},
            
            # Regional citations
            {"citation": "123 N.E.2d 456", "name": "Sample Northeast Case", "type": "regional"},
            {"citation": "456 S.W.3d 789", "name": "Sample Southwest Case", "type": "regional"},
            {"citation": "789 P.3d 123", "name": "Sample Pacific Case", "type": "regional"},
        ]
    
    async def test_single_method(self, method_name: str, citation: str, case_name: str = None) -> Dict:
        """Test a single search method."""
        start_time = time.time()
        success = False
        error = None
        
        try:
            if method_name == 'google_scholar':
                result = await self.searcher.search_google_scholar(citation, case_name)
            elif method_name == 'justia':
                result = await self.searcher.search_justia(citation, case_name)
            elif method_name == 'oscn':
                result = await self.searcher.search_oscn(citation, case_name)
            else:
                result = {'verified': False, 'error': 'Unknown method'}
            
            success = result.get('verified', False)
            error = result.get('error')
            
        except Exception as e:
            error = str(e)
        
        duration = time.time() - start_time
        
        return {
            'method': method_name,
            'citation': citation,
            'case_name': case_name,
            'success': success,
            'duration': duration,
            'error': error
        }
    
    async def test_citation_comprehensive(self, citation_data: Dict) -> Dict:
        """Test all methods for a single citation."""
        citation = citation_data['citation']
        case_name = citation_data.get('name')
        citation_type = citation_data.get('type', 'unknown')
        
        logger.info(f"Testing citation: {citation} ({citation_type})")
        
        # Get priority methods for this citation type
        priority_methods = self.searcher._get_search_priority(citation)
        
        results = []
        first_success = None
        
        # Test each method in priority order
        for method in priority_methods:
            result = await self.test_single_method(method, citation, case_name)
            results.append(result)
            
            if result['success'] and first_success is None:
                first_success = method
        
        return {
            'citation': citation,
            'case_name': case_name,
            'type': citation_type,
            'results': results,
            'first_success': first_success,
            'any_success': any(r['success'] for r in results),
            'total_duration': sum(r['duration'] for r in results)
        }
    
    async def run_optimization_test(self, test_citations: List[Dict]) -> Dict:
        """Run comprehensive optimization test."""
        logger.info(f"Starting optimization test with {len(test_citations)} citations")
        
        all_results = []
        start_time = time.time()
        
        for citation_data in test_citations:
            result = await self.test_citation_comprehensive(citation_data)
            all_results.append(result)
            
            # Log progress
            if result['any_success']:
                logger.info(f"✓ {result['citation']} - Success via {result['first_success']}")
            else:
                logger.warning(f"✗ {result['citation']} - No methods succeeded")
        
        total_time = time.time() - start_time
        
        # Analyze results
        analysis = self.analyze_results(all_results)
        
        return {
            'test_results': all_results,
            'analysis': analysis,
            'total_time': total_time,
            'method_stats': self.searcher.get_method_stats()
        }
    
    def analyze_results(self, results: List[Dict]) -> Dict:
        """Analyze test results and provide optimization recommendations."""
        total_citations = len(results)
        successful_citations = sum(1 for r in results if r['any_success'])
        success_rate = successful_citations / total_citations if total_citations > 0 else 0
        
        # Method performance analysis
        method_performance = {}
        for result in results:
            for method_result in result['results']:
                method = method_result['method']
                if method not in method_performance:
                    method_performance[method] = {
                        'total_calls': 0,
                        'successful_calls': 0,
                        'total_duration': 0,
                        'avg_duration': 0
                    }
                
                perf = method_performance[method]
                perf['total_calls'] += 1
                perf['total_duration'] += method_result['duration']
                
                if method_result['success']:
                    perf['successful_calls'] += 1
        
        # Calculate averages and success rates
        for method, perf in method_performance.items():
            perf['success_rate'] = perf['successful_calls'] / perf['total_calls'] if perf['total_calls'] > 0 else 0
            perf['avg_duration'] = perf['total_duration'] / perf['total_calls'] if perf['total_calls'] > 0 else 0
        
        # Citation type analysis
        type_analysis = {}
        for result in results:
            citation_type = result['type']
            if citation_type not in type_analysis:
                type_analysis[citation_type] = {
                    'total': 0,
                    'successful': 0,
                    'avg_duration': 0,
                    'total_duration': 0
                }
            
            type_analysis[citation_type]['total'] += 1
            type_analysis[citation_type]['total_duration'] += result['total_duration']
            
            if result['any_success']:
                type_analysis[citation_type]['successful'] += 1
        
        for citation_type, analysis in type_analysis.items():
            analysis['success_rate'] = analysis['successful'] / analysis['total'] if analysis['total'] > 0 else 0
            analysis['avg_duration'] = analysis['total_duration'] / analysis['total'] if analysis['total'] > 0 else 0
        
        # Generate optimization recommendations
        recommendations = self.generate_recommendations(method_performance, type_analysis)
        
        return {
            'overall_success_rate': success_rate,
            'total_citations': total_citations,
            'successful_citations': successful_citations,
            'method_performance': method_performance,
            'type_analysis': type_analysis,
            'recommendations': recommendations
        }
    
    def generate_recommendations(self, method_performance: Dict, type_analysis: Dict) -> List[str]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []
        
        # Method-specific recommendations
        for method, perf in method_performance.items():
            if perf['success_rate'] < 0.3:
                recommendations.append(f"Method '{method}' has low success rate ({perf['success_rate']:.1%}). Consider improving implementation or removing from priority list.")
            elif perf['avg_duration'] > 5.0:
                recommendations.append(f"Method '{method}' is slow (avg {perf['avg_duration']:.1f}s). Consider optimizing or reducing priority.")
        
        # Type-specific recommendations
        for citation_type, analysis in type_analysis.items():
            if analysis['success_rate'] < 0.5:
                recommendations.append(f"Citation type '{citation_type}' has low success rate ({analysis['success_rate']:.1%}). May need specialized handling.")
        
        # General recommendations
        if len(recommendations) == 0:
            recommendations.append("All methods performing well. Current strategy is optimal.")
        
        return recommendations
    
    def save_results(self, results: Dict, output_file: str = "web_search_optimization_results.json"):
        """Save optimization results to file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {output_file}")
    
    def print_summary(self, results: Dict):
        """Print a summary of optimization results."""
        analysis = results['analysis']
        
        print("\n" + "="*60)
        print("WEB SEARCH OPTIMIZATION RESULTS")
        print("="*60)
        
        print(f"\nOverall Performance:")
        print(f"  Total Citations: {analysis['total_citations']}")
        print(f"  Successful: {analysis['successful_citations']}")
        print(f"  Success Rate: {analysis['overall_success_rate']:.1%}")
        print(f"  Total Time: {results['total_time']:.1f}s")
        
        print(f"\nMethod Performance:")
        for method, perf in analysis['method_performance'].items():
            print(f"  {method}:")
            print(f"    Success Rate: {perf['success_rate']:.1%} ({perf['successful_calls']}/{perf['total_calls']})")
            print(f"    Avg Duration: {perf['avg_duration']:.2f}s")
        
        print(f"\nCitation Type Analysis:")
        for citation_type, analysis_data in analysis['type_analysis'].items():
            print(f"  {citation_type}:")
            print(f"    Success Rate: {analysis_data['success_rate']:.1%} ({analysis_data['successful']}/{analysis_data['total']})")
            print(f"    Avg Duration: {analysis_data['avg_duration']:.2f}s")
        
        print(f"\nRecommendations:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print("="*60)

async def main():
    """Main optimization function."""
    optimizer = WebSearchOptimizer()
    
    try:
        await optimizer.initialize()
        
        # Load test citations
        test_citations = optimizer.load_test_citations("extracted_citations_sample.json")
        
        # Run optimization test
        results = await optimizer.run_optimization_test(test_citations)
        
        # Print summary
        optimizer.print_summary(results)
        
        # Save results
        optimizer.save_results(results)
        
    finally:
        await optimizer.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 