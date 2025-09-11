"""
Service Interfaces for Citation Processing

This module defines the contracts (interfaces) for all citation processing services.
Using abstract base classes ensures consistent APIs and enables dependency injection.
"""

from abc import ABC, abstractmethodfrom src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

from typing import List, Dict, Any, Optional, Tuple
from src.models import CitationResult, ProcessingConfig


class ICitationExtractor(ABC):
    """Interface for citation extraction services."""
    
    @abstractmethod
    def extract_citations(self, text: str) -> List[CitationResult]:
        """
        Extract citations from text using various methods (regex, eyecite, etc.).
        
        Args:
            text: The text to extract citations from
            
        Returns:
            List of CitationResult objects with basic extraction data
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, citation: CitationResult, text: str) -> CitationResult:
        """
        Extract metadata (case name, date, context) for a citation.
        
        Args:
            citation: Citation to extract metadata for
            text: Full text for context extraction
            
        Returns:
            Updated CitationResult with metadata
        """
        pass


class ICitationVerifier(ABC):
    """Interface for citation verification services."""
    
    @abstractmethod
    async def verify_citations(self, citations: List[CitationResult]) -> List[CitationResult]:
        """
        Verify citations using external APIs and databases.
        
        Args:
            citations: List of citations to verify
            
        Returns:
            Updated citations with verification results
        """
        pass
    
    @abstractmethod
    async def verify_single_citation(self, citation: CitationResult) -> CitationResult:
        """
        Verify a single citation.
        
        Args:
            citation: Citation to verify
            
        Returns:
            Updated citation with verification results
        """
        pass


class ICitationClusterer(ABC):
    """Interface for citation clustering services."""
    
    @abstractmethod
    def detect_parallel_citations(self, citations: List[CitationResult], text: str) -> List[CitationResult]:
        """
        Detect and group parallel citations that refer to the same case.
        
        Args:
            citations: List of citations to analyze
            text: Original text for context
            
        Returns:
            Updated citations with parallel citation relationships
        """
        pass
    
    @abstractmethod
    def cluster_citations(self, citations: List[CitationResult]) -> List[Dict[str, Any]]:
        """
        Group citations into clusters based on case relationships.
        
        Args:
            citations: List of citations to cluster
            
        Returns:
            List of cluster dictionaries with grouped citations
        """
        pass


class ICitationProcessor(ABC):
    """Interface for the main citation processing orchestrator."""
    
    @abstractmethod
    async def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process text through the complete citation pipeline.
        
        Args:
            text: Text to process
            
        Returns:
            Dictionary with citations and clusters
        """
        pass
    
    @abstractmethod
    async def process_document_citations(self, document_text: str, document_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Process document citations with optional type-specific handling.
        
        Args:
            document_text: Document text to process
            document_type: Optional document type for specialized processing
            
        Returns:
            Dictionary with processing results
        """
        pass


class IServiceContainer(ABC):
    """Interface for dependency injection container."""
    
    @abstractmethod
    def get_extractor(self) -> ICitationExtractor:
        """Get citation extractor service."""
        pass
    
    @abstractmethod
    def get_verifier(self) -> ICitationVerifier:
        """Get citation verifier service."""
        pass
    
    @abstractmethod
    def get_clusterer(self) -> ICitationClusterer:
        """Get citation clusterer service."""
        pass
    
    @abstractmethod
    def get_processor(self) -> ICitationProcessor:
        """Get main citation processor."""
        pass
