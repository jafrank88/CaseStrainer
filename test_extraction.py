#!/usr/bin/env python3
"""
Enhanced case name extraction with improved patterns and context handling.
"""
import re
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable, Pattern, Tuple, Any
from functools import lru_cache

@dataclass
class ExtractionResult:
    """Container for case name extraction results."""
    case_name: str = ""
    confidence: float = 0.0
    method: str = ""
    raw_matches: List[str] = field(default_factory=list)
    context: str = ""
    position: Tuple[int, int] = (0, 0)
    validation_errors: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0

class CaseNameExtractor:
    """Enhanced case name extractor with improved patterns and context handling."""
    
    def __init__(self, enable_cache: bool = True, max_cache_size: int = 1000):
        self.enable_cache = enable_cache
        self._cache = {}
        self._max_cache_size = max_cache_size
        self._setup_patterns()
        self._setup_validation_rules()
    
    def _setup_patterns(self):
        """Initialize and compile regex patterns for case name extraction."""
        self.patterns = [
            # Standard v. format (e.g., "Smith v. Jones")
            {
                'name': 'standard_v',
                'pattern': r'([A-Z][A-Za-z\-\']+(?:,?\s+(?:[A-Z]\.?\s+)*[A-Z][A-Za-z\-\']+)*)\s+v\.?\s+([A-Z][A-Za-z\-\']+(?:,?\s+(?:[A-Z]\.?\s+)*[A-Z][A-Za-z\-\']+)*)',
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'confidence': 0.95,
                'context_before': 100,
                'context_after': 50
            },
            # Standard vs. format (e.g., "Smith vs. Jones")
            {
                'name': 'standard_vs',
                'pattern': r'([A-Z][A-Za-z\-\']+(?:,?\s+(?:[A-Z]\.?\s+)*[A-Z][A-Za-z\-\']+)*)\s+vs\.?\s+([A-Z][A-Za-z\-\']+(?:,?\s+(?:[A-Z]\.?\s+)*[A-Z][A-Za-z\-\']+)*)',
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'confidence': 0.9,
                'context_before': 100,
                'context_after': 50
            },
            # In re format (e.g., "In re Smith")
            {
                'name': 'in_re',
                'pattern': r'(?:^|\W)In\s+re\s+([A-Z][A-Za-z\-\']+(?:\s+[A-Z][A-Za-z\-\']+)*)',
                'format': lambda m: f"In re {m.group(1).strip()}",
                'confidence': 0.9,
                'context_before': 50,
                'context_after': 30
            },
            # Ex parte format (e.g., "Ex parte Smith")
            {
                'name': 'ex_parte',
                'pattern': r'(?:^|\W)Ex\s+parte\s+([A-Z][A-Za-z\-\']+(?:\s+[A-Z][A-Za-z\-\']+)*)',
                'format': lambda m: f"Ex parte {m.group(1).strip()}",
                'confidence': 0.9,
                'context_before': 50,
                'context_after': 30
            },
            # The [Party] v. [Party] format at start of sentence or after common prefixes
            {
                'name': 'sentence_start',
                'pattern': r'(?:^|\b(?:In|The\s+case\s+of|See|See\s+also|Cf\.?|E\.g\.?|I\.e\.?|But\s+see|But\s+cf\.?|Compare|Accord|But\s+see\s+also|See\s+generally|See\s+e\.g\.|See\s+also|See\s+id\.|Id\.|Id\s+at|Id\.\s+at|Id\.\s+\*\d+|\(?:(?:[A-Za-z]\s*,\s*)*[A-Za-z]\s+)?(?:holding|concluding|finding|stating|reasoning|explaining|affirming|reversing|remanding|vacating|denying|granting|dismissing)\b[^\n\.;:]+?[;:,\s])([A-Z][A-Za-z\-\']+(?:,?\s+(?:[A-Z]\.?\s+)*[A-Z][A-Za-z\-\']+)*\s+v\.?\s+[A-Z][A-Za-z\-\']+(?:,?\s+(?:[A-Z]\.?\s+)*[A-Z][A-Za-z\-\']+)*)',
                'format': lambda m: m.group(2).strip(),
                'confidence': 0.92,
                'context_before': 200,
                'context_after': 100
            },
            # Case name followed by citation in parentheses
            {
                'name': 'with_citation',
                'pattern': r'([A-Z][A-Za-z\-\']+(?:,?\s+(?:[A-Z]\.?\s+)*[A-Z][A-Za-z\-\']+)*\s+v\.?\s+[A-Z][A-Za-z\-\']+(?:,?\s+(?:[A-Z]\.?\s+)*[A-Z][A-Za-z\-\']+)*)\s*\([^)]*\d+\s+[A-Za-z\.]+\s+\d+[^)]*\)',
                'format': lambda m: m.group(1).strip(),
                'confidence': 0.93,
                'context_before': 100,
                'context_after': 50
            }
        
        # Compile all patterns with re.IGNORECASE flag
        for p in self.patterns:
            p['compiled'] = re.compile(p['pattern'], re.IGNORECASE)
    
    def _setup_validation_rules(self):
        """Set up validation rules for extracted case names."""
        self.validation_rules = {
            'min_length': 5,
            'max_length': 200,
            'banned_phrases': [
                # Citation patterns
                r'\b\d+\s+[A-Za-z\.]+\s+\d+\b',  # e.g., 123 F.3d 456
                r'\b\d+\s+[A-Za-z\.]+\s+\d+\s+\d+\b',  # e.g., 410 U.S. 113
                # Legal references
                r'\b(see also|see,? e\.g\.|cf\.|id\.|supra|infra|et\s+seq\.|et\s+al\.|e\.g\.|i\.e\.|\d{4})\b',
                # Legal actions
                r'\b(holding|concluding|finding|stating|reasoning|explaining|affirming|reversing|remanding|vacating|denying|granting|dismissing)\b',
                # Case metadata
                r'\b(case|matter|appeal|petition|in the matter of|re:)\b',
                # Court names
                r'\b(court|panel|circuit|district|supreme court|appellate court|appellate division|court of appeals)\b',
                # Common false positives
                r'\b(opinion|judgment|order|memorandum|decision|ruling|case no\.?|docket no\.?|no\.\s*\d+)\b',
                # Page/paragraph references
                r'\b(page|p\.?|para\.?|¶)\s*\d+\b',
                # Years
                r'\b(19|20)\d{2}\b'
            ],
            'min_confidence': 0.5
        }
    
    @lru_cache(maxsize=1000)
    def extract_case_name(self, text: str, citation: str = None) -> ExtractionResult:
        """Extract case name from text, optionally near a citation.
        
        Args:
            text: The text to search for case names
            citation: Optional citation to search near
            
        Returns:
            ExtractionResult containing the extracted case name and metadata
        """
        start_time = time.time()
        result = ExtractionResult()
        
        try:
            # Generate a cache key
            cache_key = f"{hash(text[:100])}:{hash(citation) if citation else 'none'}"
            
            # Check cache if enabled
            if self.enable_cache and cache_key in self._cache:
                return self._cache[cache_key]
            
            # If citation is provided, try to find case name near it
            if citation:
                citation_pos = text.find(citation)
                if citation_pos != -1:
                    # Try different context windows around the citation
                    for window_size in [200, 100, 50]:
                        context_start = max(0, citation_pos - window_size)
                        context_end = min(len(text), citation_pos + len(citation) + window_size)
                        context = text[context_start:context_end]
                        
                        # Try to find case names in this context
                        result = self._extract_from_text(context)
                        if result.case_name:
                            # Adjust position to be relative to full text
                            result.position = (
                                context_start + result.position[0],
                                context_start + result.position[1]
                            )
                            result.context = context
                            break
            
            # If no match found near citation or no citation provided, try the whole text
            if not result.case_name:
                result = self._extract_from_text(text)
                result.context = text[:200] + '...' if len(text) > 200 else text
            
            # Calculate processing time
            result.processing_time_ms = (time.time() - start_time) * 1000
            
            # Cache the result
            if self.enable_cache:
                self._cache[cache_key] = result
                # Limit cache size
                if len(self._cache) > self._max_cache_size:
                    self._cache.pop(next(iter(self._cache)))
            
            return result
            
        except Exception as e:
            result.validation_errors.append(f"Error during extraction: {str(e)}")
            result.processing_time_ms = (time.time() - start_time) * 1000
            return result
    
    def _extract_from_text(self, text: str) -> ExtractionResult:
        """Extract case name from the given text with enhanced validation.
        
        Args:
            text: The text to search for case names
            
        Returns:
            ExtractionResult with the best match and metadata
        """
        result = ExtractionResult()
        
        # Try each pattern and keep track of the best match
        for pattern_info in sorted(self.patterns, key=lambda x: -x['confidence']):
            matches = list(pattern_info['compiled'].finditer(text))
            
            for match in matches:
                case_name = pattern_info['format'](match)
                confidence = pattern_info['confidence']
                
                # Apply position-based scoring (higher is better)
                position_score = self._calculate_position_score(match.start(), len(text))
                confidence *= position_score
                
                # Check if this is the best match so far
                if (self._is_valid_case_name(case_name) and 
                    confidence > result.confidence and 
                    confidence >= self.validation_rules['min_confidence']):
                    
                    # Clean up the case name
                    cleaned_name = self._clean_case_name(case_name)
                    
                    # Only update if cleaning didn't invalidate the name
                    if self._is_valid_case_name(cleaned_name):
                        result.case_name = cleaned_name
                        result.confidence = min(confidence, 1.0)
                        result.method = pattern_info['name']
                        result.raw_matches = [match.group(0)]
                        result.position = (match.start(), match.end())
        
        return result
    
    def _calculate_position_score(self, match_start: int, text_length: int) -> float:
        """Calculate a score based on the position of the match in the text.
        
        Higher scores are given to matches that appear earlier in the text,
        as case names are more likely to appear near the beginning.
        """
        if text_length == 0:
            return 1.0
            
        # Normalize position to 0-1 range (0 = start, 1 = end)
        position_ratio = match_start / text_length
        
        # Higher score for matches earlier in the text
        # This is a simple linear decay, but could be adjusted
        return max(0.5, 1.0 - (position_ratio * 0.5))
    
    def _clean_case_name(self, case_name: str) -> str:
        """Clean up a case name by removing common issues."""
        if not case_name:
            return ""
            
        # Remove leading/trailing whitespace and punctuation
        cleaned = case_name.strip(' .,;:()[]{}')
        
        # Remove common prefixes
        prefixes = ["In the matter of ", "In re ", "Ex parte ", "The "]
        for prefix in prefixes:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        # Clean up any remaining punctuation
        cleaned = re.sub(r'[\[\]{}()\";,]+', '', cleaned)
        
        # Standardize spacing around 'v.'
        cleaned = re.sub(r'\s+v\.?\s+', ' v. ', cleaned, flags=re.IGNORECASE)
        
        # Remove any remaining leading/trailing whitespace
        return cleaned.strip()
    
    def _is_valid_case_name(self, case_name: str) -> bool:
        """Validate that a potential case name meets all criteria.
        
        Args:
            case_name: The case name to validate
            
        Returns:
            bool: True if the case name appears valid, False otherwise
        """
        if not case_name:
            return False
            
        # Check length constraints
        if (len(case_name) < self.validation_rules['min_length'] or 
            len(case_name) > self.validation_rules['max_length']):
            return False
        
        # Check for banned phrases
        for pattern in self.validation_rules['banned_phrases']:
            if re.search(pattern, case_name, re.IGNORECASE):
                return False
        
        # Check if it matches any of our case name patterns
        case_lower = case_name.lower()
        
        # Check for standard v. format (e.g., "Smith v. Jones")
        if ' v. ' in case_lower or ' vs. ' in case_lower or ' v ' in case_lower:
            return self._has_valid_party_structure(case_name)
        
        # Check for in re format
        if 'in re ' in case_lower:
            parts = re.split(r'in\s+re\s+', case_name, flags=re.IGNORECASE)
            if len(parts) >= 2 and parts[1].strip():
                return True
        
        # Check for ex parte format
        if 'ex parte ' in case_lower:
            parts = re.split(r'ex\s+parte\s+', case_name, flags=re.IGNORECASE)
            if len(parts) >= 2 and parts[1].strip():
                return True
        
        # If we get here, it doesn't match any known case name format
        return False
    
    def _has_valid_party_structure(self, case_name: str) -> bool:
        """Check if the case name has a valid party structure."""
        if not case_name:
            return False
            
        # Clean up the case name first
        case_name = case_name.strip()
        
        # Standard v. format (e.g., "Smith v. Jones")
        if ' v. ' in case_name or ' vs. ' in case_name or ' v ' in case_name.lower():
            # Split on v., vs., or v (with optional periods and spaces)
            parties = re.split(r'\s+v\.?\s+|\s+vs\.?\s+|\s+v\s+', case_name, flags=re.IGNORECASE)
            if len(parties) >= 2:
                # Handle cases with citations or other text after the defendant's name
                plaintiff = parties[0].strip()
                defendant = re.split(r'[,\s]', parties[1].strip(), 1)[0].strip()
                
                # Basic validation of party names
                return (self._is_valid_party_name(plaintiff) and 
                        self._is_valid_party_name(defendant))
        
        # In re format (e.g., "In re Smith")
        elif ' in re ' in case_name.lower():
            parts = re.split(r'in\s+re\s+', case_name, flags=re.IGNORECASE)
            if len(parts) >= 2:
                name = re.split(r'[,\s]', parts[1].strip(), 1)[0].strip()
                return self._is_valid_party_name(name)
        
        # Ex parte format (e.g., "Ex parte Smith")
        elif ' ex parte ' in case_name.lower():
            parts = re.split(r'ex\s+parte\s+', case_name, flags=re.IGNORECASE)
            if len(parts) >= 2:
                name = re.split(r'[,\s]', parts[1].strip(), 1)[0].strip()
                return self._is_valid_party_name(name)
                    
        return False
    
    def _is_valid_party_name(self, name: str) -> bool:
        """Check if a party name is valid."""
        if not name or not name.strip():
            return False
            
        name = name.strip()
        
        # Check for minimum length (at least 2 characters)
        if len(name) < 2:
            return False
            
        # Check for at least one letter
        if not any(c.isalpha() for c in name):
            return False
            
        # Remove common titles and suffixes
        name_clean = re.sub(
            r'\b(Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Hon\.?|Judge|Justice|Chief Justice|J\.|C\.J\.|P\.J\.|Inc\.?|L\.?L\.?C\.?|L\.?P\.?|Corp\.?|Co\.?|Ltd\.?|P\.?C\.?|et\s+al\.?)\b', 
            '', name, flags=re.IGNORECASE).strip()
        
        # Remove any remaining punctuation except spaces, hyphens, and ampersands
        name_clean = re.sub(r'[^\w\s\-&]', '', name_clean).strip()
        
        # If after cleaning we have nothing left, it's not a valid name
        if not name_clean:
            return False
            
        # Check for invalid patterns
        invalid_patterns = [
            r'^\s*$',  # Empty or whitespace only
            r'^[A-Z]\.?$',  # Single initial
            r'^\d+$',  # Numbers only
            r'^[^a-zA-Z]+$',  # No letters
            r'\b(and|or|the|of|in|for|at|on|by|with|to|from|et|al|no|case|matter|appeal|petition|re|ex|parte|in re|ex parte|v|vs|versus)\b',
            r'\b(court|judge|justice|panel|circuit|district|supreme|appellate|division|county|state|federal|united states|u\.?s\.?|f\.?d\.?|f\.?supp\.?|f\.?3d|so\.?2d)\b',
            r'\d{4}',  # Years
            r'[^\w\s\-&]',  # Invalid characters (after cleanup)
            r'\b(case|matter|appeal|petition|re:)\b'  # Common false positives
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, name_clean, re.IGNORECASE):
                return False
                
        return True

def test_with_document():
    """Test case name extraction with various document types and formats."""
    print("=== Testing Enhanced Case Name Extraction ===\n")
    
    # Initialize the extractor with caching enabled
    extractor = CaseNameExtractor(enable_cache=True)
    
    # Test cases with different formats and scenarios
    test_cases = [
        {
            'name': 'Standard v. format',
            'text': "In Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), the court held that...",
            'citation': "123 F.3d 456",
            'expected': "Smith v. Jones"
        },
        {
            'name': 'Standard vs. format',
            'text': "The case of Roe vs. Wade, 410 U.S. 113 (1973), established...",
            'citation': "410 U.S. 113",
            'expected': "Roe v. Wade"
        },
        {
            'name': 'In re format',
            'text': "The bankruptcy court's decision in In re Smith, 123 B.R. 45 (Bankr. 9th Cir. 1990) held that...",
            'citation': "123 B.R. 45",
            'expected': "In re Smith"
        },
        {
            'name': 'Ex parte format',
            'text': "The court granted the petition for a writ of habeas corpus in Ex parte Smith, 123 S.W.3d 1 (Tex. 2003).",
            'citation': "123 S.W.3d 1",
            'expected': "Ex parte Smith"
        },
        {
            'name': 'Error document (no case names)',
            'text': """
            # Syntax Error Fix Summary

            ## Problem

            The URL upload tool failed with the following error:

            {
                "success": false,
                "processing_mode": "enqueue_failed",
                "error_details": "Error 111 connecting to 127.0.0.1:6379. Connection refused."
            }
            """,
            'citation': "127.0.0.1:6379",
            'expected': ""
        },
        {
            'name': 'Multiple cases in text',
            'text': """
            In Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), the court followed the reasoning 
            of Doe v. Roe, 456 F.3d 789 (2d Cir. 2019), but distinguished it from 
            Johnson v. Smith, 789 F.3d 123 (D.C. Cir. 2021).
            """,
            'citation': "456 F.3d 789",
            'expected': "Doe v. Roe"
        },
        {
            'name': 'Case at start of sentence',
            'text': "Smith v. Jones established the precedent that...",
            'citation': None,
            'expected': "Smith v. Jones"
        },
        {
            'name': 'False positive prevention',
            'text': "The court held that the defendant's argument, while creative, was without merit.",
            'citation': None,
            'expected': ""
        }
    ]
    
    # Run all test cases
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print("-" * 50)
        
        # Extract case name
        if test['citation']:
            result = extractor.extract_case_name(test['text'], test['citation'])
            print(f"  Citation: {test['citation']}")
        else:
            result = extractor.extract_case_name(test['text'])
        
        # Print results
        print(f"  Extracted: {result.case_name or '[No case name found]'}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Method: {result.method}")
        
        # Check if the result matches the expected value
        if test['expected']:
            if result.case_name == test['expected']:
                print(f"  ✅ Expected: {test['expected']}")
            else:
                print(f"  ❌ Expected: {test['expected']}")
        else:
            if not result.case_name:
                print("  ✅ Correctly found no case name")
            else:
                print(f"  ❌ Expected no case name but found: {result.case_name}")
        
        # Print processing time if available
        if hasattr(result, 'processing_time_ms'):
            print(f"  Processing time: {result.processing_time_ms:.2f}ms")
        
        # Print validation errors if any
        if hasattr(result, 'validation_errors') and result.validation_errors:
            print("  Validation errors:")
            for error in result.validation_errors:
                print(f"    - {error}")
    
    # Performance test with a large document
    print("\n=== Performance Test ===")
    large_doc = """
    # Legal Document with Multiple Citations
    
    In the case of Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), the court considered
    the application of the precedent set in Doe v. Roe, 456 F.3d 789 (2d Cir. 2019).
    The court found the reasoning in Johnson v. Smith, 789 F.3d 123 (D.C. Cir. 2021)
    to be more persuasive in this matter.
    
    The plaintiff argued that under the standard established in Brown v. Board of Education,
    347 U.S. 483 (1954), the defendant's actions were unconstitutional. However, the
    defendant countered by citing the more recent decision in Citizens United v. FEC,
    558 U.S. 310 (2010).
    
    The court also considered the bankruptcy court's ruling in In re Smith, 123 B.R. 45
    (Bankr. 9th Cir. 1990), as well as the Supreme Court's decision in Marbury v. Madison,
    5 U.S. 137 (1803), which established the principle of judicial review.
    
    In its analysis, the court distinguished the present case from the facts of
    Plessy v. Ferguson, 163 U.S. 537 (1896), and instead found the reasoning in
    Obergefell v. Hodges, 576 U.S. 644 (2015), to be more applicable.
    """ * 10  # Repeat to make it larger
    
    print("\nTesting with a large document ({} characters)...".format(len(large_doc)))
    
    # Time the extraction
    start_time = time.time()
    result = extractor.extract_case_name(large_doc, "123 F.3d 456")
    elapsed = (time.time() - start_time) * 1000
    
    print(f"  Extracted: {result.case_name or '[No case name found]'}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Processing time: {elapsed:.2f}ms")
    
    # Cache test
    print("\n=== Cache Test ===")
    start_time = time.time()
    for _ in range(100):
        extractor.extract_case_name("Smith v. Jones, 123 F.3d 456 (9th Cir. 2020)")
    cached_time = (time.time() - start_time) * 1000
    
    # Disable cache and test again
    extractor.enable_cache = False
    start_time = time.time()
    for _ in range(100):
        extractor.extract_case_name("Smith v. Jones, 123 F.3d 456 (9th Cir. 2020)")
    uncached_time = (time.time() - start_time) * 1000
    
    print(f"  100 extractions with cache: {cached_time:.2f}ms")
    print(f"  100 extractions without cache: {uncached_time:.2f}ms")
    print(f"  Cache speedup: {uncached_time / cached_time:.1f}x")
    
    print("\n=== Test Complete ===\n")

if __name__ == "__main__":
    test_with_document()
