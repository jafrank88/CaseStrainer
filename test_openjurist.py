import asyncio
import aiohttp
import re
from urllib.parse import quote_plus

async def test_openjurist_citation():
    citation = "567 P.3d 625"
    url = f"https://openjurist.org/open-jurist-search-results?q={quote_plus(citation)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://openjurist.org/"
    }
    async with aiohttp.ClientSession() as session:
        print(f"Testing OpenJurist citation search: {url}")
        try:
            async with session.get(url, headers=headers, timeout=10) as resp:
                print(f"Status: {resp.status}")
                html = await resp.text()
                print(f"Content length: {len(html)} characters")
                if "cloudflare" in html.lower() or "enable javascript" in html.lower():
                    print("❌ Blocked by Cloudflare or anti-bot page")
                elif re.search(re.escape(citation), html, re.IGNORECASE):
                    print("✅ Citation found in content!")
                    return True
                else:
                    print("❌ Citation not found in content")
                    print(f"Content preview: {html[:200]}...")
        except Exception as e:
            print(f"❌ Exception: {e}")
    return False

if __name__ == "__main__":
    result = asyncio.run(test_openjurist_citation())
    print(f"\nFinal result: {'SUCCESS' if result else 'FAILED'}") 