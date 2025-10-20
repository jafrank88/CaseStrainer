"""Test fallback verification for the five v. Garland cases"""
import asyncio
import logging
from datetime import datetime

# Set up logging to see all messages
logging.basicConfig(
    level=logging.ERROR,
    format='%(message)s'
)

from src.unified_verification_master import UnifiedVerificationMaster

# The five v. Garland cases
test_cases = [
    {
        'citation': '11 F.4th 1133',
        'case_name': 'Alam v. Garland',
        'year': '2021'
    },
    {
        'citation': '9 F.4th 1052',
        'case_name': 'Sharma v. Garland',
        'year': '2020'
    },
    {
        'citation': '124 F.4th 690',
        'case_name': 'Singh v. Garland',
        'year': '2024'
    },
    {
        'citation': '69 F.4th 544',
        'case_name': 'Umana-Escobar v. Garland',
        'year': '2023'
    },
    {
        'citation': '89 F.4th 754',
        'case_name': 'Alcarez-Rodriguez v. Garland',
        'year': '2024'
    }
]

async def test_all_cases():
    print("="*80)
    print("TESTING FALLBACK VERIFICATION FOR 5 v. GARLAND CASES")
    print("="*80)
    print(f"\nStart time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Rate limiting: 2.0 seconds between requests per domain")
    print(f"Expected time: ~2-3 minutes (with delays)")
    print("\n" + "="*80 + "\n")
    
    verifier = UnifiedVerificationMaster()
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        citation = test_case['citation']
        case_name = test_case['case_name']
        year = test_case['year']
        
        print(f"\n{i}. Testing: {citation} - {case_name} ({year})")
        print("-"*80)
        
        try:
            result = await verifier.verify_citation(
                citation=citation,
                extracted_case_name=case_name,
                extracted_date=year,
                timeout=30.0,  # 30 second timeout per citation
                enable_fallback=True
            )
            
            # Store result
            results.append({
                'citation': citation,
                'case_name': case_name,
                'verified': result.verified,
                'source': result.source,
                'canonical_name': result.canonical_name,
                'error': result.error
            })
            
            # Print result
            if result.verified:
                print(f"   ✅ VERIFIED via {result.source}")
                print(f"   Canonical name: {result.canonical_name}")
            else:
                print(f"   ❌ NOT VERIFIED")
                print(f"   Error: {result.error}")
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
            results.append({
                'citation': citation,
                'case_name': case_name,
                'verified': False,
                'source': None,
                'canonical_name': None,
                'error': str(e)
            })
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    verified_count = sum(1 for r in results if r['verified'])
    total_count = len(results)
    
    print(f"\nVerification Rate: {verified_count}/{total_count} ({verified_count/total_count*100:.1f}%)")
    print(f"\nEnd time: {datetime.now().strftime('%H:%M:%S')}")
    
    print("\nDetailed Results:")
    print("-"*80)
    
    for r in results:
        status = "✅" if r['verified'] else "❌"
        print(f"{status} {r['citation']:<20} | {r['case_name']:<35}")
        if r['verified']:
            print(f"   Source: {r['source']}")
            print(f"   Canonical: {r['canonical_name']}")
        else:
            print(f"   Error: {r['error']}")
        print()
    
    # Print sources used
    if verified_count > 0:
        print("\nSources Used:")
        print("-"*80)
        sources = {}
        for r in results:
            if r['verified'] and r['source']:
                sources[r['source']] = sources.get(r['source'], 0) + 1
        
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count} citation(s)")
    
    print("\n" + "="*80)
    
    return results

if __name__ == "__main__":
    results = asyncio.run(test_all_cases())
