#!/usr/bin/env python3
"""
Custom RQ Worker for Windows compatibility
This script patches RQ to disable SIGALRM before starting the worker
"""

import platform
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import and apply the patch immediately
try:
    from src.rq_windows_patch import patch_rq_for_windows
    patch_rq_for_windows()
except ImportError:
    # Fallback if src module not available
    def patch_rq_for_windows():
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
                rq.timeouts.DeathPenalty = WindowsDeathPenalty
                
                print("[RQ PATCH] Successfully patched RQ for Windows compatibility")
            except Exception as e:
                print(f"[RQ PATCH] Failed to patch RQ for Windows: {e}")
    
    patch_rq_for_windows()

if __name__ == '__main__':
    # Now import and run RQ worker
    from rq.cli import main
    main() 