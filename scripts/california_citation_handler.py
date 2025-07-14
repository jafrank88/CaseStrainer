#!/usr/bin/env python3
"""
California Citation Handler
==========================

Handles California-specific citation formats like:
- Brandt v. Superior Court (1985) 37 Cal.3d 813 [210 Cal.Rptr. 211, 693 P.2d 796]
- Smith v. Jones (2020) 45 Cal.4th 123 [180 Cal.Rptr.3d 456, 340 P.3d 789]
- Doe v. Roe (1995) 12 Cal.App.4th 567 [15 Cal.Rptr.2d 234]
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CaliforniaCitation:
    """Represents a parsed California citation."""
    case_name: str
    year: str
    primary_citation: str
    parallel_citations: List[str]
    full_text: str
    start_index: int
    end_index: int
    confidence: float = 0.0


class CaliforniaCitationHandler:
    """Handles California-specific citation formats."""
    
    def __init__(self):
        # California citation patterns
        self.california_patterns = {
            # Full pattern with parallel citations in brackets
            'full_california': re.compile(
                r'([A-Z][A-Za-z0-9&.,\'\\-]*(?:[\s,][A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]*(?:[\s,][A-Za-z0-9&.,\'\\-]+)*)\s*\((\d{4})\)\s+(\d+)\s+(Cal\.(?:3d|4th|App\.(?:3d|4th)?))\s+(\d+)(?:\s*\[([^\]]+)\])?',
                re.IGNORECASE
            ),
            
            # Pattern without parallel citations
            'simple_california': re.compile(
                r'([A-Z][A-Za-z0-9&.,\'\\-]*(?:[\s,][A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]*(?:[\s,][A-Za-z0-9&.,\'\\-]+)*)\s*\((\d{4})\)\s+(\d+)\s+(Cal\.(?:3d|4th|App\.(?:3d|4th)?))\s+(\d+)',
                re.IGNORECASE
            ),
            
            # Pattern for parallel citations only (when case name is elsewhere)
            'parallel_only': re.compile(
                r'(\d+)\s+(Cal\.(?:3d|4th|App\.(?:3d|4th)?))\s+(\d+)(?:\s*\[([^\]]+)\])?',
                re.IGNORECASE
            ),
            
            # Pattern for case name with year in parentheses
            'case_name_with_year': re.compile(
                r'([A-Z][A-Za-z0-9&.,\'\\-]*(?:[\s,][A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]*(?:[\s,][A-Za-z0-9&.,\'\\-]+)*)\s*\((\d{4})\)',
                re.IGNORECASE
            )
        }
        
        # California reporter mappings
        self.california_reporters = {
            'Cal.3d': 'California Reports, Third Series',
            'Cal.4th': 'California Reports, Fourth Series',
            'Cal.App.3d': 'California Appellate Reports, Third Series',
            'Cal.App.4th': 'California Appellate Reports, Fourth Series',
            'Cal.Rptr.': 'California Reporter',
            'Cal.Rptr.2d': 'California Reporter, Second Series',
            'Cal.Rptr.3d': 'California Reporter, Third Series',
            'P.2d': 'Pacific Reporter, Second Series',
            'P.3d': 'Pacific Reporter, Third Series'
        }
    
    def extract_california_citations(self, text: str) -> List[CaliforniaCitation]:
        """Extract all California citations from text."""
        citations = []
        
        # Try full pattern first
        for match in self.california_patterns['full_california'].finditer(text):
            citation = self._parse_full_california_match(match, text)
            if citation:
                citations.append(citation)
        
        # Try simple pattern for citations without parallel citations
        for match in self.california_patterns['simple_california'].finditer(text):
            citation = self._parse_simple_california_match(match, text)
            if citation:
                citations.append(citation)
        
        # Try parallel citations only (when case name is found separately)
        for match in self.california_patterns['parallel_only'].finditer(text):
            citation = self._parse_parallel_only_match(match, text)
            if citation:
                citations.append(citation)
        
        return citations
    
    def _parse_full_california_match(self, match, text: str) -> Optional[CaliforniaCitation]:
        """Parse a full California citation match."""
        try:
            case_name = match.group(1).strip()
            year = match.group(2)
            volume = match.group(3)
            reporter = match.group(4)
            page = match.group(5)
            parallel_text = match.group(6) if match.group(6) else ""
            
            # Build primary citation
            primary_citation = f"{volume} {reporter} {page}"
            
            # Parse parallel citations
            parallel_citations = self._parse_parallel_citations(parallel_text)
            
            # Calculate confidence based on completeness
            confidence = 0.9 if parallel_citations else 0.8
            
            return CaliforniaCitation(
                case_name=case_name,
                year=year,
                primary_citation=primary_citation,
                parallel_citations=parallel_citations,
                full_text=match.group(0),
                start_index=match.start(),
                end_index=match.end(),
                confidence=confidence
            )
        except Exception as e:
            print(f"Error parsing full California citation: {e}")
            return None
    
    def _parse_simple_california_match(self, match, text: str) -> Optional[CaliforniaCitation]:
        """Parse a simple California citation match (no parallel citations)."""
        try:
            case_name = match.group(1).strip()
            year = match.group(2)
            volume = match.group(3)
            reporter = match.group(4)
            page = match.group(5)
            
            primary_citation = f"{volume} {reporter} {page}"
            
            return CaliforniaCitation(
                case_name=case_name,
                year=year,
                primary_citation=primary_citation,
                parallel_citations=[],
                full_text=match.group(0),
                start_index=match.start(),
                end_index=match.end(),
                confidence=0.7
            )
        except Exception as e:
            print(f"Error parsing simple California citation: {e}")
            return None
    
    def _parse_parallel_only_match(self, match, text: str) -> Optional[CaliforniaCitation]:
        """Parse parallel citations only (when case name is found elsewhere)."""
        try:
            volume = match.group(1)
            reporter = match.group(2)
            page = match.group(3)
            parallel_text = match.group(4) if match.group(4) else ""
            
            primary_citation = f"{volume} {reporter} {page}"
            parallel_citations = self._parse_parallel_citations(parallel_text)
            
            # Try to find case name in surrounding context
            context_start = max(0, match.start() - 200)
            context_end = min(len(text), match.end() + 200)
            context = text[context_start:context_end]
            
            case_name = self._extract_case_name_from_context(context)
            
            return CaliforniaCitation(
                case_name=case_name or "Unknown Case",
                year="",  # Will need to be extracted from context
                primary_citation=primary_citation,
                parallel_citations=parallel_citations,
                full_text=match.group(0),
                start_index=match.start(),
                end_index=match.end(),
                confidence=0.6
            )
        except Exception as e:
            print(f"Error parsing parallel-only citation: {e}")
            return None
    
    def _parse_parallel_citations(self, parallel_text: str) -> List[str]:
        """Parse parallel citations from bracketed text."""
        if not parallel_text:
            return []
        
        citations = []
        
        # Split by common separators
        parts = re.split(r'[,;]\s*', parallel_text)
        
        for part in parts:
            part = part.strip()
            if part:
                # Look for citation patterns in the parallel text
                citation_match = re.search(r'(\d+)\s+(Cal\.Rptr\.(?:2d|3d)?|P\.(?:2d|3d))\s+(\d+)', part, re.IGNORECASE)
                if citation_match:
                    volume = citation_match.group(1)
                    reporter = citation_match.group(2)
                    page = citation_match.group(3)
                    citations.append(f"{volume} {reporter} {page}")
                else:
                    # If no clear pattern, add the part as-is
                    citations.append(part)
        
        return citations
    
    def _extract_case_name_from_context(self, context: str) -> Optional[str]:
        """Extract case name from surrounding context."""
        # Look for case name patterns in the context
        case_name_match = self.california_patterns['case_name_with_year'].search(context)
        if case_name_match:
            return case_name_match.group(1).strip()
        
        # Fallback: look for any "v." pattern
        v_pattern = re.search(r'([A-Z][A-Za-z0-9&.,\'\\-]*(?:[\s,][A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]*(?:[\s,][A-Za-z0-9&.,\'\\-]+)*)', context, re.IGNORECASE)
        if v_pattern:
            return v_pattern.group(1).strip()
        
        return None
    
    def normalize_california_citation(self, citation: CaliforniaCitation) -> Dict[str, str]:
        """Normalize a California citation to standard format."""
        return {
            'case_name': citation.case_name,
            'year': citation.year,
            'primary_citation': citation.primary_citation,
            'parallel_citations': citation.parallel_citations,
            'full_citation': citation.full_text,
            'reporter_info': self.california_reporters.get(
                citation.primary_citation.split()[1], 
                'Unknown Reporter'
            )
        }
    
    def get_california_citation_variations(self, citation: CaliforniaCitation) -> List[str]:
        """Generate variations of a California citation."""
        variations = []
        
        # Primary citation
        variations.append(citation.primary_citation)
        
        # With case name
        if citation.case_name:
            variations.append(f"{citation.case_name} ({citation.year}) {citation.primary_citation}")
        
        # With parallel citations
        if citation.parallel_citations:
            parallel_text = f" [{', '.join(citation.parallel_citations)}]"
            variations.append(f"{citation.primary_citation}{parallel_text}")
            
            if citation.case_name:
                variations.append(f"{citation.case_name} ({citation.year}) {citation.primary_citation}{parallel_text}")
        
        return variations


def test_california_citation_handler():
    """Test the California citation handler."""
    handler = CaliforniaCitationHandler()
    
    # Test cases
    test_cases = [
        "Brandt v. Superior Court (1985) 37 Cal.3d 813 [210 Cal.Rptr. 211, 693 P.2d 796]",
        "Smith v. Jones (2020) 45 Cal.4th 123 [180 Cal.Rptr.3d 456, 340 P.3d 789]",
        "Doe v. Roe (1995) 12 Cal.App.4th 567 [15 Cal.Rptr.2d 234]",
        "Brown v. Wilson (2010) 25 Cal.3d 456",
        "Johnson v. State (2005) 38 Cal.App.3d 789 [120 Cal.Rptr. 456]"
    ]
    
    print("🧪 TESTING CALIFORNIA CITATION HANDLER")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case}")
        print("-" * 40)
        
        citations = handler.extract_california_citations(test_case)
        
        if citations:
            for j, citation in enumerate(citations, 1):
                print(f"  Citation {j}:")
                print(f"    Case Name: {citation.case_name}")
                print(f"    Year: {citation.year}")
                print(f"    Primary: {citation.primary_citation}")
                print(f"    Parallel: {citation.parallel_citations}")
                print(f"    Confidence: {citation.confidence:.2f}")
                
                # Show variations
                variations = handler.get_california_citation_variations(citation)
                print(f"    Variations: {variations}")
        else:
            print("  ❌ No citations found")
    
    print(f"\n✅ Testing complete!")


if __name__ == '__main__':
    test_california_citation_handler() 