"""
Unified Clustering Master (Refactored)
========================================

This is a refactored version that delegates to the modular clustering package.
Maintains backward compatibility while using the new modular implementation.
"""

import re
import logging
import time
from typing import Dict, Any, Optional, List, Set, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

from src.utils.reporter_utils import extract_reporter_type
from src.utils.cluster_filter import filter_cluster_members_by_reporter

# Import modular clustering components
from . import detection, propagation, validation, utils

logger = logging.getLogger(__name__)

# Import cross-document deduplication
try:
    from src.cross_document_deduplication import deduplicate_clusters_cross_document
    CROSS_DEDUP_AVAILABLE = True
    logger.info("Cross-document deduplication successfully imported")
except ImportError:
    CROSS_DEDUP_AVAILABLE = False
    deduplicate_clusters_cross_document = None

# Import spatial clustering
try:
    from src.spatial_clustering import cluster_citations_spatial
    SPATIAL_CLUSTERING_AVAILABLE = True
    logger.info("Spatial clustering successfully imported")
except ImportError:
    SPATIAL_CLUSTERING_AVAILABLE = False
    cluster_citations_spatial = None


class ClusterType(Enum):
    """Types of citation clusters."""
    PARALLEL = "parallel"
    CANONICAL = "canonical"
    EXTRACTED = "extracted"
    MIXED = "mixed"


@dataclass
class ClusterResult:
    """Standardized result from clustering."""
    cluster_id: str
    cluster_type: ClusterType
    case_name: Optional[str] = None
    case_year: Optional[str] = None
    citations: List[Any] = None
    size: int = 0
    confidence: float = 0.0
    metadata: Dict[str, Any] = None
    verification_status: Optional[str] = None


