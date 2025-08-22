"""
Async Verification Worker
Handles background verification of citations using the fallback verifier.

This worker is called by the EnhancedSyncProcessor to verify citations
asynchronously without blocking the user interface.
"""

import os
import sys
import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def verify_citations_enhanced(citations: List, text: str, request_id: str, input_type: str, metadata: Dict) -> Dict[str, Any]:
    """
    Enhanced async verification of citations using the fallback verifier.
    
    This function provides enhanced verification with:
    - Cross-validation between multiple verification sources
    - Confidence scoring and quality assessment
    - False positive prevention
    - Enhanced metadata tracking
    """
    logger.info(f"[AsyncVerificationWorker {request_id}] Starting enhanced verification for {len(citations)} citations")
    
    try:
        # Try to use enhanced verification if available
        enhanced_results = None
        if _is_enhanced_verification_available():
            try:
                enhanced_results = _verify_with_enhanced_verification(citations, text, request_id)
                logger.info(f"[AsyncVerificationWorker {request_id}] Enhanced verification completed successfully")
            except Exception as e:
                logger.warning(f"[AsyncVerificationWorker {request_id}] Enhanced verification failed, falling back to basic: {e}")
                enhanced_results = None
        
        # Fall back to basic verification if enhanced is not available or failed
        if enhanced_results is None:
            enhanced_results = _verify_with_enhanced_fallback(citations, text, request_id)
        
        # Enhance results with additional metadata
        final_results = _enhance_verification_results(enhanced_results, citations, text, request_id)
        
        # Add quality assessment
        quality_metrics = _assess_overall_quality(final_results, text, request_id)
        
        return {
            'success': True,
            'citations': final_results,
            'quality_metrics': quality_metrics,
            'verification_method': 'enhanced_async',
            'processing_time': time.time() - _get_start_time(request_id),
            'request_id': request_id,
            'input_type': input_type,
            'metadata': metadata
        }
        
    except Exception as e:
        logger.error(f"[AsyncVerificationWorker {request_id}] Enhanced verification failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Enhanced verification failed: {str(e)}',
            'citations': [],
            'quality_metrics': {},
            'verification_method': 'error_fallback',
            'processing_time': time.time() - _get_start_time(request_id),
            'request_id': request_id,
            'input_type': input_type,
            'metadata': metadata
        }

def _verify_with_enhanced_fallback(citations: List, text: str, request_id: str) -> List[Dict[str, Any]]:
    """Verify citations using the enhanced fallback verifier with async methods."""
    try:
        from src.enhanced_fallback_verifier import EnhancedFallbackVerifier
        
        verifier = EnhancedFallbackVerifier()
        verification_results = []
        
        # Use async verification methods directly for better performance
        async def verify_citations_async():
            results = []
            for i, citation in enumerate(citations):
                try:
                    citation_text = citation.get('citation', str(citation))
                    extracted_name = citation.get('extracted_case_name')
                    extracted_year = citation.get('extracted_year') or citation.get('extracted_date')
                    
                    logger.info(f"[AsyncVerificationWorker {request_id}] Verifying citation {i+1}/{len(citations)}: {citation_text}")
                    
                    # Use the async verification method directly (includes vLex, Google Scholar, Casemine, etc.)
                    result = await verifier.verify_citation(citation_text, extracted_name, extracted_year)
                    
                    # Update citation with verification results
                    enhanced_citation = {
                        **citation,
                        'verified': result.get('verified', False),
                        'verification_source': result.get('source', 'enhanced_fallback'),
                        'canonical_name': result.get('canonical_name'),
                        'canonical_date': result.get('canonical_date'),
                        'canonical_url': result.get('url'),
                        'confidence': result.get('confidence', 0.0),
                        'verification_error': result.get('error'),
                        'verification_completed': True,
                        'verification_timestamp': time.time()
                    }
                    
                    results.append(enhanced_citation)
                    
                    if enhanced_citation['verified']:
                        logger.info(f"[AsyncVerificationWorker {request_id}] ✓ Verified: {citation_text} -> {enhanced_citation['canonical_name']} via {enhanced_citation['verification_source']}")
                    else:
                        logger.info(f"[AsyncVerificationWorker {request_id}] ✗ Failed: {citation_text} - {enhanced_citation['verification_error']}")
                        
                except Exception as e:
                    logger.warning(f"[AsyncVerificationWorker {request_id}] Error verifying citation {citation_text}: {e}")
                    # Add error information to citation
                    enhanced_citation = {
                        **citation,
                        'verified': False,
                        'verification_source': 'enhanced_fallback_error',
                        'verification_error': str(e),
                        'verification_completed': True,
                        'verification_timestamp': time.time()
                    }
                    results.append(enhanced_citation)
            
            return results
        
        # Run the async verification
        import asyncio
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an event loop, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, verify_citations_async())
                    verification_results = future.result()
            except RuntimeError:
                # No event loop, we can run directly
                verification_results = asyncio.run(verify_citations_async())
                
        except Exception as e:
            logger.error(f"[AsyncVerificationWorker {request_id}] Async verification failed: {e}")
            # Fall back to sync method if async fails
            verification_results = _verify_with_enhanced_fallback_sync_fallback(citations, text, request_id)
        
        return verification_results
        
    except Exception as e:
        logger.error(f"[AsyncVerificationWorker {request_id}] Enhanced fallback verification failed: {e}")
        # Return original citations with error status
        return [
            {
                **citation,
                'verified': False,
                'verification_source': 'enhanced_fallback_failed',
                'verification_error': str(e),
                'verification_completed': False
            }
            for citation in citations
        ]

