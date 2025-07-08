#!/usr/bin/env python3
"""
Citation Verification Module

DEPRECATED: This module is deprecated. All functionality has been integrated
into the unified pipeline (UnifiedCitationProcessor with EnhancedMultiSourceVerifier).
Use the unified processor instead.

This module will be removed in a future version.
"""

import warnings
warnings.warn(
    "src.citation_verification is deprecated. All functionality has been integrated "
    "into UnifiedCitationProcessor with EnhancedMultiSourceVerifier. Use the unified pipeline instead.",
    DeprecationWarning,
    stacklevel=2
)

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import time
import json
import requests
from urllib.parse import quote_plus
import unicodedata
import string
from difflib import SequenceMatcher
