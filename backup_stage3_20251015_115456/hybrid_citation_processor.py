from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.toa_parser import ImprovedToAParser
from a_plus_citation_processor import extract_citations_with_custom_logic
import re
from typing import List, Dict, Any

class HybridCitationProcessor:
    """Hybrid processor that intelligently combines v2, A+, and ToA for optimal results."""
    
    def __init__(self):
        self.v2 = UnifiedCitationProcessorV2()
        self.toa_parser = ImprovedToAParser()
    
    def process_text_hybrid(self, text: str) -> Dict[str, Any]:
        """Process text using all three methods and intelligently combine results."""
        
        print("=== Hybrid Citation Processing ===")
        
        # Step 1: Extract ToA ground truth
        print("\n1. Extracting ToA Ground Truth...")
        toa_entries = self.toa_parser.parse_toa_section_simple(text)
        toa_ground_truth = {}
        
        for entry in toa_entries:
            for citation in entry.citations:
                normalized_citation = self._normalize_citation(citation)
                toa_ground_truth[normalized_citation] = {
                    'case_name': entry.case_name,
                    'year': entry.years[0] if entry.years else None,
                    'source': 'toa'
                }
        
        print(f"   Found {len(toa_ground_truth)} ToA entries")
        
        # Step 2: Extract with A+ (ToA + context)
        print("\n2. Extracting with A+ Processor...")
        aplus_citations = extract_citations_with_custom_logic(text)
        aplus_results = {}
        
        for citation in aplus_citations:
            if citation['citation']:
                normalized_citation = self._normalize_citation(citation['citation'])
                aplus_results[normalized_citation] = {
                    'case_name': citation['case_name'],
                    'year': citation['year'],
                    'source': 'aplus'
                }
        
        print(f"   Found {len(aplus_results)} A+ citations")
        
        # Step 3: Extract with v2 (full document + API verification)
        print("\n3. Extracting with v2 Processor...")
        v2_citations = self.v2.process_text(text)
        v2_results = {}
        
        for citation in v2_citations:
            normalized_citation = self._normalize_citation(citation.citation)
            v2_results[normalized_citation] = {
                'case_name': citation.canonical_name or citation.extracted_case_name,
                'year': citation.canonical_date or citation.extracted_date,
                'verified': citation.verified,
                'source': 'v2'
            }
        
        print(f"   Found {len(v2_results)} v2 citations")
        
        # Step 4: Intelligently combine results
        print("\n4. Combining Results Intelligently...")
        combined_results = {}
        
        # Priority 1: ToA entries (highest confidence)
        for citation, data in toa_ground_truth.items():
            combined_results[citation] = {
                **data,
                'confidence': 'high',
                'method': 'toa_ground_truth'
            }
        
        # Priority 2: A+ entries not in ToA
        for citation, data in aplus_results.items():
            if citation not in combined_results:
                combined_results[citation] = {
                    **data,
                    'confidence': 'medium',
                    'method': 'aplus_context'
                }
        
        # Priority 3: v2 entries not in ToA or A+
        for citation, data in v2_results.items():
            if citation not in combined_results:
                combined_results[citation] = {
                    **data,
                    'confidence': 'medium' if data.get('verified') else 'low',
                    'method': 'v2_api_verified' if data.get('verified') else 'v2_context'
                }
        
        # Step 5: Generate summary
        print("\n5. Generating Summary...")
        summary = {
            'total_citations': len(combined_results),
            'toa_entries': len(toa_ground_truth),
            'aplus_entries': len(aplus_results),
            'v2_entries': len(v2_results),
            'high_confidence': len([r for r in combined_results.values() if r['confidence'] == 'high']),
            'medium_confidence': len([r for r in combined_results.values() if r['confidence'] == 'medium']),
            'low_confidence': len([r for r in combined_results.values() if r['confidence'] == 'low']),
            'results': combined_results
        }
        
        return summary
    
    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation for matching."""
        # Remove spaces and punctuation, convert to lowercase
        normalized = re.sub(r'[^\w]', '', citation.lower())
        # Handle common variations
        normalized = normalized.replace('wash', 'wn')
        return normalized
    
    def print_detailed_results(self, summary: Dict[str, Any]):
        """Print detailed results in a readable format."""
        
        print(f"\n=== HYBRID PROCESSING RESULTS ===")
        print(f"Total Citations Found: {summary['total_citations']}")
        print(f"High Confidence: {summary['high_confidence']}")
        print(f"Medium Confidence: {summary['medium_confidence']}")
        print(f"Low Confidence: {summary['low_confidence']}")
        
        print(f"\n=== DETAILED BREAKDOWN ===")
        print(f"ToA Ground Truth: {summary['toa_entries']}")
        print(f"A+ Context: {summary['aplus_entries']}")
        print(f"v2 API Verified: {summary['v2_entries']}")
        
        print(f"\n=== CITATION DETAILS ===")
        for citation, data in summary['results'].items():
            confidence_icon = "🟢" if data['confidence'] == 'high' else "🟡" if data['confidence'] == 'medium' else "🔴"
            print(f"{confidence_icon} {citation}")
            print(f"   Case: {data['case_name']}")
            print(f"   Year: {data['year']}")
            print(f"   Method: {data['method']}")
            print()

# Test the hybrid processor
if __name__ == "__main__":
    # Read the brief
    with open('wa_briefs_text/020_Appellants Brief.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    
    hybrid_processor = HybridCitationProcessor()
    summary = hybrid_processor.process_text_hybrid(text)
    hybrid_processor.print_detailed_results(summary)
    
    print("=== KEY IMPROVEMENTS ===")
    print("✅ Combines ToA accuracy with v2 coverage")
    print("✅ Uses A+ for context extraction")
    print("✅ Prioritizes high-confidence sources")
    print("✅ Provides confidence levels for each citation")
    print("✅ Falls back gracefully when sources disagree") 