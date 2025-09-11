"""
Citation Processing Services

This package contains the modular citation processing services that replace
the monolithic unified_citation_processor_v2.py with focused, maintainable components.

Architecture:
- CitationExtractor: Pure extraction logic (regex, eyecite)
- CitationVerifier: API integrations (CourtListener, web search)
- CitationClusterer: Grouping and parallel citation detection
- CitationProcessor: Orchestrator that coordinates all services
"""

from .interfaces import (from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

    ICitationExtractor,
    ICitationVerifier, 
    ICitationClusterer,
    ICitationProcessor
)

from .citation_extractor import CitationExtractor
from .citation_verifier import CitationVerifier
from .citation_clusterer import CitationClusterer
from .citation_processor import CitationProcessor, ServiceContainer

__all__ = [
    'ICitationExtractor',
    'ICitationVerifier',
    'ICitationClusterer', 
    'ICitationProcessor',
    'CitationExtractor',
    'CitationVerifier',
    'CitationClusterer',
    'CitationProcessor',
    'ServiceContainer'
]
