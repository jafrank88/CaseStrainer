"""
Async Verification Worker
Handles background verification of citations using the fallback verifier.

Provides asynchronous citation verification without blocking the user interface.
"""

import os

import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def verify_citations_enhanced(
    citations: List,
    text: str,
    request_id: str,
    input_type: str,
    metadata: Dict,
    progress_callback: Optional[callable] = None,
) -> Dict[str, Any]:
    """
    Enhanced async verification of citations using the fallback verifier.

    This function provides enhanced verification with:
    - Cross-validation between multiple verification sources
    - Confidence scoring and quality assessment
    - False positive prevention
    - Enhanced metadata tracking
    """
    logger.info(f"[AsyncVerificationWorker {request_id}] Starting enhanced verification for {len(citations)} citations")

    # Update progress at start of verification
    if progress_callback:
        progress_callback(15, "verification", "Starting citation verification")

    try:
        enhanced_results = None
        if _is_enhanced_verification_available():
            try:
                if progress_callback:
                    progress_callback(20, "verification", "Running enhanced verification")
                enhanced_results = _verify_with_enhanced_verification(citations, text, request_id)
                logger.info(f"[AsyncVerificationWorker {request_id}] Enhanced verification completed successfully")
            except Exception as e:
                logger.warning(
                    f"[AsyncVerificationWorker {request_id}] Enhanced verification failed, falling back to basic: {e}"
                )
                enhanced_results = None

        if enhanced_results is None:
            if progress_callback:
                progress_callback(25, "verification", "Running fallback verification")
            enhanced_results = _verify_with_enhanced_fallback(citations, text, request_id)

        if progress_callback:
            progress_callback(80, "verification", "Processing verification results")

        final_results = _enhance_verification_results(enhanced_results, citations, text, request_id)

        if progress_callback:
            progress_callback(90, "verification", "Assessing result quality")

        quality_metrics = _assess_overall_quality(final_results, text, request_id)

        if progress_callback:
            progress_callback(95, "verification", "Finalizing verification results")

        return {
            "success": True,
            "citations": final_results,
            "quality_metrics": quality_metrics,
            "verification_method": "enhanced_async",
            "processing_time": time.time() - _get_start_time(request_id),
            "request_id": request_id,
            "input_type": input_type,
            "metadata": metadata,
        }

    except Exception as e:
        logger.error(f"[AsyncVerificationWorker {request_id}] Enhanced verification failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Enhanced verification failed: {str(e)}",
            "citations": [],
            "quality_metrics": {},
            "verification_method": "error_fallback",
            "processing_time": time.time() - _get_start_time(request_id),
            "request_id": request_id,
            "input_type": input_type,
            "metadata": metadata,
        }


def _verify_with_enhanced_fallback(citations: List, text: str, request_id: str) -> List[Dict[str, Any]]:
    """Verify citations using the enhanced fallback verifier with async methods."""
    try:
        from src.unified_verification_master import UnifiedVerificationMaster

        verifier = UnifiedVerificationMaster()
        verification_results = []

        async def verify_citations_async():
            # Use batch verification for better performance
            logger.info(
                f"[AsyncVerificationWorker {request_id}] Using batch verification for {len(citations)} citations"
            )

            # Prepare data for batch verification
            citation_texts = []
            extracted_names = []
            extracted_years = []

            for citation in citations:
                citation_texts.append(citation.get("citation", str(citation)))
                extracted_names.append(citation.get("extracted_case_name"))
                extracted_years.append(citation.get("extracted_year") or citation.get("extracted_date"))

            # Call batch verification
            batch_results = await verifier.verify_citations_batch(
                citation_texts,
                extracted_names,
                extracted_years,
                batch_size=50,  # Process 50 citations at a time
                timeout_per_citation=10.0,
                progress_callback=progress_callback,
            )

            # Convert batch results back to enhanced citation format
            results = []
            for i, (citation, verification_result) in enumerate(zip(citations, batch_results)):
                # CRITICAL FIX: Override extracted date with canonical date from verification
                # This fixes the date contamination issue where dates are extracted from
                # citing context instead of the cited case
                final_date = verification_result.canonical_date
                date_source = "verified" if (verification_result.verified and final_date) else "extracted"

                # Fall back to extracted date only if no canonical date available
                if not final_date:
                    final_date = citation.get("extracted_date") or citation.get("extracted_year")

                enhanced_citation = {
                    **citation,
                    "verified": verification_result.verified,
                    "verification_source": verification_result.source,
                    "canonical_name": verification_result.canonical_name,
                    "canonical_date": final_date,  # Use verified date
                    "extracted_date": citation.get("extracted_date")
                    or citation.get("extracted_year"),  # Preserve original
                    "date_source": date_source,  # Track where date came from
                    "canonical_url": verification_result.url,
                    "confidence": verification_result.confidence,
                    "verification_error": verification_result.error,
                    "verification_completed": True,
                    "verification_timestamp": time.time(),
                }

                results.append(enhanced_citation)

                if enhanced_citation["verified"]:
                    logger.info(
                        f"[AsyncVerificationWorker {request_id}] ✓ Verified: {citation_texts[i]} -> {enhanced_citation['canonical_name']} via {enhanced_citation['verification_source']}"
                    )
                else:
                    logger.info(
                        f"[AsyncVerificationWorker {request_id}] ✗ Failed: {citation_texts[i]} - {enhanced_citation['verification_error']}"
                    )

            return results

        import asyncio

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, verify_citations_async())
                    verification_results = future.result()
            except RuntimeError:
                verification_results = asyncio.run(verify_citations_async())

        except Exception as e:
            logger.error(f"[AsyncVerificationWorker {request_id}] Async verification failed: {e}")
            verification_results = _verify_with_enhanced_fallback_sync_fallback(citations, text, request_id)

        return verification_results

    except Exception as e:
        logger.error(f"[AsyncVerificationWorker {request_id}] Enhanced fallback verification failed: {e}")
        return [
            {
                **citation,
                "verified": False,
                "verification_source": "enhanced_fallback_failed",
                "verification_error": str(e),
                "verification_completed": False,
            }
            for citation in citations
        ]


