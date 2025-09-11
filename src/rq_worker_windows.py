"""
Custom RQ Worker for Windows compatibility
This script patches RQ to disable SIGALRM before starting the worker
"""

import platform
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import sys
import os
import logging

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from .rq_windows_patch import patch_rq_for_windows
    try:
        result = patch_rq_for_windows()  # Returns bool indicating success
        if result:
            logger.info("[RQ WORKER] RQ patch applied successfully")
        else:
            logger.info("[RQ WORKER] RQ patch not needed (not on Windows)")
    except Exception as e:
        logger.warning(f"[RQ WORKER] RQ patch failed: {e}")
except ImportError:
    def patch_rq_for_windows() -> bool:
        """Patch RQ to disable SIGALRM on Windows"""
        if platform.system() == 'Windows':
            try:
                import rq.timeouts
                from rq.timeouts import BaseDeathPenalty
                
                class WindowsDeathPenalty(BaseDeathPenalty):
                    def setup_death_penalty(self): 
                        pass
                    def cancel_death_penalty(self): 
                        pass
                
                if hasattr(rq.timeouts, 'DeathPenalty'):  # type: ignore
                    rq.timeouts.DeathPenalty = WindowsDeathPenalty  # type: ignore
                
                logger.info("[RQ PATCH] Successfully patched RQ for Windows compatibility")
                return True
            except Exception as e:
                logger.error(f"[RQ PATCH] Failed to patch RQ for Windows: {e}")
                return False
        return False
    
    result = patch_rq_for_windows()
    if result:
        logger.info("[RQ WORKER] RQ patch applied successfully (fallback)")
    else:
        logger.info("[RQ WORKER] RQ patch not needed (fallback)")

if __name__ == '__main__':
    try:
        from rq.cli.cli import main  # type: ignore
    except ImportError:
        try:
            from rq.cli import main  # type: ignore
        except ImportError:
            from rq.cli.worker import main  # type: ignore
    main() 