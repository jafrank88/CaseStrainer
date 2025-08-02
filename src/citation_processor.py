"""
Citation Processor

This module contains citation processing and clustering logic, including
parallel citation detection and citation grouping.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from src.models import CitationResult
from src.citation_types import CitationList, CitationDict
from src.citation_utils import (
    normalize_case_name_for_clustering, is_similar_citation, 
    is_similar_date, calculate_similarity, deduplicate_citations,
    extract_context, is_valid_case_name
)

logger = logging.getLogger(__name__)

class CitationProcessor:
    """Citation processing and clustering functionality."""
    
    def __init__(self):
        self._init_state_reporter_mapping()
    
    def _init_state_reporter_mapping(self):
        """Initialize state-reporter mappings."""
        self.state_reporter_mapping = {
            'P.': ['California', 'Pennsylvania'],
            'N.W.': ['Iowa', 'Michigan', 'Minnesota', 'Nebraska', 'North Dakota', 'South Dakota', 'Wisconsin'],
            'S.W.': ['Arkansas', 'Kentucky', 'Missouri', 'Tennessee', 'Texas'],
            'N.E.': ['Illinois', 'Indiana', 'Massachusetts', 'New York', 'Ohio'],
            'S.E.': ['Georgia', 'North Carolina', 'South Carolina', 'Virginia', 'West Virginia'],
            'A.': ['Alaska', 'Arizona', 'Colorado', 'Connecticut', 'Delaware', 'Hawaii', 'Idaho', 'Kansas', 'Maine', 'Maryland', 'Montana', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'Oklahoma', 'Oregon', 'Rhode Island', 'Utah', 'Vermont', 'Washington', 'Wyoming'],
            'So.': ['Alabama', 'Florida', 'Louisiana', 'Mississippi'],
        }
    
    def detect_parallel_citations(self, citations: CitationList, text: str) -> CitationList:
        """Detect and group parallel citations."""
        if not citations or len(citations) < 2:
            return citations
        
        # Group citations by similarity
        groups = self._group_similar_citations(citations)
        
        # Process each group
        processed_citations = []
        for group in groups:
            if len(group) > 1:
                # This is a group of parallel citations
                processed_group = self._process_parallel_group(group, text)
                processed_citations.extend(processed_group)
            else:
                # Single citation
                processed_citations.extend(group)
        
        return processed_citations
    
    def _group_similar_citations(self, citations: CitationList) -> List[CitationList]:
        """Group citations by similarity."""
        if not citations:
            return []
        
        groups = []
        used = set()
        
        for i, citation1 in enumerate(citations):
            if i in used:
                continue
            
            group = [citation1]
            used.add(i)
            
            for j, citation2 in enumerate(citations[i+1:], i+1):
                if j in used:
                    continue
                
                if self._are_citations_same_case(citation1, citation2):
                    group.append(citation2)
                    used.add(j)
            
            groups.append(group)
        
        return groups
    
    def _are_citations_same_case(self, citation1: CitationResult, citation2: CitationResult) -> bool:
        """Check if two citations refer to the same case."""
        if not citation1 or not citation2:
            return False
        
        # Check if they have the same extracted case name
        name1 = getattr(citation1, 'extracted_case_name', '')
        name2 = getattr(citation2, 'extracted_case_name', '')
        
        if name1 and name2:
            normalized1 = normalize_case_name_for_clustering(name1)
            normalized2 = normalize_case_name_for_clustering(name2)
            
            if normalized1 == normalized2:
                return True
        
        # Check if citation texts are similar
        if is_similar_citation(citation1.citation, citation2.citation):
            return True
        
        # Check if dates are similar
        date1 = getattr(citation1, 'extracted_date', '')
        date2 = getattr(citation2, 'extracted_date', '')
        
        if date1 and date2 and is_similar_date(date1, date2):
            return True
        
        return False
    
    def _process_parallel_group(self, group: CitationList, text: str) -> CitationList:
        """Process a group of parallel citations."""
        if not group:
            return []
        
        # Find the best citation in the group (highest confidence or most complete)
        best_citation = self._select_best_citation(group)
        
        # Propagate information from best citation to others
        if best_citation:
            for citation in group:
                if citation != best_citation:
                    self._propagate_canonical_info(best_citation, citation)
        
        return group
    
    def _select_best_citation(self, group: CitationList) -> Optional[CitationResult]:
        """Select the best citation from a group based on confidence and completeness."""
        if not group:
            return None
        
        best_citation = group[0]
        best_score = self._calculate_citation_score(best_citation)
        
        for citation in group[1:]:
            score = self._calculate_citation_score(citation)
            if score > best_score:
                best_score = score
                best_citation = citation
        
        return best_citation
    
    def _calculate_citation_score(self, citation: CitationResult) -> float:
        """Calculate a score for citation quality."""
        score = 0.0
        
        # Base confidence
        score += getattr(citation, 'confidence', 0.0)
        
        # Bonus for verification
        if getattr(citation, 'verified', False):
            score += 0.5
        
        # Bonus for having canonical information
        if getattr(citation, 'canonical_name', None):
            score += 0.3
        
        if getattr(citation, 'canonical_date', None):
            score += 0.2
        
        # Bonus for having extracted information
        if getattr(citation, 'extracted_case_name', None):
            score += 0.2
        
        if getattr(citation, 'extracted_date', None):
            score += 0.1
        
        return score
    
    def _propagate_canonical_info(self, source: CitationResult, target: CitationResult):
        """Propagate canonical information from source to target citation."""
        if not source or not target:
            return
        
        # Propagate canonical name
        if getattr(source, 'canonical_name', None) and not getattr(target, 'canonical_name', None):
            target.canonical_name = source.canonical_name
        
        # Propagate canonical date
        if getattr(source, 'canonical_date', None) and not getattr(target, 'canonical_date', None):
            target.canonical_date = source.canonical_date
        
        # Propagate URL
        if getattr(source, 'url', None) and not getattr(target, 'url', None):
            target.url = source.url
        
        # Propagate verification status
        if getattr(source, 'verified', False) and not getattr(target, 'verified', False):
            target.verified = True
            target.source = source.source
    
    def cluster_citations_by_name_and_year(self, citations: CitationList) -> List[CitationList]:
        """Cluster citations by case name and year."""
        if not citations:
            return []
        
        clusters = []
        used = set()
        
        for i, citation1 in enumerate(citations):
            if i in used:
                continue
            
            cluster = [citation1]
            used.add(i)
            
            name1 = getattr(citation1, 'extracted_case_name', '')
            date1 = getattr(citation1, 'extracted_date', '')
            
            for j, citation2 in enumerate(citations[i+1:], i+1):
                if j in used:
                    continue
                
                name2 = getattr(citation2, 'extracted_case_name', '')
                date2 = getattr(citation2, 'extracted_date', '')
                
                # Check if names are similar
                if name1 and name2:
                    similarity = calculate_similarity(name1, name2)
                    if similarity > 0.7:  # High similarity threshold
                        # Check if dates are similar
                        if not date1 or not date2 or is_similar_date(date1, date2):
                            cluster.append(citation2)
                            used.add(j)
            
            if len(cluster) > 1:
                clusters.append(cluster)
        
        return clusters
    
    def calculate_confidence(self, citation: CitationResult, text: str) -> float:
        """Calculate confidence score for a citation."""
        if not citation:
            return 0.0
        
        confidence = 0.0
        
        # Base confidence from source
        confidence += getattr(citation, 'confidence', 0.0)
        
        # Bonus for verification
        if getattr(citation, 'verified', False):
            confidence += 0.3
        
        # Bonus for having context
        if text and citation.start_index is not None and citation.end_index is not None:
            context = extract_context(text, citation.start_index, citation.end_index)
            if len(context) > 50:  # Good context
                confidence += 0.1
        
        # Bonus for having extracted information
        if getattr(citation, 'extracted_case_name', None):
            confidence += 0.1
        
        if getattr(citation, 'extracted_date', None):
            confidence += 0.1
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def infer_reporter_from_citation(self, citation: str) -> Optional[str]:
        """Infer reporter from citation string."""
        if not citation:
            return None
        
        reporter_patterns = {
            'P.3d': r'\b\d+\s+P\.3d\b',
            'P.2d': r'\b\d+\s+P\.2d\b',
            'N.W.2d': r'\b\d+\s+N\.W\.2d\b',
            'N.W.': r'\b\d+\s+N\.W\.\b',
            'S.W.3d': r'\b\d+\s+S\.W\.3d\b',
            'S.W.2d': r'\b\d+\s+S\.W\.2d\b',
            'S.W.': r'\b\d+\s+S\.W\.\b',
            'N.E.2d': r'\b\d+\s+N\.E\.2d\b',
            'N.E.': r'\b\d+\s+N\.E\.\b',
            'So.3d': r'\b\d+\s+So\.3d\b',
            'So.2d': r'\b\d+\s+So\.2d\b',
            'So.': r'\b\d+\s+So\.\b',
            'S.E.2d': r'\b\d+\s+S\.E\.2d\b',
            'S.E.': r'\b\d+\s+S\.E\.\b',
            'A.3d': r'\b\d+\s+A\.3d\b',
            'A.2d': r'\b\d+\s+A\.2d\b',
            'A.': r'\b\d+\s+A\.\b',
            'WL': r'\b\d{4}\s+WL\s+\d+\b',
            'LEXIS': r'\b\d{4}\s+[A-Za-z\.\s]+LEXIS\s+\d+\b',
            'LEXIS_ALT': r'\b\d{4}\s+LEXIS\s+\d+\b',
        }
        
        for reporter, pattern in reporter_patterns.items():
            if re.search(pattern, citation, re.IGNORECASE):
                return reporter
        
        return None
    
    def get_possible_states_for_reporter(self, reporter: str) -> List[str]:
        """Get all possible states for a given regional reporter."""
        return self.state_reporter_mapping.get(reporter, [])
    
    def infer_state_from_citation(self, citation: str) -> Optional[str]:
        """Infer the expected state from the citation abbreviation."""
        state_map = {
            'Wn.': 'Washington',
            'Wash.': 'Washington',
            'Cal.': 'California',
            'Kan.': 'Kansas',
            'Or.': 'Oregon',
            'Idaho': 'Idaho',
            'Nev.': 'Nevada',
            'Colo.': 'Colorado',
            'Mont.': 'Montana',
            'Utah': 'Utah',
            'Ariz.': 'Arizona',
            'N.M.': 'New Mexico',
            'Alaska': 'Alaska',
        }
        
        for abbr, state in state_map.items():
            if abbr in citation:
                return state
        
        return None 