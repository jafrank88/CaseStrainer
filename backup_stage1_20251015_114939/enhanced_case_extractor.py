#!/usr/bin/env python3
"""
Enhanced Case Extractor - Integrates LegalCaseExtractor with adaptive ToA finder
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import time

@dataclass
class CaseExtraction:
    """Represents an extracted legal case citation"""
    full_match: str
    case_name: str
    party_1: Optional[str] = None
    party_2: Optional[str] = None
    volume: Optional[str] = None
    reporter: Optional[str] = None
    page: Optional[str] = None
    pincite: Optional[str] = None
    year: Optional[str] = None
    case_type: Optional[str] = None  # 'standard', 'in_re', 'ex_parte'
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None

class LegalCaseExtractor:
    """Extract legal case names with citations and years from legal documents"""
    
    def __init__(self):
        self.patterns = self._compile_patterns()
        self.reporter_patterns = self._get_reporter_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile all regex patterns for case extraction"""
        patterns = {}
        
        # Standard adversarial cases (Party v. Party)
        patterns['standard'] = re.compile(
            r'(?:see\s+(?:also\s+)?)?'  # Optional "see" or "see also"
            r'([A-Z][^,]*?(?:Inc\.|Corp\.|LLC|Co\.|Ltd\.|et al\.)?)'  # Party 1
            r'\s+v\.\s+'  # " v. "
            r'([^,]+?(?:Inc\.|Corp\.|LLC|Co\.|Ltd\.|et al\.)?)'  # Party 2
            r',\s*'  # Comma separator
            r'(\d+)\s+'  # Volume
            r'([A-Z]+\.?\d*[a-z]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pincite
            r'.*?'  # Optional additional citation info
            r'\(([^)]*\d{4}[^)]*)\)',  # Year in parentheses
            re.IGNORECASE
        )
        
        # In re cases
        patterns['in_re'] = re.compile(
            r'(?:see\s+(?:also\s+)?)?'  # Optional "see" or "see also"
            r'In re\s+'  # "In re "
            r'([^,]+?)'  # Case subject
            r',\s*'  # Comma separator
            r'(\d+)\s+'  # Volume
            r'([A-Z]+\.?\d*[a-z]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pincite
            r'.*?'  # Optional additional citation info
            r'\(([^)]*\d{4}[^)]*)\)',  # Year in parentheses
            re.IGNORECASE
        )
        
        # Ex parte cases
        patterns['ex_parte'] = re.compile(
            r'(?:see\s+(?:also\s+)?)?'  # Optional "see" or "see also"
            r'Ex parte\s+'  # "Ex parte "
            r'([^,]+?)'  # Case subject
            r',\s*'  # Comma separator
            r'(\d+)\s+'  # Volume
            r'([A-Z]+\.?\d*[a-z]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pincite
            r'.*?'  # Optional additional citation info
            r'\(([^)]*\d{4}[^)]*)\)',  # Year in parentheses
            re.IGNORECASE
        )
        
        # Matter of cases
        patterns['matter_of'] = re.compile(
            r'(?:see\s+(?:also\s+)?)?'  # Optional "see" or "see also"
            r'Matter of\s+'  # "Matter of "
            r'([^,]+?)'  # Case subject
            r',\s*'  # Comma separator
            r'(\d+)\s+'  # Volume
            r'([A-Z]+\.?\d*[a-z]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pincite
            r'.*?'  # Optional additional citation info
            r'\(([^)]*\d{4}[^)]*)\)',  # Year in parentheses
            re.IGNORECASE
        )
        
        return patterns
    
    def _get_reporter_patterns(self) -> Dict[str, List[str]]:
        """Define common legal reporter abbreviations by jurisdiction"""
        return {
            'federal': [
                'F\\.', 'F\\.2d', 'F\\.3d', 'F\\.4th',
                'F\\.Supp\\.', 'F\\.Supp\\.2d', 'F\\.Supp\\.3d',
                'F\\.R\\.D\\.'
            ],
            'supreme_court': [
                'U\\.S\\.', 'S\\.Ct\\.', 'L\\.Ed\\.', 'L\\.Ed\\.2d'
            ],
            'state': [
                'P\\.', 'P\\.2d', 'P\\.3d',
                'A\\.', 'A\\.2d', 'A\\.3d',
                'N\\.E\\.', 'N\\.E\\.2d', 'N\\.E\\.3d',
                'S\\.E\\.', 'S\\.E\\.2d', 'S\\.E\\.3d',
                'S\\.W\\.', 'S\\.W\\.2d', 'S\\.W\\.3d',
                'So\\.', 'So\\.2d', 'So\\.3d',
                'N\\.W\\.', 'N\\.W\\.2d', 'N\\.W\\.3d'
            ]
        }
    
    def extract_cases(self, text: str) -> List[CaseExtraction]:
        """Extract all legal cases from text"""
        extractions = []
        
        for case_type, pattern in self.patterns.items():
            matches = pattern.finditer(text)
            
            for match in matches:
                extraction = self._parse_match(match, case_type)
                if extraction:
                    extractions.append(extraction)
        
        # Remove duplicates and sort by position
        extractions = self._deduplicate_extractions(extractions)
        return sorted(extractions, key=lambda x: x.start_pos or 0)
    
    def _parse_match(self, match: re.Match, case_type: str) -> Optional[CaseExtraction]:
        """Parse a regex match into a CaseExtraction object"""
        try:
            groups = match.groups()
            
            if case_type == 'standard':
                return CaseExtraction(
                    full_match=match.group(0),
                    case_name=f"{groups[0]} v. {groups[1]}",
                    party_1=groups[0].strip(),
                    party_2=groups[1].strip(),
                    volume=groups[2],
                    reporter=groups[3],
                    page=groups[4],
                    pincite=groups[5] if len(groups) > 5 and groups[5] else None,
                    year=self._extract_year(groups[6] if len(groups) > 6 else groups[5]),
                    case_type='standard',
                    start_pos=match.start(),
                    end_pos=match.end()
                )
            
            elif case_type in ['in_re', 'ex_parte', 'matter_of']:
                prefix = case_type.replace('_', ' ').title()
                return CaseExtraction(
                    full_match=match.group(0),
                    case_name=f"{prefix} {groups[0]}",
                    party_1=groups[0].strip(),
                    volume=groups[1],
                    reporter=groups[2],
                    page=groups[3],
                    pincite=groups[4] if len(groups) > 4 and groups[4] else None,
                    year=self._extract_year(groups[5] if len(groups) > 5 else groups[4]),
                    case_type=case_type,
                    start_pos=match.start(),
                    end_pos=match.end()
                )
            
        except (IndexError, AttributeError):
            return None
        
        return None
    
    def _extract_year(self, year_string: str) -> Optional[str]:
        """Extract 4-digit year from year string"""
        if not year_string:
            return None
        
        year_match = re.search(r'(\d{4})', year_string)
        return year_match.group(1) if year_match else None
    
    def _deduplicate_extractions(self, extractions: List[CaseExtraction]) -> List[CaseExtraction]:
        """Remove duplicate extractions based on position overlap"""
        if not extractions:
            return []
        
        # Sort by start position
        sorted_extractions = sorted(extractions, key=lambda x: x.start_pos or 0)
        deduplicated = [sorted_extractions[0]]
        
        for extraction in sorted_extractions[1:]:
            # Check if this extraction overlaps with the last one
            last_extraction = deduplicated[-1]
            if (extraction.start_pos >= last_extraction.end_pos or 
                extraction.end_pos <= last_extraction.start_pos):
                deduplicated.append(extraction)
        
        return deduplicated
    
    def validate_against_toa(self, body_extractions: List[CaseExtraction], 
                            toa_extractions: List[CaseExtraction]) -> Dict[str, List[CaseExtraction]]:
        """Validate body extractions against Table of Authorities"""
        toa_case_names = {ext.case_name.lower() for ext in toa_extractions}
        
        validated = []
        unvalidated = []
        
        for extraction in body_extractions:
            if extraction.case_name.lower() in toa_case_names:
                validated.append(extraction)
            else:
                unvalidated.append(extraction)
        
        return {
            'validated': validated,
            'unvalidated': unvalidated,
            'toa_only': [ext for ext in toa_extractions 
                        if ext.case_name.lower() not in 
                        {ext.case_name.lower() for ext in body_extractions}]
        }
    
    def get_extraction_stats(self, extractions: List[CaseExtraction]) -> Dict[str, int]:
        """Get statistics about extractions"""
        stats = {
            'total': len(extractions),
            'standard': len([e for e in extractions if e.case_type == 'standard']),
            'in_re': len([e for e in extractions if e.case_type == 'in_re']),
            'ex_parte': len([e for e in extractions if e.case_type == 'ex_parte']),
            'matter_of': len([e for e in extractions if e.case_type == 'matter_of']),
            'with_pincites': len([e for e in extractions if e.pincite])
        }
        return stats

