"""
Detailed test with logging to see what's happening
"""
import asyncio
import sys
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

# Verify API key is loaded
print(f"Environment API Key: {os.getenv('COURTLISTENER_API_KEY')[:20] if os.getenv('COURTLISTENER_API_KEY') else 'NOT FOUND'}...")

async def test_with_logging():
    """Test with full logging enabled."""
    
    print("=" * 80)
    print("DETAILED VERIFICATION TEST: 521 U.S. 811")
    print("=" * 80)
    
    from src.unified_verification_master import UnifiedVerificationMaster
    
    master = UnifiedVerificationMaster()
    
    print(f"\nAPI Key configured: {bool(master.api_key)}")
    if master.api_key:
        print(f"API Key (first 10 chars): {master.api_key[:10]}...")
    
    print("\nCalling verify_citation...")
    result = await master.verify_citation(
        citation="521 U.S. 811",
        extracted_case_name="Branson",
        extracted_date="1997"
    )
    
    print(f"\n{'='*80}")
    print(f"RESULT:")
    print(f"{'='*80}")
    print(f"Verified: {result.verified}")
    print(f"Canonical Name: {result.canonical_name}")
    print(f"Canonical Date: {result.canonical_date}")
    print(f"Error: {result.error}")
    print(f"Source: {result.source}")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(test_with_logging())