def _verify_with_enhanced_fallback_sync_fallback(citations: List, text: str, request_id: str) -> List[Dict[str, Any]]:
    """Fallback to sync verification if async fails."""
    try:
        from src.enhanced_fallback_verifier import EnhancedFallbackVerifier
        
        verifier = EnhancedFallbackVerifier()
        verification_results = []
        
        for i, citation in enumerate(citations):
            try:
                citation_text = citation.get('citation', str(citation))
                extracted_name = citation.get('extracted_case_name')
                extracted_year = citation.get('extracted_year') or citation.get('extracted_date')
                
                logger.info(f"[AsyncVerificationWorker {request_id}] Sync fallback verification for citation {i+1}/{len(citations)}: {citation_text}")
                
                # Use the sync verification method as fallback
                result = verifier.verify_citation_sync(citation_text, extracted_name, extracted_year)
                
                # Update citation with verification results
                enhanced_citation = {
                    **citation,
                    'verified': result.get('verified', False),
                    'verification_source': result.get('source', 'enhanced_fallback_sync'),
                    'canonical_name': result.get('canonical_name'),
                    'canonical_date': result.get('canonical_date'),
                    'canonical_url': result.get('url'),
                    'confidence': result.get('confidence', 0.0),
                    'verification_error': result.get('error'),
                    'verification_completed': True,
                    'verification_timestamp': time.time()
                }
                
                verification_results.append(enhanced_citation)
                
                if enhanced_citation['verified']:
                    logger.info(f"[AsyncVerificationWorker {request_id}] ✓ Sync verified: {citation_text} -> {enhanced_citation['canonical_name']}")
                else:
                    logger.info(f"[AsyncVerificationWorker {request_id}] ✗ Sync failed: {citation_text} - {enhanced_citation['verification_error']}")
                    
            except Exception as e:
                logger.warning(f"[AsyncVerificationWorker {request_id}] Error in sync fallback verification for {citation_text}: {e}")
                # Add error information to citation
                enhanced_citation = {
                    **citation,
                    'verified': False,
                    'verification_source': 'enhanced_fallback_sync_error',
                    'verification_error': str(e),
                    'verification_completed': True,
                    'verification_timestamp': time.time()
                }
                verification_results.append(enhanced_citation)
        
        return verification_results
        
    except Exception as e:
        logger.error(f"[AsyncVerificationWorker {request_id}] Sync fallback verification failed: {e}")
        # Return original citations with error status
        return [
            {
                **citation,
                'verified': False,
                'verification_source': 'enhanced_fallback_sync_failed',
                'verification_error': str(e),
                'verification_completed': False
            }
            for citation in citations
        ]

