"""
Standalone Citation Parser
A simple citation parser that doesn't depend on other modules to avoid circular imports.
"""

import re
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class CitationParser:
    """
    Simple citation parser for extracting case names and dates from text.
    """
    
    def __init__(self):
        # Enhanced case name patterns to capture full case names including LLC parts
        self.case_name_patterns = [
            # Most comprehensive: v. or vs. or versus, allow for LLC, Inc., etc., and ampersands, apostrophes
            r"([A-Z][A-Za-z&\s,\.\'\-]{1,120}?\s+v\.?\s+[A-Z][A-Za-z&\s,\.\'\-]{1,120}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)",
            r"([A-Z][A-Za-z&\s,\.\'\-]{1,120}?\s+vs\.?\s+[A-Z][A-Za-z&\s,\.\'\-]{1,120}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)",
            r"([A-Z][A-Za-z&\s,\.\'\-]{1,120}?\s+versus\s+[A-Z][A-Za-z&\s,\.\'\-]{1,120}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)",
            # Pattern for Dep't of cases
            r"(Dep't\s+of\s+[A-Za-z&\s,\.\'\-]{1,120}?\s+v\.?\s+[A-Za-z&\s,\.\'\-]{1,120}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)",
            r"(Department\s+of\s+[A-Za-z&\s,\.\'\-]{1,120}?\s+v\.?\s+[A-Za-z&\s,\.\'\-]{1,120}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)",
            # In re cases
            r"(In\s+re\s+[A-Za-z&\s,\.\'\-]{1,120}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)",
            # Estate of cases
            r"(Estate\s+of\s+[A-Za-z&\s,\.\'\-]{1,120}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)",
            # State/People/United States cases
            r"(State\s+v\.?\s+[A-Za-z&\s,\.\'\-]{1,120}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)",
            r"(People\s+v\.?\s+[A-Za-z&\s,\.\'\-]{1,120}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)",
            r"(United\s+States\s+v\.?\s+[A-Za-z&\s,\.\'\-]{1,120}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)",
            # Ex rel cases
            r"([A-Z][A-Za-z&\s,\.\'\-]+?\s+ex\s+rel\.?\s+[A-Za-z&\s,\.\'\-]+?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)",
            # Fallback: any v. pattern
            r"([A-Z][A-Za-z&\s,\.\'\-]{1,120}?\s+v\.?\s+[A-Z][A-Za-z&\s,\.\'\-]{1,120}?)(?=\s*[,;:.])",
        ]
        
        # Enhanced date patterns to capture dates from parentheses
        self.date_patterns = [
            r'\((\d{4})\)',  # (2020) - most common format
            r'\((\d{4})\s*\)',  # (2020 ) - with trailing space
            r'\(\s*(\d{4})\s*\)',  # ( 2020 ) - with spaces
            r'\b(\d{4})\b',  # 2020 - standalone year
            # Enhanced patterns from enhanced_extraction_utils.py
            r'(?:decided|filed|issued|released|argued|submitted)\s+(?:in\s+)?(\d{4})\b',
            r'\b(19|20)\d{2}\b',  # Simple year pattern
        ]
    
    def extract_from_text(self, text: str, citation: str) -> Dict[str, Any]:
        """
        Extract case name and date from text using citation as context.
        Now more robust: captures all text from the start of the case name up to the volume number of the citation.
        """
        import logging
        logger = logging.getLogger("case_name_extraction")
        try:
            result = {
                'case_name': None,
                'year': None,
                'full_citation_found': False,
                'extraction_method': 'standalone_parser'
            }

            # Try exact match first
            citation_index = text.find(citation)
            matched_citation = citation
            if citation_index == -1:
                # Try regex match: allow for optional year in parentheses or after comma
                import re
                citation_escaped = re.escape(citation)
                citation_no_year = re.sub(r'\s*\(?\d{4}\)?$', '', citation)
                citation_no_year_escaped = re.escape(citation_no_year.strip())
                pattern = rf'({citation_no_year_escaped})(?:\s*[\(,]\s*(\d{{4}})[\)]?)?'
                match = re.search(pattern, text)
                logger.info(f"[DEBUG] Regex citation search pattern: {pattern}")
                if match:
                    citation_index = match.start(1)
                    matched_citation = match.group(0)
                    if match.lastindex and match.lastindex >= 2 and match.group(2):
                        result['year'] = match.group(2)
                        logger.info(f"[DEBUG] Year found in regex match: {match.group(2)}")
                else:
                    logger.warning(f"[DEBUG] Citation not found by regex in text: '{citation}'")

            if citation_index == -1:
                logger.warning(f"[DEBUG] Citation not found in text: '{citation}'")
                return result

            result['full_citation_found'] = True
            result['matched_citation'] = matched_citation

            # Get context before citation (up to 500 chars)
            context_start = max(0, citation_index - 500)
            context_before = text[context_start:citation_index]

            logger.info(f"[DEBUG] Citation: '{citation}'")
            logger.info(f"[DEBUG] Context before citation (len={len(context_before)}): ...{context_before[-200:]}\n")

            # --- FIXED LOGIC: Extract the last valid case name in the immediate context before the citation ---
            import re
            last_case_name = None
            last_match_end = None
            for pattern in self.case_name_patterns:
                matches = list(re.finditer(pattern, context_before, re.IGNORECASE))
                logger.info(f"[DEBUG] Trying case name pattern: {pattern}")
                if matches:
                    logger.info(f"[DEBUG] {len(matches)} matches found for pattern: {pattern}")
                    for m in matches:
                        logger.info(f"[DEBUG]   Match: '{m.group(1)}'")
                    # Take the last (closest to citation) match
                    match = matches[-1]
                    candidate = match.group(1).strip()
                    candidate = re.sub(r',[\s]*$', '', candidate)
                    if self._is_valid_case_name(candidate):
                        last_case_name = candidate
                        last_match_end = match.end(1)
                        logger.info(f"[DEBUG] Valid case name candidate: '{candidate}'")
                    else:
                        logger.info(f"[DEBUG] Invalid case name candidate: '{candidate}'")
                else:
                    logger.info(f"[DEBUG] No matches for pattern: {pattern}")
            # Append trailing business entity suffixes if present
            if last_case_name and last_match_end is not None:
                suffixes = [
                    ', LLC', ', L.L.C.', ', LLP', ', L.L.P.', ', Inc.', ', Incorporated', ', Ltd.', ', Co.', ', Corp.', ', Corporation', ', P.C.', ', P.A.', ', S.C.', ', N.A.', ', PLC', ', PC', ', LP', ', LLLP', ', PLLC', ', P.L.L.C.'
                ]
                trailing = context_before[last_match_end:]
                suffix_pattern = r'(,\s*(?:LLC|L\.L\.C\.|LLP|L\.L\.P\.|Inc\.|Incorporated|Ltd\.|Co\.|Corp\.|Corporation|P\.C\.|P\.A\.|S\.C\.|N\.A\.|PLC|PC|LP|LLLP|PLLC|P\.L\.L\.C\.))'
                matches = list(re.finditer(suffix_pattern, trailing, re.IGNORECASE))
                if matches:
                    logger.info(f"[DEBUG] Appending business suffixes to case name: {last_case_name}")
                    for m in matches:
                        logger.info(f"[DEBUG]   Suffix found: '{m.group(1)}'")
                        last_case_name += m.group(1)
            if last_case_name:
                result['case_name'] = last_case_name
                logger.info(f"[DEBUG] Final extracted case name: '{last_case_name}'")
            else:
                logger.warning(f"[DEBUG] No valid case name found before citation: '{citation}'")
            # --- END FIXED LOGIC ---

            # Extract year from context before, after, or citation, unless already found
            if not result['year']:
                context_after_start = citation_index + len(matched_citation)
                context_after = text[context_after_start:context_after_start + 100]
                year = self._extract_year_from_context(context_before, matched_citation, context_after)
                if year:
                    result['year'] = year
                    logger.info(f"[DEBUG] Year extracted from context: {year}")
                else:
                    logger.warning(f"[DEBUG] No year found in context for citation: '{citation}'")

            # If no case name found, try fallback using full citation and context
            if not result['case_name']:
                full_citation = self.find_full_citation_in_text(text, citation)
                if full_citation:
                    fallback_case_name = self.find_case_name_before_citation(text, full_citation)
                    if fallback_case_name and self._is_valid_case_name(fallback_case_name):
                        result['case_name'] = fallback_case_name
                        result['extraction_method'] = 'fallback_case_name_before_citation'
                        logger.info(f"[DEBUG] Fallback case name extraction succeeded: '{fallback_case_name}'")
                    else:
                        logger.warning(f"[DEBUG] Fallback case name extraction failed for citation: '{citation}'")
                else:
                    logger.warning(f"[DEBUG] Full citation not found for fallback extraction: '{citation}'")

            return result

        except Exception as e:
            logger.error(f"Error in extract_from_text: {e}")
            return {
                'case_name': None,
                'year': None,
                'full_citation_found': False,
                'extraction_method': f'error: {str(e)}'
            }
    
    def _extract_case_name_from_context(self, context: str) -> Optional[str]:
        """Extract case name from context."""
        try:
            # Look for case names in the last 150 characters (closer to citation)
            recent_context = context[-150:] if len(context) > 150 else context
            logger.debug(f"Case name extraction context: '{recent_context}'")

            # Use patterns as-is without modification
            for pattern in self.case_name_patterns:
                matches = list(re.finditer(pattern, recent_context, re.IGNORECASE))
                if matches:
                    # Take the last (most recent) match
                    match = matches[-1]
                    logger.debug(f"Matched case name: '{match.group(1)}' with pattern: '{pattern}'")
                    case_name = self._clean_case_name(match.group(1))
                    # Additional cleaning: remove leading text that's not part of case name
                    case_name = self._extract_just_case_name(case_name)
                    if self._is_valid_case_name(case_name):
                        return case_name
            return None
        except Exception as e:
            logger.warning(f"Error extracting case name from context: {e}")
            return None
    
    def _extract_just_case_name(self, text: str) -> str:
        """Extract just the case name from potentially longer text."""
        # Look for the last occurrence of a case name pattern
        case_patterns = [
            # More precise patterns to avoid capturing extra text
            r'([A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            r'([A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;])',
            r'([A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)',
            # Pattern for "Dep't of" cases
            r'(Dep\'t\s+of\s+[A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            r'(Dep\'t\s+of\s+[A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)',
        ]
        
        for pattern in case_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                # Take the last match
                match = matches[-1]
                return self._clean_case_name(match.group(1))
        
        return text
    
    def _extract_year_from_context(self, context_before: str, citation: str, context_after: str = None) -> Optional[str]:
        """Extract year from context before citation, after citation, or citation itself."""
        try:
            # PRIORITY 1: Look for year in parentheses in the citation itself (most reliable)
            for pattern in self.date_patterns:
                matches = re.findall(pattern, citation)
                if matches:
                    year = matches[0]
                    if self._is_valid_year(year):
                        return year
            
            # PRIORITY 2: Look for year in parentheses in context after citation
            if context_after:
                for pattern in self.date_patterns:
                    matches = re.findall(pattern, context_after)
                    if matches:
                        # Take the first match (closest to citation)
                        year = matches[0]
                        if self._is_valid_year(year):
                            return year
            
            # PRIORITY 3: Look for year in context before citation
            for pattern in self.date_patterns:
                matches = re.findall(pattern, context_before)
                if matches:
                    # Take the last match (closest to citation)
                    year = matches[-1]
                    if self._is_valid_year(year):
                        return year
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting year from context: {e}")
            return None
    
    def _clean_case_name(self, case_name: str) -> str:
        """Clean and normalize case name while preserving full names."""
        if not case_name:
            return ""
        
        # Remove leading/trailing whitespace
        case_name = case_name.strip()
        
        # Remove leading text that's not part of case name
        # Look for common leading phrases to remove
        leading_patterns = [
            r'^.*?\b(held|in|that|the|principle|applies)\s+',
            r'^.*?\b(court|held|in)\s+',
            r'^.*?\b(federal|court|may|ask|this)\s+',
        ]
        
        for pattern in leading_patterns:
            case_name = re.sub(pattern, '', case_name, flags=re.IGNORECASE)
        
        # Remove trailing punctuation but preserve internal punctuation
        case_name = re.sub(r'[,\s]*$', '', case_name)
        case_name = re.sub(r'[.;:]$', '', case_name)
        
        # Clean up multiple spaces
        case_name = re.sub(r'\s+', ' ', case_name)
        
        # Preserve LLC, Inc., Corp., etc. - don't truncate these
        # Only remove if they're at the very end and not part of the case name
        if case_name.endswith(', LLC') or case_name.endswith(', Inc.') or case_name.endswith(', Corp.'):
            # Keep these as they're part of the case name
            pass
        else:
            # Remove trailing commas and periods that aren't part of abbreviations
            case_name = re.sub(r',\s*$', '', case_name)
            case_name = re.sub(r'\.\s*$', '', case_name)
        
        return case_name.strip()
    
    def _is_valid_case_name(self, case_name: str) -> bool:
        """Validate if a case name looks legitimate."""
        if not case_name or len(case_name.strip()) < 5:
            return False
        
        # Clean the case name
        case_name = case_name.strip()
        
        # Must contain "v." or "vs." (indicating it's a case name)
        if not re.search(r'\bv\.?\s+', case_name, re.IGNORECASE):
            return False
        
        # Must start with a capital letter
        if not case_name[0].isupper():
            return False
        
        # Must not be too long (likely not a case name if > 100 chars)
        if len(case_name) > 100:
            return False
        
        # Must not contain obvious non-case-name text
        invalid_patterns = [
            r'\b(questions?|law|review|de\s+novo|statute|meaning)\b',
            r'\b(certified|we\s+also|review|meaning)\b',
            r'\b(federal\s+court|may\s+ask|this\s+court)\b',
            r'\b(necessary|resolve|case|before|federal)\b',
            r'\b(Washington|law|when|resolution)\b',
            r'\b(held|in|that|the|principle|applies)\b',
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, case_name, re.IGNORECASE):
                return False
        
        return True
    
    def _is_valid_year(self, year: str) -> bool:
        """Validate if extracted text is a valid year."""
        try:
            year_int = int(year)
            return 1800 <= year_int <= 2030
        except (ValueError, TypeError):
            return False 

    def parse_json_citation(self, json_citation: str) -> dict:
        """
        Parse citation string into volume, reporter, page, and parallel citation components.
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
        if len(parts) < 3:
            return result
        i = 0
        if i < len(parts) and parts[i].isdigit():
            result['primary_volume'] = parts[i]
            i += 1
        reporter_parts = []
        while i < len(parts) and not parts[i].isdigit():
            reporter_parts.append(parts[i])
            i += 1
            if len(reporter_parts) >= 3:
                break
            if i < len(parts) and parts[i].isdigit():
                break
        if reporter_parts:
            result['primary_reporter'] = ' '.join(reporter_parts)
        if i < len(parts) and parts[i].isdigit():
            result['primary_page'] = parts[i]
            i += 1
        if i < len(parts):
            if i < len(parts) and parts[i].isdigit():
                result['parallel_volume'] = parts[i]
                i += 1
            parallel_reporter_parts = []
            while i < len(parts) and not parts[i].isdigit():
                parallel_reporter_parts.append(parts[i])
                i += 1
                if len(parallel_reporter_parts) >= 3:
                    break
                if i < len(parts) and parts[i].isdigit():
                    break
            if parallel_reporter_parts:
                result['parallel_reporter'] = ' '.join(parallel_reporter_parts)
            if i < len(parts) and parts[i].isdigit():
                result['parallel_page'] = parts[i]
                i += 1
        return result

    def normalize_reporter(self, reporter: str) -> list:
        """
        Generate all possible variations of a reporter name for matching.
        """
        if not reporter:
            return []
        variations = [reporter]
        if 'Wash' in reporter:
            variations.append(reporter.replace('Wash.', 'Wn.').replace('Wash', 'Wn'))
            variations.append(reporter.replace('Wash.', 'Wn.').replace('Wash', 'Wn.'))
        elif 'Wn' in reporter:
            variations.append(reporter.replace('Wn.', 'Wash.').replace('Wn', 'Wash'))
            variations.append(reporter.replace('Wn', 'Washington'))
        original = reporter
        variations.append(re.sub(r'\s+', '', original))
        variations.append(re.sub(r'\.', '. ', original))
        variations.append(re.sub(r'\s+', ' ', original))
        seen = set()
        unique_variations = []
        for var in variations:
            if var not in seen:
                seen.add(var)
                unique_variations.append(var)
        return unique_variations

    def find_full_citation_in_text(self, text: str, json_citation: str) -> str:
        """
        Try to find the full citation in the text using flexible reporter patterns.
        """
        parsed = self.parse_json_citation(json_citation)
        if not parsed['primary_volume'] or not parsed['primary_page']:
            return None
        volume = parsed['primary_volume']
        page = parsed['primary_page']
        reporter_variations = []
        if parsed['primary_reporter']:
            reporter_variations = self.normalize_reporter(parsed['primary_reporter'])
        for reporter in reporter_variations:
            escaped_reporter = re.escape(reporter)
            flexible_reporter = escaped_reporter.replace(r"\ ", r"\\s*")
            patterns = [
                rf'{volume}\\s+{escaped_reporter}\\s+{page}(?:,\\s*\\d+(?:-\\d+)?)*(?:,\\s*\\d{{1,3}}\\s+[A-Za-z\\. ]+\\d+(?:,\\s*\\d+(?:-\\d+)?)*)*\\s*\\(\\d{{4}}\\)',
                rf'{volume}\\s+{escaped_reporter}\\s+{page}(?:,\\s*\\d+(?:-\\d+)?)*\\s*\\(\\d{{4}}\\)',
                rf'{volume}\\s+{escaped_reporter}\\s+{page}\\s*\\(\\d{{4}}\\)',
                rf'{volume}\\s+{flexible_reporter}\\s+{page}[^()]*\\(\\d{{4}}\\)'
            ]
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(0)
        return None

    def find_case_name_before_citation(self, text: str, full_citation: str) -> str:
        """
        Find the case name immediately before the citation in the text.
        """
        idx = text.find(full_citation)
        if idx == -1:
            return None
        context = text[max(0, idx-500):idx]
        # Use a broad pattern for case names
        pattern = r'([A-Z][A-Za-z\s,\.\'-]{1,80}?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]{1,80}?)\s*[,;:.]?$'
        match = re.search(pattern, context, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None 

    def is_case_name_associated_with_citation(self, context: str, case_name: str, citation: str) -> bool:
        """
        Check if a case name is actually associated with the specific citation we're looking for.
        This prevents picking up case names from other citations in the same context.
        """
        # Look for the case name followed by the citation in close proximity
        # Pattern: case_name, citation
        pattern = rf'{re.escape(case_name)}\s*,\s*{re.escape(citation)}'
        if re.search(pattern, context, re.IGNORECASE):
            return True
        
        # Look for case name followed by citation within 50 characters
        case_name_index = context.find(case_name)
        citation_index = context.find(citation)
        
        if case_name_index != -1 and citation_index != -1:
            # Case name should come before citation
            if case_name_index < citation_index:
                distance = citation_index - case_name_index
                if distance <= 50:  # Within 50 characters
                    return True
        
        return False

    def starts_with_signal_word(self, text: str) -> bool:
        """
        Check if text starts with common signal words that indicate it's not a case name.
        """
        signal_words = [
            'the', 'this', 'that', 'these', 'those', 'a', 'an',
            'held', 'in', 'principle', 'applies', 'court', 'federal',
            'may', 'ask', 'necessary', 'resolve', 'case', 'before',
            'when', 'resolution', 'question', 'law', 'review', 'de',
            'novo', 'statute', 'meaning', 'certified', 'we', 'also'
        ]
        
        words = text.lower().split()
        if words and words[0] in signal_words:
            return True
        return False

    def clean_case_name_enhanced(self, case_name: str) -> str:
        """
        Enhanced case name cleaning with better handling of edge cases.
        """
        if not case_name:
            return ""
        
        # Remove extra whitespace
        case_name = re.sub(r'\s+', ' ', case_name).strip()
        
        # Remove trailing punctuation
        case_name = re.sub(r'[,\s]+$', '', case_name)
        case_name = case_name.rstrip('.,;:')
        
        # Normalize spacing around "v."
        case_name = re.sub(r'\s+v\.\s+', ' v. ', case_name)
        case_name = re.sub(r'\s+vs\.\s+', ' v. ', case_name)
        case_name = re.sub(r'\s+versus\s+', ' v. ', case_name)
        
        # Normalize spacing around "In re"
        case_name = re.sub(r'\s+In\s+re\s+', ' In re ', case_name)
        
        # Remove leading text that's not part of case name
        leading_patterns = [
            r'^.*?\b(held|in|that|the|principle|applies)\s+',
            r'^.*?\b(court|held|in)\s+',
            r'^.*?\b(federal|court|may|ask|this)\s+',
        ]
        
        for pattern in leading_patterns:
            case_name = re.sub(pattern, '', case_name, flags=re.IGNORECASE)
        
        # Preserve LLC, Inc., Corp., etc. - don't truncate these
        if case_name.endswith(', LLC') or case_name.endswith(', Inc.') or case_name.endswith(', Corp.'):
            pass
        else:
            # Remove trailing commas and periods that aren't part of abbreviations
            case_name = re.sub(r',\s*$', '', case_name)
            case_name = re.sub(r'\.\s*$', '', case_name)
        
        return case_name.strip() 

class DateExtractor:
    """Date extraction utilities - enhanced with patterns from EnhancedDateExtractor."""
    
    def __init__(self):
        # Enhanced date patterns from EnhancedDateExtractor
        self.date_patterns = [
            # ISO format: 2024-01-15
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',
            
            # US format: 01/15/2024, 1/15/2024
            r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',
            
            # US format with month names: January 15, 2024, Jan 15, 2024
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b',
            
            # Year only in parentheses: (2024)
            r'\((\d{4})\)',
            
            # Year in citation context: decided in 2024, filed in 2024
            r'(?:decided|filed|issued|released|argued|submitted)\s+(?:in\s+)?(\d{4})\b',
            
            # Simple year pattern: 2024
            r'\b(19|20)\d{2}\b',
            
            # Date with ordinal: January 15th, 2024
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b',
            
            # European format: 15/01/2024 (ambiguous, but common)
            r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',
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
    
    def extract_date(self, text: str, citation: str = None) -> Optional[str]:
        """
        Extract date from text, optionally using citation as context.
        Prioritizes a year in parentheses immediately after the citation if present.
        Args:
            text: The text to search for dates
            citation: Optional citation to use for context positioning
        Returns:
            Extracted date in ISO format (YYYY-MM-DD) or None if not found
        """
        try:
            if not text:
                return None

            # If citation is provided, look for a year in parentheses immediately after the citation
            if citation:
                citation_index = text.find(citation)
                if citation_index != -1:
                    after_citation = text[citation_index + len(citation): citation_index + len(citation) + 20]
                    match = re.search(r'\(\s*(\d{4})\s*\)', after_citation)
                    if match:
                        year = match.group(1)
                        if 1900 <= int(year) <= 2100:
                            return f"{year}-01-01"
                # Fallback to context-based extraction
                return self._extract_with_citation_context(text, citation)

            # Otherwise, search the entire text
            return self._extract_from_full_text(text)

        except Exception as e:
            logger.warning(f"Error extracting date: {e}")
            return None
    
    def extract_year(self, text: str, citation: str = None) -> Optional[str]:
        """
        Extract just the year from text.
        
        Args:
            text: The text to search for years
            citation: Optional citation to use for context positioning
            
        Returns:
            Extracted year as string or None if not found
        """
        try:
            date = self.extract_date(text, citation)
            if date:
                return date.split('-')[0]
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting year: {e}")
            return None
    
    def _extract_with_citation_context(self, text: str, citation: str) -> Optional[str]:
        """Extract date using citation as context anchor."""
        try:
            # Find citation in text
            citation_index = text.find(citation)
            if citation_index == -1:
                return self._extract_from_full_text(text)
            
            # Get context around citation (200 chars before, 100 chars after)
            context_start = max(0, citation_index - 200)
            context_end = min(len(text), citation_index + len(citation) + 100)
            context = text[context_start:context_end]
            
            return self._parse_date_patterns(context)
            
        except Exception as e:
            logger.warning(f"Error extracting date with citation context: {e}")
            return None
    
    def _extract_from_full_text(self, text: str) -> Optional[str]:
        """Extract date from full text without citation context."""
        try:
            return self._parse_date_patterns(text)
            
        except Exception as e:
            logger.warning(f"Error extracting date from full text: {e}")
            return None
    
    def _parse_date_patterns(self, text: str) -> Optional[str]:
        """Parse date patterns and return the best match."""
        try:
            best_date = None
            best_confidence = 0
            
            for pattern in self.date_patterns:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                for match in matches:
                    groups = match.groups()
                    date_str = self._parse_date_groups(groups, pattern)
                    
                    if date_str:
                        # Calculate confidence based on pattern type
                        confidence = self._calculate_date_confidence(pattern, groups)
                        
                        if confidence > best_confidence:
                            best_date = date_str
                            best_confidence = confidence
            
            return best_date
            
        except Exception as e:
            logger.warning(f"Error parsing date patterns: {e}")
            return None
    
    def _parse_date_groups(self, groups: tuple, pattern: str) -> Optional[str]:
        """Parse date groups and return ISO format date string."""
        try:
            if len(groups) == 3:
                # Full date pattern
                if 'January|February' in pattern:
                    # Month name format
                    month_name, day, year = groups
                    month = self.month_map.get(month_name.lower(), '01')
                elif pattern == r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b':
                    # ISO format
                    year, month, day = groups
                else:
                    # Assume US format (MM/DD/YYYY)
                    month, day, year = groups
                
                # Validate and format
                try:
                    year_int = int(year)
                    month_int = int(month)
                    day_int = int(day)
                    
                    if 1900 <= year_int <= 2100 and 1 <= month_int <= 12 and 1 <= day_int <= 31:
                        return f"{year_int:04d}-{month_int:02d}-{day_int:02d}"
                except (ValueError, TypeError):
                    pass
                    
            elif len(groups) == 1:
                # Year only pattern
                year = groups[0]
                try:
                    year_int = int(year)
                    if 1900 <= year_int <= 2100:
                        return f"{year_int:04d}-01-01"  # Default to January 1st
                except (ValueError, TypeError):
                    pass
            
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing date groups: {e}")
            return None
    
    def _calculate_date_confidence(self, pattern: str, groups: tuple) -> float:
        """Calculate confidence score for a date match."""
        try:
            confidence = 0.5  # Base confidence
            
            # Higher confidence for specific patterns
            if 'January|February' in pattern:
                confidence += 0.3  # Full month names are more reliable
            elif pattern == r'\((\d{4})\)':
                confidence += 0.2  # Parenthesized years are common in citations
            elif pattern == r'\b(19|20)\d{2}\b':
                confidence += 0.1  # Simple year patterns
            
            # Validate year range
            if len(groups) >= 1:
                try:
                    year = int(groups[0])
                    if 1900 <= year <= 2100:
                        confidence += 0.2
                    else:
                        confidence -= 0.3
                except (ValueError, TypeError):
                    confidence -= 0.3
            
            return max(0.0, min(1.0, confidence))
            
        except Exception:
            return 0.0
    
    def extract_date_multi_pattern(self, text: str, citation_start: int, citation_end: int) -> Optional[str]:
        """
        Use multiple detection strategies for date extraction.
        """
        context = self._get_adaptive_context(text, citation_start, citation_end)
        citation_text = text[citation_start:citation_end]
        
        def extract_immediate_parentheses():
            after_citation = text[citation_end:citation_end+20]
            match = re.search(r'\(\s*(\d{4})\s*\)', after_citation)
            if match:
                year = match.group(1)
                if 1900 <= int(year) <= 2100:
                    return f"{year}-01-01"
            return None
        
        def extract_from_sentence():
            # Look for year in the same sentence
            sentence = context
            match = re.search(r'(19|20)\d{2}', sentence)
            if match:
                year = match.group(0)
                if 1900 <= int(year) <= 2100:
                    return f"{year}-01-01"
            return None
        
        def extract_from_paragraph():
            # Look for year in the paragraph
            para = context
            match = re.search(r'(19|20)\d{2}', para)
            if match:
                year = match.group(0)
                if 1900 <= int(year) <= 2100:
                    return f"{year}-01-01"
            return None
        
        def extract_from_citation_text():
            # Look for year inside the citation text
            match = re.search(r'(19|20)\d{2}', citation_text)
            if match:
                year = match.group(0)
                if 1900 <= int(year) <= 2100:
                    return f"{year}-01-01"
            return None
        
        strategies = [
            extract_immediate_parentheses,
            extract_from_sentence,
            extract_from_paragraph,
            extract_from_citation_text
        ]
        for strategy in strategies:
            try:
                result = strategy()
                if result:
                    return result
            except Exception:
                continue
        return None
    
    def _get_adaptive_context(self, text: str, citation_start: int, citation_end: int) -> str:
        """
        Adaptive context window based on sentence and paragraph boundaries.
        """
        # Look for sentence boundaries
        sentence_start = text.rfind('.', 0, citation_start) + 1
        sentence_end = text.find('.', citation_end)
        if sentence_end == -1:
            sentence_end = len(text)
        
        # Look for paragraph boundaries
        para_start = text.rfind('\n\n', 0, citation_start) + 2
        para_end = text.find('\n\n', citation_end)
        if para_end == -1:
            para_end = len(text)
        
        # Use the most appropriate boundary
        context_start = max(sentence_start, para_start, citation_start - 500)
        context_end = min(sentence_end, para_end, citation_end + 200)
        
        return text[context_start:context_end]

    @staticmethod
    def extract_date_from_context_precise(text: str, citation_start: int, citation_end: int) -> Optional[str]:
        """Extract date with precise context to avoid wrong years."""
        
        # Strategy 1: Look immediately after citation (highest priority)
        immediate_after = text[citation_end:citation_end + 50]  # Increased window
        year_match = re.search(r'\((\d{4})\)', immediate_after)
        if year_match:
            year = year_match.group(1)
            if 1800 <= int(year) <= 2030:
                return f"{year}-01-01"
        
        # Strategy 2: Look in same sentence only (not entire document)
        # Find sentence boundaries around citation
        sentence_start = max(0, text.rfind('.', 0, citation_start) + 1)
        sentence_end = text.find('.', citation_end)
        if sentence_end == -1:
            sentence_end = len(text)
        
        sentence = text[sentence_start:sentence_end]
        
        # Look for year in this sentence only
        year_matches = re.findall(r'\((\d{4})\)', sentence)
        for year in year_matches:
            if 1800 <= int(year) <= 2030:
                return f"{year}-01-01"
        
        # Strategy 3: Look for year in broader context around citation
        context_start = max(0, citation_start - 100)
        context_end = min(len(text), citation_end + 100)
        context = text[context_start:context_end]
        
        year_matches = re.findall(r'\((\d{4})\)', context)
        for year in year_matches:
            if 1800 <= int(year) <= 2030:
                return f"{year}-01-01"
        
        return None

    @staticmethod
    def extract_date_from_context(text: str, citation_start: int, citation_end: int, context_window: int = 300) -> Optional[str]:
        """
        Extract date from context around a citation. Now with expanded patterns and larger window.
        Enhanced: If no date is found by regex, scan the 50 characters after the citation for a 4-digit year in parentheses or after a comma/semicolon.
        """
        try:
            context_start = max(0, citation_start - context_window)
            context_end = min(len(text), citation_end + context_window)
            context_before = text[context_start:citation_start]
            context_after = text[citation_end:context_end]
            full_context = context_before + context_after

            # Expanded date patterns
            date_patterns = [
                r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',  # ISO
                r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',  # US
                r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b',
                r'\((\d{4})\)',  # (2024)
                r'(?:decided|filed|issued|released|argued|submitted|entered|adjudged|rendered|delivered|opinion\s+filed)\s+(?:on\s+)?(?:the\s+)?(?:day\s+of\s+)?([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{4})',
                r'\b(19|20)\d{2}\b',  # year
                r'\b(\d{4})\s+Wash\.\s+App\.',  # e.g. 1989 Wash. App.
                r'\b(\d{4})\s+LEXIS\b',  # e.g. 1989 LEXIS
                r'\b(\d{4})\s+WL\b',  # e.g. 1989 WL
            ]
            month_map = {
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
            for pattern in date_patterns:
                matches = re.finditer(pattern, full_context, re.IGNORECASE)
                for match in matches:
                    groups = match.groups()
                    if len(groups) == 3:
                        if pattern == r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b':
                            year, month, day = groups
                        elif pattern == r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b':
                            month, day, year = groups
                        elif 'January|February' in pattern:
                            month_name, day, year = groups
                            month = month_map.get(month_name.lower(), '01')
                        else:
                            continue
                        try:
                            year = int(year)
                            month = int(month)
                            day = int(day)
                            if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                                return f"{year:04d}-{month:02d}-{day:02d}"
                        except (ValueError, TypeError):
                            continue
                    elif len(groups) == 1:
                        year = groups[0]
                        try:
                            year_int = int(year)
                            if 1900 <= year_int <= 2100:
                                return f"{year_int:04d}-01-01"
                        except (ValueError, TypeError):
                            continue
            # --- NEW FALLBACK: scan after citation for (YYYY) or , YYYY or ; YYYY ---
            after = text[citation_end:citation_end+50]
            # Try (YYYY)
            m = re.search(r'\((19|20)\d{2}\)', after)
            if m:
                return f"{m.group(1)}-01-01"
            # Try , YYYY or ; YYYY
            m = re.search(r'[;,]\s*(19|20)\d{2}', after)
            if m:
                return f"{m.group(1)}-01-01"
            # Try just a 4-digit year
            m = re.search(r'(19|20)\d{2}', after)
            if m:
                return f"{m.group(1)}-01-01"
            return None
        except Exception as e:
            logger.warning(f"Error extracting date from context: {e}")
            return None


def safe_set_extracted_date(citation, new_date, source="unknown"):
    """
    Safely set extracted_date on a citation, preventing overwriting better dates with worse ones.
    
    Args:
        citation: Citation object with extracted_date attribute
        new_date: New date to potentially set
        source: Source of the date assignment for debugging
        
    Returns:
        bool: True if date was set/changed, False if skipped
    """
    try:
        # Skip if new_date is empty or None
        if not new_date or new_date.strip() == "":
            return False
        
        # Skip if new_date is "N/A" or similar
        if new_date.strip().upper() in ["N/A", "NONE", "NULL", "UNKNOWN"]:
            return False
        
        current_date = getattr(citation, 'extracted_date', None)
        
        # If no current date, set the new one
        if not current_date or current_date.strip() == "" or current_date.strip().upper() in ["N/A", "NONE", "NULL", "UNKNOWN"]:
            citation.extracted_date = new_date
            logger.debug(f"Set extracted_date to '{new_date}' from source '{source}'")
            return True
        
        # If current date is better (more specific), keep it
        # Full date (YYYY-MM-DD) is better than year-only (YYYY)
        if len(current_date) > len(new_date):
            logger.debug(f"Keeping better current date '{current_date}' over '{new_date}' from '{source}'")
            return False
        
        # If dates are same length, prefer the current one (first come, first served)
        if len(current_date) == len(new_date):
            logger.debug(f"Keeping existing date '{current_date}' over '{new_date}' from '{source}'")
            return False
        
        # New date is better, set it
        citation.extracted_date = new_date
        logger.debug(f"Updated extracted_date from '{current_date}' to '{new_date}' from source '{source}'")
        return True
        
    except Exception as e:
        logger.warning(f"Error in safe_set_extracted_date: {e}")
        return False


def validate_citation_dates(citation):
    """
    Validate that a citation has a valid extracted_date.
    
    Args:
        citation: Citation object with extracted_date attribute
        
    Returns:
        bool: True if date is valid, False otherwise
    """
    try:
        date = getattr(citation, 'extracted_date', None)
        
        # Check if date exists and is not empty
        if not date or date.strip() == "":
            return False
        
        # Check if date is not a placeholder
        if date.strip().upper() in ["N/A", "NONE", "NULL", "UNKNOWN"]:
            return False
        
        # Check if date has valid format (YYYY-MM-DD or YYYY)
        if not re.match(r'^\d{4}(-\d{2}-\d{2})?$', date):
            return False
        
        # Check if year is reasonable
        year = int(date.split('-')[0])
        if not (1800 <= year <= 2030):
            return False
        
        return True
        
    except Exception as e:
        logger.warning(f"Error validating citation date: {e}")
        return False


# Compatibility functions for existing code
def extract_date_enhanced(text: str, citation: str = None) -> Optional[str]:
    """Enhanced date extraction function - compatibility wrapper."""
    extractor = DateExtractor()
    return extractor.extract_date(text, citation)


def extract_year_enhanced(text: str, citation: str = None) -> Optional[str]:
    """Enhanced year extraction function - compatibility wrapper."""
    extractor = DateExtractor()
    return extractor.extract_year(text, citation) 