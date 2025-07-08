"""
CaseStrainer - A tool for analyzing and validating legal citations.
"""

# Set up logging by default
from .config import configure_logging

configure_logging()

__version__ = "0.5.8"

# Explicitly export configure_logging
__all__ = ["configure_logging"]

# Import key modules to make them available when importing the package
# These imports are done after version and logging setup to avoid circular imports
# and ensure proper initialization

# Global variable to store the vue_api blueprint
_vue_api_blueprint = None


# Lazy imports to avoid circular imports
def _lazy_import():
    """Lazy import of modules to avoid circular imports."""
    global _vue_api_blueprint

    # Import the blueprint creation function
    from .vue_api_endpoints import create_blueprint

    # Create the blueprint if it doesn't exist
    if _vue_api_blueprint is None:
        _vue_api_blueprint = create_blueprint()

    # Import other modules
    from .citation_api import citation_api
    from src.citation_utils import (
        extract_all_citations,
        extract_citations_from_text,
        verify_citation,
    )
    from .config import (
        ALLOWED_EXTENSIONS,
        UPLOAD_FOLDER,
        DATABASE_FILE,
    )
    from .courtlistener_integration import (
        batch_citation_validation,
        check_citation_exists,
        generate_case_summary_from_courtlistener,
        search_citation,
        setup_courtlistener_api,
    )

    return {
        "citation_api": citation_api,
        "extract_all_citations": extract_all_citations,
        "extract_citations_from_text": extract_citations_from_text,
        "verify_citation": verify_citation,
        "vue_api": _vue_api_blueprint,  # Include the vue_api blueprint
        "ALLOWED_EXTENSIONS": ALLOWED_EXTENSIONS,
        "UPLOAD_FOLDER": UPLOAD_FOLDER,
        "DATABASE_FILE": DATABASE_FILE,
        "batch_citation_validation": batch_citation_validation,
        "check_citation_exists": check_citation_exists,
        "generate_case_summary_from_courtlistener": generate_case_summary_from_courtlistener,
        "search_citation": search_citation,
        "setup_courtlistener_api": setup_courtlistener_api,
    }


# Lazy load the modules when they are first accessed
_imported = {}


def __getattr__(name):
    if not _imported:
        _imported.update(_lazy_import())
    if name in _imported:
        return _imported[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
