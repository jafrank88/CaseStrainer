import requests
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import logging
import json
from typing import List
import sys

logger = logging.getLogger(__name__)

# from src.models import CitationResult

# This module previously contained deprecated verification functions.
# All verification functionality has been moved to:
# - src.unified_citation_clustering.cluster_citations_unified() for batch verification
# - src.enhanced_courtlistener_verification for CourtListener API integration
# - src.enhanced_fallback_verifier for fallback verification methods

# Use cluster_citations_unified() with enable_verification=True for modern verification