def _verify_with_enhanced_fallback_sync_fallback(citations: List, text: str, request_id: str) -> List[Dict[str, Any]]:
    """Fallback to sync verification if async fails."""
    try:
        from src.unified_verification_master import UnifiedVerificationMaster

        verifier = UnifiedVerificationMaster()

        # Use batch verification even in sync fallback for efficiency
        logger.info(
            f"[AsyncVerificationWorker {request_id}] Using batch verification in sync fallback for {len(citations)} citations"
        )

        # Prepare data for batch verification
        citation_texts = []
        extracted_names = []
        extracted_years = []

        for citation in citations:
            citation_texts.append(citation.get("citation", str(citation)))
            extracted_names.append(citation.get("extracted_case_name"))
            extracted_years.append(citation.get("extracted_year") or citation.get("extracted_date"))

        # Use batch verification in sync context
        import asyncio

        batch_results = asyncio.run(
            verifier.verify_citations_batch(
                citation_texts,
                extracted_names,
                extracted_years,
                batch_size=50,  # Process 50 citations at a time
                timeout_per_citation=10.0,
            )
        )

        # Convert batch results back to enhanced citation format
        verification_results = []
        for i, (citation, verification_result) in enumerate(zip(citations, batch_results)):
            enhanced_citation = {
                **citation,
                "verified": verification_result.verified,
                "verification_source": verification_result.source,
                "canonical_name": verification_result.canonical_name,
                "canonical_date": verification_result.canonical_date,
                "canonical_url": verification_result.url,
                "confidence": verification_result.confidence,
                "verification_error": verification_result.error,
                "verification_completed": True,
                "verification_timestamp": time.time(),
            }

            verification_results.append(enhanced_citation)

            if enhanced_citation["verified"]:
                logger.info(
                    f"[AsyncVerificationWorker {request_id}] ✓ Sync batch verified: {citation_texts[i]} -> {enhanced_citation['canonical_name']}"
                )
            else:
                logger.info(
                    f"[AsyncVerificationWorker {request_id}] ✗ Sync batch failed: {citation_texts[i]} - {enhanced_citation['verification_error']}"
                )

        return verification_results

    except Exception as e:
        logger.error(f"[AsyncVerificationWorker {request_id}] Sync fallback verification failed: {e}")
        return [
            {
                **citation,
                "verified": False,
                "verification_source": "enhanced_fallback_sync_failed",
                "verification_error": str(e),
                "verification_completed": False,
            }
            for citation in citations
        ]


