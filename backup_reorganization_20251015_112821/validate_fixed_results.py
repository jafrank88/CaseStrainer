"""
Validate the fixed results against known correct case names.
"""

import json

# Load fixed results
with open(r'D:\dev\casestrainer\24-2626_FIXED.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

citations = results.get('citations', [])

# Known correct case names
known_correct = {
    "333 F.3d 1018": "Batzel v. Smith",
    "304 U.S. 64": "Erie Railroad Co. v. Tompkins",
    "546 U.S. 345": "Will v. Hallock",
    "506 U.S. 139": "P.R. Aqueduct & Sewer Auth. v. Metcalf & Eddy, Inc.",
    "830 F.3d 881": "Manzari v. Associated Newspapers Ltd.",
    "190 F.3d 963": "United States ex rel. Newsham v. Lockheed Missiles & Space Co.",
    "129 F.4th 1196": "Gopher Media LLC v. Melone",
    "511 U.S. 863": "Digital Equip. Corp. v. Desktop Direct, Inc.",
    "337 U.S. 541": "Cohen v. Beneficial Indus. Loan Corp.",
    "515 U.S. 304": "Johnson v. Jones",
    "558 U.S. 100": "Mohawk Indus., Inc. v. Carpenter",
    "859 F.3d 720": "SolarCity Corp. v. Salt River Project Agric. Improvement & Power Dist.",
    "706 F.3d 1009": "DC Comics v. Pacific Pictures Corp.",
    "736 F.3d 1180": "Makaeff v. Trump Univ., LLC",
    "82 F.4th 785": "Martinez v. ZoomInfo Techs., Inc.",
    "90 F.4th 1042": "Martinez v. ZoomInfo Techs., Inc.",
    "814 F.3d 116": "Ernst v. Carrigan",
    "98 F.4th 1320": "Coomer v. Make Your Life Epic LLC",
    "472 U.S. 511": "Mitchell v. Forsyth",
    "825 F.3d 1043": "Hyan v. Hummer",
}

print("=" * 100)
print("VALIDATION: Fixed Results vs. Document")
print("=" * 100)
print()

matches = []
mismatches = []

for cit in citations:
    cit_text = cit.get('citation', '').strip()
    extracted = cit.get('extracted_case_name', '')
    
    if cit_text in known_correct:
        expected = known_correct[cit_text]
        
        # Normalize
        extracted_norm = (extracted or '').lower().replace(',', '').replace('.', '').strip()
        expected_norm = expected.lower().replace(',', '').replace('.', '').strip()
        
        # Check match
        if extracted_norm and (extracted_norm in expected_norm or expected_norm in extracted_norm):
            matches.append(cit_text)
            print(f"✅ {cit_text}: {extracted}")
        else:
            mismatches.append({
                'citation': cit_text,
                'expected': expected,
                'extracted': extracted or 'N/A'
            })
            print(f"❌ {cit_text}:")
            print(f"   Expected:  {expected}")
            print(f"   Extracted: {extracted or 'N/A'}")
            print()

print()
print("=" * 100)
print(f"SUMMARY: {len(matches)}/{len(known_correct)} correct ({len(matches)*100//len(known_correct)}%)")
print("=" * 100)

if len(mismatches) > 0:
    print()
    print(f"Still {len(mismatches)} mismatches remaining. Need to continue fixing backend.")
