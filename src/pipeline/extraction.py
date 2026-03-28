"""Stage 1: Citation extraction. Thin wrapper around UnifiedCitationProcessorV2.process_text."""

import logging
from typing import Any, Dict

from src.pipeline.context import ProcessingContext

logger = logging.getLogger(__name__)


async def run_extract_citations(
    processor: Any, text: str, context: ProcessingContext
) -> Dict[str, Any]:
    """Extract citations from text. Returns dict with 'citations' and other keys.
    Text is normalized before extraction so positions and citation strings are consistent
    (e.g. Supp3d -> Supp. 3d, PDF artifacts fixed)."""
    try:
        logger.info(f"[PIPELINE-{context.trace_id}] run_extract_citations: normalizing text ({len(text or '')} chars)")
        from src.utils.text_normalizer import normalize_text
        text = normalize_text(text) if text else text
        logger.info(f"[PIPELINE-{context.trace_id}] run_extract_citations: normalize done, calling process_text with {len(text)} chars")
        # CRITICAL: Update context so clustering gets same text citation indices were computed from
        context.input_text = text
        result = await processor.process_text(text)
        citations_count = len(result.get("citations", []))
        logger.info(
            f"[PIPELINE-{context.trace_id}] _extract_citations: process_text returned {citations_count} citations"
        )
        context.metadata["extraction_count"] = citations_count
        return result
    except Exception as e:
        logger.error(
            f"[PIPELINE-{context.trace_id}] _extract_citations FAILED: {e}", exc_info=True
        )
        context.add_error(str(e), "extraction")
        raise
