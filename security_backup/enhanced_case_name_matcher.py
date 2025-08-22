#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced case name matching for citation verification.
Implements fuzzy matching and canonical name normalization to handle
variations like "In re Marriage of Black" vs "In re Black".
"""

import re
import logging
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class EnhancedCaseNameMatcher:
    """
    Enhanced case name matcher that handles legal case name variations
    and implements fuzzy matching for citation verification.
    """
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        
        # Common legal abbreviations and their expansions
        self.legal_abbreviations = {
            'inc': 'incorporated',
            'corp': 'corporation', 
            'ltd': 'limited',
            'llc': 'limited liability company',
            'co': 'company',
            'assoc': 'association',
            'bros': 'brothers',
            'dr': 'doctor',
            'jr': 'junior',
            'sr': 'senior',
            'st': 'street',
            'mt': 'mount',
            'ft': 'fort',
            'univ': 'university',
            'nat\'l': 'national',
            'fed': 'federal',
            'comm\'n': 'commission',
            'bd': 'board',
            'ctr': 'center',
            'dept': 'department',
            'hosp': 'hospital',
            'cnty': 'county',
            'mfg': 'manufacturing',
            'int\'l': 'international',
            'dist': 'district',
            'munic': 'municipal',
            'town': 'township',
            'vlg': 'village'
        }
        
        # Common legal prefixes and their variations
        self.legal_prefixes = {
            'in re': ['in re', 'in the matter of', 'matter of', 're'],
            'ex parte': ['ex parte', 'ex parte', 'exparte'],
            'ex rel': ['ex rel', 'ex rel.', 'ex relatio', 'ex relatione'],
            'state': ['state', 'commonwealth', 'people'],
            'united states': ['united states', 'u.s.', 'us', 'federal'],
            'county': ['county', 'cnty', 'co.'],
            'city': ['city', 'municipality', 'municipal']
        }
        
        # Common legal suffixes that can be dropped
        self.droppable_suffixes = [
            ', inc.', ', corp.', ', ltd.', ', llc.', ', co.',
            ', petitioner', ', respondent', ', appellant', ', appellee',
            ', defendant', ', plaintiff', ', relator', ', real party in interest'
        ]
    
    def normalize_case_name(self, case_name: str, purpose: str = "verification") -> str:
        """
        Normalize a case name for comparison.
        
        Args:
            case_name: The case name to normalize
            purpose: The purpose of normalization ("verification", "clustering", "display")
            
        Returns:
            The normalized case name
        """
        if not case_name:
            return ""
        
        # Convert to lowercase
        normalized = case_name.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Handle legal prefixes consistently
        for prefix, variations in self.legal_prefixes.items():
            for variation in variations:
                if normalized.startswith(variation + ' '):
                    normalized = normalized.replace(variation, prefix, 1)
                    break
        
        # Expand common legal abbreviations
        for abbrev, expansion in self.legal_abbreviations.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            normalized = re.sub(pattern, expansion, normalized)
        
        # Remove droppable suffixes for verification purposes
        if purpose == "verification":
            for suffix in self.droppable_suffixes:
                if normalized.endswith(suffix):
                    normalized = normalized[:-len(suffix)]
                    break
        
        # Remove punctuation and normalize spacing
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip()
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two case names using multiple methods.
        
        Args:
            name1: First case name
            name2: Second case name
            
        Returns:
            Similarity score from 0.0 to 1.0
        """
        if not name1 or not name2:
            return 0.0
        
        # Normalize both names
        norm1 = self.normalize_case_name(name1, "verification")
        norm2 = self.normalize_case_name(name2, "verification")
        
        if not norm1 or not norm2:
            return 0.0
        
        # Method 1: Exact match after normalization
        if norm1 == norm2:
            return 1.0
        
        # Method 2: Sequence matcher (overall similarity)
        seq_similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Method 3: Word-based similarity (handles reordering)
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if len(words1) == 0 and len(words2) == 0:
            word_similarity = 1.0
        elif len(words1) == 0 or len(words2) == 0:
            word_similarity = 0.0
        else:
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            word_similarity = intersection / union if union > 0 else 0.0
        
        # Method 4: Substring matching (handles partial matches)
        substring_similarity = 0.0
        if norm1 in norm2 or norm2 in norm1:
            substring_similarity = min(len(norm1), len(norm2)) / max(len(norm1), len(norm2))
        
        # Method 5: Key word matching (for legal case names)
        key_words1 = self._extract_key_words(norm1)
        key_words2 = self._extract_key_words(norm2)
        
        if key_words1 and key_words2:
            key_word_similarity = len(key_words1.intersection(key_words2)) / len(key_words1.union(key_words2))
        else:
            key_word_similarity = 0.0
        
        # Combine methods with weights optimized for legal case names
        combined_similarity = (
            0.25 * seq_similarity +
            0.30 * word_similarity +
            0.20 * substring_similarity +
            0.25 * key_word_similarity
        )
        
        if self.debug_mode:
            logger.debug(f"Case name similarity: '{name1}' vs '{name2}'")
            logger.debug(f"  Normalized: '{norm1}' vs '{norm2}'")
            logger.debug(f"  Sequence: {seq_similarity:.3f}, Word: {word_similarity:.3f}")
            logger.debug(f"  Substring: {substring_similarity:.3f}, Key words: {key_word_similarity:.3f}")
            logger.debug(f"  Combined: {combined_similarity:.3f}")
        
        return combined_similarity
    
    def _extract_key_words(self, normalized_name: str) -> set:
        """
        Extract key words from a normalized case name.
        Focuses on meaningful words that identify the case.
        """
        # Split into words and filter out common legal words
        words = normalized_name.split()
        
        # Filter out very short words and common legal terms
        legal_stop_words = {
            'the', 'of', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'within', 'without',
            'against', 'toward', 'towards', 'upon', 'until', 'since', 'while',
            'where', 'when', 'why', 'how', 'what', 'which', 'who', 'whom',
            'whose', 'this', 'that', 'these', 'those', 'a', 'an', 'as', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall'
        }
        
        key_words = set()
        for word in words:
            # Only include words that are meaningful
            if (len(word) > 2 and 
                word not in legal_stop_words and
                not word.isdigit()):
                key_words.add(word)
        
        return key_words
    
    def is_likely_same_case(self, name1: str, name2: str, threshold: float = 0.7) -> bool:
        """
        Determine if two case names likely refer to the same case.
        
        Args:
            name1: First case name
            name2: Second case name
            threshold: Similarity threshold (default: 0.7)
            
        Returns:
            True if names likely refer to the same case
        """
        similarity = self.calculate_similarity(name1, name2)
        return similarity >= threshold
    
    def find_best_match(self, target_name: str, candidate_names: List[str], 
                       threshold: float = 0.6) -> Optional[Tuple[str, float]]:
        """
        Find the best matching case name from a list of candidates.
        
        Args:
            target_name: The target case name to match
            candidate_names: List of candidate case names
            threshold: Minimum similarity threshold
            
        Returns:
            Tuple of (best_match, similarity_score) or None if no good match
        """
        if not candidate_names:
            return None
        
        best_match = None
        best_score = 0.0
        
        for candidate in candidate_names:
            score = self.calculate_similarity(target_name, candidate)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = candidate
        
        if best_match:
            return (best_match, best_score)
        
        return None
    
    def normalize_for_verification(self, case_name: str) -> str:
        """
        Normalize case name specifically for verification purposes.
        This is more aggressive than general normalization.
        """
        if not case_name:
            return ""
        
        # Start with general normalization
        normalized = self.normalize_case_name(case_name, "verification")
        
        # Additional verification-specific normalizations
        
        # Remove common legal prefixes that might vary
        for prefix in ['in re', 'ex parte', 'ex rel']:
            if normalized.startswith(prefix + ' '):
                # Keep only the essential part after the prefix
                parts = normalized.split(' ', 2)
                if len(parts) >= 3:
                    normalized = ' '.join(parts[1:])
                break
        
        # Remove common legal suffixes
        for suffix in ['petitioner', 'respondent', 'appellant', 'appellee', 
                      'defendant', 'plaintiff', 'relator']:
            if normalized.endswith(' ' + suffix):
                normalized = normalized[:-len(suffix) - 1]
                break
        
        # Clean up any remaining extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized


# Global instance for easy access
enhanced_matcher = EnhancedCaseNameMatcher()


def calculate_case_name_similarity(name1: str, name2: str) -> float:
    """Convenience function for backward compatibility."""
    return enhanced_matcher.calculate_similarity(name1, name2)


def is_likely_same_case(name1: str, name2: str, threshold: float = 0.7) -> bool:
    """Convenience function for backward compatibility."""
    return enhanced_matcher.is_likely_same_case(name1, name2, threshold)


def find_best_match(target_name: str, candidate_names: List[str], 
                   threshold: float = 0.6) -> Optional[Tuple[str, float]]:
    """Convenience function for backward compatibility."""
    return enhanced_matcher.find_best_match(target_name, candidate_names, threshold)
