"""
Shared CourtListener throttle across workers.

Uses Redis sliding-window tokens when Redis is reachable; falls back to an
in-process limiter when Redis is unavailable. The throttle is citation-cost
based (not request-count based): batch requests reserve one token per citation.
"""

from __future__ import annotations

import os
import random
import threading
import time
from collections import deque
from typing import Any, Deque, Optional

import logging

logger = logging.getLogger(__name__)

_WINDOW_SECONDS = 60.0
_LOCAL_LOCK = threading.Lock()
_LOCAL_TOKENS: Deque[float] = deque()
_REDIS_CLIENT: Optional[Any] = None
_REDIS_INIT_ATTEMPTED = False
_REDIS_SCRIPT_SHA: Optional[str] = None
_REDIS_SCRIPT = """
local key = KEYS[1]
local now_ms = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local cost = tonumber(ARGV[4])
local member_prefix = ARGV[5]

redis.call('ZREMRANGEBYSCORE', key, '-inf', now_ms - window_ms)
local current = redis.call('ZCARD', key)
if (current + cost) <= limit then
  for i = 1, cost do
    redis.call('ZADD', key, now_ms, member_prefix .. ':' .. tostring(i))
  end
  redis.call('PEXPIRE', key, window_ms + 2000)
  return 0
end

local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
if oldest[2] then
  local wait_ms = window_ms - (now_ms - tonumber(oldest[2])) + 5
  if wait_ms < 1 then
    wait_ms = 1
  end
  return wait_ms
end
return window_ms
"""


def _cfg_int(name: str, default: int) -> int:
    try:
        from src.config import get_config_value

        raw = get_config_value(name, default)
    except Exception:
        raw = os.getenv(name, default)
    try:
        return int(raw)
    except Exception:
        return int(default)


def _cfg_bool(name: str, default: bool) -> bool:
    try:
        from src.config import get_bool_config_value

        return bool(get_bool_config_value(name, default))
    except Exception:
        raw = str(os.getenv(name, str(default))).strip().lower()
        return raw in ("1", "true", "yes", "on")


def _redis_init():
    global _REDIS_CLIENT, _REDIS_INIT_ATTEMPTED, _REDIS_SCRIPT_SHA
    if _REDIS_INIT_ATTEMPTED:
        return
    _REDIS_INIT_ATTEMPTED = True
    try:
        from redis import Redis
        from src.config import REDIS_URL

        _REDIS_CLIENT = Redis.from_url(REDIS_URL)
        _REDIS_CLIENT.ping()
        _REDIS_SCRIPT_SHA = _REDIS_CLIENT.script_load(_REDIS_SCRIPT)
        logger.info("[CL-THROTTLE] Redis-backed throttle enabled")
    except Exception as exc:
        _REDIS_CLIENT = None
        _REDIS_SCRIPT_SHA = None
        logger.warning(f"[CL-THROTTLE] Redis unavailable, using local throttle fallback: {exc}")


def _acquire_local(cost: int, limit_per_min: int) -> int:
    now = time.time()
    with _LOCAL_LOCK:
        while _LOCAL_TOKENS and (now - _LOCAL_TOKENS[0]) >= _WINDOW_SECONDS:
            _LOCAL_TOKENS.popleft()
        if len(_LOCAL_TOKENS) + cost <= limit_per_min:
            for _ in range(cost):
                _LOCAL_TOKENS.append(now)
            return 0
        oldest = _LOCAL_TOKENS[0] if _LOCAL_TOKENS else now
        wait_ms = int(max(1.0, (_WINDOW_SECONDS - (now - oldest)) * 1000.0))
        return wait_ms


def _acquire_redis(cost: int, limit_per_min: int, key: str) -> int:
    global _REDIS_SCRIPT_SHA
    if _REDIS_CLIENT is None:
        return -1
    now_ms = int(time.time() * 1000)
    member_prefix = f"{now_ms}:{os.getpid()}:{random.randint(1000, 999999)}"
    try:
        if not _REDIS_SCRIPT_SHA:
            return -1
        result = _REDIS_CLIENT.evalsha(
            _REDIS_SCRIPT_SHA,
            1,
            key,
            str(now_ms),
            str(int(_WINDOW_SECONDS * 1000)),
            str(int(limit_per_min)),
            str(int(max(1, cost))),
            member_prefix,
        )
        return int(result)
    except Exception:
        try:
            _REDIS_SCRIPT_SHA = _REDIS_CLIENT.script_load(_REDIS_SCRIPT)
            if not _REDIS_SCRIPT_SHA:
                return -1
            result = _REDIS_CLIENT.evalsha(
                _REDIS_SCRIPT_SHA,
                1,
                key,
                str(now_ms),
                str(int(_WINDOW_SECONDS * 1000)),
                str(int(limit_per_min)),
                str(int(max(1, cost))),
                member_prefix,
            )
            return int(result)
        except Exception:
            return -1


def throttle_courtlistener(cost: int = 1, context: str = "lookup") -> None:
    """
    Acquire global CourtListener budget before issuing a request.

    cost: estimated citation units for this request.
    context: log label (lookup/batch/search).
    """
    if not _cfg_bool("COURTLISTENER_GLOBAL_THROTTLE_ENABLED", True):
        return

    limit_per_min = max(1, _cfg_int("COURTLISTENER_GLOBAL_LIMIT_PER_MIN", 5000))
    max_wait_s = max(1, _cfg_int("COURTLISTENER_GLOBAL_THROTTLE_MAX_WAIT_SECONDS", 45))
    key = str(
        os.getenv("COURTLISTENER_GLOBAL_THROTTLE_KEY")
        or f"{os.getenv('APP_NAME', 'casestrainer')}:courtlistener:throttle"
    ).strip()

    _redis_init()
    deadline = time.monotonic() + float(max_wait_s)
    wait_logged = False
    c = max(1, int(cost))

    while True:
        wait_ms = _acquire_redis(c, limit_per_min, key)
        if wait_ms < 0:
            wait_ms = _acquire_local(c, limit_per_min)
        if wait_ms <= 0:
            return

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            if not wait_logged:
                logger.warning(
                    f"[CL-THROTTLE] Budget wait timeout in {context}; proceeding without slot "
                    f"(cost={c}, limit_per_min={limit_per_min})"
                )
            return

        sleep_s = min(wait_ms / 1000.0, remaining, 2.0)
        if not wait_logged:
            logger.info(
                f"[CL-THROTTLE] Waiting for budget in {context}: ~{wait_ms}ms "
                f"(cost={c}, limit_per_min={limit_per_min})"
            )
            wait_logged = True
        time.sleep(max(0.001, sleep_s))