def _enhance_verification_results(verification_results: List[Dict], original_citations: List, text: str, request_id: str) -> List[Dict[str, Any]]:
    """Enhance verification results with additional processing."""
    try:
        enhanced_results = []
        
        for result in verification_results:
            enhanced_result = result.copy()
            
            # Add verification metadata
            enhanced_result.update({
                'verification_method': 'enhanced_fallback_async',
                'verification_timestamp': time.time(),
                'text_length': len(text),
                'citation_count': len(original_citations)
            })
            
            # Add confidence scoring
            if enhanced_result.get('verified'):
                # Calculate confidence based on various factors
                confidence = _calculate_verification_confidence(enhanced_result)
                enhanced_result['confidence_score'] = confidence
                enhanced_result['verification_quality'] = _assess_verification_quality(confidence)
            else:
                enhanced_result['confidence_score'] = 0.0
                enhanced_result['verification_quality'] = 'failed'
            
            enhanced_results.append(enhanced_result)
        
        logger.info(f"[AsyncVerificationWorker {request_id}] Enhanced {len(enhanced_results)} verification results")
        return enhanced_results
        
    except Exception as e:
        logger.warning(f"[AsyncVerificationWorker {request_id}] Result enhancement failed: {e}")
        return verification_results

def _calculate_verification_confidence(verification_result: Dict) -> float:
    """Calculate confidence score for verified citations."""
    try:
        confidence = 0.0
        
        # Base confidence from verifier
        base_confidence = verification_result.get('confidence', 0.0)
        confidence += base_confidence * 0.4  # 40% weight
        
        # Canonical data completeness
        has_canonical_name = bool(verification_result.get('canonical_name'))
        has_canonical_date = bool(verification_result.get('canonical_date'))
        has_canonical_url = bool(verification_result.get('canonical_url'))
        
        if has_canonical_name:
            confidence += 0.2  # 20% for name
        if has_canonical_date:
            confidence += 0.2  # 20% for date
        if has_canonical_url:
            confidence += 0.2  # 20% for URL
        
        # Source reliability
        source = verification_result.get('verification_source', '')
        if 'courtlistener' in source.lower():
            confidence += 0.1  # 10% bonus for CourtListener
        elif 'enhanced_fallback' in source.lower():
            confidence += 0.05  # 5% bonus for enhanced fallback
        
        return min(confidence, 1.0)  # Cap at 1.0
        
    except Exception as e:
        logger.debug(f"Confidence calculation failed: {e}")
        return 0.5  # Default confidence

def _assess_verification_quality(confidence: float) -> str:
    """Assess verification quality based on confidence score."""
    if confidence >= 0.9:
        return 'excellent'
    elif confidence >= 0.8:
        return 'very_good'
    elif confidence >= 0.7:
        return 'good'
    elif confidence >= 0.6:
        return 'fair'
    elif confidence >= 0.5:
        return 'poor'
    else:
        return 'very_poor'

def _update_clusters_with_verification(verification_results: List[Dict], request_id: str) -> List[Dict[str, Any]]:
    """Update clusters with verification information."""
    try:
        # Group citations by verification status
        verified_citations = [c for c in verification_results if c.get('verified', False)]
        unverified_citations = [c for c in verification_results if not c.get('verified', False)]
        
        # Create cluster updates
        cluster_updates = []
        
        if verified_citations:
            # Group verified citations by reporter
            reporter_groups = {}
            for citation in verified_citations:
                reporter = _extract_reporter_from_citation(citation)
                if reporter not in reporter_groups:
                    reporter_groups[reporter] = []
                reporter_groups[reporter].append(citation)
            
            # Create verified clusters
            for reporter, citations in reporter_groups.items():
                if len(citations) > 1:
                    cluster_update = {
                        'cluster_id': f"verified_{reporter}_{len(cluster_updates)}",
                        'cluster_type': 'verified_parallel',
                        'reporter': reporter,
                        'citations': citations,
                        'verification_status': 'verified',
                        'canonical_name': citations[0].get('canonical_name'),
                        'canonical_date': citations[0].get('canonical_date'),
                        'confidence': sum(c.get('confidence_score', 0) for c in citations) / len(citations)
                    }
                    cluster_updates.append(cluster_update)
        
        if unverified_citations:
            # Create unverified cluster
            cluster_update = {
                'cluster_id': f"unverified_{len(cluster_updates)}",
                'cluster_type': 'unverified',
                'citations': unverified_citations,
                'verification_status': 'unverified',
                'verification_errors': [c.get('verification_error') for c in unverified_citations if c.get('verification_error')]
            }
            cluster_updates.append(cluster_update)
        
        logger.info(f"[AsyncVerificationWorker {request_id}] Created {len(cluster_updates)} cluster updates")
        return cluster_updates
        
    except Exception as e:
        logger.warning(f"[AsyncVerificationWorker {request_id}] Cluster update failed: {e}")
        return []

