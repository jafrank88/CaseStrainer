#!/usr/bin/env python3
"""
Custom RQ Worker for Windows compatibility
This script patches RQ to disable SIGALRM before starting the worker
"""

import platform
import sys
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import and apply the patch immediately
try:
    from .rq_windows_patch import patch_rq_for_windows
    # Apply the patch and handle the return value
    try:
        result = patch_rq_for_windows()  # Returns bool indicating success
        if result:
            logger.info("[RQ WORKER] RQ patch applied successfully")
        else:
            logger.info("[RQ WORKER] RQ patch not needed (not on Windows)")
    except Exception as e:
        logger.warning(f"[RQ WORKER] RQ patch failed: {e}")
        # Ignore any errors from the patch
except ImportError:
    # Fallback if src module not available
    def patch_rq_for_windows() -> bool:
        """Patch RQ to disable SIGALRM on Windows"""
        if platform.system() == 'Windows':
            try:
                # Import and patch before any RQ imports
                import rq.timeouts
                from rq.timeouts import BaseDeathPenalty
                
                class WindowsDeathPenalty(BaseDeathPenalty):
                    def setup_death_penalty(self): 
                        pass
                    def cancel_death_penalty(self): 
                        pass
                
                # Replace the default death penalty class
                if hasattr(rq.timeouts, 'DeathPenalty'):  # type: ignore
                    rq.timeouts.DeathPenalty = WindowsDeathPenalty  # type: ignore
                
                logger.info("[RQ PATCH] Successfully patched RQ for Windows compatibility")
                return True
            except Exception as e:
                logger.error(f"[RQ PATCH] Failed to patch RQ for Windows: {e}")
                return False
        return False
    
    # Apply the fallback patch
    result = patch_rq_for_windows()
    if result:
        logger.info("[RQ WORKER] RQ patch applied successfully (fallback)")
    else:
        logger.info("[RQ WORKER] RQ patch not needed (fallback)")

if __name__ == '__main__':
    # Now import and run RQ worker
    try:
        from rq.cli.cli import main  # type: ignore
    except ImportError:
        try:
            from rq.cli import main  # type: ignore
        except ImportError:
            # Fallback for different RQ versions
            from rq.cli.worker import main  # type: ignore
    main() 