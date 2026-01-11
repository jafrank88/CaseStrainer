"""
Spatial Citation Clustering
============================

Clusters citations based on their spatial proximity to case names and years in the document.

Key Principle:
    Citations should only cluster together if they appear between the same 
    extracted case name and extracted year in the document.

This approach:
- Eliminates complex court-level and volume validation
- Uses document structure as the clustering signal
- Matches how humans read citations in legal documents
- More accurate and faster than metadata-based clustering
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class SpatialRegion:
    """A region in the document defined by a case name and year."""
    case_name: str
    year: str
    start_pos: int
    end_pos: int
    case_name_pos: int
    year_pos: int


class SpatialClusterer:
    """
    Clusters citations based on spatial proximity to case names and years.
    
    Algorithm:
    1. Find all case names in the document (pattern: "Name v. Name")
    2. Find all years in parentheses after case names
    3. Define regions between (case_name, year) pairs
    4. Group citations that fall within the same region
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_region_size = self.config.get("max_region_size", 200)  # Max chars between name and year (reduced from 500)
        self.debug = self.config.get("debug", False)
    
    def cluster_citations_spatial(
        self, 
        citations: List[Any], 
        text: str
    ) -> List[Dict[str, Any]]:
        """
        Cluster citations based on spatial proximity to case names and years.
        
        Args:
            citations: List of citation objects with .citation and .start_index
            text: Full document text
            
        Returns:
            List of cluster dictionaries
        """
        if not citations or not text:
            return []
        
        logger.info(f"[SPATIAL] Starting spatial clustering for {len(citations)} citations")
        
        # USER FIX 2026-01-10: Filter out citations already in TOA section
        # TOA entries already have correct case names and shouldn't be re-clustered
        non_toa_citations = []
        toa_citations = []
        for cit in citations:
            in_toa = False
            if isinstance(cit, dict):
                in_toa = cit.get("metadata", {}).get("in_toa_section", False)
            elif hasattr(cit, "metadata"):
                metadata = getattr(cit, "metadata", {})
                in_toa = metadata.get("in_toa_section", False) if isinstance(metadata, dict) else False
            
            if in_toa:
                toa_citations.append(cit)
            else:
                non_toa_citations.append(cit)
        
        logger.info(f"[SPATIAL] Filtered: {len(non_toa_citations)} body citations, {len(toa_citations)} TOA citations (skipped)")
        
        # Only cluster non-TOA citations
        citations_to_cluster = non_toa_citations
        
        if not citations_to_cluster:
            logger.info("[SPATIAL] No body citations to cluster (all in TOA)")
            return []
        
        # Step 1: Find all spatial regions (case_name + year pairs)
        regions = self._find_spatial_regions(text)
        logger.info(f"[SPATIAL] Found {len(regions)} spatial regions")
        
        # Step 2: Assign each citation to a region
        citation_to_region = self._assign_citations_to_regions(citations_to_cluster, regions, text)
        
        # Step 3: Group citations by region
        region_groups = defaultdict(list)
        unassigned = []
        
        for citation in citations_to_cluster:
            # Extract citation text properly from dict or object
            if isinstance(citation, dict):
                cit_text = citation.get("citation", "")
            else:
                cit_text = getattr(citation, "citation", str(citation))
            region_id = citation_to_region.get(cit_text)
            
            if region_id is not None:
                region_groups[region_id].append(citation)
            else:
                unassigned.append(citation)
        
        logger.info(f"[SPATIAL] Grouped into {len(region_groups)} regions, {len(unassigned)} unassigned")
        
        # Step 4: Create clusters from groups
        clusters = []
        cluster_id = 1
        
        for region_id, group_citations in region_groups.items():
            region = regions[region_id]
            
            cluster = {
                "cluster_id": f"spatial_{cluster_id}",
                "cluster_case_name": region.case_name,  # Frontend expects this field
                "cluster_year": region.year,  # Frontend expects this field
                "canonical_name": region.case_name,
                "extracted_name": region.case_name,
                "canonical_date": region.year,
                "extracted_date": region.year,
                "cluster_members": [],
                "citations": [],  # Frontend expects this field
                "cluster_size": len(group_citations),
                "method": "spatial_clustering",
                "region_start": region.start_pos,
                "region_end": region.end_pos,
            }
            
            for cit in group_citations:
                # Extract citation text properly from dict or object
                if isinstance(cit, dict):
                    citation_text = cit.get("citation", "")
                    # Copy the full citation dict for the citations array
                    citation_obj = cit.copy()
                    # Ensure extracted fields are set from the region
                    citation_obj["extracted_case_name"] = region.case_name
                    citation_obj["extracted_date"] = region.year
                else:
                    citation_text = getattr(cit, "citation", str(cit))
                    # Convert object to dict for citations array
                    citation_obj = {
                        "citation": citation_text,
                        "extracted_case_name": region.case_name,
                        "extracted_date": region.year,
                        "canonical_name": getattr(cit, "canonical_name", None),
                        "canonical_date": getattr(cit, "canonical_date", None),
                        "verified": getattr(cit, "verified", False),
                        "start_index": getattr(cit, "start_index", None),
                    }
                
                member = {
                    "citation": citation_text,
                    "extracted_case_name": region.case_name,
                    "extracted_date": region.year,
                    "canonical_name": getattr(cit, "canonical_name", None) if not isinstance(cit, dict) else cit.get("canonical_name"),
                    "canonical_date": getattr(cit, "canonical_date", None) if not isinstance(cit, dict) else cit.get("canonical_date"),
                    "verified": getattr(cit, "verified", False) if not isinstance(cit, dict) else cit.get("verified", False),
                    "start_index": getattr(cit, "start_index", None) if not isinstance(cit, dict) else cit.get("start_index"),
                }
                cluster["cluster_members"].append(member)
                cluster["citations"].append(citation_obj)
            
            clusters.append(cluster)
            cluster_id += 1
        
        # Step 5: Handle unassigned citations (create individual clusters)
        for cit in unassigned:
            # Extract fields properly from dict or object
            if isinstance(cit, dict):
                extracted_name = cit.get("extracted_case_name", "N/A")
                extracted_date = cit.get("extracted_date", "N/A")
                citation_text = cit.get("citation", "")
                canonical_name = cit.get("canonical_name")
                canonical_date = cit.get("canonical_date")
                verified = cit.get("verified", False)
                start_index = cit.get("start_index")
            else:
                extracted_name = getattr(cit, "extracted_case_name", "N/A")
                extracted_date = getattr(cit, "extracted_date", "N/A")
                citation_text = getattr(cit, "citation", str(cit))
                canonical_name = getattr(cit, "canonical_name", None)
                canonical_date = getattr(cit, "canonical_date", None)
                verified = getattr(cit, "verified", False)
                start_index = getattr(cit, "start_index", None)
            
            # Create citation object for frontend
            citation_obj = cit.copy() if isinstance(cit, dict) else {
                "citation": citation_text,
                "extracted_case_name": extracted_name,
                "extracted_date": extracted_date,
                "canonical_name": canonical_name,
                "canonical_date": canonical_date,
                "verified": verified,
                "start_index": start_index,
            }
            
            cluster = {
                "cluster_id": f"spatial_{cluster_id}",
                "cluster_case_name": extracted_name,  # Frontend expects this field
                "cluster_year": extracted_date,  # Frontend expects this field
                "canonical_name": canonical_name or extracted_name,
                "extracted_name": extracted_name,
                "canonical_date": canonical_date or extracted_date,
                "extracted_date": extracted_date,
                "cluster_members": [{
                    "citation": citation_text,
                    "extracted_case_name": extracted_name,
                    "extracted_date": extracted_date,
                    "canonical_name": canonical_name,
                    "canonical_date": canonical_date,
                    "verified": verified,
                    "start_index": start_index,
                }],
                "citations": [citation_obj],  # Frontend expects this field
                "cluster_size": 1,
                "method": "spatial_clustering_unassigned",
            }
            clusters.append(cluster)
            cluster_id += 1
        
        logger.info(f"[SPATIAL] Created {len(clusters)} total clusters")
        return clusters
    
    def _find_spatial_regions(self, text: str) -> List[SpatialRegion]:
        """
        Find all spatial regions in the document.
        
        A region is defined by:
        - A case name (pattern: "Name v. Name")
        - Followed by a year in parentheses within max_region_size chars
        
        Returns:
            List of SpatialRegion objects
        """
        regions = []
        
        # Pattern for case names: "Word v. Word" or "Word v Word"
        # Use greedy matching to capture full names, but stop at punctuation that indicates end
        # Match: "Berenyi v. District Director" but not "Berenyi v. District Director, 123 U.S."
        case_name_pattern = r'\b([A-Z][A-Za-z\'\-\.&,\s]+)\s+v\.?\s+([A-Z][A-Za-z\'\-\.&,\s]+?)(?=\s*,|\s*\(|\s+\d+\s+[A-Z]|\s*$)'
        
        # Find all case names
        for match in re.finditer(case_name_pattern, text):
            case_name = match.group(0).strip()
            # Remove trailing commas or periods
            case_name = case_name.rstrip('.,')
            case_name_pos = match.start()
            
            # Look for year in parentheses after the case name
            # Search within max_region_size characters
            search_start = match.end()
            search_end = min(len(text), search_start + self.max_region_size)
            search_region = text[search_start:search_end]
            
            # Pattern for year in parentheses: (2023) or (Conn. 2023) etc.
            # Must be the FIRST year found to avoid matching citations within the region
            year_pattern = r'\((?:[^)]*?)(\d{4})\)'
            year_match = re.search(year_pattern, search_region)
            
            if year_match:
                year = year_match.group(1)
                year_pos = search_start + year_match.start()
                
                # Validate year range
                if 1800 <= int(year) <= 2030:
                    # Define region from case name to year
                    region = SpatialRegion(
                        case_name=case_name,
                        year=year,
                        start_pos=case_name_pos,
                        end_pos=year_pos + len(year_match.group(0)),
                        case_name_pos=case_name_pos,
                        year_pos=year_pos,
                    )
                    regions.append(region)
                    
                    if self.debug:
                        logger.debug(f"[SPATIAL] Found region: '{case_name}' ({year}) at {case_name_pos}-{region.end_pos}")
        
        return regions
    
    def _assign_citations_to_regions(
        self, 
        citations: List[Any], 
        regions: List[SpatialRegion],
        text: str
    ) -> Dict[str, int]:
        """
        Assign each citation to the nearest spatial region.
        
        A citation is assigned to a region if:
        1. It appears after the case name
        2. It appears before the NEXT case name (or before the year if last region)
        3. It's the closest region if multiple regions match
        
        Returns:
            Dict mapping citation text to region index
        """
        citation_to_region = {}
        
        # Sort regions by position to determine boundaries
        sorted_regions = sorted(enumerate(regions), key=lambda x: x[1].case_name_pos)
        
        for citation in citations:
            # Extract citation text properly from dict or object
            if isinstance(citation, dict):
                cit_text = citation.get("citation", "")
            else:
                cit_text = getattr(citation, "citation", str(citation))
            
            cit_pos = getattr(citation, "start_index", None) if not isinstance(citation, dict) else citation.get("start_index")
            
            if cit_pos is None:
                # Try to find position in text
                cit_pos = text.find(cit_text)
                if cit_pos == -1:
                    continue
            
            # Find the region this citation belongs to
            best_region_idx = None
            best_distance = float('inf')
            
            for i, (orig_idx, region) in enumerate(sorted_regions):
                # Citation must be after this region's case name
                if cit_pos < region.case_name_pos:
                    continue
                
                # Determine the end boundary for this region
                # Citations must appear BETWEEN case name and year (not after)
                # ALL regions end at the year position - citations after the year are unassigned
                region_end = region.year_pos  # End at opening parenthesis before year
                
                # Check if citation is within this region's boundaries
                if cit_pos <= region_end:
                    # Calculate distance from case name
                    distance = cit_pos - region.case_name_pos
                    if distance < best_distance:
                        best_distance = distance
                        best_region_idx = orig_idx
                    # Since regions are sorted, we found the right region
                    break
            
            if best_region_idx is not None:
                citation_to_region[cit_text] = best_region_idx
                
                if self.debug:
                    region = regions[best_region_idx]
                    logger.info(f"[SPATIAL-ASSIGN] '{cit_text}' -> region {best_region_idx} ('{region.case_name}') at distance {best_distance}")
                    logger.debug(
                        f"[SPATIAL] Assigned '{cit_text}' to region '{region.case_name}' ({region.year})"
                    )
        
        return citation_to_region


def cluster_citations_spatial(
    citations: List[Any],
    text: str,
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function for spatial clustering.
    
    Args:
        citations: List of citation objects
        text: Full document text
        config: Optional configuration dict
        
    Returns:
        List of cluster dictionaries
    """
    clusterer = SpatialClusterer(config)
    return clusterer.cluster_citations_spatial(citations, text)
