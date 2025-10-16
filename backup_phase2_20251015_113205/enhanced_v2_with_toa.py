from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.toa_parser import ImprovedToAParser
from a_plus_citation_processor import extract_citations_with_custom_logic
import re

class EnhancedV2Processor:
    """Enhanced v2 processor that uses ToA data to improve extraction accuracy."""
    
    def __init__(self):
        self.v2 = UnifiedCitationProcessorV2()
        self.toa_parser = ImprovedToAParser()
    
    def process_text_with_toa_enhancement(self, text: str):
        """Process text using v2 but enhance with ToA data."""
        
        # Step 1: Extract ToA data as ground truth
        print("=== Step 1: Extracting ToA Ground Truth ===")
        toa_entries = self.toa_parser.parse_toa_section_simple(text)
        toa_ground_truth = {}
        
        for entry in toa_entries:
            for citation in entry.citations:
                # Normalize citation for matching
                normalized_citation = self._normalize_citation(citation)
                toa_ground_truth[normalized_citation] = {
                    'case_name': entry.case_name,
                    'year': entry.years[0] if entry.years else None
                }
        
        print(f"Found {len(toa_ground_truth)} ToA entries as ground truth")
        for citation, data in toa_ground_truth.items():
            print(f"  {citation} -> {data['case_name']} ({data['year']})")
        
        # Step 2: Extract citations with v2
        print("\n=== Step 2: Extracting Citations with v2 ===")
        v2_citations = self.v2.process_text(text)
        
        # Step 3: Enhance v2 results with ToA data
        print("\n=== Step 3: Enhancing v2 Results with ToA Data ===")
        enhanced_citations = []
        
        for citation in v2_citations:
            normalized_citation = self._normalize_citation(citation.citation)
            
            # Check if we have ToA ground truth for this citation
            if normalized_citation in toa_ground_truth:
                toa_data = toa_ground_truth[normalized_citation]
                
                # Enhance the citation with ToA data
                enhanced_citation = citation
                enhanced_citation.extracted_case_name = toa_data['case_name']
                enhanced_citation.extracted_date = toa_data['year']
                enhanced_citation.canonical_name = toa_data['case_name']  # Use ToA as canonical
                enhanced_citation.canonical_date = toa_data['year']
                enhanced_citation.verified = True
                enhanced_citation.method = "v2_enhanced_with_toa"
                
                print(f"✅ Enhanced: {citation.citation} -> {toa_data['case_name']} ({toa_data['year']})")
            else:
                print(f"⚠️  No ToA match: {citation.citation} -> {citation.extracted_case_name} ({citation.extracted_date})")
            
            enhanced_citations.append(citation)
        
        return enhanced_citations, toa_ground_truth
    
    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation for matching."""
        # Remove spaces and punctuation, convert to lowercase
        normalized = re.sub(r'[^\w]', '', citation.lower())
        # Handle common variations
        normalized = normalized.replace('wash', 'wn')
        normalized = normalized.replace('p2d', 'p2d')
        normalized = normalized.replace('p3d', 'p3d')
        return normalized
    
    def compare_extraction_methods(self, text: str):
        """Compare v2, A+, and enhanced v2 results."""
        
        print("=== Comparing Extraction Methods ===\n")
        
        # Method 1: Standard v2
        print("1. Standard v2:")
        v2_citations = self.v2.process_text(text)
        v2_case_names = [c.extracted_case_name for c in v2_citations if c.extracted_case_name]
        print(f"   Found {len(v2_case_names)} case names")
        
        # Method 2: A+ (ToA only)
        print("\n2. A+ (ToA only):")
        aplus_citations = extract_citations_with_custom_logic(text)
        aplus_case_names = [c['case_name'] for c in aplus_citations if c['case_name']]
        print(f"   Found {len(aplus_case_names)} case names")
        
        # Method 3: Enhanced v2 with ToA
        print("\n3. Enhanced v2 with ToA:")
        enhanced_citations, toa_truth = self.process_text_with_toa_enhancement(text)
        enhanced_case_names = [c.extracted_case_name for c in enhanced_citations if c.extracted_case_name]
        print(f"   Found {len(enhanced_case_names)} case names")
        
        # Show overlap
        print(f"\n=== Overlap Analysis ===")
        v2_set = set(v2_case_names)
        aplus_set = set(aplus_case_names)
        enhanced_set = set(enhanced_case_names)
        
        print(f"v2 ∩ A+: {len(v2_set & aplus_set)}")
        print(f"Enhanced ∩ A+: {len(enhanced_set & aplus_set)}")
        print(f"Enhanced ∩ v2: {len(enhanced_set & v2_set)}")
        
        return {
            'v2': v2_citations,
            'aplus': aplus_citations,
            'enhanced': enhanced_citations,
            'toa_ground_truth': toa_truth
        }

# Test the enhanced processor
if __name__ == "__main__":
    # Read the brief
    with open('wa_briefs_text/020_Appellants Brief.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    
    enhanced_processor = EnhancedV2Processor()
    results = enhanced_processor.compare_extraction_methods(text)
    
    print(f"\n=== Summary ===")
    print("Enhanced v2 with ToA provides:")
    print("- Better case name accuracy using ToA as ground truth")
    print("- More comprehensive coverage (v2 finds more citations)")
    print("- Verified canonical names from ToA")
    print("- Fallback to v2's context extraction for non-ToA citations") 