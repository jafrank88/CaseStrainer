"""Test direct access to CaseMine judgment page for 346 F.R.D. 102"""
import requests
import re
import html

def test_direct_access():
    """Test direct access to the CaseMine judgment page"""
    
    case_url = "https://www.casemine.com/judgement/us/66e11cf2ab3a454de71ffe6c"
    citation = "346 F.R.D. 102"
    
    print(f"Testing direct access to CaseMine judgment page")
    print(f"URL: {case_url}")
    print(f"Looking for citation: {citation}")
    print()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    # Get page
    print("=" * 60)
    print("STEP 1: Loading judgment page")
    print("=" * 60)
    resp = requests.get(case_url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ Page load failed with status {resp.status_code}")
        return
    
    content = resp.text
    print(f"Content length: {len(content)} characters")
    
    # Extract case name
    print("\n" + "=" * 60)
    print("STEP 2: Extracting case name")
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
    
    # Extract date
    print("\n" + "=" * 60)
    print("STEP 3: Extracting date")
    print("=" * 60)
    
    ym = re.search(r"\b(19|20)\d{2}\b", content[:4000])
    if ym:
        print(f"Found year: {ym.group(0)}")
    else:
        print("❌ No year found")
    
    # Check citation presence
    print("\n" + "=" * 60)
    print("STEP 4: Checking citation presence")
    print("=" * 60)
    
    cit_patterns = [
        re.escape(citation),
        citation.replace(" ", r"\s+"),
        citation.replace(".", r"\.?"),
    ]
    
    found_any = False
    for i, pattern in enumerate(cit_patterns, 1):
        found = re.search(pattern, content, re.IGNORECASE)
        if found:
            print(f"✅ Pattern {i} matched: {pattern}")
            print(f"   Match: {found.group()}")
            found_any = True
        else:
            print(f"❌ Pattern {i} NOT matched: {pattern}")
    
    # Check for "F.R.D." specifically
    print("\n" + "=" * 60)
    print("STEP 5: Checking for F.R.D. reporter")
    print("=" * 60)
    
    if "F.R.D." in content:
        print("✅ 'F.R.D.' found in content")
        # Find context around F.R.D.
        frd_matches = re.finditer(r'.{0,50}F\.R\.D\..{0,50}', content, re.IGNORECASE)
        for i, match in enumerate(list(frd_matches)[:5], 1):
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
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if name:
        print(f"✅ Case name: {name}")
    else:
        print("❌ No case name found")
    
    if found_any:
        print(f"✅ Citation '{citation}' found on page")
    else:
        print(f"❌ Citation '{citation}' NOT found on page")
    
    if name and found_any:
        print("\n✅ This case SHOULD be verified by CaseMine")
    else:
        print("\n⚠️  This case may not be verifiable by CaseMine")

if __name__ == "__main__":
    test_direct_access()