class UnifiedClusteringMaster:
    """
    THE SINGLE, AUTHORITATIVE clustering implementation (MODULAR VERSION).
    
    This refactored class uses the modular clustering package:
    - detection: Parallel and structural group detection
    - propagation: Metadata propagation within clusters
    - validation: Cluster quality validation
    - utils: Utility functions
    
    Maintains full backward compatibility with the original implementation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the master clustering engine."""
        self.config = config or {}
        self.debug_mode = self.config.get("debug_mode", False)
        self.min_cluster_size = self.config.get("min_cluster_size", 1)
        self.case_name_similarity_threshold = self.config.get(
            "case_name_similarity_threshold", 0.95
        )
        self.proximity_threshold = self.config.get("proximity_threshold", 150)
        self.enable_verification = self.config.get("enable_verification", True)
        self.use_spatial_clustering = self.config.get("use_spatial_clustering", True)

        self._setup_patterns()
        logger.info(f"UnifiedClusteringMaster initialized - modular version")

    def _setup_patterns(self):
        """Setup regex patterns for clustering."""
        self.patterns = {
            "washington_parallel": re.compile(
                r"(\d+)\s+(?:Wn\.|Wash\.)\d*d\s+\d+.*?(\d+)\s+(?:P\.|A\.)\d*d\s+\d+"
            ),
            "federal_parallel": re.compile(
                r"(\d+)\s+F\.\d*d\s+\d+.*?(\d+)\s+U\.S\.\s+\d+"
            ),
            "supreme_parallel": re.compile(
                r"(\d+)\s+S\.\s*Ct\.\s+\d+.*?(\d+)\s+L\.\s*Ed\.\d*d\s+\d+"
            ),
            "generic_parallel": re.compile(
                r"(\d+)\s+[A-Z][a-z]*\.\d*d?\s+\d+.*?(\d+)\s+[A-Z][a-z]*\.\d*d?\s+\d+"
            ),
            "separator_patterns": re.compile(r"[;,]\s*(?:see\s+)?(?:also\s+)?"),
            "case_name_v": re.compile(
                r"([A-Z][A-Za-z0-9&\'\\s-]+)\\s+v\.\\s+([A-Z][A-Za-z0-9&\'\\s-]+)"
            ),
            "case_name_in_re": re.compile(
                r"(In\\s+re\\s+[A-Z][a-zA-Z\\s\'&\\-\\.]{2,80})", re.IGNORECASE
            ),
            "case_name_state": re.compile(
                r"(State|People|Commonwealth)\\s+v\.\\s+([A-Z][a-zA-Z\\s\'&\\-\\.]{2,80})",
                re.IGNORECASE
            ),
            "year_patterns": re.compile(r"\((\d{4})\)|\b(19|20)\d{2}\b"),
        }

    def cluster_citations(
        self, 
        citations: List[Any], 
        original_text: str = "", 
        enable_verification: bool = None,
        request_id: str = "",
        progress_callback: Optional[Callable[[int, str, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Main clustering method using modular components.
        
        Args:
            citations: List of citations to cluster
            original_text: Original document text
            enable_verification: Whether to enable verification
            request_id: Optional request ID for tracking
            progress_callback: Optional progress callback
            
        Returns:
            List of cluster dictionaries
        """
        if not citations:
            return []
        
        if enable_verification is None:
            enable_verification = self.enable_verification
        
        logger.info(f"[CLUSTERING] Starting modular clustering of {len(citations)} citations")
        
        # Step 1: Detect parallel groups using modular detection
        parallel_groups = detection.detect_parallel_groups(
            citations, 
            proximity_threshold=self.proximity_threshold
        )
        
        # Step 2: Detect structural groups
        structural_groups = detection.detect_structural_groups(
            citations, 
            original_text
        ) if original_text else []
        
        # Step 3: Merge groups
        all_groups = self._merge_groups(parallel_groups, structural_groups)
        
        # Step 3.5: Split groups by extracted_case_name
        # Proximity grouping may combine different cases cited near each other
        # (e.g., "Larimore v. Blaylock, 259 Va. 568 ... Swindle v. State, 10 Tenn. 581")
        all_groups = self._split_groups_by_extracted_name(all_groups)
        
        # Step 4: Validate and score clusters
        validated_clusters = []
        for group in all_groups:
            validation_result = validation.validate_cluster(
                group, 
                min_size=self.min_cluster_size
            )
            
            # CRITICAL FIX: Always create clusters, even if validation fails
            # Single citations and failed validations should still be returned
            # Just mark them with appropriate flags
            if len(group) >= self.min_cluster_size:
                # Propagate metadata
                propagation.propagate_metadata(group)
                
                # Calculate confidence
                confidence = validation.calculate_cluster_confidence(group)
                
                # Extract best case name and year from group
                best_case_name = propagation._select_best_case_name(group)
                best_year = propagation._select_best_year(group)
                
                # Extract extracted_name (from document) and canonical_name (from verification)
                # by scanning citations in the group
                extracted_name = None
                extracted_date = None
                canonical_name = None
                canonical_date = None
                canonical_url = None
                cluster_members = []
                
                for cit in group:
                    cit_text = propagation._get_attr(cit, "citation", "")
                    if cit_text:
                        cluster_members.append(cit_text)
                    
                    # Get best extracted_case_name from group
                    if not extracted_name or extracted_name == "N/A":
                        ecn = propagation._get_attr(cit, "extracted_case_name")
                        if ecn and ecn != "N/A":
                            extracted_name = ecn
                    
                    # Get best extracted_date from group
                    if not extracted_date:
                        ed = propagation._get_attr(cit, "extracted_date")
                        if ed and ed != "N/A":
                            extracted_date = ed
                    
                    # Get canonical data from verified citations
                    if not canonical_name or canonical_name == "N/A":
                        cn = propagation._get_attr(cit, "canonical_name")
                        if cn and cn != "N/A":
                            canonical_name = cn
                    if not canonical_date:
                        cd = propagation._get_attr(cit, "canonical_date")
                        if cd:
                            canonical_date = cd
                    if not canonical_url:
                        cu = propagation._get_attr(cit, "canonical_url")
                        if cu:
                            canonical_url = cu
                
                cluster_dict = {
                    "cluster_id": f"cluster_{len(validated_clusters)}",
                    "citations": group,
                    "size": len(group),
                    "cluster_size": len(group),
                    "confidence": confidence,
                    "validation": validation_result,
                    "is_validated": validation_result.get("valid", False),
                    # Fields expected by pipeline and frontend
                    "case_name": best_case_name,
                    "cluster_case_name": best_case_name,
                    "year": best_year,
                    "cluster_year": best_year,
                    "extracted_name": extracted_name or best_case_name or "N/A",
                    "extracted_date": extracted_date or best_year,
                    "canonical_name": canonical_name,
                    "canonical_date": canonical_date,
                    "canonical_url": canonical_url,
                    "cluster_members": cluster_members,
                }
                
                validated_clusters.append(cluster_dict)
        
        logger.info(f"[CLUSTERING] Created {len(validated_clusters)} validated clusters")
        return validated_clusters

    def _merge_groups(
        self, 
        parallel_groups: List[List[Any]], 
        structural_groups: List[List[Any]]
    ) -> List[List[Any]]:
        """Merge parallel and structural groups, removing duplicates."""
        # Use frozenset of citation IDs for deduplication
        seen = set()
        merged = []
        
        for group in parallel_groups + structural_groups:
            # Create unique key - handle both dict and object citations
            def get_citation_key(c):
                # Try dict-style get first, then attribute access
                if isinstance(c, dict):
                    return c.get("citation", str(c))
                # For objects, try citation attribute, then string representation
                return getattr(c, 'citation', getattr(c, 'text', str(c)))
            
            key = frozenset(get_citation_key(c) for c in group)
            
            if key not in seen:
                seen.add(key)
                merged.append(group)
        
        return merged

    def _split_groups_by_extracted_name(self, groups: List[List[Any]]) -> List[List[Any]]:
        """
        Split proximity groups where citations have different extracted_case_name values.
        
        Proximity detection groups nearby citations together, but citations for
        different cases may appear close together in text (e.g., "Larimore v. Blaylock,
        259 Va. 568 ... Swindle v. State, 10 Tenn. 581"). This method splits such
        groups so each case gets its own cluster.
        """
        result = []
        for group in groups:
            if len(group) <= 1:
                result.append(group)
                continue
            
            # Collect extracted_case_name for each citation
            name_to_cits: Dict[str, List[Any]] = {}
            no_name_cits: List[Any] = []
            
            for cit in group:
                ecn = propagation._get_attr(cit, "extracted_case_name", "") or ""
                if ecn and ecn != "N/A" and " v. " in ecn:
                    # Normalize: lowercase, strip whitespace
                    norm = re.sub(r"\s+", " ", ecn.strip().lower())
                    # Extract first party for grouping (handles abbreviation differences)
                    parts = re.split(r"\s+v\.\s+", norm, maxsplit=1)
                    first_party = parts[0].strip().split()[-1] if parts else norm
                    
                    # Find matching group by first party
                    matched = False
                    for key in list(name_to_cits.keys()):
                        key_parts = re.split(r"\s+v\.\s+", key, maxsplit=1)
                        key_first = key_parts[0].strip().split()[-1] if key_parts else key
                        if first_party == key_first:
                            name_to_cits[key].append(cit)
                            matched = True
                            break
                    if not matched:
                        name_to_cits[norm] = [cit]
                else:
                    no_name_cits.append(cit)
            
            # If all citations have the same name (or no names), keep as one group
            if len(name_to_cits) <= 1:
                result.append(group)
                continue
            
            # Split into separate groups
            logger.info(
                f"[CLUSTER-SPLIT-ECN] Splitting proximity group of {len(group)} citations "
                f"into {len(name_to_cits)} groups by extracted_case_name: "
                f"{list(name_to_cits.keys())}"
            )
            
            # Assign no-name citations to the first group (they're likely series citations)
            first_key = True
            for name, cits in name_to_cits.items():
                if first_key and no_name_cits:
                    cits.extend(no_name_cits)
                    first_key = False
                else:
                    first_key = False
                result.append(cits)
        
        return result

    def _select_best_case_name(self, group: List[Any]) -> Optional[str]:
        """Delegate to utils module."""
        return utils._select_best_case_name(group)

    def _score_case_name(self, name: str) -> float:
        """Score a case name for quality."""
        score = 0.0
        
        # Prefer longer names (more complete)
        score += min(len(name) / 50.0, 1.0)
        
        # Check for "v." or "v" (proper case name format)
        if " v." in name or " v " in name.lower():
            score += 1.0
        
        # Penalize truncated names
        if utils.is_truncated_name(name):
            score -= 0.5
        
        # Check for proper nouns (capitalized words)
        words = name.split()
        capitalized = sum(1 for w in words if w and w[0].isupper())
        score += capitalized / max(len(words), 1)
        
        return max(0.0, min(1.0, score))

    def _clean_case_name_from_extraction(self, name: str) -> str:
        """Clean case name extracted from text."""
        if not name:
            return ""
        
        # Remove common sentence fragments
        fragments = [
            "see ", "see, ", "see also ", "cf. ", "e.g., ", "i.e., ",
            "accord ", "contra ", "but see ", "compare ", "citing ",
        ]
        
        name_lower = name.lower()
        for fragment in fragments:
            if name_lower.startswith(fragment):
                name = name[len(fragment):]
                break
        
        # Clean up
        name = name.strip()
        name = re.sub(r"\s+", " ", name)
        
        return name

    def _is_truncated_name(self, name: str) -> bool:
        """Delegate to utils module."""
        return utils.is_truncated_name(name)

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two case names."""
        from difflib import SequenceMatcher
        
        if not name1 or not name2:
            return 0.0
        
        # Normalize
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()
        
        return SequenceMatcher(None, n1, n2).ratio()

    def _extract_document_primary_case_name(self, text: str) -> Optional[str]:
        """
        Extract the primary case name from the document header.
        
        The primary case name typically appears at the beginning of legal documents in formats like:
        - "PLAINTIFF v. DEFENDANT"
        - "In the Matter of CASE NAME"
        - In briefs: "CASE NAME\nNo. 12-3456"
        
        This is used for contamination filtering to prevent cited case names from being
        incorrectly extracted as the document's own case name.
        
        Args:
            text: Full document text
            
        Returns:
            The document's primary case name, or None if not found
        """
        if not text or len(text) < 50:
            return None
        
        # Look at first 2000 characters (enough for case caption)
        header = text[:2000]
        
        # Strategy 1: Look for case name pattern before "No." (case number)
        case_number_match = re.search(r'No\.\s+\d{2,4}-\d{3,5}', header, re.IGNORECASE)
        if case_number_match:
            # Look backwards from case number for case name
            before_case_num = header[:case_number_match.start()]
            
            # Look for "Plaintiffs" or "Plaintiff" marker
            plaintiffs_marker = re.search(r'Plaintiffs?\s*[-–]\s*Appellants?', before_case_num, re.IGNORECASE)
            if plaintiffs_marker:
                # Extract from start to plaintiffs marker
                plaintiff_section = before_case_num[:plaintiffs_marker.start()].strip()
                # Take last 500 chars to get the plaintiff names
                plaintiff_section = plaintiff_section[-500:]
                
                # Find first complete party name (handles "COMPANY NAME, a corp; PERSON NAME, individual")
                # Look for pattern: ALL CAPS NAME followed by comma or semicolon
                first_party = re.search(r'([A-Z][A-Z\s&\.,\'-]{8,100}?)(?:,|\;)', plaintiff_section, re.DOTALL)
                if first_party:
                    plaintiff_name = first_party.group(1).strip()
                    # Clean up trailing punctuation and descriptions
                    plaintiff_name = re.sub(r',\s*a\s+.*$', '', plaintiff_name)
                    plaintiff_name = re.sub(r',\s*an\s+.*$', '', plaintiff_name)
                    plaintiff_name = plaintiff_name.strip().strip(',').strip()
                    
                    # Find defendant after plaintiffs marker
                    after_plaintiffs = before_case_num[plaintiffs_marker.end():]
                    v_match = re.search(r'v\.\s*([A-Z][A-Za-z\s\.,&\-\']{5,80})', after_plaintiffs, re.IGNORECASE)
                    if v_match:
                        defendant_name = v_match.group(1).strip()
                        # Clean defendant name
                        defendant_name = re.sub(r',\s*(?:an?\s+)?individual.*$', '', defendant_name, flags=re.IGNORECASE)
                        defendant_name = defendant_name.strip().strip(',').strip()
                        
                        case_name = f"{plaintiff_name} v. {defendant_name}"
                        logger.info(f"[CONTAMINATION-FILTER] Found primary case: '{case_name}'")
                        return case_name
            
            # Fallback: single-plaintiff logic
            v_pattern = re.search(r'([A-Z][A-Za-z\s\.,&\-\']{5,80})\s+v\.\s+([A-Z][A-Za-z\s\.,&\-\']{5,80})', before_case_num, re.IGNORECASE)
            if v_pattern:
                case_name = f"{v_pattern.group(1).strip()} v. {v_pattern.group(2).strip()}"
                logger.info(f"[CONTAMINATION-FILTER] Found primary case: '{case_name}'")
                return case_name
        
        # Strategy 2: Look for case name in first few lines
        lines = header.split('\n')
        for i, line in enumerate(lines[:30]):
            line = line.strip()
            if ' v. ' in line and len(line) > 10 and len(line) < 150:
                # Skip lines that contain citation patterns (volume reporter page)
                if re.search(r'\d+\s+\w+\.\s*\d*\s+\d+', line):
                    continue
                # Skip lines starting with signal words (e.g., "See United States v. ...")
                if re.match(r'^(?:See|Cf\.|Compare|But see|Accord)', line, re.IGNORECASE):
                    continue
                # Skip syllabus boilerplate text
                if any(phrase in line.lower() for phrase in ['syllabus', 'reporter of decisions', 'headnote', 'slip opinion']):
                    continue
                # Clean up common patterns
                cleaned = re.sub(r'^\s*(?:IN\s+THE\s+)?(?:MATTER\s+OF\s+)?', '', line, flags=re.IGNORECASE)
                cleaned = re.sub(r'\s*,?\s*(?:Appellant|Appellee|Plaintiff|Defendant|Petitioner|Respondent)s?\s*$', '', cleaned, flags=re.IGNORECASE)
                
                if ' v. ' in cleaned and len(cleaned) > 10:
                    logger.info(f"[CONTAMINATION-FILTER] Found primary case: '{cleaned}'")
                    return cleaned
        
        # Strategy 3: Pattern match for common formats
        pattern = r'([A-Z][A-Za-z\s\.,&\-\']{8,80})\s+v\.\s+([A-Za-z][A-Za-z\s\.,&\-\']{8,80})(?:\s*,|\s+No\.)'
        match = re.search(pattern, header)
        if match:
            case_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
            logger.info(f"[CONTAMINATION-FILTER] Found primary case: '{case_name}'")
            return case_name
        
        logger.debug("[CONTAMINATION-FILTER] Could not extract document primary case name")
        return None


# Module-level convenience function
def cluster_citations_unified_master(
    citations: List[Any],
    original_text: str = "",
    enable_verification: bool = None,
    request_id: str = "",
    config: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[int, str, str], None]] = None
) -> List[Dict[str, Any]]:
    """
    THE SINGLE, UNIFIED CLUSTERING FUNCTION (MODULAR VERSION).
    
    This function replaces ALL 45+ duplicate clustering functions.
    Uses the new modular clustering package internally.
    
    Returns:
        List of cluster dictionaries with comprehensive metadata
    """
    clusterer = UnifiedClusteringMaster(config)
    return clusterer.cluster_citations(
        citations, 
        original_text, 
        enable_verification, 
        request_id, 
        progress_callback
    )
