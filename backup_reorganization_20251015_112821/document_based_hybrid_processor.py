from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.toa_parser import ImprovedToAParser
from a_plus_citation_processor import extract_citations_with_custom_logic
import re
from typing import List, Dict, Any

class DocumentBasedHybridProcessor:
    """Document-based hybrid processor that ensures case names and years come from the user's document."""
    
    def __init__(self):
        self.v2 = UnifiedCitationProcessorV2()
        self.toa_parser = ImprovedToAParser()
    
    def process_text_document_based(self, text: str) -> Dict[str, Any]:
        """Process text ensuring case names and years come from the document."""
        
        print("=== Document-Based Hybrid Processing ===")
        
        # Step 1: Extract ToA ground truth (from document)
        print("\n1. Extracting ToA Ground Truth from Document...")
        toa_entries = self.toa_parser.parse_toa_section_simple(text)
        toa_ground_truth = {}
        
        for entry in toa_entries:
            for citation in entry.citations:
                normalized_citation = self._normalize_citation(citation)
                toa_ground_truth[normalized_citation] = {
                    'case_name': entry.case_name,
                    'year': entry.years[0] if entry.years else None,
                    'source': 'toa_document',
                    'confidence': 'high'
                }
        
        print(f"   Found {len(toa_ground_truth)} ToA entries from document")
        
        # Step 2: Extract with A+ (document-based context extraction)
        print("\n2. Extracting with A+ (Document Context)...")
        aplus_citations = extract_citations_with_custom_logic(text)
        aplus_results = {}
        
        for citation in aplus_citations:
            if citation['citation'] and citation['case_name']:
                normalized_citation = self._normalize_citation(citation['citation'])
                aplus_results[normalized_citation] = {
                    'case_name': citation['case_name'],
                    'year': citation['year'],
                    'source': 'aplus_document_context',
                    'confidence': 'medium'
                }
        
        print(f"   Found {len(aplus_results)} A+ citations from document context")
        
        # Step 3: Extract with v2 (document-based extraction only)
        print("\n3. Extracting with v2 (Document-Based Only)...")
        v2_citations = self.v2.process_text(text)
        v2_results = {}
        
        for citation in v2_citations:
            normalized_citation = self._normalize_citation(citation.citation)
            
            # Only use document-based extracted data, not API canonical data
            case_name = citation.extracted_case_name  # From document context
            year = citation.extracted_date  # From document context
            
            if case_name:  # Only include if we found a case name in the document
                v2_results[normalized_citation] = {
                    'case_name': case_name,
                    'year': year,
                    'source': 'v2_document_context',
                    'confidence': 'medium' if citation.verified else 'low',
                    'api_verified': citation.verified
                }
        
        print(f"   Found {len(v2_results)} v2 citations with document-based case names")
        
        # Step 4: Intelligently combine document-based results
        print("\n4. Combining Document-Based Results...")
        combined_results = {}
        
        # Priority 1: ToA entries (highest confidence, from document)
        for citation, data in toa_ground_truth.items():
            combined_results[citation] = {
                **data,
                'method': 'toa_document_ground_truth'
            }
        
        # Priority 2: A+ entries not in ToA (from document context)
        for citation, data in aplus_results.items():
            if citation not in combined_results:
                combined_results[citation] = {
                    **data,
                    'method': 'aplus_document_context'
                }
        
        # Priority 3: v2 entries not in ToA or A+ (from document context)
        for citation, data in v2_results.items():
            if citation not in combined_results:
                combined_results[citation] = {
                    **data,
                    'method': 'v2_document_context'
                }
        
        # Step 5: Verify all case names appear in document
        print("\n5. Verifying Case Names Appear in Document...")
        verified_results = {}
        
        for citation, data in combined_results.items():
            case_name = data['case_name']
            year = data['year']
            
            # Check if case name appears in document
            case_name_in_doc = self._verify_case_name_in_document(text, case_name)
            year_in_doc = self._verify_year_in_document(text, year) if year else False
            
            if case_name_in_doc:
                verified_results[citation] = {
                    **data,
                    'case_name_verified_in_doc': True,
                    'year_verified_in_doc': year_in_doc
                }
            else:
                print(f"   ⚠️  Case name '{case_name}' not found in document for citation {citation}")
        
        # Step 6: Generate summary
        print("\n6. Generating Summary...")
        summary = {
            'total_citations': len(verified_results),
            'toa_entries': len([r for r in verified_results.values() if r['source'] == 'toa_document']),
            'aplus_entries': len([r for r in verified_results.values() if r['source'] == 'aplus_document_context']),
            'v2_entries': len([r for r in verified_results.values() if r['source'] == 'v2_document_context']),
            'high_confidence': len([r for r in verified_results.values() if r['confidence'] == 'high']),
            'medium_confidence': len([r for r in verified_results.values() if r['confidence'] == 'medium']),
            'low_confidence': len([r for r in verified_results.values() if r['confidence'] == 'low']),
            'case_names_verified': len([r for r in verified_results.values() if r['case_name_verified_in_doc']]),
            'years_verified': len([r for r in verified_results.values() if r.get('year_verified_in_doc', False)]),
            'results': verified_results
        }
        
        return summary
    
    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation for matching."""
        normalized = re.sub(r'[^\w]', '', citation.lower())
        normalized = normalized.replace('wash', 'wn')
        return normalized
    
    def _verify_case_name_in_document(self, text: str, case_name: str) -> bool:
        """Verify that a case name appears in the document."""
        if not case_name:
            return False
        
        # Normalize both for comparison
        normalized_case_name = re.sub(r'[^\w\s]', '', case_name.lower())
        normalized_text = re.sub(r'[^\w\s]', '', text.lower())
        
        # Check if case name appears in document
        return normalized_case_name in normalized_text
    
    def _verify_year_in_document(self, text: str, year: str) -> bool:
        """Verify that a year appears in the document."""
        if not year:
            return False
        
        # Look for the year in the document
        return str(year) in text
    
    def print_detailed_results(self, summary: Dict[str, Any]):
        """Print detailed results in a readable format."""
        
        print(f"\n=== DOCUMENT-BASED HYBRID RESULTS ===")
        print(f"Total Citations Found: {summary['total_citations']}")
        print(f"High Confidence: {summary['high_confidence']}")
        print(f"Medium Confidence: {summary['medium_confidence']}")
        print(f"Low Confidence: {summary['low_confidence']}")
        print(f"Case Names Verified in Document: {summary['case_names_verified']}")
        print(f"Years Verified in Document: {summary['years_verified']}")
        
        print(f"\n=== DETAILED BREAKDOWN ===")
        print(f"ToA Document: {summary['toa_entries']}")
        print(f"A+ Document Context: {summary['aplus_entries']}")
        print(f"v2 Document Context: {summary['v2_entries']}")
        
        print(f"\n=== CITATION DETAILS (Document-Based) ===")
        for citation, data in summary['results'].items():
            confidence_icon = "🟢" if data['confidence'] == 'high' else "🟡" if data['confidence'] == 'medium' else "🔴"
            case_verified = "✅" if data['case_name_verified_in_doc'] else "❌"
            year_verified = "✅" if data.get('year_verified_in_doc', False) else "❌"
            
            print(f"{confidence_icon} {citation}")
            print(f"   Case: {data['case_name']} {case_verified}")
            print(f"   Year: {data['year']} {year_verified}")
            print(f"   Method: {data['method']}")
            print()

# Test the document-based hybrid processor
if __name__ == "__main__":
    # Read the brief
    with open('wa_briefs_text/020_Appellants Brief.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    
    doc_processor = DocumentBasedHybridProcessor()
    summary = doc_processor.process_text_document_based(text)
    doc_processor.print_detailed_results(summary)
    
    print("=== KEY FEATURES ===")
    print("✅ All case names and years come from the document")
    print("✅ ToA provides authoritative document-based ground truth")
    print("✅ A+ extracts from document context around citations")
    print("✅ v2 uses document context, not external API data")
    print("✅ Verification ensures everything appears in the document")
    print("✅ No external data used for case names/years") 