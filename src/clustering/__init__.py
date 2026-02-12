"""
Clustering Package for CaseStrainer
====================================

This package provides modular clustering functionality,
breaking down the monolithic unified_clustering_master.py
into focused, testable modules.

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
