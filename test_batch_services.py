import asyncio
import random
import time
from src.websearch_utils import LegalWebsearchEngine

SAMPLE_CITATIONS = [
    "567 P.3d 625", "410 U.S. 113", "123 F.3d 456", "999 N.E.2d 123", "42 Cal. 3d 456",
    "2019 WL 123456", "876 S.W.2d 789", "321 F. Supp. 2d 654", "12 Mass. App. Ct. 345",
    "2021 IL App (1st) 210123", "100 So. 3d 456", "789 A.2d 123", "456 Mich. 789",
    "2020 NY Slip Op 01234", "345 S.E.2d 678", "234 Kan. 567", "2022-Ohio-1234",
    "123 N.W.2d 456", "567 S.C. 890", "2023 BL 123456"
]

SERVICES = [
    "courtlistener", "bing", "duckduckgo", "justia", "leagle", "findlaw"
]

async def test_citation_with_service(searcher, citation, service):
    method = getattr(searcher, f"search_{service}")
    try:
        result = await method(citation)
        return result.get("verified", False)
    except Exception as e:
        return False

async def batch_test():
    random.shuffle(SAMPLE_CITATIONS)
    results = {service: [] for service in SERVICES}

    async with LegalWebsearchEngine() as searcher:
        for citation in SAMPLE_CITATIONS[:20]:
            services_order = SERVICES[:]
            random.shuffle(services_order)
            print(f"\nTesting citation: {citation}")
            for service in services_order:
                print(f"  - {service} ...", end="")
                verified = await test_citation_with_service(searcher, citation, service)
                results[service].append(verified)
                print("✓" if verified else "✗")
                await asyncio.sleep(1.5)  # Delay to avoid rate limiting

    # Summarize results
    print("\nSummary:")
    for service in SERVICES:
        total = len(results[service])
        success = sum(results[service])
        print(f"{service}: {success}/{total} ({success/total:.0%})")

if __name__ == "__main__":
    asyncio.run(batch_test()) 