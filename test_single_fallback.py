"""Quick test of single citation fallback"""
import asyncio
import logging

# Set up logging to see all messages
logging.basicConfig(level=logging.ERROR, format='%(message)s')

from src.unified_verification_master import UnifiedVerificationMaster

async def test():
    print("Testing fallback for: 11 F.4th 1133 - Alam v. Garland")
    verifier = UnifiedVerificationMaster()
    
    result = await verifier.verify_citation(
        citation='11 F.4th 1133',
        extracted_case_name='Alam v. Garland',
        extracted_date='2021',
        timeout=15.0,
        enable_fallback=True
    )
    
    print(f"\nRESULT:")
    print(f"  Verified: {result.verified}")
    print(f"  Source: {result.source}")
    print(f"  Canonical Name: {result.canonical_name}")
    print(f"  Error: {result.error}")

if __name__ == "__main__":
    asyncio.run(test())
