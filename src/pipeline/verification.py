"""Stages 2-3: Citation verification and parallel verification with timeout."""

import asyncio
import logging
import os
from typing import Any, List

from src.models import CitationResult
from src.pipeline.context import ProcessingContext

logger = logging.getLogger(__name__)


async def run_verify_citations(
    processor: Any,
    citations: List[CitationResult],
    text: str,
    context: ProcessingContext,
) -> List[CitationResult]:
    """Verify citations and get canonical data with timeout protection."""
    import time as _time
    _stage2_t0 = _time.time()
    try:
        async def verify_with_timeout():
            result = processor._verify_citations_sync(citations, text)
            return result

        base_timeout = 30
        per_citation_timeout = 3
        max_timeout = 120
        timeout_seconds = min(
            max_timeout, max(base_timeout, len(citations) * per_citation_timeout)
        )
        logger.info(
            f"[PIPELINE-{context.trace_id}] Progressive verification timeout: {timeout_seconds}s for {len(citations)} citations"
        )

        try:
            verified_citations = await asyncio.wait_for(
                verify_with_timeout(), timeout=timeout_seconds
            )
            context.metadata["verification_count"] = len(verified_citations)
            logger.info(
                f"[PIPELINE-{context.trace_id}] Verification completed, returned {len(verified_citations)} citations in {_time.time()-_stage2_t0:.2f}s"
            )
            return verified_citations
        except asyncio.TimeoutError:
            logger.warning(
                f"[PIPELINE-{context.trace_id}] Verification timed out after {timeout_seconds}s, returning original citations (elapsed {_time.time()-_stage2_t0:.2f}s)"
            )
            context.add_warning(
                f"Verification timed out after {timeout_seconds}s", "verification"
            )
            return citations

    except Exception as e:
        logger.error(
            f"[PIPELINE-{context.trace_id}] Verification error details: "
            f"Citations count: {len(citations)}, "
            f"Error type: {type(e).__name__}, "
            f"Error message: {str(e)}"
        )
        courtlistener_key = os.environ.get("COURTLISTENER_API_KEY", "")
        if not courtlistener_key:
            logger.error(
                f"[PIPELINE-{context.trace_id}] CRITICAL: COURTLISTENER_API_KEY is not set! "
                "Verification requires a valid CourtListener API key."
            )
        else:
            logger.info(
                f"[PIPELINE-{context.trace_id}] CourtListener API key is set (length: {len(courtlistener_key)})"
            )
        context.add_error(str(e), "verification")
        return citations


async def run_parallel_verification(
    processor: Any,
    citations: List[CitationResult],
    context: ProcessingContext,
) -> List[CitationResult]:
    """Apply parallel verification: ensure bidirectional parallels and propagate canonical to cluster."""
    import time as _time
    _stage3_t0 = _time.time()
    try:
        try:
            text = getattr(context, "input_text", "") or ""
            processor.ensure_bidirectional_parallels(citations, text)
        except Exception:
            pass
        processor.propagate_canonical_to_cluster(citations)

        parallel_count = sum(
            1 for c in citations if getattr(c, "true_by_parallel", False)
        )
        context.metadata["parallel_verifications"] = parallel_count
        logger.info(
            f"[PIPELINE-{context.trace_id}] Parallel verification completed - {parallel_count} citations marked in {_time.time()-_stage3_t0:.2f}s"
        )
        return citations
    except Exception as e:
        context.add_error(str(e), "parallel_verification")
        return citations