def _enhance_verification_results(
    verification_results: List[Dict], original_citations: List, text: str, request_id: str
) -> List[Dict[str, Any]]:
    """Enhance verification results with additional processing."""
    try:
        enhanced_results = []

        for result in verification_results:
            if isinstance(result, dict):
                enhanced_result = result.copy()
            else:
                enhanced_result = {
                    "citation": getattr(result, "citation", str(result)),
                    "extracted_case_name": getattr(result, "extracted_case_name", None),
                    "extracted_date": getattr(result, "extracted_date", None),
                    "verified": getattr(result, "verified", False),
                    "canonical_name": getattr(result, "canonical_name", None),
                    "canonical_date": getattr(result, "canonical_date", None),
                    "canonical_url": getattr(result, "canonical_url", None),
                    "source": getattr(result, "source", "unknown"),
                    "validation_method": getattr(result, "validation_method", "unknown"),
                    "confidence": getattr(result, "confidence", 0.0),
                    "url": getattr(result, "url", None),
                }

            enhanced_result.update(
                {
                    "verification_method": "enhanced_fallback_async",
                    "verification_timestamp": time.time(),
                    "text_length": len(text),
                    "citation_count": len(original_citations),
                }
            )

            if enhanced_result.get("verified"):
                confidence = _calculate_verification_confidence(enhanced_result)
                enhanced_result["confidence_score"] = confidence
                enhanced_result["verification_quality"] = _assess_verification_quality(confidence)
            else:
                enhanced_result["confidence_score"] = 0.0
                enhanced_result["verification_quality"] = "failed"

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

        base_confidence = verification_result.get("confidence", 0.0)
        confidence += base_confidence * 0.4  # 40% weight

        has_canonical_name = bool(verification_result.get("canonical_name"))
        has_canonical_date = bool(verification_result.get("canonical_date"))
        has_canonical_url = bool(verification_result.get("canonical_url"))

        if has_canonical_name:
            confidence += 0.2  # 20% for name
        if has_canonical_date:
            confidence += 0.2  # 20% for date
        if has_canonical_url:
            confidence += 0.2  # 20% for URL

        source = verification_result.get("verification_source", "")
        if "courtlistener" in source.lower():
            confidence += 0.1  # 10% bonus for CourtListener
        elif "enhanced_fallback" in source.lower():
            confidence += 0.05  # 5% bonus for enhanced fallback

        return min(confidence, 1.0)  # Cap at 1.0

    except Exception as e:
        return 0.5  # Default confidence


def _assess_verification_quality(confidence: float) -> str:
    """Assess verification quality based on confidence score."""
    if confidence >= 0.9:
        return "excellent"
    elif confidence >= 0.8:
        return "very_good"
    elif confidence >= 0.7:
        return "good"
    elif confidence >= 0.6:
        return "fair"
    elif confidence >= 0.5:
        return "poor"
    else:
        return "very_poor"


