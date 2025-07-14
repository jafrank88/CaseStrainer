"""
Vue API Blueprint Import Module

This module provides the api_blueprint import that app.py expects.
It imports the vue_api blueprint from vue_api_endpoints.py with robust error handling
and multiple import path strategies for different deployment scenarios.
"""

import logging
import sys
from typing import Optional

# Set up module-level logger
logger = logging.getLogger(__name__)

# Global to store the imported blueprint
api_blueprint: Optional[object] = None


def _attempt_import_with_path(import_path: str, module_name: str) -> Optional[object]:
    """
    Attempt to import the vue_api blueprint from a specific path.
    
    Args:
        import_path: The import path to try (e.g., 'src.vue_api_endpoints')
        module_name: Human-readable name for logging
        
    Returns:
        The imported blueprint or None if import fails
    """
    try:
        if import_path.startswith('.'):
            # Relative import
            from . import vue_api_endpoints
            blueprint = getattr(vue_api_endpoints, 'vue_api', None)
        else:
            # Absolute import
            module = __import__(import_path, fromlist=['vue_api'])
            blueprint = getattr(module, 'vue_api', None)
        
        if blueprint is not None:
            logger.info(f"Successfully imported vue_api blueprint from {module_name}")
            print(f"Successfully imported vue_api blueprint from {module_name}")
            return blueprint
        else:
            logger.warning(f"Module {module_name} found but vue_api attribute missing")
            return None
            
    except ImportError as e:
        logger.debug(f"Import attempt failed for {module_name}: {e}")
        return None
    except AttributeError as e:
        logger.warning(f"Module {module_name} exists but vue_api not found: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error importing from {module_name}: {e}")
        return None


def _get_blueprint() -> Optional[object]:
    """
    Attempt to import the vue_api blueprint using multiple strategies.
    
    Returns:
        The imported blueprint or None if all attempts fail
    """
    # Strategy 1: Relative import (when this module is part of a package)
    blueprint = _attempt_import_with_path('.vue_api_endpoints', 'vue_api_endpoints.py (relative)')
    if blueprint is not None:
        return blueprint
    
    # Strategy 2: Direct relative import
    try:
        from .vue_api_endpoints import vue_api
        logger.info("Successfully imported vue_api blueprint via direct relative import")
        print("Successfully imported vue_api blueprint via direct relative import")
        return vue_api
    except ImportError:
        pass
    
    # Strategy 3: Absolute import from src package
    blueprint = _attempt_import_with_path('src.vue_api_endpoints', 'src.vue_api_endpoints')
    if blueprint is not None:
        return blueprint
    
    # Strategy 4: Direct absolute import
    try:
        from .vue_api_endpoints import vue_api
        logger.info("Successfully imported vue_api blueprint via direct absolute import")
        print("Successfully imported vue_api blueprint via direct absolute import")
        return vue_api
    except ImportError:
        pass
    
    # Strategy 5: Try without src prefix (for different project structures)
    blueprint = _attempt_import_with_path('vue_api_endpoints', 'vue_api_endpoints (no prefix)')
    if blueprint is not None:
        return blueprint
    
    # Strategy 6: Last resort - try importing from current directory
    try:
        import vue_api_endpoints
        vue_api = getattr(vue_api_endpoints, 'vue_api', None)
        if vue_api is not None:
            logger.info("Successfully imported vue_api blueprint from current directory")
            print("Successfully imported vue_api blueprint from current directory")
            return vue_api
    except (ImportError, AttributeError):
        pass
    
    return None


def _validate_blueprint(blueprint: object) -> bool:
    """
    Validate that the imported object is actually a Flask Blueprint.
    
    Args:
        blueprint: The object to validate
        
    Returns:
        True if valid blueprint, False otherwise
    """
    try:
        # Check if it has blueprint-like attributes
        if hasattr(blueprint, 'name') and hasattr(blueprint, 'url_prefix'):
            return True
        
        # Check if it's a Flask Blueprint (more thorough check)
        if hasattr(blueprint, '__class__'):
            class_name = blueprint.__class__.__name__
            if 'Blueprint' in class_name:
                return True
        
        # Check for blueprint methods
        blueprint_methods = ['route', 'before_request', 'after_request']
        if all(hasattr(blueprint, method) for method in blueprint_methods):
            return True
        
        logger.warning("Imported object doesn't appear to be a valid Flask Blueprint")
        return False
        
    except Exception as e:
        logger.error(f"Error validating blueprint: {e}")
        return False


