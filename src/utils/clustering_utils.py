"""
Utilities for citation clustering with strict data separation.

CRITICAL PRINCIPLE:
- Clustering must use ONLY extracted data from the user's document
- NEVER use canonical data (from APIs) for clustering
- Canonical data is for verification display only
"""

import re
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


def normalize_case_name_for_clustering(case_name: Optional[str]) -> str:
    """
    Normalize a case name for clustering purposes.
    
    Args:
        case_name: The case name to normalize
        
    Returns:
        Normalized case name suitable for clustering
    """
    if not case_name or case_name in ('N/A', 'Unknown', 'Unknown Case'):
        return 'unknown'
    
    # Convert to lowercase
    normalized = case_name.lower()
    
    # Remove common variations
    normalized = re.sub(r'\s+v\.?\s+', '_v_', normalized)
    normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation
    normalized = re.sub(r'\s+', '_', normalized)  # Replace spaces with underscores
    
    return normalized


def create_cluster_key_from_extracted_data(
    extracted_case_name: Optional[str],
    extracted_date: Optional[str],
    citation_text: str = ""
) -> str:
    """
    Create a cluster key using ONLY extracted data from the user's document.
    
    CRITICAL: This function must NEVER use canonical data.
    
    Args:
        extracted_case_name: Case name extracted from user's document
        extracted_date: Year extracted from user's document (should be 4-digit year)
        citation_text: The citation text (for fallback)
        
    Returns:
        Cluster key string
    """
    # Validate extracted_date is a clean year
    clean_year = None
    if extracted_date and extracted_date not in ('N/A', 'Unknown', 'Unknown Year'):
        # If it's a full ISO date, extract just the year
        if re.match(r'^\d{4}-\d{2}-\d{2}', str(extracted_date)):
            clean_year = str(extracted_date)[:4]
            logger.warning(
                f"[CLUSTER-KEY] extracted_date contained full ISO date '{extracted_date}'. "
                f"Using year: '{clean_year}'"
            )
        elif re.match(r'^\d{4}$', str(extracted_date)):
            clean_year = str(extracted_date)
        else:
            # Try to extract any 4-digit year
            year_match = re.search(r'(\d{4})', str(extracted_date))
            if year_match:
                clean_year = year_match.group(1)
                logger.warning(
                    f"[CLUSTER-KEY] Extracted year '{clean_year}' from malformed date '{extracted_date}'"
                )
    
    # Normalize case name
    if extracted_case_name and extracted_case_name not in ('N/A', 'Unknown', 'Unknown Case'):
        normalized_name = normalize_case_name_for_clustering(extracted_case_name)
    else:
        # Fallback to citation text if no case name
        normalized_name = citation_text.replace(' ', '_').replace('.', '_')[:50]
    
    # Create cluster key
    if clean_year:
        cluster_key = f"{normalized_name}_{clean_year}"
    else:
        # No year available - cluster by name only
        cluster_key = f"{normalized_name}_no_year"
    
    # Sanitize the key
    cluster_key = re.sub(r'[^\w_]', '', cluster_key)
    
    return cluster_key


def validate_cluster_key(cluster_key: str, source: str = "unknown") -> bool:
    """
    Validate that a cluster key doesn't contain canonical data contamination.
    
    Args:
        cluster_key: The cluster key to validate
        source: Source of the key for logging
        
    Returns:
        True if valid, False if contaminated
    """
    # Check for ISO date patterns (YYYY-MM-DD)
    if re.search(r'\d{4}-\d{2}-\d{2}', cluster_key):
        logger.error(
            f"[CLUSTER-KEY-CONTAMINATION] Cluster key from {source} contains ISO date: '{cluster_key}'"
        )
        return False
    
    # Check for "canonical" prefix
    if cluster_key.startswith('canonical_'):
        logger.error(
            f"[CLUSTER-KEY-CONTAMINATION] Cluster key from {source} uses canonical prefix: '{cluster_key}'"
        )
        return False
    
    return True


__all__ = [
    'normalize_case_name_for_clustering',
    'create_cluster_key_from_extracted_data',
    'validate_cluster_key',
]
