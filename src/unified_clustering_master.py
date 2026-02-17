"""
Unified Clustering Master - Compatibility Layer
===============================================

This module now serves as a compatibility layer that delegates to
the modular clustering package in src/clustering/.

The original implementation has been moved to:
- src/clustering/master.py
- src/clustering/detection.py  
- src/clustering/propagation.py
- src/clustering/validation.py
- src/clustering/utils.py

For new code, import directly from src.clustering:
    from src.clustering import UnifiedClusteringMaster
    from src.clustering.detection import detect_parallel_groups
"""

import warnings
import logging
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger(__name__)

# Issue deprecation warning
warnings.warn(
    "unified_clustering_master.py is deprecated. "
    "Use src.clustering module instead. "
    "Import: from src.clustering import UnifiedClusteringMaster",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from modular package
from src.clustering import (
    UnifiedClusteringMaster,
    ClusterType,
    ClusterResult,
    cluster_citations_unified_master,
)

from src.clustering.detection import (
    detect_parallel_groups,
    detect_structural_groups,
    find_best_cluster_seed,
    are_citations_parallel,
)

from src.clustering.propagation import (
    propagate_metadata,
    merge_cluster_metadata,
    propagate_parallel_status,
)

from src.clustering.validation import (
    validate_cluster,
    calculate_cluster_confidence,
    is_valid_cluster_size,
    check_cluster_overlap,
    merge_clusters_if_similar,
)

from src.clustering.utils import (
    sort_citations_by_position,
    extract_reporter_type_safe,
    group_citations_by_reporter,
    get_citation_distance,
    are_citations_adjacent,
    extract_year_from_citation,
    clean_case_name,
    is_truncated_name,
    calculate_position_overlap,
    merge_citation_data,
)

__all__ = [
    # Main class and types
    "UnifiedClusteringMaster",
    "ClusterType",
    "ClusterResult",
    "cluster_citations_unified_master",
    # Detection
    "detect_parallel_groups",
    "detect_structural_groups",
    "find_best_cluster_seed",
    "are_citations_parallel",
    # Propagation
    "propagate_metadata",
    "merge_cluster_metadata",
    "propagate_parallel_status",
    # Validation
    "validate_cluster",
    "calculate_cluster_confidence",
    "is_valid_cluster_size",
    "check_cluster_overlap",
    "merge_clusters_if_similar",
    # Utils
    "sort_citations_by_position",
    "extract_reporter_type_safe",
    "group_citations_by_reporter",
    "get_citation_distance",
    "are_citations_adjacent",
    "extract_year_from_citation",
    "clean_case_name",
    "is_truncated_name",
    "calculate_position_overlap",
    "merge_citation_data",
]

logger.info("unified_clustering_master.py loaded via compatibility layer (modular clustering)")
