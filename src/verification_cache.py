#!/usr/bin/env python3
"""
Simple verification cache for successfully found cases only
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class VerificationCache:
    """
    Simple cache for successfully verified citations.
    Only stores successful verifications, not failures.
    This avoids issues with new cases being added to legal databases.
    """
    
    def __init__(self, cache_file: str = "data/verification_cache.json"):
        self.cache_file = cache_file
        self.cache: Dict[str, Dict] = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached verifications")
        except Exception as e:
            logger.warning(f"Failed to load verification cache: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save verification cache: {e}")
    
    def get(self, citation: str) -> Optional[Dict]:
        """Get cached verification result for a citation"""
        # Normalize citation for lookup
        normalized = citation.strip().lower()
        return self.cache.get(normalized)
    
    def set(self, citation: str, result: Dict):
        """Cache a successful verification result"""
        # Only cache successful verifications
        if not result.get('verified', False):
            return
        
        normalized = citation.strip().lower()
        
        # Store essential data
        self.cache[normalized] = {
            'canonical_name': result.get('canonical_name'),
            'canonical_date': result.get('canonical_date'),
            'canonical_url': result.get('canonical_url'),
            'source': result.get('source'),
            'confidence': result.get('confidence'),
            'method': result.get('method'),
            'cached_at': datetime.now().isoformat(),
            'original_citation': citation
        }
        
        # Save to disk
        self._save_cache()
        logger.debug(f"Cached verification for: {citation}")
    
    def clear_old_entries(self, days: int = 365):
        """Clear cache entries older than specified days"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        removed = 0
        
        for citation, entry in list(self.cache.items()):
            try:
                cached_at = datetime.fromisoformat(entry['cached_at']).timestamp()
                if cached_at < cutoff:
                    del self.cache[citation]
                    removed += 1
            except:
                # Remove invalid entries
                del self.cache[citation]
                removed += 1
        
        if removed > 0:
            self._save_cache()
            logger.info(f"Cleared {removed} old cache entries")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = len(self.cache)
        sources = {}
        
        for entry in self.cache.values():
            source = entry.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        return {
            'total_entries': total,
            'sources': sources,
            'cache_file': self.cache_file
        }


# Global cache instance
_verification_cache = None

def get_verification_cache() -> VerificationCache:
    """Get the global verification cache instance"""
    global _verification_cache
    if _verification_cache is None:
        _verification_cache = VerificationCache()
    return _verification_cache
