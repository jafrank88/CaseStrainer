import os
import sys
import json
import asyncio

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.unified_verification_master import UnifiedVerificationMaster

# Ensure registry is enabled for this smoke run unless already set by environment
os.environ.setdefault("VERIFY_USE_REGISTRY", "true")

CITATIONS = [
    ("521 U.S. 811", "Raines v. Byrd", "1997"),
    ("161 U.S. 519", "United States v. E.C. Knight Co.", "1895"),
]

async def run_smoke():
    m = UnifiedVerificationMaster()
    out = []
    for cit, name, date in CITATIONS:
        try:
            res = await m.verify_citation(cit, name, date, timeout=20.0, enable_fallback=True)
            out.append({
                "citation": cit,
                "verified": bool(getattr(res, 'verified', False)),
                "possible_match": bool(getattr(res, 'possible_match', False)),
                "source": getattr(res, 'source', None),
                "method": getattr(res, 'method', None),
                "canonical_name": getattr(res, 'canonical_name', None),
                "canonical_date": getattr(res, 'canonical_date', None),
                "canonical_url": getattr(res, 'canonical_url', None),
                "error": getattr(res, 'error', None),
            })
        except Exception as e:
            out.append({"citation": cit, "verified": False, "error": str(e)})
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    # Show whether API key is present, and that registry flag is set
    print(json.dumps({
        "VERIFY_USE_REGISTRY": os.getenv("VERIFY_USE_REGISTRY"),
        "COURTLISTENER_API_KEY_PRESENT": bool(os.getenv("COURTLISTENER_API_KEY"))
    }))
    asyncio.run(run_smoke())
