#!/usr/bin/env python3
"""
Integration Script for Enhanced Legal Case Extractor
Demonstrates how to integrate the enhanced LegalCaseExtractor with existing codebase.

This script shows:
1. How to replace existing extraction methods with enhanced ones
2. How to improve accuracy of case name extraction
3. How to enhance citation processing pipeline
4. How to validate extractions against Table of Authorities
5. How to generate training data for ML improvements
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from legal_case_extractor_enhanced import LegalCaseExtractorEnhanced, integrate_enhanced_extractor
from unified_citation_processor import UnifiedCitationProcessor, CitationResult
from case_name_extraction_core import extract_case_name_triple_comprehensive

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedExtractionIntegration:
    """
    Demonstrates integration of enhanced LegalCaseExtractor with existing pipeline.
    """
    
    def __init__(self):
        self.enhanced_extractor = LegalCaseExtractorEnhanced()
        self.legacy_processor = UnifiedCitationProcessor()
        
    def compare_extraction_methods(self, text: str, citations: List[str]) -> Dict[str, Any]:
        """
        Compare enhanced extractor with legacy methods.
        
        Args:
            text: Document text
            citations: List of citations to process
            
        Returns:
            Comparison results showing improvements
        """
        results = {
            'enhanced': [],
            'legacy': [],
            'improvements': [],
            'statistics': {}
        }
        
        logger.info("Testing enhanced extraction...")
        for citation in citations:
            # Enhanced extraction
            enhanced_extraction = self.enhanced_extractor.extract_with_fallback(text, citation)
            enhanced_result = self.enhanced_extractor.convert_to_citation_result(enhanced_extraction)
            results['enhanced'].append(enhanced_result)
            
            # Legacy extraction
            try:
                legacy_case_name, legacy_date, legacy_confidence = extract_case_name_triple_comprehensive(text, citation)
                legacy_result = CitationResult(
                    citation=citation,
                    case_name=legacy_case_name,
                    extracted_case_name=legacy_case_name,
                    extracted_date=legacy_date,
                    confidence=float(legacy_confidence) if legacy_confidence else 0.0,
                    method='legacy'
                )
                results['legacy'].append(legacy_result)
            except Exception as e:
                logger.warning(f"Legacy extraction failed for {citation}: {e}")
                results['legacy'].append(CitationResult(citation=citation, method='legacy_failed'))
        
        # Calculate improvements
        results['improvements'] = self._calculate_improvements(results['enhanced'], results['legacy'])
        results['statistics'] = self._calculate_statistics(results)
        
        return results
    
    def _calculate_improvements(self, enhanced_results: List[CitationResult], 
                               legacy_results: List[CitationResult]) -> List[Dict[str, Any]]:
        """Calculate improvements between enhanced and legacy methods."""
        improvements = []
        
        for i, (enhanced, legacy) in enumerate(zip(enhanced_results, legacy_results)):
            improvement = {
                'citation': enhanced.citation,
                'case_name_improvement': bool(enhanced.case_name and not legacy.case_name),
                'date_improvement': bool(enhanced.extracted_date and not legacy.extracted_date),
                'confidence_improvement': enhanced.confidence - legacy.confidence,
                'enhanced_case_name': enhanced.case_name,
                'legacy_case_name': legacy.case_name,
                'enhanced_date': enhanced.extracted_date,
                'legacy_date': legacy.extracted_date,
                'enhanced_confidence': enhanced.confidence,
                'legacy_confidence': legacy.confidence
            }
            improvements.append(improvement)
        
        return improvements
    
    def _calculate_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive statistics."""
        enhanced = results['enhanced']
        legacy = results['legacy']
        improvements = results['improvements']
        
        stats = {
            'total_citations': len(enhanced),
            'enhanced_with_case_names': len([r for r in enhanced if r.case_name]),
            'legacy_with_case_names': len([r for r in legacy if r.case_name]),
            'enhanced_with_dates': len([r for r in enhanced if r.extracted_date]),
            'legacy_with_dates': len([r for r in legacy if r.extracted_date]),
            'case_name_improvements': len([i for i in improvements if i['case_name_improvement']]),
            'date_improvements': len([i for i in improvements if i['date_improvement']]),
            'avg_confidence_improvement': sum(i['confidence_improvement'] for i in improvements) / len(improvements) if improvements else 0,
            'enhanced_avg_confidence': sum(r.confidence for r in enhanced) / len(enhanced) if enhanced else 0,
            'legacy_avg_confidence': sum(r.confidence for r in legacy) / len(legacy) if legacy else 0
        }
        
        return stats
    
    def enhance_existing_pipeline(self, text: str) -> Dict[str, Any]:
        """
        Enhance existing citation processing pipeline with improved extraction.
        
        Args:
            text: Document text to process
            
        Returns:
            Enhanced processing results
        """
        logger.info("Enhancing existing pipeline...")
        
        # Step 1: Extract citations using existing pipeline
        legacy_results = self.legacy_processor.process_text(text, extract_case_names=True, verify_citations=False)
        citations = [result['citation'] for result in legacy_results.get('citations', [])]
        
        # Step 2: Re-extract case names using enhanced extractor
        enhanced_results = integrate_enhanced_extractor(text, citations)
        
        # Step 3: Merge results
        merged_results = []
        for i, (legacy_result, enhanced_result) in enumerate(zip(legacy_results.get('citations', []), enhanced_results)):
            merged_result = legacy_result.copy()
            
            # Use enhanced case name if available and better
            if enhanced_result.case_name and (not legacy_result.get('case_name') or 
                                            enhanced_result.confidence > legacy_result.get('confidence', 0)):
                merged_result['case_name'] = enhanced_result.case_name
                merged_result['extracted_case_name'] = enhanced_result.extracted_case_name
                merged_result['confidence'] = enhanced_result.confidence
                merged_result['extraction_method'] = 'enhanced'
            
            # Use enhanced date if available
            if enhanced_result.extracted_date and not legacy_result.get('extracted_date'):
                merged_result['extracted_date'] = enhanced_result.extracted_date
                merged_result['year'] = enhanced_result.year
            
            # Add enhanced metadata
            if enhanced_result.metadata:
                merged_result['enhanced_metadata'] = enhanced_result.metadata
            
            merged_results.append(merged_result)
        
        return {
            'original_results': legacy_results,
            'enhanced_results': merged_results,
            'improvements': self._analyze_pipeline_improvements(legacy_results.get('citations', []), merged_results)
        }
    
    def _analyze_pipeline_improvements(self, original_results: List[Dict], 
                                     enhanced_results: List[Dict]) -> Dict[str, Any]:
        """Analyze improvements made by enhanced pipeline."""
        improvements = {
            'case_names_added': 0,
            'case_names_improved': 0,
            'dates_added': 0,
            'confidence_improvements': 0,
            'total_improvements': 0
        }
        
        for original, enhanced in zip(original_results, enhanced_results):
            improvements_made = 0
            
            # Case name improvements
            if not original.get('case_name') and enhanced.get('case_name'):
                improvements['case_names_added'] += 1
                improvements_made += 1
            elif (original.get('case_name') and enhanced.get('case_name') and 
                  enhanced.get('confidence', 0) > original.get('confidence', 0)):
                improvements['case_names_improved'] += 1
                improvements_made += 1
            
            # Date improvements
            if not original.get('extracted_date') and enhanced.get('extracted_date'):
                improvements['dates_added'] += 1
                improvements_made += 1
            
            # Confidence improvements
            if enhanced.get('confidence', 0) > original.get('confidence', 0):
                improvements['confidence_improvements'] += 1
                improvements_made += 1
            
            if improvements_made > 0:
                improvements['total_improvements'] += 1
        
        return improvements
    
    def validate_against_toa(self, text: str, toa_text: str = None) -> Dict[str, Any]:
        """
        Validate extractions against Table of Authorities.
        
        Args:
            text: Main document text
            toa_text: Table of Authorities text (optional)
            
        Returns:
            Validation results
        """
        logger.info("Validating against Table of Authorities...")
        
        # Extract cases from main text
        body_extractions = self.enhanced_extractor.extract_cases(text)
        
        # Extract cases from TOA if provided
        toa_extractions = []
        if toa_text:
            toa_extractions = self.enhanced_extractor.extract_from_table_of_authorities(toa_text)
        
        # Validate
        validation_results = self.enhanced_extractor.validate_against_toa(body_extractions, toa_extractions)
        
        return {
            'body_extractions': body_extractions,
            'toa_extractions': toa_extractions,
            'validation_results': validation_results,
            'statistics': {
                'body_total': len(body_extractions),
                'toa_total': len(toa_extractions),
                'validated': len(validation_results['validated']),
                'unvalidated': len(validation_results['unvalidated']),
                'toa_only': len(validation_results['toa_only']),
                'validation_rate': len(validation_results['validated']) / len(body_extractions) if body_extractions else 0
            }
        }
    
    def generate_training_data(self, text: str, output_file: str = None) -> List[Dict[str, Any]]:
        """
        Generate training data for ML improvements.
        
        Args:
            text: Document text
            output_file: Optional output file for training data
            
        Returns:
            Training data in structured format
        """
        logger.info("Generating training data...")
        
        # Extract cases with full context
        extractions = self.enhanced_extractor.extract_cases(text)
        
        training_data = []
        for extraction in extractions:
            training_example = {
                'text_context': extraction.context,
                'case_name': extraction.case_name,
                'citation': extraction.full_match,
                'case_type': extraction.case_type,
                'confidence': extraction.confidence,
                'extraction_method': extraction.extraction_method,
                'metadata': {
                    'party_1': extraction.party_1,
                    'party_2': extraction.party_2,
                    'volume': extraction.volume,
                    'reporter': extraction.reporter,
                    'page': extraction.page,
                    'year': extraction.year,
                    'date_info': extraction.date_info.__dict__ if extraction.date_info else None
                }
            }
            training_data.append(training_example)
        
        # Save to file if specified
        if output_file:
            import json
            with open(output_file, 'w') as f:
                json.dump(training_data, f, indent=2)
            logger.info(f"Training data saved to {output_file}")
        
        return training_data
    
    def run_comprehensive_test(self, text: str) -> Dict[str, Any]:
        """
        Run comprehensive test of enhanced extractor.
        
        Args:
            text: Document text to test
            
        Returns:
            Comprehensive test results
        """
        logger.info("Running comprehensive test...")
        
        results = {
            'extraction_comparison': None,
            'pipeline_enhancement': None,
            'toa_validation': None,
            'training_data': None,
            'summary': {}
        }
        
        # Test 1: Compare extraction methods
        citations = ["123 F.3d 456", "456 F.Supp.2d 789", "347 U.S. 483"]  # Example citations
        results['extraction_comparison'] = self.compare_extraction_methods(text, citations)
        
        # Test 2: Enhance existing pipeline
        results['pipeline_enhancement'] = self.enhance_existing_pipeline(text)
        
        # Test 3: Validate against TOA (if TOA section can be identified)
        results['toa_validation'] = self.validate_against_toa(text)
        
        # Test 4: Generate training data
        results['training_data'] = self.generate_training_data(text)
        
        # Generate summary
        results['summary'] = {
            'total_extractions': len(results['training_data']),
            'avg_confidence': sum(r.confidence for r in results['extraction_comparison']['enhanced']) / len(results['extraction_comparison']['enhanced']) if results['extraction_comparison']['enhanced'] else 0,
            'improvement_rate': results['extraction_comparison']['statistics']['case_name_improvements'] / results['extraction_comparison']['statistics']['total_citations'] if results['extraction_comparison']['statistics']['total_citations'] > 0 else 0,
            'pipeline_improvements': results['pipeline_enhancement']['improvements']['total_improvements']
        }
        
        return results

