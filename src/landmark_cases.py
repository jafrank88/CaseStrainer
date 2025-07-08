#!/usr/bin/env python3
"""
Landmark Cases Module

DEPRECATED: This module is deprecated. The landmark cases database and functionality
has been removed as of 2025-05-22. All functionality has been integrated into the
unified pipeline (UnifiedCitationProcessor).

This module will be removed in a future version.
"""

import warnings
warnings.warn(
    "src.landmark_cases is deprecated. The landmark cases database has been removed. "
    "All functionality has been integrated into UnifiedCitationProcessor. "
    "Use the unified pipeline instead.",
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
