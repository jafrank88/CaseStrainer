"""
Case Extraction Strategies Module
===================================

Different strategies for extracting case names from text.
"""

import re
import logging
from typing import Optional, Dict, Any, List, Tuple
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ExtractionStrategy(ABC):
    """Abstract base class for extraction strategies."""
    
    @abstractmethod
    def extract(self, text: str, citation: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Extract case name and date from text."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name."""
        pass


class ProximityStrategy(ExtractionStrategy):
    """Extract case name based on proximity to citation."""
    
    name = "proximity"
    
    # Common case name patterns (include \- in party names for "Daily J.-Am.", "Exxon Corp.", etc.)
    CASE_NAME_PATTERNS = [
        # Pattern: "Plaintiff v. Defendant, Citation"
        re.compile(r"([A-Z][A-Za-z0-9&\'\s,\.\-]+?)\s+v\.\s+([A-Z][A-Za-z0-9&\'\s,\.\-]+?)(?:,\s*\d+|$)"),
        # Pattern: "In re Name"
        re.compile(r"(In\s+re\s+[A-Z][a-zA-Z\s\'&\.\-]+?)(?:,\s*\d+|$)", re.IGNORECASE),
        # Pattern: "State/People v. Defendant"
        re.compile(r"(State|People|Commonwealth)\s+(?:of\s+\w+\s+)?v\.\s+([A-Z][a-zA-Z\s\'&\.\-]+?)(?:,\s*\d+|$)"),
    ]
    
    def extract(self, text: str, citation: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Extract case name using proximity-based patterns."""
        if not text:
            return None
        
        best_match = None
        best_confidence = 0.0
        
        for pattern in self.CASE_NAME_PATTERNS:
            match = pattern.search(text)
            if match:
                # Calculate confidence based on match quality
                matched_text = match.group(0)
                confidence = self._calculate_confidence(matched_text)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = match
        
        if best_match:
            matched_text = best_match.group(0)
            # Clean up the match
            case_name = self._clean_match(matched_text)
            
            return {
                "case_name": case_name,
                "confidence": best_confidence,
                "method": "proximity",
                "raw_match": matched_text,
            }
        
        return None
    
    def _calculate_confidence(self, text: str) -> float:
        """Calculate confidence score for a match."""
        score = 0.5  # Base score
        
        # Higher confidence if contains "v." (proper case format)
        if " v." in text or " v " in text.lower():
            score += 0.3
        
        # Check for proper length (not too short, not too long)
        words = text.split()
        if 3 <= len(words) <= 20:
            score += 0.1
        
        # Penalize if looks like a statute or regulation
        if any(word in text.lower() for word in ["act", "code", "statute", "regulation"]):
            score -= 0.2
        
        return min(1.0, max(0.0, score))
    
    def _clean_match(self, text: str) -> str:
        """Clean up the matched case name."""
        # Remove trailing punctuation
        text = text.rstrip(",.;:")
        
        # Remove common prefixes that shouldn't be part of case name
        prefixes = ["see ", "see, ", "see also ", "cf. ", "citing ", "accord ", "contra "]
        for prefix in prefixes:
            if text.lower().startswith(prefix):
                text = text[len(prefix):]
        
        return text.strip()


class PatternStrategy(ExtractionStrategy):
    """Extract case name using regex pattern matching."""
    
    name = "pattern"
    
    # More comprehensive patterns (include \- for "J.-Am.", etc.)
    PATTERNS = [
        # Standard case format with parties
        (re.compile(r"([A-Z][A-Za-z0-9&\'\s,\.\-]+?)\s+v\.\s+([A-Z][A-Za-z0-9&\'\s,\.\-]+)"), 0.9),
        # In re proceedings
        (re.compile(r"(In\s+re\s+[A-Z][a-zA-Z\s\'&\-\.]{2,80})", re.IGNORECASE), 0.85),
        # Ex parte
        (re.compile(r"(Ex\s+parte\s+[A-Z][a-zA-Z\s\'&\-\.]{2,80})", re.IGNORECASE), 0.85),
        # State/People prosecutions
        (re.compile(r"(State|People|Commonwealth)\s+(?:of\s+\w+\s+)?v\.\s+([A-Z][a-zA-Z\s\'&\-\.]{2,80})"), 0.8),
        # United States prosecutions
        (re.compile(r"(United\s+States)\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.]{2,80})"), 0.85),
    ]
    
    def extract(self, text: str, citation: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Extract case name using comprehensive patterns."""
        if not text:
            return None
        
        best_result = None
        best_confidence = 0.0
        
        for pattern, base_confidence in self.PATTERNS:
            match = pattern.search(text)
            if match:
                matched_text = match.group(0)
                
                # Adjust confidence based on match quality
                confidence = self._refine_confidence(matched_text, base_confidence)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_result = {
                        "case_name": matched_text.strip(),
                        "confidence": confidence,
                        "method": "pattern",
                        "pattern_type": pattern.pattern[:50],
                    }
        
        return best_result
    
    def _refine_confidence(self, text: str, base: float) -> float:
        """Refine confidence based on text quality."""
        confidence = base
        
        # Boost for good length
        if 10 <= len(text) <= 100:
            confidence += 0.05
        
        # Penalize for suspicious patterns
        if "..." in text:
            confidence -= 0.15
        if text.count("(") != text.count(")"):
            confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))


class MLStrategy(ExtractionStrategy):
    """ML-based extraction (placeholder for future ML implementation)."""
    
    name = "ml"
    
    def extract(self, text: str, citation: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """ML-based extraction (not yet implemented)."""
        # Placeholder - would integrate with ML model
        logger.debug("ML extraction not yet implemented, falling back to pattern")
        return None


def get_strategies() -> List[ExtractionStrategy]:
    """Get all available extraction strategies in priority order."""
    return [
        ProximityStrategy(),
        PatternStrategy(),
        # MLStrategy(),  # Not yet implemented
    ]
