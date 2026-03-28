"""
Vue API route modules. Each module exposes register_*_routes(bp) to attach routes to the vue_api blueprint.
"""

from src.api.routes.health import register_health_routes
from src.api.routes.metrics import register_metrics_routes
from src.api.routes.progress import register_progress_routes
from src.api.routes.task_status import register_task_status_routes
from src.api.routes.verification import register_verification_routes
from src.api.routes.analyze import register_analyze_routes


def register_all_routes(bp):
    """Register all domain routes onto the given blueprint."""
    register_health_routes(bp)
    register_metrics_routes(bp)
    register_progress_routes(bp)
    register_task_status_routes(bp)
    register_verification_routes(bp)
    register_analyze_routes(bp)