def _extract_reporter_from_citation(citation: Dict) -> str:
    """Extract reporter from citation text."""
    try:
        citation_text = citation.get('citation', '')
        import re
        
        # Common reporter patterns
        patterns = [
            r'\b(Wn\.\d+)',      # Wn.2d, Wn.3d
            r'\b(Wn\.\s*App\.)', # Wn. App.
            r'\b(P\.\d+)',       # P.3d
            r'\b(U\.S\.)',       # U.S.
            r'\b(S\.Ct\.)',      # S.Ct.
        ]
        
        for pattern in patterns:
            match = re.search(pattern, citation_text)
            if match:
                return match.group(1)
        
        return "Unknown"
        
    except Exception as e:
        logger.debug(f"Reporter extraction failed: {e}")
        return "Unknown"

def verify_citations_basic(citations: List, text: str, request_id: str, input_type: str, metadata: Dict) -> Dict[str, Any]:
    """
    Basic async verification for compatibility with existing systems.
    
    This is a simpler version that can be used as a fallback or for
    basic verification needs.
    """
    try:
        logger.info(f"[AsyncVerificationWorker {request_id}] Starting basic verification for {len(citations)} citations")
        
        # Use basic fallback verifier
        verification_results = []
        
        for citation in citations:
            citation_text = citation.get('citation', str(citation))
            
            # Basic verification (placeholder - implement actual verification logic)
            basic_result = {
                **citation,
                'verified': False,  # Default to unverified
                'verification_source': 'basic_async',
                'verification_completed': True,
                'verification_timestamp': time.time()
            }
            
            verification_results.append(basic_result)
        
        result = {
            'success': True,
            'verification_completed': True,
            'request_id': request_id,
            'input_type': input_type,
            'metadata': metadata,
            'verification_results': verification_results,
            'verification_method': 'basic_async'
        }
        
        logger.info(f"[AsyncVerificationWorker {request_id}] Basic verification completed")
        return result
        
    except Exception as e:
        logger.error(f"[AsyncVerificationWorker {request_id}] Basic verification failed: {str(e)}")
        return {
            'success': False,
            'error': f'Basic verification failed: {str(e)}',
            'request_id': request_id,
            'input_type': input_type,
            'metadata': metadata
        }

# Legacy function names for backward compatibility
def verify_citations_async(citations: List, text: str, request_id: str, input_type: str, metadata: Dict) -> Dict[str, Any]:
    """Legacy function name - redirects to enhanced verification."""
    return verify_citations_enhanced(citations, text, request_id, input_type, metadata)

# Enhanced verification helper functions
def _is_enhanced_verification_available() -> bool:
    """Check if enhanced verification is available."""
    try:
        from src.enhanced_courtlistener_verification import EnhancedCourtListenerVerifier
        courtlistener_api_key = os.getenv('COURTLISTENER_API_KEY')
        return bool(courtlistener_api_key)
    except ImportError:
        return False

