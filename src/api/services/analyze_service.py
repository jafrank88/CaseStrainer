"""
Analyze request handler: request parsing, progress wiring, sync vs async decision,
call to process_citations_unified or enqueue (process_citation_task_direct), response shaping.

The route (api.routes.analyze) is thin: get request, call handle_analyze, return response.
Implementation lives in api.services.analyze_pipeline.analyze_request; vue_api_endpoints_updated
keeps _analyze_impl as a thin backward-compatible shim.
"""

import logging

logger = logging.getLogger(__name__)


def handle_analyze(request):
    """
    Handle POST /analyze: parse request (file/JSON/form/URL), resolve force_mode and enable_verification,
    run sync (UnifiedInputProcessor / process_citations_unified) or enqueue async (process_citation_task_direct),
    return JSON response or task_id for polling.
    """
    from src.api.services.analyze_pipeline import analyze_request
    return analyze_request(request)
