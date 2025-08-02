#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bluebook Citation Formatter for CaseStrainer

This module provides functionality to format legal citations according to 
The Bluebook: A Uniform System of Citation (21st Edition) standards.

Key features:
- Proper case name formatting (italics, abbreviations)
- Standardized reporter abbreviations
- Correct spacing and punctuation
- Pinpoint citation formatting
- Court identification when needed
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BluebookCitation:
    """Represents a properly formatted Bluebook citation."""
    case_name: str
    citation: str
    year: Optional[str] = None
    court: Optional[str] = None
    pinpoint: Optional[str] = None
    full_citation: str = ""
    
    def __post_init__(self):
        if not self.full_citation:
            self.full_citation = self._build_full_citation()
    
    def _build_full_citation(self) -> str:
        """Build the complete Bluebook citation."""
        parts = []
        
        # Case name (italicized)
        if self.case_name:
            parts.append(f"*{self.case_name}*")
        
        # Citation
        if self.citation:
            parts.append(self.citation)
        
        # Pinpoint
        if self.pinpoint:
            parts.append(f"at {self.pinpoint}")
        
        # Court and year
        court_year = []
        if self.court and self.court != "U.S.":  # Don't include court for U.S. Supreme Court
            court_year.append(self.court)
        if self.year:
            court_year.append(self.year)
        
        if court_year:
            parts.append(f"({' '.join(court_year)})")
        
        return ", ".join(parts)


