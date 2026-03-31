#!/usr/bin/env python3
"""
Diagnostic script to check CaseStrainer verification configuration.

This script checks:
1. CourtListener API key configuration
2. Redis connection
3. Verification system imports
4. Test verification with a sample citation
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Check critical environment variables."""
    logger.info("=" * 60)
    logger.info("ENVIRONMENT VARIABLES CHECK")
    logger.info("=" * 60)

    # Check CourtListener API key
    courtlistener_key = os.environ.get("COURTLISTENER_API_KEY", "")
    if courtlistener_key:
        logger.info(f"✅ COURTLISTENER_API_KEY: Set (length: {len(courtlistener_key)})")
        # Show first/last few characters for verification
        if len(courtlistener_key) > 10:
            masked = courtlistener_key[:4] + "..." + courtlistener_key[-4:]
            logger.info(f"   Key preview: {masked}")
    else:
        logger.error("❌ COURTLISTENER_API_KEY: NOT SET!")
        logger.error("   Verification will fail without this API key.")
        logger.error("   Get a free API key from: https://www.courtlistener.com/help/api/")
        logger.error("   Set it with: export COURTLISTENER_API_KEY='your-key-here'")

    # Check Redis configuration
    redis_url = os.environ.get("REDIS_URL", "")
    if redis_url:
        logger.info(f"✅ REDIS_URL: {redis_url}")
    else:
        logger.warning("⚠️  REDIS_URL: Not set (will use default)")

    # Check verification enabled
    enable_verification = os.environ.get("ENABLE_VERIFICATION", "")
    if enable_verification:
        logger.info(f"   ENABLE_VERIFICATION: {enable_verification}")
    else:
        logger.info("   ENABLE_VERIFICATION: Not set (defaults to True)")

    logger.info("")
    return bool(courtlistener_key)

def check_redis_connection():
    """Check Redis connection."""
    logger.info("=" * 60)
    logger.info("REDIS CONNECTION CHECK")
    logger.info("=" * 60)

    try:
        import redis
        redis_url = os.environ.get("REDIS_URL", "redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0")
        logger.info(f"Connecting to Redis: {redis_url}")

        r = redis.from_url(redis_url, socket_connect_timeout=5)
        r.ping()
        logger.info("✅ Redis connection: SUCCESS")

        # Check Redis info
        info = r.info()
        logger.info(f"   Redis version: {info.get('redis_version', 'unknown')}")
        logger.info(f"   Connected clients: {info.get('connected_clients', 'unknown')}")
        logger.info("")
        return True
    except ImportError:
        logger.error("❌ Redis library not installed: pip install redis")
        logger.info("")
        return False
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {str(e)}")
        logger.error("   Make sure Redis is running: docker ps | grep redis")
        logger.info("")
        return False

def check_imports():
    """Check critical imports."""
    logger.info("=" * 60)
    logger.info("IMPORTS CHECK")
    logger.info("=" * 60)

    imports_ok = True

    # Check verification modules
    try:
        from src.unified_verification_master import verify_citation_sync
        logger.info("✅ unified_verification_master: OK")
    except ImportError as e:
        logger.error(f"❌ unified_verification_master: FAILED - {e}")
        imports_ok = False

    try:
        from src.verification_manager import VerificationManager
        logger.info("✅ verification_manager: OK")
    except ImportError as e:
        logger.error(f"❌ verification_manager: FAILED - {e}")
        imports_ok = False

    try:
        from src.unified_processing_pipeline import UnifiedProcessingPipeline
        logger.info("✅ unified_processing_pipeline: OK")
    except ImportError as e:
        logger.error(f"❌ unified_processing_pipeline: FAILED - {e}")
        imports_ok = False

    try:
        from src.config import COURTLISTENER_API_KEY
        logger.info("✅ config: OK")
        if COURTLISTENER_API_KEY:
            logger.info(f"   Config has API key: YES (length: {len(COURTLISTENER_API_KEY)})")
        else:
            logger.error("   Config has API key: NO")
    except ImportError as e:
        logger.error(f"❌ config: FAILED - {e}")
        imports_ok = False

    logger.info("")
    return imports_ok

def test_verification():
    """Test verification with a sample citation."""
    logger.info("=" * 60)
    logger.info("VERIFICATION TEST")
    logger.info("=" * 60)

    try:
        from src.unified_verification_master import verify_citation_sync
        from src.models import CitationResult

        # Test with a well-known Supreme Court case
        test_citation = CitationResult(
            citation="410 U.S. 113",
            case_name="Roe v. Wade",
            year="1973",
            reporter="U.S.",
            volume="410",
            page="113"
        )

        logger.info(f"Testing verification for: {test_citation.citation} ({test_citation.case_name})")
        logger.info("This may take 5-10 seconds...")

        result = verify_citation_sync(test_citation, "")

        if result.is_verified:
            logger.info("✅ VERIFICATION SUCCESS!")
            logger.info(f"   Canonical name: {result.canonical_name}")
            logger.info(f"   Canonical date: {result.canonical_date}")
            logger.info(f"   Canonical URL: {result.canonical_url}")
            logger.info(f"   Verification source: {result.verification_source}")
            return True
        else:
            logger.warning("⚠️  Verification returned unverified status")
            logger.warning(f"   This might indicate an API issue or rate limiting")
            return False

    except Exception as e:
        logger.error(f"❌ Verification test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Run all diagnostic checks."""
    logger.info("\n" + "=" * 60)
    logger.info("CASESTRAINER VERIFICATION DIAGNOSTIC")
    logger.info("=" * 60 + "\n")

    results = {
        "environment": check_environment_variables(),
        "redis": check_redis_connection(),
        "imports": check_imports(),
    }

    # Only test verification if prerequisites are met
    if results["environment"] and results["imports"]:
        results["verification"] = test_verification()
    else:
        logger.warning("⚠️  Skipping verification test due to configuration issues")
        results["verification"] = False

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info("=" * 60)

    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {check}")

    all_passed = all(results.values())

    if all_passed:
        logger.info("\n🎉 All checks passed! Verification should work correctly.")
        logger.info("\nIf you're still seeing unverified citations:")
        logger.info("1. Check the backend logs: tail -f src/logs/*.log")
        logger.info("2. Look for 'Verification ENABLED' or 'Verification DISABLED' messages")
        logger.info("3. Check for timeout or API errors")
    else:
        logger.error("\n⚠️  Some checks failed. Fix the issues above before testing verification.")

        if not results["environment"]:
            logger.error("\nTO FIX: Set your CourtListener API key:")
            logger.error("  1. Get a free key: https://www.courtlistener.com/help/api/")
            logger.error("  2. Add to .env file: COURTLISTENER_API_KEY=your-key-here")
            logger.error("  3. Or export: export COURTLISTENER_API_KEY=your-key-here")

    logger.info("")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
