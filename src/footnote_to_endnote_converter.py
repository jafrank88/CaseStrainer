"""
Footnote to Endnote Converter for PDF Text Extraction

Converts footnotes in PDF text to endnotes to improve citation extraction quality.
Footnotes often disrupt text flow and cause proximity issues for citation clustering.

Author: CaseStrainer Team
Date: 2025-10-07
"""

import re
import logging
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FootnoteBlock:
    """Represents a detected footnote block."""
    number: str
    content: str
    page_num: int
    position: str  # 'bottom', 'inline', 'margin'


class FootnoteToEndnoteConverter:
    """
    Converts footnotes to endnotes in PDF-extracted text.
    
    Benefits:
    - Cleaner main text flow
    - Better citation proximity detection
    - Improved parallel citation clustering
    - Easier reference tracking
    """
    
    def __init__(self, enable_conversion: bool = True):
        """
        Initialize converter.
        
        Args:
            enable_conversion: Whether to enable footnote-to-endnote conversion
        """
        self.enable_conversion = enable_conversion
        self.footnote_patterns = self._compile_patterns()
        
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for footnote detection."""
        return {
            # Numbered footnotes: "1. Citation text" or "1 Citation text"
            'numbered': re.compile(r'^(\d+)[\.\s]\s*(.+)$', re.MULTILINE),
            
            # Superscript numbers: "¹ Citation text"
            'superscript': re.compile(r'^([¹²³⁴⁵⁶⁷⁸⁹⁰]+)\s*(.+)$', re.MULTILINE),
            
            # Lettered footnotes: "a. Citation text" or "a Citation text"
            'lettered': re.compile(r'^([a-z])[\.\s]\s*(.+)$', re.MULTILINE),
            
            # Symbol footnotes: "* Citation text" or "† Citation text"
            'symbol': re.compile(r'^([*†‡§¶#]+)\s*(.+)$', re.MULTILINE),
            
            # Footnote section headers
            'section_header': re.compile(r'^[-=]{3,}$|^FOOTNOTES?$|^NOTES?$', re.IGNORECASE | re.MULTILINE),
        }
    
    def convert(self, text: str, preserve_markers: bool = True) -> Tuple[str, int]:
        """
        Convert footnotes to endnotes in extracted text.
        
        Args:
            text: Raw text extracted from PDF
            preserve_markers: Keep footnote reference markers in main text
            
        Returns:
            Tuple of (converted_text, footnote_count)
        """
        if not self.enable_conversion:
            return text, 0
        
        logger.info("🔄 Converting footnotes to endnotes...")
        
        # Try multiple detection strategies
        strategies = [
            self._convert_section_based,
            self._convert_pattern_based,
            self._convert_page_based,
        ]
        
        for strategy in strategies:
            try:
                converted_text, count = strategy(text, preserve_markers)
                if count > 0:
                    logger.info(f"✅ Converted {count} footnotes to endnotes using {strategy.__name__}")
                    return converted_text, count
            except Exception as e:
                logger.debug(f"Strategy {strategy.__name__} failed: {e}")
                continue
        
        logger.info("ℹ️  No footnotes detected, returning original text")
        return text, 0
    
    def _convert_section_based(self, text: str, preserve_markers: bool) -> Tuple[str, int]:
        """
        Convert footnotes that are in a dedicated section.
        
        Example:
        ---
        Main text here.
        
        FOOTNOTES
        1. First footnote
        2. Second footnote
        """
        lines = text.split('\n')
        main_text = []
        endnotes = []
        in_footnote_section = False
        current_footnote = None
        
        for line in lines:
            # Detect footnote section start
            if self.footnote_patterns['section_header'].match(line.strip()):
                in_footnote_section = True
                continue
            
            if in_footnote_section:
                # Try to match footnote patterns
                matched = False
                for pattern_name, pattern in self.footnote_patterns.items():
                    if pattern_name == 'section_header':
                        continue
                    
                    match = pattern.match(line.strip())
                    if match:
                        # Save previous footnote
                        if current_footnote:
                            endnotes.append(current_footnote)
                        
                        # Start new footnote
                        number = match.group(1)
                        content = match.group(2)
                        current_footnote = f"[Endnote {len(endnotes) + 1}] {content}"
                        matched = True
                        break
                
                if not matched and current_footnote:
                    # Continuation of previous footnote
                    current_footnote += " " + line.strip()
            else:
                main_text.append(line)
        
        # Save last footnote
        if current_footnote:
            endnotes.append(current_footnote)
        
        if not endnotes:
            raise ValueError("No footnotes found in section-based detection")
        
        # Combine main text with endnotes
        result = '\n'.join(main_text)
        result += "\n\n" + "=" * 60 + "\n"
        result += "ENDNOTES (Converted from Footnotes)\n"
        result += "=" * 60 + "\n\n"
        result += "\n\n".join(endnotes)
        
        return result, len(endnotes)
    
    def _convert_pattern_based(self, text: str, preserve_markers: bool) -> Tuple[str, int]:
        """
        Convert footnotes based on pattern matching throughout text.
        
        Detects footnotes by looking for consistent numbering patterns.
        """
        lines = text.split('\n')
        main_text = []
        endnotes = []
        footnote_numbers_seen = set()
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                main_text.append(line)
                continue
            
            # Check if line starts with a footnote pattern
            is_footnote = False
            for pattern_name, pattern in self.footnote_patterns.items():
                if pattern_name == 'section_header':
                    continue
                
                match = pattern.match(stripped)
                if match:
                    number = match.group(1)
                    
                    # Verify this looks like a footnote (not just any numbered line)
                    if self._looks_like_footnote(stripped, number):
                        content = match.group(2)
                        endnote_num = len(endnotes) + 1
                        endnotes.append(f"[Endnote {endnote_num}] {content}")
                        footnote_numbers_seen.add(number)
                        is_footnote = True
                        break
            
            if not is_footnote:
                main_text.append(line)
        
        if not endnotes:
            raise ValueError("No footnotes found in pattern-based detection")
        
        # Combine
        result = '\n'.join(main_text)
        result += "\n\n" + "=" * 60 + "\n"
        result += "ENDNOTES (Converted from Footnotes)\n"
        result += "=" * 60 + "\n\n"
        result += "\n\n".join(endnotes)
        
        return result, len(endnotes)
    
    def _convert_page_based(self, text: str, preserve_markers: bool) -> Tuple[str, int]:
        """
        Convert footnotes by detecting page breaks and bottom-of-page content.
        
        Assumes footnotes are at the bottom of pages, separated by page breaks.
        """
        # Look for common page break markers
        page_break_patterns = [
            r'\f',  # Form feed
            r'Page \d+',
            r'-{10,}',
            r'={10,}',
        ]
        
        # Split by page breaks
        pages = re.split('|'.join(page_break_patterns), text)
        
        main_text = []
        endnotes = []
        
        for page_num, page in enumerate(pages):
            lines = page.split('\n')
            
            # Assume footnotes are in bottom 20% of page
            # (rough heuristic - may need tuning)
            split_point = int(len(lines) * 0.8)
            
            page_main = lines[:split_point]
            page_bottom = lines[split_point:]
            
            # Check if bottom section contains footnotes
            footnotes_found = False
            for line in page_bottom:
                stripped = line.strip()
                if not stripped:
                    continue
                
                # Check for footnote patterns
                for pattern_name, pattern in self.footnote_patterns.items():
                    if pattern_name == 'section_header':
                        continue
                    
                    match = pattern.match(stripped)
                    if match:
                        content = match.group(2)
                        endnote_num = len(endnotes) + 1
                        endnotes.append(f"[Endnote {endnote_num}] (Page {page_num + 1}) {content}")
                        footnotes_found = True
                        break
                
                if not footnotes_found:
                    # Not a footnote, add to main text
                    page_main.append(line)
            
            main_text.extend(page_main)
        
        if not endnotes:
            raise ValueError("No footnotes found in page-based detection")
        
        # Combine
        result = '\n'.join(main_text)
        result += "\n\n" + "=" * 60 + "\n"
        result += "ENDNOTES (Converted from Footnotes)\n"
        result += "=" * 60 + "\n\n"
        result += "\n\n".join(endnotes)
        
        return result, len(endnotes)
    
    def _looks_like_footnote(self, line: str, number: str) -> bool:
        """
        Heuristic to determine if a numbered line is actually a footnote.
        
        Footnotes typically:
        - Start with a number/symbol
        - Contain citations or references
        - Are shorter than main text paragraphs
        - May contain legal citation patterns
        """
        # Check for citation patterns
        citation_indicators = [
            r'\d+\s+[A-Z][a-z]+\.?\s+\d+',  # "123 F.3d 456"
            r'\d+\s+U\.S\.',  # "123 U.S."
            r'\d+\s+S\.\s*Ct\.',  # "123 S. Ct."
            r'v\.',  # "Smith v. Jones"
            r'Id\.',  # "Id."
            r'Ibid\.',  # "Ibid."
            r'supra',  # "supra note 5"
            r'infra',  # "infra note 10"
        ]
        
        for pattern in citation_indicators:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        # Check line length (footnotes are often shorter)
        if len(line) < 200:  # Arbitrary threshold
            return True
        
        return False


# Convenience function
def convert_footnotes_to_endnotes(text: str, enable: bool = True) -> Tuple[str, int]:
    """
    Convenience function to convert footnotes to endnotes.
    
    Args:
        text: Raw text extracted from PDF
        enable: Whether to enable conversion
        
    Returns:
        Tuple of (converted_text, footnote_count)
    """
    converter = FootnoteToEndnoteConverter(enable_conversion=enable)
    return converter.convert(text)


if __name__ == "__main__":
    # Test with sample text
    sample_text = """
This is the main text of the document. It contains several citations.¹

The Supreme Court held that standing requires injury in fact.² This principle
has been applied consistently.³

FOOTNOTES
1. See Smith v. Jones, 123 U.S. 456 (1990).
2. Lujan v. Defenders of Wildlife, 504 U.S. 555 (1992).
3. Id. at 560-61.
"""
    
    converted, count = convert_footnotes_to_endnotes(sample_text)
    print(f"Converted {count} footnotes")
    print("\n" + "=" * 60)
    print(converted)
