# Start centralized background maintenance system
try:
    from ..background_tasks import start_background_maintenance
    start_background_maintenance()
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Failed to start background maintenance system: {e}") 