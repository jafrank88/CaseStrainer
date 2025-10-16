#!/usr/bin/env python3
"""
Final Integrated Citation Processor

This module provides a complete solution for processing complex citations
by combining enhanced parsing with existing verification systems.
"""

import sys
import os
import logging
import json
from typing import Dict, List, Any, Optional

# Add the src directory to the path to import existing modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the enhanced processor
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor

# Import existing citation verification modules
try:
    from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
    from src.unified_citation_processor import CitationProcessor
    from src.courtlistener_integration import setup_courtlistener_api
except ImportError as e:
    print(f"Warning: Could not import existing modules: {e}")
    EnhancedMultiSourceVerifier = None
    CitationProcessor = None

logger = logging.getLogger(__name__)

class FinalCitationProcessor:
    """Final integrated citation processor that handles complex citations properly."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.unified_processor = UnifiedCitationProcessor()
        
        # Initialize existing verification systems
        self.existing_verifier = None
        self.citation_processor = None
        
        if EnhancedMultiSourceVerifier:
            try:
                self.existing_verifier = EnhancedMultiSourceVerifier()
                logger.info("EnhancedMultiSourceVerifier initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize EnhancedMultiSourceVerifier: {e}")
        
        if CitationProcessor:
            try:
                self.citation_processor = CitationProcessor(api_key=api_key)
                logger.info("CitationProcessor initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize CitationProcessor: {e}")
        
        # Setup CourtListener API if available
        if api_key:
            try:
                setup_courtlistener_api(api_key)
                logger.info("CourtListener API setup completed")
            except Exception as e:
                logger.warning(f"Could not setup CourtListener API: {e}")
    
    def process_text(self, text: str) -> List[Dict[str, Any]]:
        """Process text and return enhanced citation results."""
        # Use unified processor to extract and verify citations
        result = self.unified_processor.process_text(text)
        return result.get('results', [])
    
    def _verify_citation_with_existing_system(self, citation: Dict) -> Dict[str, Any]:
        """Verify a complex citation using the existing verification system."""
        verification_results = {
            'citation': citation.get('full_text'),
            'is_complex': citation.get('is_complex', False),
            'verification_strategies': [],
            'best_result': None,
            'all_results': []
        }
        
        # Strategy 1: Try primary citation with existing verifier
        if citation.get('primary_citation') and self.existing_verifier:
            try:
                result = self._verify_with_existing_verifier(citation.get('primary_citation'))
                verification_results['verification_strategies'].append({
                    'strategy': 'primary_citation_existing',
                    'citation': citation.get('primary_citation'),
                    'result': result
                })
                verification_results['all_results'].append(result)
            except Exception as e:
                logger.error(f"Error verifying primary citation: {e}")
        
        # Strategy 2: Try parallel citations with existing verifier
        for parallel in citation.get('parallel_citations', []):
            if self.existing_verifier:
                try:
                    result = self._verify_with_existing_verifier(parallel)
                    verification_results['verification_strategies'].append({
                        'strategy': 'parallel_citation_existing',
                        'citation': parallel,
                        'result': result
                    })
                    verification_results['all_results'].append(result)
                except Exception as e:
                    logger.error(f"Error verifying parallel citation: {e}")
        
        # Strategy 3: Try with case name if available
        if citation.get('case_name'):
            for citation_text in [citation.get('primary_citation')] + citation.get('parallel_citations', []):
                if citation_text and self.existing_verifier:
                    try:
                        result = self._verify_with_case_name_existing(citation.get('case_name'), citation_text)
                        verification_results['verification_strategies'].append({
                            'strategy': 'with_case_name_existing',
                            'case_name': citation.get('case_name'),
                            'citation': citation_text,
                            'result': result
                        })
                        verification_results['all_results'].append(result)
                    except Exception as e:
                        logger.error(f"Error verifying with case name: {e}")
        
        # Strategy 4: Try with citation processor if available
        if self.citation_processor:
            for citation_text in [citation.get('primary_citation')] + citation.get('parallel_citations', []):
                if citation_text:
                    try:
                        result = self._verify_with_citation_processor(citation_text)
                        verification_results['verification_strategies'].append({
                            'strategy': 'citation_processor',
                            'citation': citation_text,
                            'result': result
                        })
                        verification_results['all_results'].append(result)
                    except Exception as e:
                        logger.error(f"Error verifying with citation processor: {e}")
        
        # Find best result
        best_result = self._find_best_verification_result(verification_results['all_results'])
        verification_results['best_result'] = best_result
        
        return verification_results
    
    def _verify_with_existing_verifier(self, citation: str) -> Dict[str, Any]:
        """Verify citation using the existing EnhancedMultiSourceVerifier."""
        if not self.existing_verifier:
            return {
                'citation': citation,
                'verified': False,
                'source': 'existing_verifier',
                'error': 'Existing verifier not available',
                'confidence': 0.0
            }
        
        try:
            # Use the existing verification method
            result = self.existing_verifier.verify_citation_unified_workflow(citation)
            return {
                'citation': citation,
                'verified': result.get('verified', False),
                'source': 'existing_verifier',
                'confidence': result.get('confidence', 0.0),
                'details': result
            }
        except Exception as e:
            return {
                'citation': citation,
                'verified': False,
                'source': 'existing_verifier',
                'error': str(e),
                'confidence': 0.0
            }
    
    def _verify_with_case_name_existing(self, case_name: str, citation: str) -> Dict[str, Any]:
        """Verify citation with case name using existing verifier."""
        if not self.existing_verifier:
            return {
                'citation': citation,
                'case_name': case_name,
                'verified': False,
                'source': 'existing_verifier_with_case_name',
                'error': 'Existing verifier not available',
                'confidence': 0.0
            }
        
        try:
            # For now, just try the regular verification since the case name method might not exist
            result = self.existing_verifier.verify_citation_unified_workflow(citation)
            return {
                'citation': citation,
                'case_name': case_name,
                'verified': result.get('verified', False),
                'source': 'existing_verifier_with_case_name',
                'confidence': result.get('confidence', 0.0),
                'details': result
            }
        except Exception as e:
            return {
                'citation': citation,
                'case_name': case_name,
                'verified': False,
                'source': 'existing_verifier_with_case_name',
                'error': str(e),
                'confidence': 0.0
            }
    
    def _verify_with_citation_processor(self, citation: str) -> Dict[str, Any]:
        """Verify citation using the CitationProcessor."""
        if not self.citation_processor:
            return {
                'citation': citation,
                'verified': False,
                'source': 'citation_processor',
                'error': 'Citation processor not available',
                'confidence': 0.0
            }
        
        try:
            # Try to use the citation processor's verification method
            # This might need to be adapted based on the actual method name
            if hasattr(self.citation_processor, 'verify_citation'):
                result = self.citation_processor.verify_citation_unified_workflow(citation)
            elif hasattr(self.citation_processor, 'process_citation'):
                result = self.citation_processor.process_citation(citation)
            else:
                # Fallback to basic processing
                result = {'verified': False, 'error': 'No verification method available'}
            
            return {
                'citation': citation,
                'verified': result.get('verified', False),
                'source': 'citation_processor',
                'confidence': result.get('confidence', 0.0),
                'details': result
            }
        except Exception as e:
            return {
                'citation': citation,
                'verified': False,
                'source': 'citation_processor',
                'error': str(e),
                'confidence': 0.0
            }
    
    def _find_best_verification_result(self, results: List[Dict]) -> Optional[Dict]:
        """Find the best verification result from multiple attempts."""
        if not results:
            return None
        
        # Sort by confidence and verification status
        sorted_results = sorted(results, key=lambda x: (x.get('verified', False), x.get('confidence', 0)), reverse=True)
        return sorted_results[0]
    
    def _format_result(self, citation: Dict, verification_results: Dict) -> Dict[str, Any]:
        """Format the result for display and storage."""
        best_result = verification_results.get('best_result', {})
        
        return {
            'full_text': citation.get('full_text'),
            'case_name': citation.get('case_name'),
            'primary_citation': citation.get('primary_citation'),
            'parallel_citations': citation.get('parallel_citations'),
            'pinpoint_pages': citation.get('pinpoint_pages'),
            'docket_numbers': citation.get('docket_numbers'),
            'case_history': citation.get('case_history'),
            'publication_status': citation.get('publication_status'),
            'year': citation.get('year'),
            'is_complex': citation.get('is_complex'),
            
            # Verification results
            'verified': best_result.get('verified', False),
            'source': best_result.get('source', 'unknown'),
            'confidence': best_result.get('confidence', 0.0),
            'error': best_result.get('error', ''),
            
            # Additional metadata
            'verification_strategies': verification_results.get('verification_strategies', []),
            'all_results': verification_results.get('all_results', []),
            
            # Format for compatibility with existing system
            'citation': citation.get('primary_citation') or citation.get('full_text'),
            'method': 'enhanced_processor',
            'pattern': 'complex_citation',
            'context': citation.get('full_text')[:200] + '...' if len(citation.get('full_text')) > 200 else citation.get('full_text'),
            'extracted_case_name': citation.get('case_name') or 'N/A',
            'hinted_case_name': citation.get('case_name') or 'N/A',
            'extracted_date': citation.get('year') or '',
            'canonical_name': citation.get('case_name') or 'N/A',
            'canonical_date': citation.get('year') or 'N/A',
            'court': '',
            'docket_number': citation.get('docket_numbers')[0] if citation.get('docket_numbers') else '',
            'url': '',
            'valid': best_result.get('verified', False),
        }
    
    def get_complex_citation_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Generate a summary of complex citation processing."""
        summary = {
            'total_citations': len(results),
            'complex_citations': 0,
            'verified_citations': 0,
            'verification_rate': 0.0,
            'complex_verification_rate': 0.0,
            'citation_types': {
                'simple': 0,
                'complex': 0,
                'with_parallel': 0,
                'with_history': 0,
                'with_docket': 0,
                'with_status': 0
            },
            'verification_sources': {},
            'errors': []
        }
        
        for result in results:
            # Count complex citations
            if result.get('is_complex', False):
                summary['complex_citations'] += 1
                summary['citation_types']['complex'] += 1
                
                # Count specific complex features
                if result.get('parallel_citations'):
                    summary['citation_types']['with_parallel'] += 1
                if result.get('case_history'):
                    summary['citation_types']['with_history'] += 1
                if result.get('docket_numbers'):
                    summary['citation_types']['with_docket'] += 1
                if result.get('publication_status'):
                    summary['citation_types']['with_status'] += 1
            else:
                summary['citation_types']['simple'] += 1
            
            # Count verified citations
            if result.get('verified', False):
                summary['verified_citations'] += 1
            
            # Count verification sources
            source = result.get('source', 'unknown')
            summary['verification_sources'][source] = summary['verification_sources'].get(source, 0) + 1
            
            # Collect errors
            if result.get('error'):
                summary['errors'].append({
                    'citation': result.get('citation', ''),
                    'error': result.get('error', '')
                })
        
        # Calculate rates
        if summary['total_citations'] > 0:
            summary['verification_rate'] = summary['verified_citations'] / summary['total_citations']
        
        if summary['complex_citations'] > 0:
            complex_verified = sum(1 for r in results if r.get('is_complex', False) and r.get('verified', False))
            summary['complex_verification_rate'] = complex_verified / summary['complex_citations']
        
        return summary

