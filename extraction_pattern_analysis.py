"""Detailed analysis of N/A citation extraction patterns"""
import re
import PyPDF2

NA_CITATIONS = [
    ("548 P.3d 226", "Erickson v. Pharmacia"),
    ("510 P.3d 326", "Dearinger v. Eli Lilly"),
    ("498 U.S. 941", "In re Marriage of Williams"),
    ("2019 WL 2066127", "Nazar v. Harbor Freight Tools"),
    ("2011 WL 3298912", "Milgard Mfg., Inc. v. Illinois Union Ins. Co."),
    ("31 Wn. App. 2d 100", "Erickson v. Pharmacia"),
    ("19 Wn. App. 2d 113", "Pope Resources, LP v. Certain Underwriters"),
    ("831 F.2d 508", "Goad v. Celotex Corp."),
    ("3 Wn.3d 1018", "Erickson v. Pharmacia")
]

def extract_pdf_text(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

print("=" * 100)
print("EXTRACTION FAILURE PATTERN ANALYSIS")
print("=" * 100)

pdf_path = r"D:\dev\casestrainer\1031351.pdf"
text = extract_pdf_text(pdf_path)

patterns_found = {
    'string_citation': [],
    'parenthetical': [],
    'cert_denied': [],
    'westlaw_with_docket': [],
    'review_granted': [],
    'signal_word': []
}

for citation, expected_name in NA_CITATIONS:
    # Find citation position
    citation_pattern = re.escape(citation).replace(r'\ ', r'\s+')
    match = re.search(citation_pattern, text, re.IGNORECASE)
    
    if not match:
        continue
    
    start = match.start()
    context_before = text[max(0, start - 500):start]
    context_after = text[start:min(len(text), start + 200)]
    
    # Clean for analysis
    before = re.sub(r'\s+', ' ', context_before)
    
    print(f"\n{'=' * 100}")
    print(f"CITATION: {citation}")
    print(f"EXPECTED: {expected_name}")
    print("=" * 100)
    
    # Extract the actual text pattern
    before_150 = before[-150:]
    print(f"\nContext (150 chars before): ...{before_150}{citation}")
    
    # Identify pattern type
    pattern_type = None
    
    # Pattern 1: String citation (multiple reporters in a row)
    # "Name, 123 Reporter 456, 789 Reporter2 012"
    string_pattern = r'([A-Z][^,]{10,80}?),\s*\d+\s+[A-Za-z.\s]+\d+,\s*\d+\s*[-–]?\s*\d*,?\s*$'
    if re.search(string_pattern, before[-200:]):
        pattern_type = "STRING_CITATION"
        patterns_found['string_citation'].append(citation)
        print(f"  ✓ Pattern: STRING CITATION (multiple reporters)")
        print(f"    Example: 'Erickson v. Pharmacia, 31 Wn. App. 2d 100, 110-11, 548 P.3d 226'")
    
    # Pattern 2: Parenthetical citation
    # "(quoting Name, 123 Reporter 456 (1990))"
    if '(' in before[-100:] and ')' not in before[-100:]:
        if 'quoting' in before[-100:].lower() or 'citing' in before[-100:].lower():
            pattern_type = "PARENTHETICAL"
            patterns_found['parenthetical'].append(citation)
            print(f"  ✓ Pattern: PARENTHETICAL CITATION")
            print(f"    Contains: quoting/citing within parentheses")
    
    # Pattern 3: cert. denied / review granted
    if 'cert. denied' in before[-100:] or 'review granted' in before[-100:]:
        pattern_type = "CERT_DENIED/REVIEW_GRANTED"
        patterns_found['cert_denied'].append(citation)
        print(f"  ✓ Pattern: CERT. DENIED / REVIEW GRANTED")
        print(f"    Example: '796 P.2d 421 (1990), cert. denied, 498 U.S. 941'")
    
    # Pattern 4: WestLaw with docket number
    # "Name, No. 2:18-CV-00348-SMJ, 2019 WL 2066127"
    if re.search(r'No\.\s+[\w:-]+,\s*$', before[-50:]):
        pattern_type = "WESTLAW_WITH_DOCKET"
        patterns_found['westlaw_with_docket'].append(citation)
        print(f"  ✓ Pattern: WESTLAW WITH DOCKET NUMBER")
        print(f"    Example: 'Nazar v. Harbor Freight, No. 2:18-CV-00348, 2019 WL 2066127'")
    
    # Pattern 5: Signal words
    signal_words = ['see', 'see also', 'compare', 'citing', 'but see', 'cf.', 'accord']
    for signal in signal_words:
        if re.search(rf'\b{signal}\b', before[-150:], re.IGNORECASE):
            if 'signal_word' not in [pattern_type]:
                patterns_found['signal_word'].append(citation)
            print(f"  ⚠️  Signal word: '{signal}'")
    
    # Try to extract case name using different strategies
    print(f"\n  🔍 EXTRACTION STRATEGIES:")
    
    # Strategy 1: Look for "Name, reporter" pattern
    name_reporter = re.search(r'([A-Z][^,;]{10,100}?),\s*\d+\s+[A-Za-z.\s]+\d+', before[-200:])
    if name_reporter:
        print(f"    1. Name before reporter: '{name_reporter.group(1)}'")
    
    # Strategy 2: Look for last "v." before citation
    v_pattern = re.findall(r'([A-Z][^,;]{5,80}\s+v\.\s+[^,;]{5,80})', before[-300:])
    if v_pattern:
        print(f"    2. Last 'v.' pattern: '{v_pattern[-1]}'")
    
    # Strategy 3: For WestLaw, look before "No."
    if 'No.' in before[-100:]:
        wl_pattern = re.search(r'([A-Z][^,;]{10,80}?),?\s+No\.', before[-150:])
        if wl_pattern:
            print(f"    3. Name before 'No.': '{wl_pattern.group(1)}'")

print("\n" + "=" * 100)
print("SUMMARY OF PATTERNS")
print("=" * 100)
for pattern, citations in patterns_found.items():
    if citations:
        print(f"\n{pattern.upper()}: {len(citations)} citation(s)")
        for cit in citations:
            print(f"  - {cit}")

print("\n" + "=" * 100)
print("EXTRACTION IMPROVEMENTS NEEDED")
print("=" * 100)
print("""
1. STRING CITATIONS (multiple reporters in row):
   - Pattern: "Name, 123 Rep 456, 789 Rep2 012"
   - Fix: Extract name from before FIRST reporter in string
   - Example: "Erickson v. Pharmacia, 31 Wn. App. 2d 100, 548 P.3d 226"
   
2. PARENTHETICAL CITATIONS:
   - Pattern: "(quoting Name, 123 Rep 456)"
   - Fix: Look inside parentheses for case name
   - Example: "(quoting In re Marriage of Williams, 115 Wn.2d 202)"

3. CERT. DENIED / REVIEW GRANTED:
   - Pattern: "123 Rep 456, cert. denied, 789 Rep2 012"
   - Fix: Look BEFORE "cert. denied" for the primary case name
   - Example: "In re Marriage, 796 P.2d 421, cert. denied, 498 U.S. 941"

4. WESTLAW WITH DOCKET:
   - Pattern: "Name, No. XX-XXXXX, 2019 WL 123456"
   - Fix: Extract name from before "No."
   - Example: "Nazar v. Harbor Freight, No. 2:18-CV-348, 2019 WL 2066127"
""")