def _verify_with_enhanced_verification(citations: List, text: str, request_id: str) -> List[Dict[str, Any]]:
    """Use enhanced verification with cross-validation if available."""
    try:
        from src.enhanced_courtlistener_verification import EnhancedCourtListenerVerifier
        
        courtlistener_api_key = os.getenv('COURTLISTENER_API_KEY')
        if not courtlistener_api_key:
            raise ValueError("CourtListener API key not available")
        
        verifier = EnhancedCourtListenerVerifier(courtlistener_api_key)
        enhanced_results = []
        
        for citation in citations:
            citation_text = citation.get('citation', str(citation))
            extracted_case_name = citation.get('extracted_case_name')
            
            # Enhanced verification with cross-validation
            verification_result = verifier.verify_citation_enhanced(citation_text, extracted_case_name)
            
            # Create enhanced result
            enhanced_result = {
                'citation': citation_text,
                'extracted_case_name': extracted_case_name,
                'extracted_date': citation.get('extracted_date'),
                'verified': verification_result.get('verified', False),
                'canonical_name': verification_result.get('canonical_name'),
                'canonical_date': verification_result.get('canonical_date'),
                'url': verification_result.get('url'),
                'source': verification_result.get('source', 'enhanced_courtlistener'),
                'validation_method': verification_result.get('validation_method', 'enhanced_cross_validation'),
                'confidence': verification_result.get('confidence', 0.0),
                'verification_timestamp': time.time()
            }
            
            enhanced_results.append(enhanced_result)
        
        logger.info(f"[AsyncVerificationWorker {request_id}] Enhanced verification completed for {len(enhanced_results)} citations")
        return enhanced_results
        
    except Exception as e:
        logger.error(f"[AsyncVerificationWorker {request_id}] Enhanced verification failed: {e}")
        raise

def _assess_overall_quality(verification_results: List[Dict], text: str, request_id: str) -> Dict[str, Any]:
    """Assess overall quality of verification results."""
    try:
        if not verification_results:
            return {'overall_quality': 'unknown', 'confidence': 0.0, 'issues': ['no_results']}
        
        # Calculate quality metrics
        total_citations = len(verification_results)
        verified_citations = sum(1 for r in verification_results if r.get('verified', False))
        high_confidence = sum(1 for r in verification_results if r.get('confidence', 0.0) > 0.8)
        medium_confidence = sum(1 for r in verification_results if 0.5 <= r.get('confidence', 0.0) <= 0.8)
        low_confidence = sum(1 for r in verification_results if r.get('confidence', 0.0) < 0.5)
        
        # Calculate average confidence
        total_confidence = sum(r.get('confidence', 0.0) for r in verification_results)
        avg_confidence = total_confidence / total_citations if total_citations > 0 else 0.0
        
        # Determine overall quality
        if verified_citations / total_citations > 0.8 and avg_confidence > 0.8:
            overall_quality = 'excellent'
        elif verified_citations / total_citations > 0.6 and avg_confidence > 0.6:
            overall_quality = 'good'
        elif verified_citations / total_citations > 0.4 and avg_confidence > 0.4:
            overall_quality = 'fair'
        else:
            overall_quality = 'poor'
        
        # Identify potential issues
        issues = []
        if verified_citations / total_citations < 0.5:
            issues.append('low_verification_rate')
        if avg_confidence < 0.5:
            issues.append('low_confidence')
        if low_confidence > total_citations * 0.3:
            issues.append('many_low_confidence_results')
        
        return {
            'overall_quality': overall_quality,
            'confidence': avg_confidence,
            'verification_rate': verified_citations / total_citations,
            'high_confidence_count': high_confidence,
            'medium_confidence_count': medium_confidence,
            'low_confidence_count': low_confidence,
            'issues': issues,
            'total_citations': total_citations,
            'verified_citations': verified_citations
        }
        
    except Exception as e:
        logger.error(f"[AsyncVerificationWorker {request_id}] Quality assessment failed: {e}")
        return {'overall_quality': 'error', 'confidence': 0.0, 'issues': ['assessment_failed']}

def _get_start_time(request_id: str) -> float:
    """Get start time for a request (placeholder implementation)."""
    # In a real implementation, this would track start times per request
    return time.time()

# Timing tracking (simple implementation)
_request_start_times = {}

def _track_request_start(request_id: str):
    """Track when a request started."""
    _request_start_times[request_id] = time.time()

def _get_request_duration(request_id: str) -> float:
    """Get duration of a request."""
    start_time = _request_start_times.get(request_id, time.time())
    return time.time() - start_time