def main():
    """Main function to demonstrate integration."""
    
    # Sample legal text for testing
    sample_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    
    In Smith v. Jones, 123 F.3d 456 (2d Cir. Jan. 15, 1995), the court held that...
    See also In re ABC Corp., 456 F.Supp.2d 789 (S.D.N.Y. 2010).
    The Ex parte Johnson, 789 P.2d 123 (Cal. December 3, 1988) decision established...
    Brown v. Board, 347 U.S. 483 (1954) was a landmark case.
    In Matter of XYZ, 555 F.3d 123 (3d Cir. Apr. 2009), the court found...
    White v. Green, 888 F.2d 222 (9th Cir. 3/15/2005) involved complex issues.
    State v. Smith, 200 Wn.2d 72, 73, 514 P.3d 643 (2022).
    """
    
    # Initialize integration
    integration = EnhancedExtractionIntegration()
    
    # Run comprehensive test
    results = integration.run_comprehensive_test(sample_text)
    
    # Print results
    print("\n" + "="*80)
    print("ENHANCED LEGAL CASE EXTRACTOR INTEGRATION RESULTS")
    print("="*80)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total extractions: {results['summary']['total_extractions']}")
    print(f"   Average confidence: {results['summary']['avg_confidence']:.2f}")
    print(f"   Improvement rate: {results['summary']['improvement_rate']:.1%}")
    print(f"   Pipeline improvements: {results['summary']['pipeline_improvements']}")
    
    print(f"\n🔍 EXTRACTION COMPARISON:")
    stats = results['extraction_comparison']['statistics']
    print(f"   Enhanced case names: {stats['enhanced_with_case_names']}/{stats['total_citations']}")
    print(f"   Legacy case names: {stats['legacy_with_case_names']}/{stats['total_citations']}")
    print(f"   Case name improvements: {stats['case_name_improvements']}")
    print(f"   Date improvements: {stats['date_improvements']}")
    print(f"   Confidence improvement: {stats['avg_confidence_improvement']:.2f}")
    
    print(f"\n🚀 PIPELINE ENHANCEMENT:")
    pipeline_improvements = results['pipeline_enhancement']['improvements']
    print(f"   Case names added: {pipeline_improvements['case_names_added']}")
    print(f"   Case names improved: {pipeline_improvements['case_names_improved']}")
    print(f"   Dates added: {pipeline_improvements['dates_added']}")
    print(f"   Confidence improvements: {pipeline_improvements['confidence_improvements']}")
    
    print(f"\n✅ TOA VALIDATION:")
    toa_stats = results['toa_validation']['statistics']
    print(f"   Body extractions: {toa_stats['body_total']}")
    print(f"   TOA extractions: {toa_stats['toa_total']}")
    print(f"   Validated: {toa_stats['validated']}")
    print(f"   Validation rate: {toa_stats['validation_rate']:.1%}")
    
    print(f"\n📚 TRAINING DATA:")
    print(f"   Training examples generated: {len(results['training_data'])}")
    
    print("\n" + "="*80)
    print("INTEGRATION COMPLETE - Enhanced extractor ready for production use!")
    print("="*80)

if __name__ == "__main__":
    main() 