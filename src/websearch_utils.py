# DEPRECATED: Use ComprehensiveWebSearchEngine in src/comprehensive_websearch_engine.py instead of LegalWebSearchEngine.
# This file is retained for legacy reference only and should not be used in new code.
# 
# The ComprehensiveWebSearchEngine provides:
# - All features from LegalWebSearchEngine
# - Enhanced Washington citation variants
# - Advanced case name extraction
# - Specialized legal database extraction
# - Similarity scoring and validation
# - Better reliability scoring
#
# Migration guide: See docs/WEB_SEARCH_MIGRATION.md

import warnings
warnings.warn(
    "LegalWebSearchEngine is deprecated. Use ComprehensiveWebSearchEngine in src/comprehensive_websearch_engine.py instead. "
    "This file will be removed in the next release.",
    DeprecationWarning,
    stacklevel=2
)

import logging

logger = logging.getLogger(__name__)

# All other imports removed as this module is deprecated and should not be used in new code.

# TODO: Remove this file in next release
# This file is kept only for backward compatibility and should not be used in new code. 