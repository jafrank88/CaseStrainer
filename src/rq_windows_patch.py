# type: ignore
import platform
import sys
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

def patch_rq_for_windows() -> bool:
    """Comprehensive patch for RQ Windows compatibility"""
    if platform.system() == 'Windows':
        try:
            # Only patch os.fork if it doesn't exist (don't override if it does)
            if not hasattr(os, 'fork'):  # type: ignore
                # Create a dummy fork function for Windows
                def dummy_fork():
                    return None
                os.fork = dummy_fork
            
            # Import and patch signal module before any RQ imports
            import signal
            
            # Create a custom signal handler that does nothing
            def noop_signal_handler(signum, frame):
                pass
            
            # Patch signal.SIGALRM to a valid signal number and set up handler
            if not hasattr(signal, 'SIGALRM'):  # type: ignore
                # Use a dummy signal number for Windows
                signal.SIGALRM = 15  # Use SIGTERM (15) as fallback
                # Set up a no-op handler for SIGALRM
                try:
                    signal.signal(signal.SIGALRM, noop_signal_handler)  # type: ignore
                except (OSError, ValueError):
                    # Ignore errors setting up signal handler on Windows
                    pass
            
            # Patch RQ timeouts to use a no-op death penalty
            try:
                from rq.timeouts import BaseDeathPenalty
                class WindowsDeathPenalty(BaseDeathPenalty):
                    def setup_death_penalty(self): 
                        # No-op for Windows
                        pass
                    def cancel_death_penalty(self): 
                        # No-op for Windows
                        pass
                
                # Replace the default death penalty class
                import rq.timeouts
                rq.timeouts.BaseDeathPenalty = WindowsDeathPenalty
                
                # Also patch the DeathPenalty class if it exists
                if hasattr(rq.timeouts, 'DeathPenalty'):  # type: ignore
                    rq.timeouts.DeathPenalty = WindowsDeathPenalty
                    
            except ImportError:
                pass  # RQ not available yet
            
            logger.info("[RQ PATCH] Successfully patched RQ for Windows compatibility")
            return True
        except Exception as e:
            logger.error(f"[RQ PATCH] Failed to patch RQ for Windows: {e}")
            return False
    return False

# Apply patch immediately when module is imported
patch_rq_for_windows() 