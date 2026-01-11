"""Debug CaseMine verification for 346 F.R.D. 102"""
import requests
import re
from urllib.parse import quote
import html

def test_casemine_346():
    """Test CaseMine search and parsing for 346 F.R.D. 102"""
    
    citation = "346 F.R.D. 102"
    query = citation.replace('"', "").replace("'", "").strip()
    search_url = f"https://www.casemine.com/search?q={quote(query).replace('%20','+')}"
    
    print(f"Testing CaseMine for: {citation}")
    print(f"Search URL: {search_url}")
    print()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    # Get search results
    print("=" * 60)
    print("STEP 1: Getting search results")
    print("=" * 60)
    resp = requests.get(search_url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ Search failed with status {resp.status_code}")
        return
    
    # Find judgment links
    html_content = resp.text
    judgement_pattern = r"href=\"(/judgement/[^\"]+)\""
    matches = re.findall(judgement_pattern, html_content, re.IGNORECASE)
    matches = list(dict.fromkeys(matches))  # dedupe
    
    print(f"\nFound {len(matches)} judgment link(s):")
    for i, link in enumerate(matches[:5], 1):
        print(f"  {i}. {link}")
    
    if not matches:
        print("❌ No judgment links found in search results")
        return
    
    # Check expected URL
    expected_id = "66e11cf2ab3a454de71ffe6c"
    expected_link = f"/judgement/us/{expected_id}"
    if expected_link in matches:
        print(f"\n✅ Expected judgment link found: {expected_link}")
    else:
        print(f"\n⚠️  Expected judgment link NOT found: {expected_link}")
    
    # Try first judgment page
    print("\n" + "=" * 60)
    print("STEP 2: Checking first judgment page")
    print("=" * 60)
    
    first_link = matches[0]
    case_url = f"https://www.casemine.com{first_link}"
    print(f"URL: {case_url}")
    
    page = requests.get(case_url, headers=headers, timeout=10)
    print(f"Status: {page.status_code}")
    
    if page.status_code != 200:
        print(f"❌ Page load failed with status {page.status_code}")
        return
    
    content = page.text
    
    # Extract case name
    print("\n" + "=" * 60)
    print("STEP 3: Extracting case name")
    print("=" * 60)
    
    name = None
    for pat in [r"<h1[^>]*>([^<]+)</h1>", r"<title>([^<]+?)\s*\|"]:
        m = re.search(pat, content, re.IGNORECASE)
        if m:
            name = re.sub(r"\s+", " ", m.group(1)).strip()
            name = html.unescape(name)
            print(f"Found name: {name}")
            break
    
    if not name:
        print("❌ No case name found")
    
    # Check citation presence
    print("\n" + "=" * 60)
    print("STEP 4: Checking citation presence")
    print("=" * 60)
    
    cit_patterns = [
        re.escape(citation),
        citation.replace(" ", r"\s+"),
        citation.replace(".", r"\.?"),
    ]
    
    for i, pattern in enumerate(cit_patterns, 1):
        found = re.search(pattern, content, re.IGNORECASE)
        if found:
            print(f"✅ Pattern {i} matched: {pattern}")
            print(f"   Match: {found.group()}")
        else:
            print(f"❌ Pattern {i} NOT matched: {pattern}")
    
    # Check for "F.R.D." specifically
    print("\nChecking for 'F.R.D.' in content:")
    if "F.R.D." in content:
        print("✅ 'F.R.D.' found in content")
        # Find context around F.R.D.
        frd_matches = re.finditer(r'.{0,50}F\.R\.D\..{0,50}', content, re.IGNORECASE)
        for i, match in enumerate(list(frd_matches)[:3], 1):
            print(f"  Context {i}: ...{match.group()}...")
    else:
        print("❌ 'F.R.D.' NOT found in content")
    
    # Check for "346" specifically
    print("\nChecking for '346' in content:")
    if "346" in content:
        print("✅ '346' found in content")
        # Find context around 346
        num_matches = re.finditer(r'.{0,30}346.{0,30}', content)
        for i, match in enumerate(list(num_matches)[:5], 1):
            print(f"  Context {i}: ...{match.group()}...")
    else:
        print("❌ '346' NOT found in content")

if __name__ == "__main__":
    test_casemine_346()