class EnhancedCaseAnalyzer:
    """Enhanced analyzer that combines ToA extraction with case extraction"""
    
    def __init__(self):
        self.toa_finder = self._create_toa_finder()
        self.case_extractor = LegalCaseExtractor()
    
    def _create_toa_finder(self):
        """Create a simple ToA finder (simplified version of your adaptive finder)"""
        class SimpleToAFinder:
            def extract_toa(self, text: str) -> Optional[str]:
                text_upper = text.upper()
                if 'TABLE OF AUTHORITIES' in text_upper:
                    start = text_upper.find('TABLE OF AUTHORITIES')
                    # Find end by looking for next major section
                    end_markers = ['I.', 'II.', 'ARGUMENT', 'CONCLUSION']
                    end = len(text)
                    for marker in end_markers:
                        pos = text_upper.find(marker, start + 100)
                        if pos != -1 and pos < end:
                            end = pos
                    return text[start:end]
                return None
        return SimpleToAFinder()
    
    def analyze_brief(self, text: str, brief_name: str = "") -> Dict:
        """Analyze a brief for ToA and case extractions"""
        start_time = time.time()
        
        # Extract ToA
        toa_text = self.toa_finder.extract_toa(text)
        
        # Extract cases from body and ToA
        body_cases = self.case_extractor.extract_cases(text)
        toa_cases = self.case_extractor.extract_cases(toa_text) if toa_text else []
        
        # Validate cases
        validation = self.case_extractor.validate_against_toa(body_cases, toa_cases)
        
        # Get statistics
        body_stats = self.case_extractor.get_extraction_stats(body_cases)
        toa_stats = self.case_extractor.get_extraction_stats(toa_cases)
        
        analysis_time = time.time() - start_time
        
        return {
            'brief_name': brief_name,
            'toa_found': toa_text is not None,
            'toa_length': len(toa_text) if toa_text else 0,
            'body_cases': body_cases,
            'toa_cases': toa_cases,
            'validation': validation,
            'body_stats': body_stats,
            'toa_stats': toa_stats,
            'analysis_time': analysis_time
        }
    
    def print_analysis(self, analysis: Dict):
        """Print a formatted analysis report"""
        print(f"\n=== Analysis: {analysis['brief_name']} ===")
        print(f"ToA found: {analysis['toa_found']}")
        print(f"ToA length: {analysis['toa_length']} characters")
        print(f"Analysis time: {analysis['analysis_time']:.3f}s")
        
        print(f"\nBody Cases: {analysis['body_stats']['total']}")
        print(f"  Standard: {analysis['body_stats']['standard']}")
        print(f"  In re: {analysis['body_stats']['in_re']}")
        print(f"  Ex parte: {analysis['body_stats']['ex_parte']}")
        print(f"  Matter of: {analysis['body_stats']['matter_of']}")
        
        print(f"\nToA Cases: {analysis['toa_stats']['total']}")
        print(f"  Standard: {analysis['toa_stats']['standard']}")
        print(f"  In re: {analysis['toa_stats']['in_re']}")
        print(f"  Ex parte: {analysis['toa_stats']['ex_parte']}")
        print(f"  Matter of: {analysis['toa_stats']['matter_of']}")
        
        validation = analysis['validation']
        print(f"\nValidation Results:")
        print(f"  Validated: {len(validation['validated'])}")
        print(f"  Unvalidated: {len(validation['unvalidated'])}")
        print(f"  ToA only: {len(validation['toa_only'])}")
        
        # Show some examples
        if validation['unvalidated']:
            print(f"\nUnvalidated cases (in body but not in ToA):")
            for case in validation['unvalidated'][:3]:
                print(f"  - {case.case_name}")
        
        if validation['toa_only']:
            print(f"\nToA-only cases (in ToA but not in body):")
            for case in validation['toa_only'][:3]:
                print(f"  - {case.case_name}")

def main():
    """Test the enhanced case analyzer"""
    analyzer = EnhancedCaseAnalyzer()
    
    briefs_dir = Path("wa_briefs_text")
    if not briefs_dir.exists():
        print("wa_briefs_text directory not found!")
        return
    
    brief_files = sorted(list(briefs_dir.glob("*.txt")))[:3]
    print("=== Enhanced Case Analysis Test ===\n")
    
    for brief_file in brief_files:
        print(f"Processing: {brief_file.name}")
        print(f"File size: {brief_file.stat().st_size} bytes")
        
        try:
            text = brief_file.read_text(encoding="utf-8")
            analysis = analyzer.analyze_brief(text, brief_file.name)
            analyzer.print_analysis(analysis)
            
        except Exception as e:
            print(f"Error processing file: {e}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    main() 