from __future__ import annotations
import asyncio
import time
import logging
from dataclasses import asdict
from typing import Any, Awaitable, Callable, Dict, List, Optional

# Provider signature: async (citation, name_hint, date_hint, timeout) -> Verification-like
VerificationCallable = Callable[[str, Optional[str], Optional[str], float], Awaitable[Any]]

logger = logging.getLogger(__name__)


class VerificationRegistry:
    """
    Simple verification registry that tries providers in order until one succeeds.
    Success = verified True or possible_match True.
    Returns a plain dict to avoid import cycles; caller converts to its own model.

    Small improvements:
    - TTL cache for positive results (avoid repeat calls in a short window)
    - Provider timing + selection logging
    - Configurable minimum per-provider time budget
    """

    def __init__(
        self,
        providers: List[VerificationCallable],
        ttl_seconds: float = 120.0,
        min_time_per_provider: float = 0.5,
        cache_enabled: bool = True,
    ):
        self.providers = providers or []
        self.ttl_seconds = max(0.0, float(ttl_seconds))
        self.min_time_per_provider = max(0.1, float(min_time_per_provider))
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, Dict[str, Any]] = {}  # key -> {"ts": float, "data": dict}

    async def verify(
        self,
        citation: str,
        name_hint: Optional[str],
        date_hint: Optional[str],
        timeout: float = 20.0,
    ) -> Dict[str, Any]:
        if not self.providers:
            return {"citation": citation, "verified": False, "error": "No providers configured"}

        # Cache hit (only for positive results to avoid masking newly verifiable cases)
        if self.cache_enabled:
            cached = self._get_cache(citation, name_hint, date_hint)
            if cached is not None and (cached.get("verified") or cached.get("possible_match")):
                logger.info("[VerifyRegistry] Cache HIT for '%s'", citation)
                return cached

        per = max(self.min_time_per_provider, timeout / max(1, len(self.providers)))
        remaining = timeout
        last_error: Optional[str] = None

        for idx, provider in enumerate(self.providers):
            if remaining <= 0:
                break
            start = time.time()
            try:
                res = await self._call_with_timeout(provider, per, citation, name_hint, date_hint)
                data = self._to_plain_dict(res, citation)
                ok = bool(data.get("verified") or data.get("possible_match"))
                logger.info(
                    "[VerifyRegistry] Provider #%d %s -> ok=%s, took=%.2fs, source=%s",
                    idx + 1,
                    getattr(provider, "__name__", str(provider)),
                    ok,
                    time.time() - start,
                    data.get("source"),
                )
                if ok:
                    if self.cache_enabled:
                        self._set_cache(citation, name_hint, date_hint, data)
                    return data
                last_error = data.get("error") or last_error
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "[VerifyRegistry] Provider #%d %s raised: %s",
                    idx + 1,
                    getattr(provider, "__name__", str(provider)),
                    e,
                )
            finally:
                remaining -= per

        return {"citation": citation, "verified": False, "error": last_error or "All providers failed"}

    async def _call_with_timeout(
        self,
        provider: VerificationCallable,
        per_timeout: float,
        citation: str,
        name_hint: Optional[str],
        date_hint: Optional[str],
    ) -> Any:
        return await asyncio.wait_for(provider(citation, name_hint, date_hint, per_timeout), timeout=per_timeout + 0.1)

    def _to_plain_dict(self, res: Any, citation: str) -> Dict[str, Any]:
        if res is None:
            return {"citation": citation, "verified": False}
        # Dataclass instance
        try:
            return asdict(res)
        except Exception:
            logger.debug("Suppressed exception", exc_info=True)
        # Object with __dict__
        if hasattr(res, "__dict__"):
            try:
                d = dict(res.__dict__)
                d.setdefault("citation", citation)
                return d
            except Exception:
                logger.debug("Suppressed exception", exc_info=True)
        # Already a dict
        if isinstance(res, dict):
            res.setdefault("citation", citation)
            return res
        # Fallback
        return {"citation": citation, "verified": False}

    def _cache_key(self, citation: str, name_hint: Optional[str], date_hint: Optional[str]) -> str:
        n = (name_hint or "").strip().lower()
        d = (str(date_hint) if date_hint is not None else "").strip().lower()
        return f"{citation.strip().lower()}|{n}|{d}"

    def _get_cache(self, citation: str, name_hint: Optional[str], date_hint: Optional[str]) -> Optional[Dict[str, Any]]:
        if not self.cache_enabled or self.ttl_seconds <= 0:
            return None
        key = self._cache_key(citation, name_hint, date_hint)
        item = self._cache.get(key)
        now = time.time()
        if item and now - item.get("ts", 0) <= self.ttl_seconds:
            return item.get("data")
        # Expired
        if item:
            self._cache.pop(key, None)
        return None

    def _set_cache(
        self, citation: str, name_hint: Optional[str], date_hint: Optional[str], data: Dict[str, Any]
    ) -> None:
        if not self.cache_enabled or self.ttl_seconds <= 0:
            return
        key = self._cache_key(citation, name_hint, date_hint)
        self._cache[key] = {"ts": time.time(), "data": dict(data)}
