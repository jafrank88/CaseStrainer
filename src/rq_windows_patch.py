import platform
import sys
import os

def patch_rq_for_windows():
    """Comprehensive patch for RQ Windows compatibility"""
    if platform.system() == 'Windows':
        try:
            # Only patch os.fork if it doesn't exist (don't override if it does)
            if not hasattr(os, 'fork'):
                os.fork = lambda: None
            
            # Import and patch signal module before any RQ imports
            import signal
            
            # Create a custom signal handler that does nothing
            def noop_signal_handler(signum, frame):
                pass
            
            # Patch signal.SIGALRM to a valid signal number and set up handler
            if not hasattr(signal, 'SIGALRM'):
                signal.SIGALRM = 15  # Use SIGTERM (15)
                # Set up a no-op handler for SIGALRM
                try:
                    signal.signal(signal.SIGALRM, noop_signal_handler)
                except (OSError, ValueError):
                    # Ignore errors setting up signal handler
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
                if hasattr(rq.timeouts, 'DeathPenalty'):
                    rq.timeouts.DeathPenalty = WindowsDeathPenalty
                    
            except ImportError:
                pass  # RQ not available yet
            
            print("[RQ PATCH] Successfully patched RQ for Windows compatibility")
            return True
        except Exception as e:
            print(f"[RQ PATCH] Failed to patch RQ for Windows: {e}")
            return False
    return False

# Apply patch immediately when module is imported
patch_rq_for_windows() 