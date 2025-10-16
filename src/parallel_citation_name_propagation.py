"""
Parallel Citation Case Name Propagation

Improves extracted_case_name accuracy by propagating case names to parallel citations.

Problem: When citations appear together, only the first has context:
  "State v. Johnson, 159 Wn.2d 700, 153 P.3d 846 (2007)"
                      ↑ has name        ↑ no name

Solution: Propagate "State v. Johnson" to both citations.
"""
import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CitationContext:
    """Represents a citation with its position in text"""
    citation: str
    case_name: Optional[str]
    start_pos: int
    end_pos: int
    reporter: str
    

class ParallelCitationPropagator:
    """
    Propagates case names to parallel citations that lack them.
    
    Strategy:
    1. Find citations that are close together (within 100 chars)
    2. If one has a case name and others don't, propagate it
    3. Verify they're truly parallel (similar context, same sentence)
    """
    
    def __init__(self):
        self.proximity_threshold = 100  # chars between citations
        self.same_sentence_threshold = 150  # chars for same sentence
        
    def propagate_case_names(
        self, 
        citations: List[Dict[str, Any]], 
        original_text: str
    ) -> List[Dict[str, Any]]:
        """
        Main method: propagate case names to parallel citations.
        
        Args:
            citations: List of citation dicts with 'citation', 'extracted_case_name', etc.
            original_text: The original document text
            
        Returns:
            Updated citations list with propagated case names
        """
        logger.info(f"[PROPAGATION] Starting parallel citation name propagation for {len(citations)} citations")
        
        # Build citation contexts with positions
        contexts = self._build_citation_contexts(citations, original_text)
        
        if not contexts:
            logger.warning("[PROPAGATION] No citation positions found in text")
            return citations
        
        # Find parallel citation groups
        groups = self._find_parallel_groups(contexts)
        
        logger.info(f"[PROPAGATION] Found {len(groups)} parallel citation groups")
        
        # Propagate case names within each group
        propagated_count = 0
        for group in groups:
            propagated_count += self._propagate_within_group(group, citations)
        
        logger.info(f"[PROPAGATION] Propagated case names to {propagated_count} citations")
        
        return citations
    
    def _build_citation_contexts(
        self, 
        citations: List[Dict[str, Any]], 
        text: str
    ) -> List[CitationContext]:
        """Build citation contexts with positions in text"""
        contexts = []
        
        for cite_dict in citations:
            citation = cite_dict.get('citation', '')
            case_name = cite_dict.get('extracted_case_name')
            
            # Find citation position in text
            # Clean citation for matching
            clean_cite = citation.replace('.', r'\.').replace('(', r'\(').replace(')', r'\)')
            pattern = re.escape(citation)
            
            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                # Try with spaces normalized
                normalized = ' '.join(citation.split())
                pattern = re.escape(normalized)
                match = re.search(pattern, text, re.IGNORECASE)
            
            if match:
                reporter = self._extract_reporter(citation)
                contexts.append(CitationContext(
                    citation=citation,
                    case_name=case_name if case_name and case_name != 'N/A' else None,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    reporter=reporter
                ))
        
        # Sort by position
        contexts.sort(key=lambda c: c.start_pos)
        
        return contexts
    
    def _extract_reporter(self, citation: str) -> str:
        """Extract reporter abbreviation from citation"""
        # Match common reporter patterns
        reporter_pattern = r'\b([A-Z][A-Za-z]*\.(?:\s*[A-Z][A-Za-z]*\.)*(?:\s*\d[a-z]{2})?)\b'
        match = re.search(reporter_pattern, citation)
        if match:
            return match.group(1)
        return ""
    
    def _find_parallel_groups(
        self, 
        contexts: List[CitationContext]
    ) -> List[List[CitationContext]]:
        """Find groups of parallel citations"""
        groups = []
        i = 0
        
        while i < len(contexts):
            # Start a new group
            current_group = [contexts[i]]
            j = i + 1
            
            # Look ahead for nearby citations
            while j < len(contexts):
                distance = contexts[j].start_pos - contexts[i].end_pos
                
                if distance <= self.proximity_threshold:
                    # Check if they're in the same sentence
                    if distance <= self.same_sentence_threshold:
                        current_group.append(contexts[j])
                        j += 1
                    else:
                        break
                else:
                    break
            
            # Only keep groups with 2+ citations
            if len(current_group) >= 2:
                groups.append(current_group)
            
            i = j if j > i + 1 else i + 1
        
        return groups
    
    def _propagate_within_group(
        self, 
        group: List[CitationContext],
        citations: List[Dict[str, Any]]
    ) -> int:
        """
        Propagate case name within a parallel citation group.
        
        Returns:
            Number of citations that received propagated names
        """
        # Find the citation with a case name
        source_name = None
        for ctx in group:
            if ctx.case_name:
                source_name = ctx.case_name
                break
        
        if not source_name:
            return 0
        
        # Propagate to citations without names
        propagated = 0
        for ctx in group:
            if not ctx.case_name:
                # Find this citation in the original list and update it
                for cite_dict in citations:
                    if cite_dict.get('citation') == ctx.citation:
                        old_name = cite_dict.get('extracted_case_name')
                        if not old_name or old_name == 'N/A':
                            cite_dict['extracted_case_name'] = source_name
                            cite_dict['propagated_from_parallel'] = True
                            logger.info(f"[PROPAGATION] {ctx.citation} ← {source_name}")
                            propagated += 1
                            break
        
        return propagated


def propagate_parallel_case_names(
    citations: List[Dict[str, Any]], 
    original_text: str
) -> List[Dict[str, Any]]:
    """
    Convenience function for parallel citation case name propagation.
    
    Args:
        citations: List of citation dicts
        original_text: Original document text
        
    Returns:
        Updated citations with propagated case names
    """
    propagator = ParallelCitationPropagator()
    return propagator.propagate_case_names(citations, original_text)
