# DEPRECATED: Use verify_citation from src.enhanced_multi_source_verifier instead of CitationVerifier.
# The CitationVerifier class and all related methods have been removed.

#!/usr/bin/env python3
"""
Citation Verification Module for CaseStrainer

This module provides comprehensive citation verification using multiple methods:
1. CourtListener Citation Lookup API
2. CourtListener Opinion Search API
3. CourtListener Cluster/Docket APIs
4. LangSearch API (backup)
5. Google Scholar (backup)

It implements a fallback mechanism to try different methods if one fails.
"""

import os
import re
import time
import json
import requests
import urllib.parse
from typing import Optional, Dict, Any, List
import traceback
import logging
from datetime import datetime, timedelta
import functools
import threading
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import rate limiter
from utils.rate_limiter import courtlistener_limiter

# API endpoints - Updated to use v4 as per requirements
COURTLISTENER_BASE_URL = "https://www.courtlistener.com/api/rest/v4/"
COURTLISTENER_CITATION_API = f"{COURTLISTENER_BASE_URL}citation-lookup/"
COURTLISTENER_SEARCH_API = f"{COURTLISTENER_BASE_URL}search/"
COURTLISTENER_OPINION_API = f"{COURTLISTENER_BASE_URL}opinions/"
COURTLISTENER_CLUSTER_API = f"{COURTLISTENER_BASE_URL}clusters/"

# Note: CourtListener API v4 requires specific parameters
# For citation-lookup, we need to use 'citation' parameter
GOOGLE_SCHOLAR_URL = "https://scholar.google.com/scholar"

# Flags to track API availability
COURTLISTENER_AVAILABLE = True
LANGSEARCH_AVAILABLE = True
GOOGLE_SCHOLAR_AVAILABLE = True

# Configuration
MAX_RETRIES = 2  # Reduced from 3 to prevent long waits
TIMEOUT_SECONDS = 8  # Reduced from 15 to fail faster
RATE_LIMIT_WAIT = 3  # seconds to wait when rate limited
MIN_RETRY_DELAY = 0.5  # minimum seconds between retries
MAX_RETRY_DELAY = 3  # maximum seconds between retries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('citation_verification.log')
    ]
)