def _update_clusters_with_verification(verification_results: List[Dict], request_id: str) -> List[Dict[str, Any]]:
    """Update clusters with verification information."""
    try:
        verified_citations = [c for c in verification_results if c.get("verified", False)]
        unverified_citations = [c for c in verification_results if not c.get("verified", False)]

        cluster_updates = []

        if verified_citations:
            reporter_groups = {}
            for citation in verified_citations:
                reporter = _extract_reporter_from_citation(citation)
                if reporter not in reporter_groups:
                    reporter_groups[reporter] = []
                reporter_groups[reporter].append(citation)

            for reporter, citations in reporter_groups.items():
                if len(citations) > 1:
                    cluster_update = {
                        "cluster_id": f"verified_{reporter}_{len(cluster_updates)}",
                        "cluster_type": "verified_parallel",
                        "reporter": reporter,
                        "citations": citations,
                        "verification_status": "verified",
                        "canonical_name": citations[0].get("canonical_name"),
                        "canonical_date": citations[0].get("canonical_date"),
                        "confidence": sum(c.get("confidence_score", 0) for c in citations) / len(citations),
                    }
                    cluster_updates.append(cluster_update)

        if unverified_citations:
            cluster_update = {
                "cluster_id": f"unverified_{len(cluster_updates)}",
                "cluster_type": "unverified",
                "citations": unverified_citations,
                "verification_status": "unverified",
                "verification_errors": [
                    c.get("verification_error") for c in unverified_citations if c.get("verification_error")
                ],
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
        citation_text = citation.get("citation", "")
        import re

        patterns = [
            r"\b(Wn\.\d+)",  # Wn.2d, Wn.3d
            r"\b(Wn\.\s*App\.)",  # Wn. App.
            r"\b(P\.\d+)",  # P.3d
            r"\b(U\.S\.)",  # U.S.
            r"\b(S\.Ct\.)",  # S.Ct.
        ]

        for pattern in patterns:
            match = re.search(pattern, citation_text)
            if match:
                return match.group(1)

        return "Unknown"

    except Exception as e:
        return "Unknown"


def verify_citations_basic(
    citations: List, text: str, request_id: str, input_type: str, metadata: Dict
) -> Dict[str, Any]:
    """
    Basic async verification for compatibility with existing systems.

    This is a simpler version that can be used as a fallback or for
    basic verification needs.
    """
    try:
        logger.info(
            f"[AsyncVerificationWorker {request_id}] Starting basic verification for {len(citations)} citations"
        )

        verification_results = []

        for citation in citations:
            citation_text = citation.get("citation", str(citation))

            basic_result = {
                **citation,
                "verified": False,  # Default to unverified
                "verification_source": "basic_async",
                "verification_completed": True,
                "verification_timestamp": time.time(),
            }

            verification_results.append(basic_result)

        result = {
            "success": True,
            "verification_completed": True,
            "request_id": request_id,
            "input_type": input_type,
            "metadata": metadata,
            "verification_results": verification_results,
            "verification_method": "basic_async",
        }

        logger.info(f"[AsyncVerificationWorker {request_id}] Basic verification completed")
        return result

    except Exception as e:
        logger.error(f"[AsyncVerificationWorker {request_id}] Basic verification failed: {str(e)}")
        return {
            "success": False,
            "error": f"Basic verification failed: {str(e)}",
            "request_id": request_id,
            "input_type": input_type,
            "metadata": metadata,
        }


def verify_citations_async(
    citations: List, text: str, request_id: str, input_type: str, metadata: Dict
) -> Dict[str, Any]:
    """Legacy function name - redirects to enhanced verification."""
    return verify_citations_enhanced(citations, text, request_id, input_type, metadata)


def _is_enhanced_verification_available() -> bool:
    """Check if enhanced verification is available."""
    try:
        pass

        courtlistener_api_key = os.getenv("COURTLISTENER_API_KEY")
        return bool(courtlistener_api_key)
    except ImportError:
        return False


def _verify_with_enhanced_verification(citations: List, text: str, request_id: str) -> List[Dict[str, Any]]:
    """Use hybrid verification: CourtListener first, then enhanced fallback if needed."""
    try:
        from src.enhanced_courtlistener_verification import EnhancedCourtListenerVerifier
        from src.enhanced_fallback_verifier import EnhancedFallbackVerifier

        courtlistener_api_key = os.getenv("COURTLISTENER_API_KEY")
        if not courtlistener_api_key:
            raise ValueError("CourtListener API key not available")

        courtlistener_verifier = EnhancedCourtListenerVerifier(courtlistener_api_key)
        fallback_verifier = EnhancedFallbackVerifier()

        enhanced_results = []

        for citation in citations:
            citation_text = citation.get("citation", str(citation))
            extracted_case_name = citation.get("extracted_case_name", None)
            extracted_date = citation.get("extracted_date", None)

            logger.info(f"[AsyncVerificationWorker {request_id}] Starting hybrid verification for: {citation_text}")

            courtlistener_result = courtlistener_verifier.verify_citation_enhanced(citation_text, extracted_case_name)

            if courtlistener_result.get("verified", False):
                logger.info(f"[AsyncVerificationWorker {request_id}] CourtListener verified: {citation_text}")
                enhanced_result = {
                    "citation": citation_text,
                    "extracted_case_name": extracted_case_name,
                    "extracted_date": extracted_date,
                    "verified": True,
                    "canonical_name": courtlistener_result.get("canonical_name"),
                    "canonical_date": courtlistener_result.get("canonical_date"),
                    "url": courtlistener_result.get("url"),
                    "source": "courtlistener",
                    "validation_method": courtlistener_result.get("validation_method", "enhanced_cross_validation"),
                    "confidence": courtlistener_result.get("confidence", 0.0),
                    "verification_timestamp": time.time(),
                    "verification_strategy": "courtlistener_only",
                }
            else:
                logger.info(
                    f"[AsyncVerificationWorker {request_id}] CourtListener failed, trying enhanced fallback for: {citation_text}"
                )

                try:
                    import asyncio

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    try:
                        fallback_result = loop.run_until_complete(
                            fallback_verifier.verify_citation(citation_text, extracted_case_name, extracted_date, False)
                        )
                    finally:
                        loop.close()
                        asyncio.set_event_loop(None)

                    if fallback_result and fallback_result.get("verified", False):
                        logger.info(
                            f"[AsyncVerificationWorker {request_id}] Enhanced fallback verified: {citation_text} via {fallback_result.get('source', 'unknown')}"
                        )
                        enhanced_result = {
                            "citation": citation_text,
                            "extracted_case_name": extracted_case_name,
                            "extracted_date": extracted_date,
                            "verified": True,
                            "canonical_name": fallback_result.get("canonical_name"),
                            "canonical_date": fallback_result.get("canonical_date"),
                            "url": fallback_result.get("url"),
                            "source": fallback_result.get("source", "enhanced_fallback"),
                            "validation_method": "enhanced_fallback_verification",
                            "confidence": fallback_result.get("confidence", 0.0),
                            "verification_timestamp": time.time(),
                            "verification_strategy": "fallback_only",
                        }
                    else:
                        logger.warning(
                            f"[AsyncVerificationWorker {request_id}] Both CourtListener and fallback failed for: {citation_text}"
                        )
                        enhanced_result = {
                            "citation": citation_text,
                            "extracted_case_name": extracted_case_name,
                            "extracted_date": extracted_date,
                            "verified": False,
                            "canonical_name": None,
                            "canonical_date": None,
                            "url": None,
                            "source": "verification_failed",
                            "validation_method": "both_failed",
                            "confidence": 0.0,
                            "verification_timestamp": time.time(),
                            "verification_strategy": "both_failed",
                        }

                except Exception as e:
                    logger.error(
                        f"[AsyncVerificationWorker {request_id}] Fallback verification error for {citation_text}: {e}"
                    )
                    enhanced_result = {
                        "citation": citation_text,
                        "extracted_case_name": extracted_case_name,
                        "extracted_date": extracted_date,
                        "verified": False,
                        "canonical_name": None,
                        "canonical_date": None,
                        "url": None,
                        "source": "fallback_error",
                        "validation_method": "fallback_error",
                        "confidence": 0.0,
                        "verification_timestamp": time.time(),
                        "verification_strategy": "fallback_error",
                    }

            enhanced_results.append(enhanced_result)

        logger.info(
            f"[AsyncVerificationWorker {request_id}] Hybrid verification completed for {len(enhanced_results)} citations"
        )
        return enhanced_results

    except Exception as e:
        logger.error(f"[AsyncVerificationWorker {request_id}] Hybrid verification failed: {e}")
        raise


def _assess_overall_quality(verification_results: List[Dict], text: str, request_id: str) -> Dict[str, Any]:
    """Assess overall quality of verification results."""
    try:
        if not verification_results:
            return {"overall_quality": "unknown", "confidence": 0.0, "issues": ["no_results"]}

        total_citations = len(verification_results)
        verified_citations = sum(1 for r in verification_results if r.get("verified", False))
        high_confidence = sum(1 for r in verification_results if r.get("confidence", 0.0) > 0.8)
        medium_confidence = sum(1 for r in verification_results if 0.5 <= r.get("confidence", 0.0) <= 0.8)
        low_confidence = sum(1 for r in verification_results if r.get("confidence", 0.0) < 0.5)

        total_confidence = sum(r.get("confidence", 0.0) for r in verification_results)
        avg_confidence = total_confidence / total_citations if total_citations > 0 else 0.0

        if verified_citations / total_citations > 0.8 and avg_confidence > 0.8:
            overall_quality = "excellent"
        elif verified_citations / total_citations > 0.6 and avg_confidence > 0.6:
            overall_quality = "good"
        elif verified_citations / total_citations > 0.4 and avg_confidence > 0.4:
            overall_quality = "fair"
        else:
            overall_quality = "poor"

        issues = []
        if verified_citations / total_citations < 0.5:
            issues.append("low_verification_rate")
        if avg_confidence < 0.5:
            issues.append("low_confidence")
        if low_confidence > total_citations * 0.3:
            issues.append("many_low_confidence_results")

        return {
            "overall_quality": overall_quality,
            "confidence": avg_confidence,
            "verification_rate": verified_citations / total_citations,
            "high_confidence_count": high_confidence,
            "medium_confidence_count": medium_confidence,
            "low_confidence_count": low_confidence,
            "issues": issues,
            "total_citations": total_citations,
            "verified_citations": verified_citations,
        }

    except Exception as e:
        logger.error(f"[AsyncVerificationWorker {request_id}] Quality assessment failed: {e}")
        return {"overall_quality": "error", "confidence": 0.0, "issues": ["assessment_failed"]}


def _get_start_time(request_id: str) -> float:
    """Get start time for a request (placeholder implementation)."""
    return time.time()


_request_start_times = {}


def _track_request_start(request_id: str):
    """Track when a request started."""
    _request_start_times[request_id] = time.time()


def _get_request_duration(request_id: str) -> float:
    """Get duration of a request."""
    start_time = _request_start_times.get(request_id, time.time())
    return time.time() - start_time
