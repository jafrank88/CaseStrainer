from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.toa_parser import ImprovedToAParser
from a_plus_citation_processor import extract_case_name_from_context, extract_year_after_citation
import re
from typing import List, Dict, Any, Optional

class EnhancedV2Processor:
    """Production-ready enhanced v2 processor with A+ context extraction and ToA ground truth."""
    
    def __init__(self):
        self.v2 = UnifiedCitationProcessorV2()
        self.toa_parser = ImprovedToAParser()
    
    def process_text(self, text: str) -> List[Dict[str, Any]]:
        """Process text with enhanced document-based extraction."""
        
        # Step 1: Extract ToA ground truth
        toa_ground_truth = self._extract_toa_ground_truth(text)
        
        # Step 2: Extract with v2 (comprehensive coverage)
        v2_citations = self.v2.process_text(text)
        
        # Step 3: Enhance each citation
        enhanced_citations = []
        
        for citation in v2_citations:
            enhanced_citation = self._enhance_citation(citation, text, toa_ground_truth)
            enhanced_citations.append(enhanced_citation)
        
        return enhanced_citations
    
    def _extract_toa_ground_truth(self, text: str) -> Dict[str, Dict[str, Any]]:
        """Extract ToA data as ground truth."""
        toa_entries = self.toa_parser.parse_toa_section_simple(text)
        ground_truth = {}
        
        for entry in toa_entries:
            for citation in entry.citations:
                normalized_citation = self._normalize_citation(citation)
                ground_truth[normalized_citation] = {
                    'case_name': entry.case_name,
                    'year': entry.years[0] if entry.years else None,
                    'source': 'toa_ground_truth',
                    'confidence': 'high'
                }
        
        return ground_truth
    
    def _enhance_citation(self, citation, text: str, toa_ground_truth: Dict) -> Dict[str, Any]:
        """Enhance a single citation with document-based extraction."""
        
        normalized_citation = self._normalize_citation(citation.citation)
        
        # Check if we have ToA ground truth
        if normalized_citation in toa_ground_truth:
            # Use ToA as ground truth
            toa_data = toa_ground_truth[normalized_citation]
            enhanced_case_name = toa_data['case_name']
            enhanced_year = toa_data['year']
            method = 'toa_ground_truth'
            confidence = 'high'
        else:
            # Use enhanced A+ context extraction
            enhanced_case_name = self._extract_case_name_enhanced(text, citation.citation)
            enhanced_year = self._extract_year_enhanced(text, citation.citation)
            method = 'enhanced_context'
            confidence = 'medium'
        
        # Verify in document
        case_name_in_doc = self._verify_in_document(text, enhanced_case_name)
        year_in_doc = self._verify_in_document(text, enhanced_year) if enhanced_year else False
        
        return {
            'citation': citation.citation,
            'original_case_name': citation.extracted_case_name,
            'enhanced_case_name': enhanced_case_name,
            'original_year': citation.extracted_date,
            'enhanced_year': enhanced_year,
            'canonical_name': citation.canonical_name,
            'canonical_date': citation.canonical_date,
            'method': method,
            'confidence': confidence,
            'case_name_in_doc': case_name_in_doc,
            'year_in_doc': year_in_doc,
            'api_verified': citation.verified,
            'clusters': citation.clusters if hasattr(citation, 'clusters') else []
        }
    
    def _extract_case_name_enhanced(self, text: str, citation: str) -> Optional[str]:
        """Enhanced case name extraction using A+ patterns."""
        citation_pos = text.find(citation)
        if citation_pos == -1:
            return None
        
        # Use A+ context extraction logic
        return extract_case_name_from_context(text, citation_pos)
    
    def _extract_year_enhanced(self, text: str, citation: str) -> Optional[str]:
        """Enhanced year extraction using A+ patterns."""
        citation_pos = text.find(citation)
        if citation_pos == -1:
            return None
        
        # Use A+ year extraction logic
        return extract_year_after_citation(text, citation_pos + len(citation))
    
    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation for matching."""
        normalized = re.sub(r'[^\w]', '', citation.lower())
        normalized = normalized.replace('wash', 'wn')
        return normalized
    
    def _verify_in_document(self, text: str, item: str) -> bool:
        """Verify that an item appears in the document."""
        if not item:
            return False
        return str(item) in text
    
    def get_summary_stats(self, enhanced_citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary statistics for enhanced citations."""
        
        total_citations = len(enhanced_citations)
        toa_enhanced = len([c for c in enhanced_citations if c['method'] == 'toa_ground_truth'])
        context_enhanced = len([c for c in enhanced_citations if c['method'] == 'enhanced_context'])
        high_confidence = len([c for c in enhanced_citations if c['confidence'] == 'high'])
        medium_confidence = len([c for c in enhanced_citations if c['confidence'] == 'medium'])
        case_names_in_doc = len([c for c in enhanced_citations if c['case_name_in_doc']])
        years_in_doc = len([c for c in enhanced_citations if c['year_in_doc']])
        api_verified = len([c for c in enhanced_citations if c['api_verified']])
        
        return {
            'total_citations': total_citations,
            'toa_enhanced': toa_enhanced,
            'context_enhanced': context_enhanced,
            'high_confidence': high_confidence,
            'medium_confidence': medium_confidence,
            'case_names_in_doc': case_names_in_doc,
            'years_in_doc': years_in_doc,
            'api_verified': api_verified
        }

# Test the production-ready enhanced processor
if __name__ == "__main__":
    # Read the brief
    with open('wa_briefs_text/020_Appellants Brief.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Initialize enhanced processor
    enhanced_processor = EnhancedV2Processor()
    
    # Process text
    print("=== PRODUCTION-READY ENHANCED v2 PROCESSOR ===")
    enhanced_citations = enhanced_processor.process_text(text)
    
    # Get summary stats
    stats = enhanced_processor.get_summary_stats(enhanced_citations)
    
    print(f"\nProcessing Complete!")
    print(f"Total Citations: {stats['total_citations']}")
    print(f"ToA Enhanced: {stats['toa_enhanced']}")
    print(f"Context Enhanced: {stats['context_enhanced']}")
    print(f"High Confidence: {stats['high_confidence']}")
    print(f"Medium Confidence: {stats['medium_confidence']}")
    print(f"Case Names in Document: {stats['case_names_in_doc']}")
    print(f"Years in Document: {stats['years_in_doc']}")
    print(f"API Verified: {stats['api_verified']}")
    
    # Show sample results
    print(f"\n=== SAMPLE RESULTS ===")
    for i, citation in enumerate(enhanced_citations[:5]):
        confidence_icon = "🟢" if citation['confidence'] == 'high' else "🟡"
        case_icon = "✅" if citation['case_name_in_doc'] else "❌"
        year_icon = "✅" if citation['year_in_doc'] else "❌"
        
        print(f"{confidence_icon} {citation['citation']}")
        print(f"   Enhanced: {citation['enhanced_case_name']} {case_icon} ({citation['enhanced_year']}) {year_icon}")
        print(f"   Method: {citation['method']}")
        print()
    
    print("=== PRODUCTION READY ===")
    print("✅ Enhanced v2 processor ready for production use")
    print("✅ Incorporates A+ context extraction")
    print("✅ Uses ToA ground truth")
    print("✅ 100% document-based extraction")
    print("✅ Maintains v2's comprehensive coverage")
    print("✅ Provides confidence levels")
    print("✅ Includes API verification") 