def _log_import_diagnostics():
    """Log diagnostic information about the import environment."""
    logger.info("=== Vue API Blueprint Import Diagnostics ===")
    logger.info(f"Python path: {sys.path}")
    logger.info(f"Current working directory: {sys.path[0] if sys.path else 'Unknown'}")
    logger.info(f"Module name: {__name__}")
    logger.info(f"Package: {__package__}")
    
    # Check what modules are available
    available_modules = []
    potential_modules = [
        'vue_api_endpoints',
        'src.vue_api_endpoints',
        '.vue_api_endpoints'
    ]
    
    for module_name in potential_modules:
        try:
            if module_name.startswith('.'):
                # Skip relative imports for this diagnostic
                continue
            __import__(module_name)
            available_modules.append(module_name)
        except ImportError:
            pass
    
    logger.info(f"Available vue_api modules: {available_modules}")
    logger.info("=== End Diagnostics ===")


# Perform the import when this module is loaded
try:
    # Log diagnostics in debug mode
    if logger.isEnabledFor(logging.DEBUG):
        _log_import_diagnostics()
    
    # Attempt to import the blueprint
    api_blueprint = _get_blueprint()
    
    if api_blueprint is not None:
        # Validate the imported blueprint
        if _validate_blueprint(api_blueprint):
            logger.info("Vue API blueprint successfully imported and validated")
        else:
            logger.warning("Vue API blueprint imported but validation failed")
            # Don't set to None here - let the app decide what to do
    else:
        logger.error("Failed to import vue_api blueprint from any location")
        print("ERROR: Failed to import vue_api blueprint from any location")
        print("Checked locations:")
        print("  - .vue_api_endpoints (relative)")
        print("  - src.vue_api_endpoints (absolute)")
        print("  - vue_api_endpoints (current directory)")
        print("Please ensure vue_api_endpoints.py exists and contains a 'vue_api' blueprint")

except Exception as e:
    logger.critical(f"Critical error during blueprint import: {e}", exc_info=True)
    print(f"CRITICAL ERROR during blueprint import: {e}")
    api_blueprint = None


# Provide helpful information about the imported blueprint
def get_blueprint_info() -> dict:
    """
    Get information about the imported blueprint for debugging.
    
    Returns:
        Dictionary with blueprint information
    """
    if api_blueprint is None:
        return {
            'status': 'not_imported',
            'blueprint': None,
            'name': None,
            'url_prefix': None,
            'routes': []
        }
    
    try:
        info = {
            'status': 'imported',
            'blueprint': str(type(api_blueprint)),
            'name': getattr(api_blueprint, 'name', 'Unknown'),
            'url_prefix': getattr(api_blueprint, 'url_prefix', None),
            'routes': []
        }
        
        # Try to get route information
        if hasattr(api_blueprint, 'deferred_functions'):
            info['deferred_functions_count'] = len(api_blueprint.deferred_functions)
        
        return info
        
    except Exception as e:
        logger.error(f"Error getting blueprint info: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'blueprint': str(type(api_blueprint)) if api_blueprint else None
        }


# Compatibility function for apps that might check import success
def is_blueprint_available() -> bool:
    """
    Check if the vue_api blueprint was successfully imported.
    
    Returns:
        True if blueprint is available, False otherwise
    """
    return api_blueprint is not None and _validate_blueprint(api_blueprint)


# Export the blueprint and utility functions
__all__ = ['api_blueprint', 'get_blueprint_info', 'is_blueprint_available']

# Print final status
if api_blueprint is not None:
    print(f"✅ Vue API blueprint ready: {getattr(api_blueprint, 'name', 'unnamed')}")
else:
    print("❌ Vue API blueprint not available") 