class BluebookFormatter:
    """
    Comprehensive Bluebook citation formatter.
    
    Handles formatting of legal citations according to Bluebook standards,
    including proper abbreviations, spacing, and punctuation.
    """
    
    def __init__(self):
        self._init_abbreviations()
        self._init_court_mappings()
        self._init_reporter_mappings()
    
    def _init_abbreviations(self):
        """Initialize common legal abbreviations per Bluebook rules."""
        self.case_name_abbreviations = {
            # Common words that should be abbreviated in case names
            "Association": "Ass'n",
            "Brothers": "Bros.",
            "Company": "Co.",
            "Corporation": "Corp.",
            "Department": "Dep't",
            "Development": "Dev.",
            "Engineering": "Eng'g",
            "Enterprise": "Enter.",
            "Equipment": "Equip.",
            "Government": "Gov't",
            "Incorporated": "Inc.",
            "Insurance": "Ins.",
            "International": "Int'l",
            "Investment": "Inv.",
            "Limited": "Ltd.",
            "Manufacturing": "Mfg.",
            "National": "Nat'l",
            "Partnership": "P'ship",
            "Railroad": "R.R.",
            "Railway": "Ry.",
            "Securities": "Sec.",
            "Service": "Serv.",
            "Transportation": "Transp.",
            "University": "Univ.",
            # Directional abbreviations
            "North": "N.",
            "South": "S.",
            "East": "E.",
            "West": "W.",
            "Northeast": "N.E.",
            "Northwest": "N.W.",
            "Southeast": "S.E.",
            "Southwest": "S.W.",
            # Legal terms
            "Administrator": "Adm'r",
            "Administratrix": "Adm'x",
            "Attorney": "Att'y",
            "Executor": "Ex'r",
            "Executrix": "Ex'x"
        }
        
        # Words that should NOT be abbreviated in case names
        self.no_abbreviate = {
            "United States", "State", "People", "Commonwealth", "City", "County",
            "In re", "Ex parte", "Matter of"
        }
    
    def _init_court_mappings(self):
        """Initialize court abbreviations for parenthetical information."""
        self.court_abbreviations = {
            # Federal Courts
            "U.S.": "U.S.",
            "United States Supreme Court": "U.S.",
            "Supreme Court": "U.S.",
            "U.S. Court of Appeals": "",  # Will be handled with circuit
            "Court of Appeals": "",
            "U.S. District Court": "",  # Will be handled with district
            "District Court": "",
            
            # Circuit Courts
            "1st Cir.": "1st Cir.",
            "2d Cir.": "2d Cir.",
            "3d Cir.": "3d Cir.",
            "4th Cir.": "4th Cir.",
            "5th Cir.": "5th Cir.",
            "6th Cir.": "6th Cir.",
            "7th Cir.": "7th Cir.",
            "8th Cir.": "8th Cir.",
            "9th Cir.": "9th Cir.",
            "10th Cir.": "10th Cir.",
            "11th Cir.": "11th Cir.",
            "D.C. Cir.": "D.C. Cir.",
            "Fed. Cir.": "Fed. Cir.",
            
            # State Supreme Courts (examples)
            "Washington Supreme Court": "Wash.",
            "California Supreme Court": "Cal.",
            "New York Court of Appeals": "N.Y.",
            "Texas Supreme Court": "Tex.",
            "Florida Supreme Court": "Fla.",
        }
    
    def _init_reporter_mappings(self):
        """Initialize proper reporter abbreviations."""
        self.reporter_abbreviations = {
            # U.S. Supreme Court
            "U.S.": "U.S.",
            "S. Ct.": "S. Ct.",
            "L. Ed.": "L. Ed.",
            "L. Ed. 2d": "L. Ed. 2d",
            
            # Federal Reporters
            "F.": "F.",
            "F.2d": "F.2d",
            "F.3d": "F.3d",
            "F.4th": "F.4th",
            "F. Supp.": "F. Supp.",
            "F. Supp. 2d": "F. Supp. 2d",
            "F. Supp. 3d": "F. Supp. 3d",
            
            # Regional Reporters
            "A.": "A.",
            "A.2d": "A.2d",
            "A.3d": "A.3d",
            "N.E.": "N.E.",
            "N.E.2d": "N.E.2d",
            "N.E.3d": "N.E.3d",
            "N.W.": "N.W.",
            "N.W.2d": "N.W.2d",
            "N.W.3d": "N.W.3d",
            "P.": "P.",
            "P.2d": "P.2d",
            "P.3d": "P.3d",
            "S.E.": "S.E.",
            "S.E.2d": "S.E.2d",
            "S.E.3d": "S.E.3d",
            "So.": "So.",
            "So. 2d": "So. 2d",
            "So. 3d": "So. 3d",
            "S.W.": "S.W.",
            "S.W.2d": "S.W.2d",
            "S.W.3d": "S.W.3d",
            
            # State Reporters (examples)
            "Wash.": "Wash.",
            "Wash. 2d": "Wash. 2d",
            "Wn.2d": "Wash. 2d",  # Normalize to standard form
            "Wn. 2d": "Wash. 2d",
            "Cal.": "Cal.",
            "Cal. 2d": "Cal. 2d",
            "Cal. 3d": "Cal. 3d",
            "Cal. 4th": "Cal. 4th",
            "Cal. 5th": "Cal. 5th",
            "N.Y.": "N.Y.",
            "N.Y.2d": "N.Y.2d",
            "N.Y.3d": "N.Y.3d"
        }
    
    def format_case_name(self, case_name: str) -> str:
        """
        Format case name according to Bluebook rules.
        
        Args:
            case_name: Raw case name
            
        Returns:
            Properly formatted case name
        """
        if not case_name:
            return ""
        
        # Clean up the case name
        case_name = case_name.strip()
        
        # Handle "In re" and "Ex parte" cases
        if case_name.startswith(("In re ", "Ex parte ", "Matter of ")):
            return case_name
        
        # Split on " v. " or " vs. "
        if " v. " in case_name:
            parties = case_name.split(" v. ", 1)
        elif " vs. " in case_name:
            parties = case_name.split(" vs. ", 1)
            case_name = " v. ".join(parties)  # Normalize to " v. "
        else:
            return case_name
        
        if len(parties) == 2:
            plaintiff = self._abbreviate_party_name(parties[0].strip())
            defendant = self._abbreviate_party_name(parties[1].strip())
            return f"{plaintiff} v. {defendant}"
        
        return case_name
    
    def _abbreviate_party_name(self, party_name: str) -> str:
        """Apply Bluebook abbreviations to a party name."""
        # Don't abbreviate certain government entities
        if any(no_abbrev in party_name for no_abbrev in self.no_abbreviate):
            return party_name
        
        # Apply abbreviations
        for full_word, abbrev in self.case_name_abbreviations.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(full_word) + r'\b'
            party_name = re.sub(pattern, abbrev, party_name, flags=re.IGNORECASE)
        
        return party_name
    
    def format_citation(self, citation: str) -> str:
        """
        Format citation string according to Bluebook spacing and abbreviation rules.
        
        Args:
            citation: Raw citation string
            
        Returns:
            Properly formatted citation
        """
        if not citation:
            return ""
        
        citation = citation.strip()
        
        # Normalize reporter abbreviations
        for variant, standard in self.reporter_abbreviations.items():
            # Create pattern that matches the reporter abbreviation
            pattern = r'\b' + re.escape(variant) + r'\b'
            citation = re.sub(pattern, standard, citation, flags=re.IGNORECASE)
        
        # Fix spacing issues
        citation = self._fix_citation_spacing(citation)
        
        return citation
    
    def _fix_citation_spacing(self, citation: str) -> str:
        """Fix common spacing issues in citations."""
        # Fix spacing around periods in reporter abbreviations
        # F.3d -> F.3d (correct)
        # F. 3d -> F.3d
        citation = re.sub(r'F\.\s+(\d+d)', r'F.\1', citation)
        citation = re.sub(r'A\.\s+(\d+d)', r'A.\1', citation)
        citation = re.sub(r'P\.\s+(\d+d)', r'P.\1', citation)
        citation = re.sub(r'S\.\s*E\.\s+(\d+d)', r'S.E.\1', citation)
        citation = re.sub(r'N\.\s*E\.\s+(\d+d)', r'N.E.\1', citation)
        citation = re.sub(r'N\.\s*W\.\s+(\d+d)', r'N.W.\1', citation)
        citation = re.sub(r'S\.\s*W\.\s+(\d+d)', r'S.W.\1', citation)
        citation = re.sub(r'So\.\s+(\d+d)', r'So. \1', citation)  # "So. 2d" has space
        
        # Fix "F. Supp." spacing
        citation = re.sub(r'F\.\s*Supp\.\s*(\d+d)?', lambda m: f"F. Supp.{' ' + m.group(1) if m.group(1) else ''}", citation)
        
        # Fix "L. Ed." spacing
        citation = re.sub(r'L\.\s*Ed\.\s*(\d+d)?', lambda m: f"L. Ed.{' ' + m.group(1) if m.group(1) else ''}", citation)
        
        # Fix "S. Ct." spacing
        citation = re.sub(r'S\.\s*Ct\.', 'S. Ct.', citation)
        
        return citation
    
    def extract_citation_components(self, citation: str) -> Dict[str, Optional[str]]:
        """
        Extract components from a citation string.
        
        Args:
            citation: Citation string to parse
            
        Returns:
            Dictionary with volume, reporter, page, and pinpoint
        """
        components: Dict[str, Optional[str]] = {
            'volume': None,
            'reporter': None,
            'page': None,
            'pinpoint': None
        }
        
        # Basic pattern: Volume Reporter Page
        pattern = r'(\d+)\s+([A-Za-z.\s\d]+?)\s+(\d+)(?:\s*,\s*(\d+))?'
        match = re.search(pattern, citation)
        
        if match:
            components['volume'] = match.group(1)
            components['reporter'] = match.group(2).strip()
            components['page'] = match.group(3)
            if match.group(4):
                components['pinpoint'] = match.group(4)
        
        return components
    
    def format_full_citation(self, case_name: str, citation: str, year: Optional[str] = None, 
                           court: Optional[str] = None, pinpoint: Optional[str] = None) -> BluebookCitation:
        """
        Create a complete Bluebook citation.
        
        Args:
            case_name: Case name
            citation: Citation string
            year: Year of decision
            court: Court that decided the case
            pinpoint: Pinpoint citation (page number)
            
        Returns:
            BluebookCitation object with properly formatted citation
        """
        formatted_case_name = self.format_case_name(case_name)
        formatted_citation = self.format_citation(citation)
        formatted_court = self._format_court(court) if court else None
        
        return BluebookCitation(
            case_name=formatted_case_name,
            citation=formatted_citation,
            year=year,
            court=formatted_court,
            pinpoint=pinpoint
        )
    
    def _format_court(self, court: str) -> Optional[str]:
        """Format court name for parenthetical."""
        if not court:
            return None
        
        # Check for exact matches first
        for court_name, abbrev in self.court_abbreviations.items():
            if court_name.lower() in court.lower():
                return abbrev if abbrev else None
        
        # Handle circuit courts
        circuit_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s+cir', court, re.IGNORECASE)
        if circuit_match:
            circuit_num = circuit_match.group(1)
            if circuit_num == "1":
                return "1st Cir."
            elif circuit_num == "2":
                return "2d Cir."
            elif circuit_num == "3":
                return "3d Cir."
            else:
                return f"{circuit_num}th Cir."
        
        # Handle D.C. Circuit
        if "d.c." in court.lower() and "cir" in court.lower():
            return "D.C. Cir."
        
        # Handle Federal Circuit
        if "fed" in court.lower() and "cir" in court.lower():
            return "Fed. Cir."
        
        # For unknown courts, return abbreviated form
        return court
    
    def format_citation_for_export(self, citation_data: Dict) -> str:
        """
        Format a citation dictionary for export in proper Bluebook format.
        
        Args:
            citation_data: Dictionary containing citation information
            
        Returns:
            Properly formatted Bluebook citation string
        """
        case_name = citation_data.get('canonical_name') or citation_data.get('extracted_case_name', '')
        citation = citation_data.get('citation', '')
        year = citation_data.get('canonical_date') or citation_data.get('extracted_date', '')
        court = citation_data.get('court', '')
        
        # Extract year from date if it's a full date
        if year and len(year) > 4:
            year_match = re.search(r'\b(19|20)\d{2}\b', year)
            if year_match:
                year = year_match.group()
        
        bluebook_citation = self.format_full_citation(case_name, citation, year, court)
        return bluebook_citation.full_citation


