"""
Vue API Blueprint Import Module

This module provides the api_blueprint import that app.py expects.
It imports the vue_api blueprint from vue_api_endpoints.py.
"""

try:
    from .vue_api_endpoints import vue_api as api_blueprint
    print("Successfully imported vue_api blueprint from vue_api_endpoints.py")
except ImportError as e:
    try:
        from src.vue_api_endpoints import vue_api as api_blueprint
        print("Successfully imported vue_api blueprint from vue_api_endpoints.py")
    except ImportError as e2:
        print(f"Failed to import vue_api blueprint: {e2}")
        api_blueprint = None 