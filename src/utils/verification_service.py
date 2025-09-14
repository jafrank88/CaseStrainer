"""
Unified verification service to consolidate verification entry points.
Provides a single interface for citation verification across different pipelines.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VerificationRequest:
    """Request object for citation verification."""
    citations: List[Dict[str, Any]]
    text: str
    verify_citations: bool = True
    timeout: int = 30

@dataclass
class VerificationResult:
    """Result object for citation verification."""
    citations: List[Dict[str, Any]]
    verification_completed: bool
    verification_queued: bool
    error: Optional[str] = None
    message: Optional[str] = None

class VerificationService:
    """
    Unified verification service that provides a single entry point
    for citation verification across different processing pipelines.
    """
    
    def __init__(self):
        self.logger = logger
    
    def verify_citations(self, request: VerificationRequest) -> VerificationResult:
        """
        Verify citations using the appropriate verification method.
        
        Args:
            request: VerificationRequest containing citations and options
            
        Returns:
            VerificationResult with verification status and updated citations
        """
        try:
            if not request.verify_citations:
                return VerificationResult(
                    citations=request.citations,
                    verification_completed=False,
                    verification_queued=False,
                    message="Verification disabled"
                )
            
            # Import verification modules dynamically to avoid circular imports
            from src.enhanced_courtlistener_verification import EnhancedCourtListenerVerifier
            from src.enhanced_fallback_verifier import EnhancedFallbackVerifier
            
            # Use enhanced verification pipeline
            verifier = EnhancedCourtListenerVerifier()
            fallback_verifier = EnhancedFallbackVerifier()
            
            # Perform verification
            verified_citations = verifier.verify_citations_batch(
                request.citations, 
                request.text,
                timeout=request.timeout
            )
            
            # Apply fallback verification if needed
            if verified_citations:
                verified_citations = fallback_verifier.verify_citations_fallback(
                    verified_citations,
                    request.text
                )
            
            return VerificationResult(
                citations=verified_citations or request.citations,
                verification_completed=True,
                verification_queued=False,
                message="Verification completed successfully"
            )
            
        except Exception as e:
            self.logger.error(f"Verification failed: {str(e)}")
            return VerificationResult(
                citations=request.citations,
                verification_completed=False,
                verification_queued=False,
                error=str(e),
                message="Verification failed"
            )
    
    def verify_citations_sync(self, citations: List[Dict[str, Any]], text: str, 
                            verify_citations: bool = True, timeout: int = 30) -> List[Dict[str, Any]]:
        """
        Synchronous verification method for backward compatibility.
        
        Args:
            citations: List of citation dictionaries
            text: Source text
            verify_citations: Whether to perform verification
            timeout: Timeout in seconds
            
        Returns:
            List of verified citation dictionaries
        """
        request = VerificationRequest(
            citations=citations,
            text=text,
            verify_citations=verify_citations,
            timeout=timeout
        )
        
        result = self.verify_citations(request)
        return result.citations

# Global instance for easy access
verification_service = VerificationService()