# Convenience functions
def format_citation_bluebook(case_name: str, citation: str, year: Optional[str] = None, 
                           court: Optional[str] = None) -> str:
    """
    Convenience function to format a single citation in Bluebook format.
    
    Args:
        case_name: Case name
        citation: Citation string  
        year: Year of decision
        court: Court name
        
    Returns:
        Formatted Bluebook citation
    """
    formatter = BluebookFormatter()
    bluebook_citation = formatter.format_full_citation(case_name, citation, year, court)
    return bluebook_citation.full_citation


def format_citations_bluebook(citations: List[Dict]) -> List[str]:
    """
    Format multiple citations in Bluebook format.
    
    Args:
        citations: List of citation dictionaries
        
    Returns:
        List of formatted Bluebook citations
    """
    formatter = BluebookFormatter()
    return [formatter.format_citation_for_export(citation) for citation in citations]


if __name__ == "__main__":
    # Test the Bluebook formatter
    formatter = BluebookFormatter()
    
    # Test cases
    test_cases = [
        {
            'canonical_name': 'State v. Sample Case',
            'citation': '171 Wash. 2d 486',
            'canonical_date': '2011',
            'court': 'Washington Supreme Court'
        },
        {
            'canonical_name': 'United States v. Nixon',
            'citation': '418 U.S. 683',
            'canonical_date': '1974',
            'court': 'U.S.'
        },
        {
            'canonical_name': 'Brown v. Board of Education',
            'citation': '347 U.S. 483',
            'canonical_date': '1954',
            'court': 'U.S.'
        }
    ]
    
    print("Testing Bluebook Citation Formatter:")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        formatted = formatter.format_citation_for_export(test_case)
        print(f"{i}. {formatted}")
    
    print("\nTesting individual components:")
    print("Case name formatting:")
    print(f"  'State v. Sample Corporation' -> '{formatter.format_case_name('State v. Sample Corporation')}'")
    print(f"  'In re Marriage of Smith' -> '{formatter.format_case_name('In re Marriage of Smith')}'")
    
    print("\nCitation formatting:")
    print(f"  '171 Wn.2d 486' -> '{formatter.format_citation('171 Wn.2d 486')}'")
    print(f"  '123 F. 3d 456' -> '{formatter.format_citation('123 F. 3d 456')}'")
