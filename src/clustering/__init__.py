"""
Clustering package (citation grouping during extraction/processing)
===================================================================

This package builds and refines **clusters of citations** (parallel groups,
metadata propagation, validation). It is the primary home for
``UnifiedClusteringMaster`` and related detection/propagation helpers.

**Relationship to ``src.pipeline.clustering``**
    The **pipeline** module owns **late-stage merge helpers** used after
    verification (e.g. ``merge_clusters_by_canonical_name``, ``merge_cluster_group``,
    ``create_clusters_from_parallel_citations``). The unified processing pipeline
    typically: extracts → verifies → calls into ``src.clustering`` / optimized
    masters → then applies pipeline merge passes and ``response_enrichment`` merges
    for API output. When adding a new merge rule, choose pipeline vs detection by
    whether it needs **verified canonical metadata** (usually pipeline/response layer).

Usage:
    from src.clustering import UnifiedClusteringMaster
    from src.clustering.detection import detect_parallel_groups
    from src.clustering.propagation import propagate_metadata
"""

from .master import UnifiedClusteringMaster, ClusterType, ClusterResult, cluster_citations_unified_master
from .detection import detect_parallel_groups, detect_structural_groups
from .propagation import propagate_metadata, merge_cluster_metadata
from .validation import validate_cluster, calculate_cluster_confidence
from .utils import sort_citations_by_position, extract_reporter_type_safe

__all__ = [
    # Main class
    "UnifiedClusteringMaster",
    "ClusterType", 
    "ClusterResult",
    "cluster_citations_unified_master",
    # Detection
    "detect_parallel_groups",
    "detect_structural_groups",
    # Propagation
    "propagate_metadata",
    "merge_cluster_metadata",
    # Validation
    "validate_cluster",
    "calculate_cluster_confidence",
    # Utils
    "sort_citations_by_position",
    "extract_reporter_type_safe",
]
