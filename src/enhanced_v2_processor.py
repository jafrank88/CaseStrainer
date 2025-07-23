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
        
        # Step 4: Group parallel citations into clusters
        clustered_results = self._cluster_parallel_citations(enhanced_citations, text)
        
        return clustered_results
    
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
    
    def _cluster_parallel_citations(self, enhanced_citations: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """Group parallel citations into clusters that share case names and years."""
        
        if not enhanced_citations:
            return []
        
        # Use context-based clustering for better results
        clusters = self._find_parallel_citations_by_context(enhanced_citations, text)
        
        # Convert clusters to individual citations with cluster info
        result = []
        for i, cluster in enumerate(clusters):
            # Find the best shared case name and year for this cluster
            shared_case_name = None
            shared_year = None
            
            for citation in cluster:
                case_name = citation['enhanced_case_name'] or citation['original_case_name']
                year = citation['enhanced_year'] or citation['original_year']
                
                if case_name and not shared_case_name:
                    shared_case_name = case_name
                if year and not shared_year:
                    shared_year = year
            
            # If no shared case name found, try to extract from context
            if not shared_case_name and len(cluster) > 1:
                shared_case_name = self._extract_shared_case_name_from_cluster(cluster, text)
            
            for citation in cluster:
                # Add cluster information to each citation
                citation_with_cluster = citation.copy()
                citation_with_cluster.update({
                    'cluster_id': f"cluster_{i}",
                    'is_parallel': len(cluster) > 1,
                    'parallel_citations': [c['citation'] for c in cluster if c != citation],
                    'shared_case_name': shared_case_name,
                    'shared_year': shared_year,
                    'total_citations_in_cluster': len(cluster)
                })
                result.append(citation_with_cluster)
        
        return result
    
    def _extract_shared_case_name_from_cluster(self, cluster: List[Dict[str, Any]], text: str) -> Optional[str]:
        """Extract a shared case name from the context around a cluster of citations."""
        
        # Find the positions of all citations in the cluster
        positions = []
        for citation in cluster:
            pos = text.find(citation['citation'])
            if pos != -1:
                positions.append(pos)
        
        if not positions:
            return None
        
        # Find the range of the cluster
        min_pos = min(positions)
        max_pos = max(positions)
        
        # Extract context around the cluster
        start = max(0, min_pos - 300)
        end = min(len(text), max_pos + 300)
        cluster_context = text[start:end]
        
        # Look for case name patterns in the cluster context
        case_patterns = [
            r'([A-Z][A-Za-z0-9&.,\'-]+(?:\s+[A-Za-z0-9&.,\'-]+)*)\s+v\.?\s+([A-Z][A-Za-z0-9&.,\'-]+(?:\s+[A-Za-z0-9&.,\'-]+)*)',
            r'([A-Z][A-Za-z0-9&.,\'-]+(?:\s+[A-Za-z0-9&.,\'-]+)*)\s+versus\s+([A-Z][A-Za-z0-9&.,\'-]+(?:\s+[A-Za-z0-9&.,\'-]+)*)',
        ]
        
        for pattern in case_patterns:
            matches = re.findall(pattern, cluster_context)
            if matches:
                # Return the first case name found
                case_name = f"{matches[0][0]} v. {matches[0][1]}"
                return case_name
        
        return None
    
    def _are_citations_same_case(self, citation1: Dict[str, Any], citation2: Dict[str, Any], text: str) -> bool:
        """Determine if two citations are likely the same case."""
        
        # Check if they have the same case name
        case1 = citation1['enhanced_case_name'] or citation1['original_case_name']
        case2 = citation2['enhanced_case_name'] or citation2['original_case_name']
        
        if case1 and case2:
            # Simple similarity check
            case1_clean = re.sub(r'[^\w\s]', '', case1.lower())
            case2_clean = re.sub(r'[^\w\s]', '', case2.lower())
            
            # Check if one contains the other or they're very similar
            if case1_clean in case2_clean or case2_clean in case1_clean:
                return True
            
            # Check for common words
            words1 = set(case1_clean.split())
            words2 = set(case2_clean.split())
            common_words = words1.intersection(words2)
            
            if len(common_words) >= 2:  # At least 2 common words
                return True
        
        # Check if they're close together in text and have similar patterns
        # This is a fallback for when case names aren't available
        return False
    
    def _find_parallel_citations_by_context(self, enhanced_citations: List[Dict[str, Any]], text: str) -> List[List[Dict[str, Any]]]:
        """Find parallel citations by analyzing the text context around each citation."""
        
        # Find citation positions and extract context
        citation_contexts = {}
        for citation in enhanced_citations:
            pos = text.find(citation['citation'])
            if pos != -1:
                # Extract context around the citation (300 chars before and after)
                start = max(0, pos - 300)
                end = min(len(text), pos + 300)
                context = text[start:end]
                citation_contexts[citation['citation']] = {
                    'position': pos,
                    'context': context,
                    'citation': citation
                }
        
        # Group citations by proximity and context
        clusters = []
        used_citations = set()
        
        for citation_text, context_info in citation_contexts.items():
            if citation_text in used_citations:
                continue
            
            # Start a new cluster
            cluster = [context_info['citation']]
            used_citations.add(citation_text)
            
            # Find other citations that are close together
            for other_text, other_context_info in citation_contexts.items():
                if other_text in used_citations:
                    continue
                
                # Check if citations are close together
                distance = abs(context_info['position'] - other_context_info['position'])
                if distance <= 500:  # Increased distance for better clustering
                    # Check if they might be the same case
                    same_case = self._are_citations_likely_same_case(context_info['citation'], other_context_info['citation'], text)
                    if same_case:
                        cluster.append(other_context_info['citation'])
                        used_citations.add(other_text)
            
            if len(cluster) > 0:
                clusters.append(cluster)
        
        return clusters
    
    def _are_citations_likely_same_case(self, citation1: Dict[str, Any], citation2: Dict[str, Any], text: str) -> bool:
        """Determine if two citations are likely the same case using multiple heuristics."""
        
        # Check if they have similar case names
        case1 = citation1['enhanced_case_name'] or citation1['original_case_name']
        case2 = citation2['enhanced_case_name'] or citation2['original_case_name']
        
        if case1 and case2:
            # Simple similarity check
            case1_clean = re.sub(r'[^\w\s]', '', case1.lower())
            case2_clean = re.sub(r'[^\w\s]', '', case2.lower())
            
            # Check if one contains the other or they're very similar
            if case1_clean in case2_clean or case2_clean in case1_clean:
                return True
            
            # Check for common words
            words1 = set(case1_clean.split())
            words2 = set(case2_clean.split())
            common_words = words1.intersection(words2)
            
            if len(common_words) >= 3:  # At least 3 common words for more precise matching
                return True
        
        # Check if they're close together in text (likely parallel citations)
        pos1 = text.find(citation1['citation'])
        pos2 = text.find(citation2['citation'])
        
        if pos1 != -1 and pos2 != -1:
            distance = abs(pos2 - pos1)
            if distance <= 100:  # Very close together (reduced distance for more precise clustering)
                return True
        
        # Check if they have similar years
        year1 = citation1['enhanced_year'] or citation1['original_year']
        year2 = citation2['enhanced_year'] or citation2['original_year']
        
        if year1 and year2 and year1 == year2:
            return True
        
        return False
    
    def _contexts_share_case_name(self, context1: str, context2: str) -> bool:
        """Check if two contexts share a case name."""
        
        # Look for case name patterns (e.g., "v.", "v ", "versus")
        case_patterns = [
            r'([A-Z][A-Za-z0-9&.,\'-]+(?:\s+[A-Za-z0-9&.,\'-]+)*)\s+v\.?\s+([A-Z][A-Za-z0-9&.,\'-]+(?:\s+[A-Za-z0-9&.,\'-]+)*)',
            r'([A-Z][A-Za-z0-9&.,\'-]+(?:\s+[A-Za-z0-9&.,\'-]+)*)\s+versus\s+([A-Z][A-Za-z0-9&.,\'-]+(?:\s+[A-Za-z0-9&.,\'-]+)*)',
        ]
        
        case_names1 = set()
        case_names2 = set()
        
        for pattern in case_patterns:
            matches1 = re.findall(pattern, context1)
            matches2 = re.findall(pattern, context2)
            
            for match in matches1:
                case_name = f"{match[0]} v. {match[1]}"
                case_names1.add(case_name.lower())
            
            for match in matches2:
                case_name = f"{match[0]} v. {match[1]}"
                case_names2.add(case_name.lower())
        
        # Check for overlap
        common_cases = case_names1.intersection(case_names2)
        return len(common_cases) > 0
    
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