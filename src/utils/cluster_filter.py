"""
Utility function for filtering cluster members.
This is in a separate module to avoid circular imports.
"""
import re
import logging
from typing import List

logger = logging.getLogger(__name__)


def filter_cluster_members_by_reporter(citation_text: str, member_citations: List[str]) -> List[str]:
    """
    Filter cluster members to exclude:
    1. Same-reporter/different-volume citations (different cases)
    2. Placeholder citations (with ____ or ___ page numbers)
    
    Parallel citations MUST be from DIFFERENT reporters for the same case.
    Same reporter + different volumes = DIFFERENT CASES entirely.
    """
    filtered = []
    
    # NOTE: We no longer skip bare placeholders here. They may have resolved
    # extracted_case_name values that aren't visible in the citation text string.
    # Unresolved placeholders are cleaned up later by _is_unresolved_placeholder
    # in unified_processing_pipeline.py after placeholder resolution.
    
    # Parse current citation
    parsed_current = None
    match = re.match(r"(\d+)\s+([A-Za-z\.\s]+)\s+(\d+|____|___)", citation_text)
    if match:
        parsed_current = {
            "volume": match.group(1),
            "reporter": match.group(2).strip(),
            "page": match.group(3)
        }
    
    for member in member_citations:
        if member == citation_text:
            continue
        
        # NOTE: No longer skipping bare placeholder members here.
        # Resolved placeholders are kept; unresolved ones cleaned up later.
            
        # Parse member citation
        parsed_member = None
        match_m = re.match(r"(\d+)\s+([A-Za-z\.\s]+)\s+(\d+|____|___)", member)
        if match_m:
            parsed_member = {
                "volume": match_m.group(1),
                "reporter": match_m.group(2).strip(),
                "page": match_m.group(3)
            }
        
        # Check if same reporter but different volume
        if parsed_current and parsed_member:
            vol_c, rep_c = parsed_current.get("volume"), parsed_current.get("reporter")
            vol_m, rep_m = parsed_member.get("volume"), parsed_member.get("reporter")
            
            if rep_c and rep_m and rep_c == rep_m and vol_c and vol_m and vol_c != vol_m:
                logger.warning(
                    f"[CLUSTER-FILTER] Excluding {member} from cluster of {citation_text}: "
                    f"same reporter '{rep_c}' but different volumes ({vol_c} vs {vol_m})"
                )
                continue
        
        filtered.append(member)
    
    return filtered
