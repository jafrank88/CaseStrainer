Architecture Overview
======================

CaseStrainer uses a modular architecture for citation processing.

Core Packages
-------------

**src.clustering**
   Citation clustering and parallel detection.
   
   - detection: Find parallel/structural groups
   - propagation: Metadata propagation within clusters
   - validation: Cluster quality validation
   - utils: Utility functions

**src.extraction**
   Case name and date extraction.
   
   - strategies: Proximity, Pattern, ML strategies
   - validation: Case name validation
   - utils: Extraction utilities

**src.verification**
   Citation verification against canonical sources.
   
   - sources: Individual verifiers (CourtListener, Justia, etc.)
   - fallback: Fallback verification
   - batch: Batch verification
   - utils: Utility functions

Data Flow
---------

1. **Input**: PDF, text, or URL
2. **Extraction**: Extract citations and case names
3. **Clustering**: Group parallel citations
4. **Verification**: Verify against canonical sources
5. **Output**: Structured citation data

Usage Examples
--------------

Clustering::

   from src.clustering import UnifiedClusteringMaster
   
   clusterer = UnifiedClusteringMaster()
   clusters = clusterer.cluster_citations(citations, text)

Extraction::

   from src.extraction import extract_case_name_and_date_unified_master
   
   result = extract_case_name_and_date_unified_master(text, citation)

Verification::

   from src.verification import UnifiedVerificationMaster
   
   verifier = UnifiedVerificationMaster(api_key="your_key")
   result = verifier.verify_citation_sync(citation)