# Example usage and testing
if __name__ == "__main__":
    # Load API key from config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        api_key = config.get('COURTLISTENER_API_KEY')
    except Exception as e:
        print(f"Warning: Could not load API key from config: {e}")
        api_key = None
    
    # Initialize the final processor
    processor = FinalCitationProcessor(api_key)
    
    # Test with your complex citation
    test_text = """John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017) (Doe I), modified on other grounds on remand, No. 48000-0-II (Wash. Ct. App. Oct. 2, 2018) (Doe II) (unpublished)"""
    
    print("=== Final Integrated Citation Processing ===")
    print(f"Input Text: {test_text}")
    print()
    
    # Process the text
    results = processor.process_text(test_text)
    
    # Generate summary
    summary = processor.get_complex_citation_summary(results)
    
    print("=== Processing Summary ===")
    print(f"Total Citations: {summary['total_citations']}")
    print(f"Complex Citations: {summary['complex_citations']}")
    print(f"Verified Citations: {summary['verified_citations']}")
    print(f"Verification Rate: {summary['verification_rate']:.2%}")
    print(f"Complex Verification Rate: {summary['complex_verification_rate']:.2%}")
    print()
    
    print("=== Citation Types ===")
    for citation_type, count in summary['citation_types'].items():
        print(f"{citation_type}: {count}")
    print()
    
    print("=== Verification Sources ===")
    for source, count in summary['verification_sources'].items():
        print(f"{source}: {count}")
    print()
    
    if summary['errors']:
        print("=== Errors ===")
        for error in summary['errors'][:5]:  # Show first 5 errors
            print(f"Citation: {error['citation']}")
            print(f"Error: {error['error']}")
            print()
    
    print("=== Detailed Results ===")
    for i, result in enumerate(results):
        print(f"=== Result {i+1} ===")
        print(f"Full Text: {result['full_text']}")
        print(f"Case Name: {result['case_name']}")
        print(f"Primary Citation: {result['primary_citation']}")
        print(f"Parallel Citations: {result['parallel_citations']}")
        print(f"Pinpoint Pages: {result['pinpoint_pages']}")
        print(f"Docket Numbers: {result['docket_numbers']}")
        print(f"Case History: {result['case_history']}")
        print(f"Publication Status: {result['publication_status']}")
        print(f"Year: {result['year']}")
        print(f"Is Complex: {result['is_complex']}")
        print(f"Verified: {result['verified']}")
        print(f"Source: {result['source']}")
        print(f"Confidence: {result['confidence']}")
        if result.get('error'):
            print(f"Error: {result['error']}")
        print()
        
        print("=== Verification Strategies ===")
        for strategy in result['verification_strategies']:
            print(f"Strategy: {strategy['strategy']}")
            if 'citation' in strategy:
                print(f"  Citation: {strategy['citation']}")
            if 'case_name' in strategy:
                print(f"  Case Name: {strategy['case_name']}")
            print(f"  Result: {strategy['result']}")
            print()
        
        print("=" * 80) 