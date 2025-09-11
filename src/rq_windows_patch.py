# type: ignore
import platform
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import sys
import os
import logging

logger = logging.getLogger(__name__)

def patch_rq_for_windows() -> bool:
    """Comprehensive patch for RQ Windows compatibility"""
    if platform.system() == 'Windows':
        try:
            if not hasattr(os, 'fork'):  # type: ignore
                def dummy_fork():
                    return None
                os.fork = dummy_fork
            
            import signal
            
            def noop_signal_handler(signum, frame):
                pass
            
            if not hasattr(signal, 'SIGALRM'):  # type: ignore
                signal.SIGALRM = 15  # Use SIGTERM (15) as fallback
                try:
                    signal.signal(signal.SIGALRM, noop_signal_handler)  # type: ignore
                except (OSError, ValueError):
                    pass
            
            try:
                from rq.timeouts import BaseDeathPenalty
                class WindowsDeathPenalty(BaseDeathPenalty):
                    def setup_death_penalty(self): 
                        pass
                    def cancel_death_penalty(self): 
                        pass
                
                import rq.timeouts
                rq.timeouts.BaseDeathPenalty = WindowsDeathPenalty
                
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

patch_rq_for_windows() 