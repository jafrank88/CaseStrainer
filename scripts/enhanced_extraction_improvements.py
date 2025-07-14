#!/usr/bin/env python3
"""
Enhanced Extraction Improvements for Case Names, Dates, and Clustering.
This script provides improved algorithms for extracting and processing legal citations.
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import sys
import os

# Add src to sys.path for local script execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, CitationResult

# Add California citation handler
from california_citation_handler import CaliforniaCitationHandler

logger = logging.getLogger(__name__)

@dataclass
class EnhancedCaseName:
    """Enhanced case name with confidence and extraction method."""
    name: str
    confidence: float
    method: str
    context: str
    position: Tuple[int, int]

@dataclass
class EnhancedDate:
    """Enhanced date with confidence and extraction method."""
    date: str
    year: str
    confidence: float
    method: str
    context: str

class EnhancedCaseNameExtractor:
    """Enhanced case name extraction with multiple strategies."""
    
    def __init__(self):
        # Comprehensive case name patterns
        self.patterns = [
            # Standard: Name v. Name
            r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            r'([A-Z][A-Za-z\s,\.\'-]+?\s+vs\.\s+[A-Z][A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            
            # Department cases
            r'(Dep\'t\s+of\s+[A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            r'(Department\s+of\s+[A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            
            # Government cases
            r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            r'(People\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            r'(United\s+States\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            
            # In re cases
            r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            r'(Matter\s+of\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            
            # Estate cases
            r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            
            # Corporate cases
            r'([A-Z][A-Za-z\s,&\.]*(?:Inc\.|LLC|Corp\.|Co\.|Ltd\.)\s+v\.\s+[A-Za-z\s,&\.]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        ]
        
        # Signal words to avoid
        self.signal_words = {
            'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from',
            'into', 'during', 'including', 'until', 'against', 'among', 'throughout',
            'despite', 'towards', 'upon', 'court', 'case', 'matter', 'opinion'
        }
    
    def extract_case_names(self, text: str, citation: str = None) -> List[EnhancedCaseName]:
        """Extract case names using multiple strategies."""
        results = []
        
        # Strategy 1: Citation-adjacent extraction
        if citation:
            adjacent_results = self._extract_adjacent_to_citation(text, citation)
            results.extend(adjacent_results)
        
        # Strategy 2: Pattern-based extraction
        pattern_results = self._extract_with_patterns(text)
        results.extend(pattern_results)
        
        # Strategy 3: Context-based extraction
        context_results = self._extract_from_context(text)
        results.extend(context_results)
        
        # Remove duplicates and rank by confidence
        unique_results = self._deduplicate_and_rank(results)
        
        return unique_results
    
    def _extract_adjacent_to_citation(self, text: str, citation: str) -> List[EnhancedCaseName]:
        """Extract case names directly adjacent to citations."""
        results = []
        
        # Find citation in text
        citation_index = text.find(citation)
        if citation_index == -1:
            return results
        
        # Look in context before citation
        context_before = text[max(0, citation_index - 200):citation_index]
        
        for i, pattern in enumerate(self.patterns):
            matches = list(re.finditer(pattern, context_before, re.IGNORECASE))
            
            for match in matches:
                case_name = self._clean_case_name(match.group(1))
                if self._is_valid_case_name(case_name):
                    confidence = self._calculate_confidence(case_name, i, True)
                    results.append(EnhancedCaseName(
                        name=case_name,
                        confidence=confidence,
                        method=f"adjacent_pattern_{i}",
                        context=context_before[max(0, match.start()-50):match.end()+50],
                        position=(match.start(), match.end())
                    ))
        
        return results
    
    def _extract_with_patterns(self, text: str) -> List[EnhancedCaseName]:
        """Extract case names using regex patterns."""
        results = []
        
        for i, pattern in enumerate(self.patterns):
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            
            for match in matches:
                case_name = self._clean_case_name(match.group(1))
                if self._is_valid_case_name(case_name):
                    confidence = self._calculate_confidence(case_name, i, False)
                    results.append(EnhancedCaseName(
                        name=case_name,
                        confidence=confidence,
                        method=f"pattern_{i}",
                        context=text[max(0, match.start()-50):match.end()+50],
                        position=(match.start(), match.end())
                    ))
        
        return results
    
    def _extract_from_context(self, text: str) -> List[EnhancedCaseName]:
        """Extract case names from sentence context."""
        results = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            for i, pattern in enumerate(self.patterns):
                matches = list(re.finditer(pattern, sentence, re.IGNORECASE))
                
                for match in matches:
                    case_name = self._clean_case_name(match.group(1))
                    if self._is_valid_case_name(case_name):
                        confidence = self._calculate_confidence(case_name, i, False) * 0.8  # Lower confidence for context
                        results.append(EnhancedCaseName(
                            name=case_name,
                            confidence=confidence,
                            method=f"context_pattern_{i}",
                            context=sentence,
                            position=(match.start(), match.end())
                        ))
        
        return results
    
    def _clean_case_name(self, name: str) -> str:
        """Clean and normalize case name."""
        if not name:
            return ""
        
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Remove trailing punctuation
        name = re.sub(r'[,\s]+$', '', name)
        name = name.rstrip('.,;:')
        
        # Normalize spacing around "v."
        name = re.sub(r'\s+v\.\s+', ' v. ', name)
        name = re.sub(r'\s+vs\.\s+', ' v. ', name)
        
        # Remove citation text that got included
        citation_patterns = [
            r',\s*\d+\s+[A-Za-z.]+(?:\s+\d+)*.*$',
            r',\s*\d+\s+[A-Za-z.]+.*$',
            r',\s*\d+.*$',
            r'\(\d{4}\).*$',
        ]
        
        for pattern in citation_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        return name.strip()
    
    def _is_valid_case_name(self, name: str) -> bool:
        """Validate case name."""
        if not name or len(name) < 5:
            return False
        
        # Must start with capital letter
        if not name[0].isupper():
            return False
        
        # Must contain "v." or "vs." or be an "In re" case
        if not re.search(r'\bv\.?\b|\bvs\.?\b|\bIn\s+re\b|\bEstate\s+of\b|\bState\s+v\.\b', name, re.IGNORECASE):
            return False
        
        # Must not be just signal words
        words = name.split()
        if len(words) < 2:
            return False
        
        # Check that at least 50% of words start with capital letters
        capital_words = sum(1 for word in words if word and word[0].isupper())
        if capital_words < len(words) * 0.5:
            return False
        
        return True
    
    def _calculate_confidence(self, case_name: str, pattern_index: int, is_adjacent: bool) -> float:
        """Calculate confidence score for extracted case name."""
        base_confidence = 0.7
        
        # Pattern-specific adjustments
        if pattern_index < 2:  # Standard v. patterns
            base_confidence += 0.2
        elif pattern_index < 4:  # Department patterns
            base_confidence += 0.15
        elif pattern_index < 7:  # Government patterns
            base_confidence += 0.1
        
        # Adjacent to citation bonus
        if is_adjacent:
            base_confidence += 0.1
        
        # Length bonus (not too short, not too long)
        if 10 <= len(case_name) <= 80:
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def _deduplicate_and_rank(self, results: List[EnhancedCaseName]) -> List[EnhancedCaseName]:
        """Remove duplicates and rank by confidence."""
        seen = set()
        unique_results = []
        
        for result in sorted(results, key=lambda x: x.confidence, reverse=True):
            normalized_name = result.name.lower().strip()
            if normalized_name not in seen:
                seen.add(normalized_name)
                unique_results.append(result)
        
        return unique_results

class EnhancedDateExtractor:
    """Enhanced date extraction with multiple strategies."""
    
    def __init__(self):
        # Comprehensive date patterns
        self.patterns = [
            # Year in parentheses: (2024)
            r'\((\d{4})\)',
            
            # ISO format: 2024-01-15
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',
            
            # US format: 01/15/2024
            r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',
            
            # Month names: January 15, 2024
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b',
            
            # Simple year: 2024
            r'\b(19|20)\d{2}\b',
            
            # Legal context: decided in 2024, filed in 2024
            r'(?:decided|filed|issued|released|argued|submitted)\s+(?:in\s+)?(\d{4})\b',
        ]
        
        self.month_map = {
            'january': '01', 'jan': '01',
            'february': '02', 'feb': '02',
            'march': '03', 'mar': '03',
            'april': '04', 'apr': '04',
            'may': '05',
            'june': '06', 'jun': '06',
            'july': '07', 'jul': '07',
            'august': '08', 'aug': '08',
            'september': '09', 'sep': '09',
            'october': '10', 'oct': '10',
            'november': '11', 'nov': '11',
            'december': '12', 'dec': '12'
        }
    
    def extract_dates(self, text: str, citation: str = None) -> List[EnhancedDate]:
        """Extract dates using multiple strategies."""
        results = []
        
        # Strategy 1: Citation-adjacent extraction (highest priority)
        if citation:
            adjacent_results = self._extract_adjacent_to_citation(text, citation)
            results.extend(adjacent_results)
        
        # Strategy 2: Pattern-based extraction
        pattern_results = self._extract_with_patterns(text)
        results.extend(pattern_results)
        
        # Strategy 3: Context-based extraction
        context_results = self._extract_from_context(text)
        results.extend(context_results)
        
        # Remove duplicates and rank by confidence
        unique_results = self._deduplicate_and_rank(results)
        
        return unique_results
    
    def _extract_adjacent_to_citation(self, text: str, citation: str) -> List[EnhancedDate]:
        """Extract dates directly adjacent to citations."""
        results = []
        
        # Find citation in text
        citation_index = text.find(citation)
        if citation_index == -1:
            return results
        
        # Look immediately after citation (highest priority)
        after_citation = text[citation_index + len(citation):citation_index + len(citation) + 50]
        
        for i, pattern in enumerate(self.patterns):
            matches = list(re.finditer(pattern, after_citation, re.IGNORECASE))
            
            for match in matches:
                date_info = self._parse_date_match(match, pattern, i)
                if date_info:
                    results.append(EnhancedDate(
                        date=date_info['date'],
                        year=date_info['year'],
                        confidence=0.9,  # High confidence for adjacent dates
                        method=f"adjacent_pattern_{i}",
                        context=after_citation[max(0, match.start()-20):match.end()+20]
                    ))
        
        return results
    
    def _extract_with_patterns(self, text: str) -> List[EnhancedDate]:
        """Extract dates using regex patterns."""
        results = []
        
        for i, pattern in enumerate(self.patterns):
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            
            for match in matches:
                date_info = self._parse_date_match(match, pattern, i)
                if date_info:
                    results.append(EnhancedDate(
                        date=date_info['date'],
                        year=date_info['year'],
                        confidence=0.7,  # Medium confidence for pattern matches
                        method=f"pattern_{i}",
                        context=text[max(0, match.start()-50):match.end()+50]
                    ))
        
        return results
    
    def _extract_from_context(self, text: str) -> List[EnhancedDate]:
        """Extract dates from sentence context."""
        results = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            for i, pattern in enumerate(self.patterns):
                matches = list(re.finditer(pattern, sentence, re.IGNORECASE))
                
                for match in matches:
                    date_info = self._parse_date_match(match, pattern, i)
                    if date_info:
                        results.append(EnhancedDate(
                            date=date_info['date'],
                            year=date_info['year'],
                            confidence=0.6,  # Lower confidence for context
                            method=f"context_pattern_{i}",
                            context=sentence
                        ))
        
        return results
    
    def _parse_date_match(self, match, pattern: str, pattern_index: int) -> Optional[Dict[str, str]]:
        """Parse date match and return structured date info."""
        try:
            groups = match.groups()
            
            if pattern_index == 0:  # (YYYY)
                year = groups[0]
                if 1900 <= int(year) <= 2100:
                    return {'date': f"{year}-01-01", 'year': year}
            
            elif pattern_index == 1:  # YYYY-MM-DD
                year, month, day = groups
                if 1900 <= int(year) <= 2100 and 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                    return {'date': f"{year}-{month:0>2}-{day:0>2}", 'year': year}
            
            elif pattern_index == 2:  # MM/DD/YYYY
                month, day, year = groups
                if 1900 <= int(year) <= 2100 and 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                    return {'date': f"{year}-{month:0>2}-{day:0>2}", 'year': year}
            
            elif pattern_index == 3:  # Month DD, YYYY
                month_name, day, year = groups
                month = self.month_map.get(month_name.lower(), '01')
                if 1900 <= int(year) <= 2100 and 1 <= int(day) <= 31:
                    return {'date': f"{year}-{month}-{day:0>2}", 'year': year}
            
            elif pattern_index == 4:  # YYYY
                year = groups[0]
                if 1900 <= int(year) <= 2100:
                    return {'date': f"{year}-01-01", 'year': year}
            
            elif pattern_index == 5:  # decided in YYYY
                year = groups[0]
                if 1900 <= int(year) <= 2100:
                    return {'date': f"{year}-01-01", 'year': year}
            
        except (ValueError, TypeError, IndexError):
            pass
        
        return None
    
    def _deduplicate_and_rank(self, results: List[EnhancedDate]) -> List[EnhancedDate]:
        """Remove duplicates and rank by confidence."""
        seen = set()
        unique_results = []
        
        for result in sorted(results, key=lambda x: x.confidence, reverse=True):
            if result.date not in seen:
                seen.add(result.date)
                unique_results.append(result)
        
        return unique_results

class EnhancedClustering:
    """Enhanced clustering with improved validation and grouping."""
    
    def __init__(self):
        self.max_distance = 100  # Maximum distance between citations in a cluster
        self.min_similarity = 0.8  # Minimum similarity for case names
    
    def cluster_citations(self, citations: List[CitationResult], text: str) -> List[Dict[str, Any]]:
        """Cluster citations with enhanced validation."""
        if not citations or len(citations) < 2:
            return []
        
        # Step 1: Group by proximity
        proximity_groups = self._group_by_proximity(citations)
        
        # Step 2: Validate and refine groups
        validated_clusters = []
        
        for group in proximity_groups:
            if len(group) < 2:
                continue
            
            # Apply validation rules
            if self._validate_cluster(group):
                cluster = self._create_cluster(group, text)
                validated_clusters.append(cluster)
        
        return validated_clusters
    
    def _group_by_proximity(self, citations: List[CitationResult]) -> List[List[CitationResult]]:
        """Group citations by proximity in text."""
        if not citations:
            return []
        
        # Sort by position in text
        sorted_citations = sorted(citations, key=lambda x: x.start_index or 0)
        
        groups = []
        current_group = []
        
        for citation in sorted_citations:
            if not current_group:
                current_group = [citation]
            else:
                prev_citation = current_group[-1]
                
                # Check if citations are close enough
                if self._are_citations_close(prev_citation, citation):
                    current_group.append(citation)
                else:
                    if len(current_group) > 1:
                        groups.append(current_group)
                    current_group = [citation]
        
        # Add the last group
        if len(current_group) > 1:
            groups.append(current_group)
        
        return groups
    
    def _are_citations_close(self, citation1: CitationResult, citation2: CitationResult) -> bool:
        """Check if two citations are close enough to be clustered."""
        if not citation1.start_index or not citation2.start_index:
            return False
        
        distance = citation2.start_index - citation1.end_index
        
        # Must be within maximum distance
        if distance > self.max_distance:
            return False
        
        # Check for explicit separation indicators
        if distance > 0:
            # Look for punctuation that suggests they're meant to be together
            return True
        
        return True
    
    def _validate_cluster(self, group: List[CitationResult]) -> bool:
        """Validate that a group of citations form a valid cluster."""
        if len(group) < 2:
            return False
        
        # Check case name consistency
        case_names = [c.extracted_case_name for c in group if c.extracted_case_name]
        if case_names:
            # All case names should be similar
            first_name = case_names[0]
            for name in case_names[1:]:
                if not self._are_case_names_similar(first_name, name):
                    return False
        
        # Check date consistency
        dates = [c.extracted_date for c in group if c.extracted_date]
        if dates:
            # All dates should be the same year
            first_date = dates[0]
            first_year = first_date.split('-')[0] if '-' in first_date else first_date[:4]
            for date in dates[1:]:
                year = date.split('-')[0] if '-' in date else date[:4]
                if year != first_year:
                    return False
        
        return True
    
    def _are_case_names_similar(self, name1: str, name2: str) -> bool:
        """Check if two case names are similar."""
        if not name1 or not name2:
            return False
        
        # Normalize names
        norm1 = name1.lower().strip()
        norm2 = name2.lower().strip()
        
        # Exact match
        if norm1 == norm2:
            return True
        
        # Check if one is contained in the other
        if norm1 in norm2 or norm2 in norm1:
            return True
        
        # Calculate similarity (simple implementation)
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        return similarity >= self.min_similarity
    
    def _create_cluster(self, group: List[CitationResult], text: str) -> Dict[str, Any]:
        """Create a cluster from a validated group."""
        # Sort by position in text
        sorted_group = sorted(group, key=lambda x: x.start_index or 0)
        
        # Get cluster metadata from the first citation
        first_citation = sorted_group[0]
        
        cluster = {
            'cluster_id': f"cluster_{len(sorted_group)}",
            'citations': [c.citation for c in sorted_group],
            'canonical_name': first_citation.canonical_name or first_citation.extracted_case_name,
            'canonical_date': first_citation.canonical_date or first_citation.extracted_date,
            'extracted_case_name': first_citation.extracted_case_name,
            'extracted_date': first_citation.extracted_date,
            'url': first_citation.url,
            'source': first_citation.source,
            'cluster_size': len(sorted_group),
            'confidence': sum(c.confidence for c in sorted_group) / len(sorted_group),
            'context': self._get_cluster_context(sorted_group, text)
        }
        
        return cluster
    
    def _get_cluster_context(self, group: List[CitationResult], text: str) -> str:
        """Get context around the cluster."""
        if not group:
            return ""
        
        first_citation = group[0]
        last_citation = group[-1]
        
        if not first_citation.start_index or not last_citation.end_index:
            return ""
        
        start = max(0, first_citation.start_index - 100)
        end = min(len(text), last_citation.end_index + 100)
        
        return text[start:end]

class EnhancedExtractionProcessor:
    """Main processor that combines all enhanced extraction capabilities."""
    
    def __init__(self):
        self.case_name_extractor = EnhancedCaseNameExtractor()
        self.date_extractor = EnhancedDateExtractor()
        self.clustering = EnhancedClustering()
        self.base_processor = UnifiedCitationProcessorV2()
        
        # Initialize California citation handler
        self.california_handler = CaliforniaCitationHandler()
        
        # Add California patterns to the existing patterns
        self.citation_patterns = {
            # California patterns
            'california_full': re.compile(
                r'([A-Z][A-Za-z0-9&.,\'\\-]*(?:[\s,][A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]*(?:[\s,][A-Za-z0-9&.,\'\\-]+)*)\s*\((\d{4})\)\s+(\d+)\s+(Cal\.(?:3d|4th|App\.(?:3d|4th)?))\s+(\d+)(?:\s*\[([^\]]+)\])?',
                re.IGNORECASE
            ),
            'california_simple': re.compile(
                r'([A-Z][A-Za-z0-9&.,\'\\-]*(?:[\s,][A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]*(?:[\s,][A-Za-z0-9&.,\'\\-]+)*)\s*\((\d{4})\)\s+(\d+)\s+(Cal\.(?:3d|4th|App\.(?:3d|4th)?))\s+(\d+)',
                re.IGNORECASE
            ),
        }
    
    def process_text_enhanced(self, text: str) -> Dict[str, Any]:
        """Process text with enhanced extraction capabilities."""
        # Step 1: Use base processor for citation extraction
        base_results = self.base_processor.process_text(text)
        
        # Step 2: Enhance case name extraction
        enhanced_case_names = self.case_name_extractor.extract_case_names(text)
        
        # Step 3: Enhance date extraction
        enhanced_dates = self.date_extractor.extract_dates(text)
        
        # Step 4: Apply enhanced clustering
        clusters = self.clustering.cluster_citations(base_results, text)
        
        # Step 5: Merge enhanced results with base results
        enhanced_results = self._merge_enhanced_results(
            base_results, enhanced_case_names, enhanced_dates
        )
        
        return {
            'citations': enhanced_results,
            'clusters': clusters,
            'enhanced_case_names': [{'name': c.name, 'confidence': c.confidence, 'method': c.method} for c in enhanced_case_names],
            'enhanced_dates': [{'date': d.date, 'year': d.year, 'confidence': d.confidence, 'method': d.method} for d in enhanced_dates],
            'statistics': {
                'total_citations': len(enhanced_results),
                'total_clusters': len(clusters),
                'enhanced_case_names': len(enhanced_case_names),
                'enhanced_dates': len(enhanced_dates)
            }
        }
    
    def _merge_enhanced_results(self, base_results: List[CitationResult], 
                               enhanced_case_names: List[EnhancedCaseName],
                               enhanced_dates: List[EnhancedDate]) -> List[CitationResult]:
        """Merge enhanced extraction results with base results."""
        # Create mappings for quick lookup
        case_name_map = {c.name.lower(): c for c in enhanced_case_names}
        date_map = {d.date: d for d in enhanced_dates}
        
        enhanced_results = []
        
        for result in base_results:
            # Try to enhance case name
            if not result.extracted_case_name or result.extracted_case_name == 'N/A':
                # Look for case name in context
                context = result.context or ""
                for case_name in enhanced_case_names:
                    if case_name.name.lower() in context.lower():
                        result.extracted_case_name = case_name.name
                        result.confidence = max(result.confidence, case_name.confidence)
                        break
            
            # Try to enhance date
            if not result.extracted_date or result.extracted_date == 'N/A':
                # Look for date in context
                context = result.context or ""
                for date_info in enhanced_dates:
                    if date_info.date in context or date_info.year in context:
                        result.extracted_date = date_info.date
                        result.confidence = max(result.confidence, date_info.confidence)
                        break
            
            enhanced_results.append(result)
        
        return enhanced_results

    def extract_citations_with_enhancements(self, text: str) -> List[Dict[str, Any]]:
        """Extract citations using enhanced patterns and strategies."""
        citations = []
        
        # Extract using existing patterns
        for pattern_name, pattern in self.citation_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                citation_data = {
                    'citation': match.group(0),
                    'pattern': pattern_name,
                    'start_index': match.start(),
                    'end_index': match.end(),
                    'context': text[max(0, match.start()-50):min(len(text), match.end()+50)],
                    'confidence': self._calculate_confidence(match, pattern_name),
                    'method': 'enhanced_regex'
                }
                citations.append(citation_data)
        
        # Add California citation extraction
        california_citations = self.california_handler.extract_california_citations(text)
        
        # Convert California citations to the standard format
        for cal_citation in california_citations:
            citation_data = {
                'citation': cal_citation.primary_citation,
                'case_name': cal_citation.case_name,
                'year': cal_citation.year,
                'confidence': cal_citation.confidence,
                'method': 'california_handler',
                'pattern': 'california_full' if cal_citation.parallel_citations else 'california_simple',
                'start_index': cal_citation.start_index,
                'end_index': cal_citation.end_index,
                'context': text[max(0, cal_citation.start_index-50):min(len(text), cal_citation.end_index+50)],
                'parallel_citations': cal_citation.parallel_citations,
                'metadata': {
                    'is_california_citation': True,
                    'reporter_info': self.california_handler.california_reporters.get(
                        cal_citation.primary_citation.split()[1], 
                        'Unknown Reporter'
                    )
                }
            }
            citations.append(citation_data)
        
        # Remove duplicates and sort by confidence
        unique_citations = self._remove_duplicates(citations)
        unique_citations.sort(key=lambda x: x['confidence'], reverse=True)
        
        return unique_citations

def main():
    """Test the enhanced extraction system."""
    # Sample legal text
    sample_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    """
    
    print("=== ENHANCED EXTRACTION TEST ===")
    print(f"Sample text length: {len(sample_text)} characters")
    
    # Initialize processor
    processor = EnhancedExtractionProcessor()
    
    # Process text
    results = processor.process_text_enhanced(sample_text)
    
    # Display results
    print(f"\n=== RESULTS ===")
    print(f"Total citations: {results['statistics']['total_citations']}")
    print(f"Total clusters: {results['statistics']['total_clusters']}")
    print(f"Enhanced case names: {results['statistics']['enhanced_case_names']}")
    print(f"Enhanced dates: {results['statistics']['enhanced_dates']}")
    
    print(f"\n=== CITATIONS ===")
    for i, citation in enumerate(results['citations'], 1):
        print(f"{i}. {citation.citation}")
        print(f"   Case name: {citation.extracted_case_name}")
        print(f"   Date: {citation.extracted_date}")
        print(f"   Confidence: {citation.confidence}")
        print()
    
    print(f"\n=== CLUSTERS ===")
    for i, cluster in enumerate(results['clusters'], 1):
        print(f"Cluster {i}:")
        print(f"  Citations: {cluster['citations']}")
        print(f"  Case name: {cluster['canonical_name']}")
        print(f"  Date: {cluster['canonical_date']}")
        print(f"  Size: {cluster['cluster_size']}")
        print()
    
    print(f"\n=== ENHANCED CASE NAMES ===")
    for case_name in results['enhanced_case_names']:
        print(f"- {case_name['name']} (confidence: {case_name['confidence']:.2f}, method: {case_name['method']})")
    
    print(f"\n=== ENHANCED DATES ===")
    for date_info in results['enhanced_dates']:
        print(f"- {date_info['date']} (confidence: {date_info['confidence']:.2f}, method: {date_info['method']})")

if __name__ == "__main__":
    main() 