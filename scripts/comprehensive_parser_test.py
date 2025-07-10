#!/usr/bin/env python3
"""
Comprehensive citation parser test script.
"""

import re
from typing import Optional, List, Dict, Tuple

class CitationParser:
    """
    Comprehensive parser for complex legal citations with parallel citations and pinpoints.
    
    Handles patterns like:
    - 171 Wn.2d 486, 493, 256 P.3d 321, 325-26 (2011)
    - 123 Wash. 456, 789 P.2d 123 (1995)
    - 456 U.S. 789, 101 S.Ct. 234, 67 L.Ed.2d 890 (1982)
    """
    
    # Common reporter patterns
    REPORTERS = {
        # Washington
        r'Wn\.?(?:\s*2d)?': 'Wn.2d',
        r'Wash\.?(?:\s*2d)?': 'Wash.2d', 
        r'Wn\.?\s*App\.?(?:\s*2d)?': 'Wn.App.2d',
        r'Wash\.?\s*App\.?(?:\s*2d)?': 'Wash.App.2d',
        
        # Pacific
        r'P\.?(?:\s*2d|\s*3d)?': 'P.3d',
        r'Pac\.?(?:\s*2d|\s*3d)?': 'Pac.3d',
        
        # Federal
        r'U\.?S\.?': 'U.S.',
        r'S\.?\s*Ct\.?': 'S.Ct.',
        r'L\.?\s*Ed\.?(?:\s*2d)?': 'L.Ed.2d',
        r'F\.?(?:\s*2d|\s*3d|\s*4th)?': 'F.3d',
        r'F\.?\s*Supp\.?(?:\s*2d|\s*3d)?': 'F.Supp.3d',
        
        # Other common reporters
        r'Cal\.?(?:\s*2d|\s*3d|\s*4th)?': 'Cal.4th',
        r'N\.?Y\.?(?:\s*2d|\s*3d)?': 'N.Y.3d',
        r'Ill\.?(?:\s*2d|\s*3d)?': 'Ill.3d',
    }
    
    def __init__(self):
        # Build comprehensive citation pattern
        reporter_pattern = '|'.join(f'(?:{pattern})' for pattern in self.REPORTERS.keys())
        
        # Pattern components:
        # Volume: 1-3 digits
        # Reporter: one of the archetypes
        # Page: starting page number
        # Pinpoint: optional specific page(s) - can be single number or range
        # Multiple parallel citations possible
        # Year at the end in parentheses
        
        self.citation_pattern = rf'''
            (?P<volume1>\d{{1,3}})\s+                           # Volume (1-3 digits)
            (?P<reporter1>{reporter_pattern})\s+                # Reporter
            (?P<page1>\d+)                                      # Starting page
            (?:,\s*(?P<pinpoint1>\d+(?:-\d+)??))?               # Optional pinpoint (single or range)
            (?:                                                 # Optional parallel citations
                ,\s*(?P<volume2>\d{{1,3}})\s+                   # Parallel volume
                (?P<reporter2>{reporter_pattern})\s+            # Parallel reporter  
                (?P<page2>\d+)                                  # Parallel page
                (?:,\s*(?P<pinpoint2>\d+(?:-\d+)?))?            # Optional parallel pinpoint
            )?
            (?:                                                 # Optional second parallel citation
                ,\s*(?P<volume3>\d{{1,3}})\s+                   # Second parallel volume
                (?P<reporter3>{reporter_pattern})\s+            # Second parallel reporter
                (?P<page3>\d+)                                  # Second parallel page
                (?:,\s*(?P<pinpoint3>\d+(?:-\d+)?))?            # Optional second parallel pinpoint
            )?
            \s*\((?P<year>\d{{4}})\)                            # Year in parentheses
        '''
        
        self.compiled_pattern = re.compile(self.citation_pattern, re.VERBOSE | re.IGNORECASE)
    
    def parse_json_citation(self, json_citation: str) -> Dict:
        """
        Parse a JSON citation format like '171 Wash. 2d 486 256 P.3d 321'
        into components for finding the full citation in text.
        """
        parts = json_citation.split()
        result = {
            'primary_volume': None,
            'primary_reporter': None, 
            'primary_page': None,
            'parallel_volume': None,
            'parallel_reporter': None,
            'parallel_page': None
        }
        
        if len(parts) >= 4:
            result['primary_volume'] = parts[0]
            # Handle multi-part reporters like "Wash. 2d"
            if len(parts) > 4 and parts[2].isdigit():
                # Format: 171 Wash. 2d 486 ...
                result['primary_reporter'] = f"{parts[1]} {parts[2]}"
                result['primary_page'] = parts[3]
                if len(parts) >= 7:
                    result['parallel_volume'] = parts[4]
                    result['parallel_reporter'] = parts[5]
                    result['parallel_page'] = parts[6]
            else:
                # Format: 171 Wn.2d 486 ...
                result['primary_reporter'] = parts[1]
                result['primary_page'] = parts[2]
                if len(parts) >= 5:
                    result['parallel_volume'] = parts[3]
                    result['parallel_reporter'] = parts[4] 
                    result['parallel_page'] = parts[5] if len(parts) > 5 else parts[4]
        
        return result
    
    def find_full_citation_in_text(self, text: str, json_citation: str) -> Optional[str]:
        """
        Find the complete citation in text that corresponds to the JSON citation.
        """
        parsed = self.parse_json_citation(json_citation)
        
        if not parsed['primary_volume'] or not parsed['primary_page']:
            return None
        
        # Convert reporter formats for searching
        search_reporters = []
        if parsed['primary_reporter']:
            # Try multiple variations
            reporter = parsed['primary_reporter']
            if 'Wash.' in reporter:
                search_reporters.extend(['Wn.2d', 'Wn. 2d', 'Wash. 2d', 'Wash.2d'])
            elif 'Wn.' in reporter:
                search_reporters.extend(['Wn.2d', 'Wn. 2d', 'Wash. 2d', 'Wash.2d'])
            else:
                search_reporters.append(reporter)
        
        # Build search patterns
        volume = parsed['primary_volume']
        page = parsed['primary_page']
        
        for reporter in search_reporters:
            # Escape special regex characters
            escaped_reporter = re.escape(reporter)
            
            # Try different pattern variations
            patterns = [
                # Full pattern with parallel citation and pinpoints
                rf'{volume}\s+{escaped_reporter}\s+{page}(?:,\s*\d+(?:-\d+)?)?(?:,\s*\d{{1,3}}\s+[A-Z][\w\.\s]+\d+(?:,\s*\d+(?:-\d+)?)?)*\s*\(\d{{4}}\)',
                
                # Simpler pattern with just primary citation
                rf'{volume}\s+{escaped_reporter}\s+{page}[,\s\d\w\.\-]*\(\d{{4}}\)',
                
                # Very flexible pattern
                rf'{volume}\s+{escaped_reporter.replace(r"\ ", r"\s*")}\s+{page}[^()]*\(\d{{4}}\)'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    return match.group(0)
        
        return None
    
    def extract_year_from_citation(self, full_citation: str) -> Optional[str]:
        """Extract year from a full citation."""
        year_match = re.search(r'\((\d{4})\)', full_citation)
        return year_match.group(1) if year_match else None
    
    def find_case_name_before_citation(self, text: str, full_citation: str) -> Optional[str]:
        """Find case name in the text before the citation."""
        citation_pos = text.find(full_citation)
        if citation_pos == -1:
            return None
        
        # Get context before citation
        before_text = text[:citation_pos].strip()
        
        # Split by sentence markers
        sentences = re.split(r'[.;]\s*', before_text)
        if not sentences:
            return None
        
        # Look in the last sentence for case name patterns
        last_sentence = sentences[-1].strip()
        
        case_patterns = [
            # Standard: Name v. Name (with comma ending)
            r'([A-Z][A-Za-z\'\.\s,&]*\s+v\.?\s+[A-Z][A-Za-z\'\.\s,&]*?)(?:\s*,\s*)?$',
            
            # Department/Agency cases: Dep't of ... v. ...
            r'(Dep\'t\s+of\s+[A-Za-z\s,&]*\s+v\.?\s+[A-Za-z\s,&]*?)(?:\s*,\s*)?$',
            
            # Department (spelled out): Department of ... v. ...
            r'(Department\s+of\s+[A-Za-z\s,&]*\s+v\.?\s+[A-Za-z\s,&]*?)(?:\s*,\s*)?$',
            
            # In re cases
            r'(In\s+re\s+[A-Za-z\s,&]*?)(?:\s*,\s*)?$',
            
            # Estate cases
            r'(Estate\s+of\s+[A-Za-z\s,&]*?)(?:\s*,\s*)?$',
            
            # State cases
            r'(State\s+v\.?\s+[A-Za-z\s,&]*?)(?:\s*,\s*)?$',
            
            # People cases
            r'(People\s+v\.?\s+[A-Za-z\s,&]*?)(?:\s*,\s*)?$',
            
            # United States cases
            r'(United\s+States\s+v\.?\s+[A-Za-z\s,&]*?)(?:\s*,\s*)?$',
        ]
        
        for pattern in case_patterns:
            match = re.search(pattern, last_sentence, re.IGNORECASE)
            if match:
                case_name = match.group(1).strip().rstrip(',').strip()
                
                # Validate it looks like a valid case name
                if self._is_valid_case_name(case_name):
                    return case_name
        
        return None
    
    def _is_valid_case_name(self, case_name: str) -> bool:
        """Validate if extracted text looks like a real case name."""
        if not case_name or len(case_name) < 5:
            return False
        
        # Must contain v. or vs. or be special case types
        case_indicators = [
            r'\s+v\.?\s+',
            r'\s+vs\.?\s+', 
            r'^In\s+re\s+',
            r'^Estate\s+of\s+',
            r'^State\s+v\.?\s+',
            r'^People\s+v\.?\s+',
            r'^United\s+States\s+v\.?\s+',
            r'^Dep\'t\s+of\s+.*\s+v\.?\s+',
            r'^Department\s+of\s+.*\s+v\.?\s+'
        ]
        
        for indicator in case_indicators:
            if re.search(indicator, case_name, re.IGNORECASE):
                return True
        
        return False
    
    def extract_from_text(self, text: str, json_citation: str) -> Dict[str, Optional[str]]:
        """
        Main extraction method - finds case name and year from text using JSON citation.
        """
        result = {
            'case_name': None,
            'year': None,
            'full_citation_found': None,
            'extraction_method': None
        }
        
        # Step 1: Find the full citation in text
        full_citation = self.find_full_citation_in_text(text, json_citation)
        if not full_citation:
            result['extraction_method'] = 'citation_not_found'
            return result
        
        result['full_citation_found'] = full_citation
        
        # Step 2: Extract year from full citation
        year = self.extract_year_from_citation(full_citation)
        if year:
            result['year'] = year
        
        # Step 3: Find case name before citation
        case_name = self.find_case_name_before_citation(text, full_citation)
        if case_name:
            result['case_name'] = case_name
            result['extraction_method'] = 'successful_extraction'
        else:
            result['extraction_method'] = 'case_name_not_found'
        
        return result

def test_comprehensive_parser():
    """Test the comprehensive citation parser."""
    
    text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)"""
    
    test_cases = [
        {
            'json_citation': '200 Wash. 2d 72, 514 P.3d 643',
            'expected_case_name': 'Convoyant, LLC v. DeepThink, LLC',
            'expected_year': '2022'
        },
        {
            'json_citation': '171 Wash. 2d 486 256 P.3d 321',
            'expected_case_name': 'Carlsen v. Glob. Client Sols., LLC',
            'expected_year': '2011'
        },
        {
            'json_citation': '146 Wash. 2d 1 43 P.3d 4',
            'expected_case_name': 'Dep\'t of Ecology v. Campbell & Gwinn, LLC',
            'expected_year': '2002'
        }
    ]
    
    parser = CitationParser()
    
    for i, test_case in enumerate(test_cases):
        print(f"\n=== TEST CASE {i+1} ===")
        print(f"JSON Citation: {test_case['json_citation']}")
        
        result = parser.extract_from_text(text, test_case['json_citation'])
        
        print(f"Full Citation Found: '{result['full_citation_found']}'")
        print(f"Extracted Case Name: '{result['case_name']}'")
        print(f"Expected Case Name: '{test_case['expected_case_name']}'")
        print(f"Case Name Match: {result['case_name'] == test_case['expected_case_name']}")
        
        print(f"Extracted Year: '{result['year']}'")
        print(f"Expected Year: '{test_case['expected_year']}'")
        print(f"Year Match: {result['year'] == test_case['expected_year']}")
        
        print(f"Extraction Method: {result['extraction_method']}")
        
        if result['case_name'] == test_case['expected_case_name'] and result['year'] == test_case['expected_year']:
            print("✅ SUCCESS: Both case name and year extracted correctly")
        else:
            print("❌ FAILED: Extraction did not match expected results")

if __name__ == "__main__":
    test_comprehensive_parser() 