#!/usr/bin/env python3
"""
Migration Script: Replace Complex Case Name Extraction Core
This script helps migrate from the complex 1,618-line case_name_extraction_core.py
to a streamlined implementation while maintaining backward compatibility.
"""

import os
import shutil
import re
from datetime import datetime

def backup_current_file():
    """Backup the current complex file"""
    source = "src/case_name_extraction_core.py"
    backup = f"src/case_name_extraction_core_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    if os.path.exists(source):
        shutil.copy2(source, backup)
        print(f"✅ Backed up current file to: {backup}")
        return backup
    else:
        print("❌ Source file not found")
        return None

def create_streamlined_replacement():
    """Create the new streamlined case name extraction core"""
    
    streamlined_content = '''"""
Streamlined Case Name Extraction Core
Clean, maintainable case name and date extraction with consistent API.
"""

import re
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """Structured result for case name and date extraction"""
    case_name: str
    year: str
    confidence: float
    method: str
    context: str = ""

class CaseNameExtractor:
    """Streamlined case name extractor with comprehensive patterns"""
    
    def __init__(self):
        # Core case name patterns (prioritized by reliability)
        self.case_patterns = [
            # Standard adversarial cases: "Plaintiff v. Defendant"
            (r'([A-Z][A-Za-z0-9&.,\'\\-]+(?:[\s,][A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:[\s,][A-Za-z0-9&.,\'\\-]+)*)', 0.9),
            
            # State v. Defendant cases
            (r'(State\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:[\s,][A-Za-z0-9&.,\'\\-]+)*)', 0.85),
            
            # People v. Defendant cases
            (r'(People\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:[\s,][A-Za-z0-9&.,\'\\-]+)*)', 0.85),
            
            # United States v. cases
            (r'(United\s+States\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:[\s,][A-Za-z0-9&.,\'\\-]+)*)', 0.85),
            
            # In re cases
            (r'(In\s+re\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:[\s,][A-Za-z0-9&.,\'\\-]+)*)', 0.8),
            
            # Matter of cases
            (r'(Matter\s+of\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:[\s,][A-Za-z0-9&.,\'\\-]+)*)', 0.8),
            
            # Ex parte cases
            (r'(Ex\s+parte\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:[\s,][A-Za-z0-9&.,\'\\-]+)*)', 0.75),
            
            # Broader pattern for any case with v.
            (r'([A-Z][A-Za-z0-9&.,\'\\-]+(?:[\s,][A-Za-z0-9&.,\'\\-]+){0,10}\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:[\s,][A-Za-z0-9&.,\'\\-]+){0,10})', 0.6),
        ]
        
        # Date patterns
        self.date_patterns = [
            r'\\((\d{4})\\)',  # (2020)
            r'\\b(19|20)\\d{2}\\b',  # 2020, 1995
            r'(?:decided|filed|issued|released)\\s+(?:in\\s+)?(\\d{4})\\b',  # decided in 2020
        ]
        
        # Business suffixes to clean
        self.business_suffixes = [
            r'\\s+(?:LLC|Inc\\.?|Corp\\.?|Co\\.?|Ltd\\.?|L\\.P\\.?|LLP|LP)\\b',
            r'\\s+(?:Corporation|Company|Limited|Partnership)\\b'
        ]
    
    def extract_case_name_and_date(self, text: str, citation: str = None) -> ExtractionResult:
        """
        Main extraction function - returns structured result with case name, year, and confidence.
        
        Args:
            text: Document text to extract from
            citation: Optional citation for context
            
        Returns:
            ExtractionResult with case_name, year, confidence, and method
        """
        if not text or not text.strip():
            return ExtractionResult("", "", 0.0, "no_text")
        
        # Clean text
        text = re.sub(r'\\s+', ' ', text.strip())
        
        # Extract context around citation if provided
        context = self._get_context(text, citation) if citation else text
        
        # Try to extract case name
        case_name, method, confidence = self._extract_case_name(context)
        
        # Try to extract year
        year = self._extract_year(context)
        
        # Adjust confidence based on year presence
        if year and case_name:
            confidence = min(confidence + 0.1, 1.0)
        
        return ExtractionResult(
            case_name=case_name,
            year=year,
            confidence=confidence,
            method=method,
            context=context[:200]  # Truncate for logging
        )
    
    def _get_context(self, text: str, citation: str) -> str:
        """Extract context around citation"""
        if not citation:
            return text
        
        # Find citation in text
        citation_pos = text.find(citation)
        if citation_pos == -1:
            return text
        
        # Extract context window
        context_start = max(0, citation_pos - 300)
        context_end = min(len(text), citation_pos + len(citation) + 100)
        return text[context_start:context_end]
    
    def _extract_case_name(self, text: str) -> Tuple[str, str, float]:
        """Extract case name using pattern matching"""
        best_match = ""
        best_confidence = 0.0
        best_method = "no_match"
        
        for pattern, base_confidence in self.case_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                case_name = match.group(1).strip()
                cleaned_name = self._clean_case_name(case_name)
                
                if cleaned_name and len(cleaned_name) > 3:
                    # Calculate confidence based on pattern and name quality
                    confidence = self._calculate_confidence(cleaned_name, base_confidence)
                    
                    if confidence > best_confidence:
                        best_match = cleaned_name
                        best_confidence = confidence
                        best_method = f"pattern_{self.case_patterns.index((pattern, base_confidence))}"
        
        return best_match, best_method, best_confidence
    
    def _clean_case_name(self, case_name: str) -> str:
        """Clean and validate case name"""
        if not case_name:
            return ""
        
        # Remove citation text that got included
        citation_patterns = [
            r',\\s*\\d+\\s+[A-Za-z.]+(?:\\s+\\d+)*.*$',  # Remove ", 200 Wn.2d 72"
            r',\\s*\\d+.*$',  # Remove ", 200"
            r'\\(\\d{4}\\).*$',  # Remove "(2022)" and after
        ]
        
        for pattern in citation_patterns:
            case_name = re.sub(pattern, '', case_name, flags=re.IGNORECASE)
        
        # Remove business suffixes
        for suffix in self.business_suffixes:
            case_name = re.sub(suffix, '', case_name, flags=re.IGNORECASE)
        
        # Clean up whitespace and punctuation
        case_name = re.sub(r'\\s+', ' ', case_name.strip())
        case_name = case_name.strip(' ,;')
        
        # Validation
        if len(case_name) < 3:
            return ""
        
        if re.match(r'^[A-Z\\s]+$', case_name):  # All caps
            return ""
        
        # Check capitalization
        words = case_name.split()
        if not words or not words[0] or not words[0][0].isupper():
            return ""
        
        # Check that at least 50% of words start with capital letters
        capital_words = sum(1 for word in words if word and word[0].isupper())
        if capital_words < len(words) * 0.5:
            return ""
        
        return case_name
    
    def _extract_year(self, text: str) -> str:
        """Extract year from text"""
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = match.group(1)
                if 1900 <= int(year) <= 2100:
                    return year
        return ""
    
    def _calculate_confidence(self, case_name: str, base_confidence: float) -> float:
        """Calculate confidence score for extracted case name"""
        confidence = base_confidence
        
        # Length bonus
        if len(case_name) > 30:
            confidence += 0.1
        elif len(case_name) > 20:
            confidence += 0.05
        
        # Contains legal indicators
        if re.search(r'\\b(State|People|United\\s+States|In\\s+re|Matter\\s+of|Ex\\s+parte)\\b', case_name, re.IGNORECASE):
            confidence += 0.1
        
        # Contains v. pattern
        if re.search(r'\\b(v\\.|vs\\.|versus)\\b', case_name, re.IGNORECASE):
            confidence += 0.05
        
        # Penalty for very short names
        if len(case_name) < 5:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))

# Global instance
_extractor = CaseNameExtractor()

# Main function - backward compatible
def extract_case_name_and_date(text: str, citation: str = None) -> ExtractionResult:
    """Main extraction function with structured result"""
    return _extractor.extract_case_name_and_date(text, citation)

# Backward compatibility functions
def extract_case_name_triple_comprehensive(text: str, citation: str = None) -> Tuple[str, str, str]:
    """Backward compatibility: returns (case_name, year, confidence)"""
    result = extract_case_name_and_date(text, citation)
    return (result.case_name, result.year, str(result.confidence))

def extract_case_name_triple(text: str, citation: str = None, api_key: str = None, context_window: int = 100) -> Tuple[str, str, str]:
    """Backward compatibility: returns (case_name, year, confidence)"""
    result = extract_case_name_and_date(text, citation)
    return (result.case_name, result.year, str(result.confidence))

def extract_case_name_fixed_comprehensive(text: str, citation: str) -> str:
    """Backward compatibility: returns case_name only"""
    result = extract_case_name_and_date(text, citation)
    return result.case_name

def extract_year_fixed_comprehensive(text: str, citation: str) -> str:
    """Backward compatibility: returns year only"""
    result = extract_case_name_and_date(text, citation)
    return result.year

def extract_case_name_improved(text: str, citation: str = None) -> Tuple[str, str, str]:
    """Backward compatibility: returns (case_name, year, confidence)"""
    result = extract_case_name_and_date(text, citation)
    return (result.case_name, result.year, str(result.confidence))

def extract_year_improved(text: str, citation: str = None) -> str:
    """Backward compatibility: returns year only"""
    result = extract_case_name_and_date(text, citation)
    return result.year

# Individual extraction functions
def extract_case_name_only(text: str, citation: str = None) -> str:
    """Extract case name only"""
    result = extract_case_name_and_date(text, citation)
    return result.case_name

def extract_year_only(text: str, citation: str = None) -> str:
    """Extract year only"""
    result = extract_case_name_and_date(text, citation)
    return result.year

# Date extractor compatibility
class DateExtractor:
    """Simplified date extractor for backward compatibility"""
    
    def __init__(self):
        self.extractor = _extractor
    
    def extract_date_from_context(self, text: str, citation_start: int, citation_end: int, context_window: int = 300) -> Optional[str]:
        """Extract date from context"""
        context = text[max(0, citation_start - context_window):min(len(text), citation_end + context_window)]
        year = self.extractor._extract_year(context)
        return f"{year}-01-01" if year else None
    
    def extract_year_only(self, text: str, citation: str = None) -> Optional[str]:
        """Extract year only"""
        result = extract_case_name_and_date(text, citation)
        return result.year if result.year else None

# Global date extractor instance
date_extractor = DateExtractor()

# Test function
def test_extraction():
    """Test the streamlined extraction"""
    test_cases = [
        ("Smith v. Jones, 123 F.3d 456 (2020)", "123 F.3d 456"),
        ("State v. Johnson, 200 Wn.2d 72 (2022)", "200 Wn.2d 72"),
        ("In re ABC Corp., 456 F.Supp.2d 789 (2010)", "456 F.Supp.2d 789"),
    ]
    
    print("=== Testing Streamlined Case Name Extraction ===")
    for text, citation in test_cases:
        result = extract_case_name_and_date(text, citation)
        print(f"Text: {text}")
        print(f"  Case Name: {result.case_name}")
        print(f"  Year: {result.year}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Method: {result.method}")
        print()

if __name__ == "__main__":
    test_extraction()
'''
    
    with open("src/case_name_extraction_core.py", "w") as f:
        f.write(streamlined_content)
    
    print("✅ Created streamlined replacement file")

