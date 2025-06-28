import asyncio
import aiohttp
import re
from urllib.parse import quote_plus

async def test_leagle_citation():
    """Test Leagle search with specific citation 567 P.3d 625 using session and cookies."""
    
    citation = "567 P.3d 625"
    search_url = f"https://www.leagle.com/leaglesearch?cite={quote_plus(citation)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.leagle.com/"
    }
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Load the search page to get cookies
        print("Loading search form to get cookies...")
        async with session.get("https://www.leagle.com/leaglesearch", headers=headers, timeout=10) as resp:
            print(f"Initial GET status: {resp.status}")
            _ = await resp.text()
            # Cookies are now set in the session
        
        # Step 2: Perform the citation search with cookies and headers
        print(f"\n--- Testing Leagle citation search: {search_url} ---")
        try:
            async with session.get(search_url, headers=headers, timeout=10) as resp:
                print(f"Status: {resp.status}")
                html = await resp.text()
                print(f"Content length: {len(html)} characters")
                
                # Check if we got the search form or actual results
                if "leagle search" in html.lower() or "search for" in html.lower():
                    print("📋 Got search form page (not results)")
                elif "search results" in html.lower() or "found" in html.lower():
                    print("🔍 Got search results page")
                else:
                    print("❓ Unknown page type")
                
                # Look for citation in the page content
                if re.search(re.escape(citation), html, re.IGNORECASE):
                    print("✅ CITATION FOUND!")
                    # Look for case information
                    if "case" in html.lower() or "opinion" in html.lower():
                        print("✅ Legal content detected!")
                    return True
                else:
                    print("❌ Citation not found in content")
                    print(f"Content preview: {html[:200]}...")
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    return False

if __name__ == "__main__":
    print("Testing Leagle search with citation: 567 P.3d 625 (with session/cookies)")
    result = asyncio.run(test_leagle_citation())
    print(f"\nFinal result: {'SUCCESS' if result else 'FAILED'}") 