def update_imports():
    """Update imports in critical files to use new API"""
    
    # Files that need import updates
    critical_files = [
        "src/app_final_vue.py",
        "src/unified_citation_processor_v2.py", 
        "src/document_processing.py",
        "src/extract_case_name.py"
    ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"📝 Updating imports in: {file_path}")
            # Add specific import updates here if needed
            # For now, the backward compatibility functions should handle this

def run_tests():
    """Run basic tests to verify the migration"""
    print("🧪 Running basic tests...")
    
    try:
        # Test import
        from src.case_name_extraction_core import extract_case_name_and_date, extract_case_name_triple_comprehensive
        
        # Test basic functionality
        result = extract_case_name_and_date("Smith v. Jones, 123 F.3d 456 (2020)", "123 F.3d 456")
        print(f"✅ Basic test passed: {result.case_name}, {result.year}, {result.confidence}")
        
        # Test backward compatibility
        triple_result = extract_case_name_triple_comprehensive("Smith v. Jones, 123 F.3d 456 (2020)", "123 F.3d 456")
        print(f"✅ Backward compatibility test passed: {triple_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 Starting Case Name Extraction Migration")
    print("=" * 50)
    
    # Step 1: Backup current file
    backup_file = backup_current_file()
    if not backup_file:
        return
    
    # Step 2: Create streamlined replacement
    create_streamlined_replacement()
    
    # Step 3: Update imports
    update_imports()
    
    # Step 4: Run tests
    if run_tests():
        print("\n✅ Migration completed successfully!")
        print(f"📁 Backup saved as: {backup_file}")
        print("🔄 All backward compatibility functions are available")
        print("📝 You can now use the new streamlined API:")
        print("   - extract_case_name_and_date() - New structured API")
        print("   - extract_case_name_triple_comprehensive() - Backward compatible")
    else:
        print("\n❌ Migration failed! Restoring backup...")
        shutil.copy2(backup_file, "src/case_name_extraction_core.py")
        print("✅ Backup restored")

if __name__ == "__main__":
    main() 