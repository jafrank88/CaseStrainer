"""
Comprehensive validation script for 24-2626.pdf
Compares extracted case names against what's actually in the document.
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Loading document and results...")

# Load the PDF text
try:
    import PyPDF2
    pdf_path = r'D:\dev\casestrainer\24-2626.pdf'
    pdf_reader = PyPDF2.PdfReader(pdf_path)
    full_text = '\n'.join([page.extract_text() for page in pdf_reader.pages])
    print(f"✅ Loaded PDF: {len(full_text)} characters, {len(pdf_reader.pages)} pages")
except Exception as e:
    print(f"❌ Failed to load PDF: {e}")
    sys.exit(1)

# Load the results
try:
    with open(r'D:\dev\casestrainer\24-2626_comprehensive_results.json', 'r') as f:
        results = json.load(f)
    citations = results.get('citations', [])
    print(f"✅ Loaded results: {len(citations)} citations")
except Exception as e:
    print(f"❌ Failed to load results: {e}")
    sys.exit(1)

print()
print("=" * 100)
print("VALIDATION: Extracted Case Names vs. Document Content")
print("=" * 100)
print()

# Known correct case names from manual inspection of the document
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
    "90 F.4th 1042": "Martinez v. ZoomInfo Techs., Inc.",  # vacated version
    "814 F.3d 116": "Ernst v. Carrigan",
    "98 F.4th 1320": "Coomer v. Make Your Life Epic LLC",
    "472 U.S. 511": "Mitchell v. Forsyth",
    "825 F.3d 1043": "Hyan v. Hummer",
}

mismatches = []
matches = []
unknown = []

for citation in citations:
    cit_text = citation.get('citation')
    extracted = citation.get('extracted_case_name', '')
    
    if not cit_text:
        continue
    
    # Normalize citation text for comparison
    cit_normalized = cit_text.strip()
    
    if cit_normalized in known_correct:
        expected = known_correct[cit_normalized]
        
        # Normalize for comparison
        extracted_norm = extracted.lower().replace(',', '').replace('.', '').strip()
        expected_norm = expected.lower().replace(',', '').replace('.', '').strip()
        
        # Check if it's a reasonable match
        if extracted_norm in expected_norm or expected_norm in extracted_norm:
            matches.append({
                'citation': cit_text,
                'expected': expected,
                'extracted': extracted,
                'status': 'MATCH'
            })
        else:
            mismatches.append({
                'citation': cit_text,
                'expected': expected,
                'extracted': extracted,
                'status': 'MISMATCH'
            })
    else:
        # Try to find the case name in the document
        # Look for the citation in the text
        cit_pos = full_text.find(cit_text)
        if cit_pos > 0:
            # Get 200 chars before the citation
            context_start = max(0, cit_pos - 200)
            context = full_text[context_start:cit_pos]
            
            unknown.append({
                'citation': cit_text,
                'extracted': extracted,
                'context': context[-100:] if len(context) > 100 else context,
                'status': 'UNKNOWN'
            })

# Print results
print(f"✅ MATCHES: {len(matches)}")
for item in matches[:5]:  # Show first 5
    print(f"   {item['citation']}: {item['extracted']}")
if len(matches) > 5:
    print(f"   ... and {len(matches) - 5} more")

print()
print(f"❌ MISMATCHES: {len(mismatches)}")
for item in mismatches:
    print(f"   {item['citation']}:")
    print(f"      Expected:  {item['expected']}")
    print(f"      Extracted: {item['extracted']}")
    print()

print(f"⚠️  UNKNOWN: {len(unknown)} (not in validation set)")

print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"Total citations validated: {len(matches) + len(mismatches)}")
print(f"Correct matches: {len(matches)} ({len(matches)*100/(len(matches)+len(mismatches)) if (len(matches)+len(mismatches)) > 0 else 0:.1f}%)")
print(f"Mismatches: {len(mismatches)} ({len(mismatches)*100/(len(matches)+len(mismatches)) if (len(matches)+len(mismatches)) > 0 else 0:.1f}%)")

if len(mismatches) == 0:
    print()
    print("🎉 ALL VALIDATIONS PASSED! Extracted case names match the document.")
else:
    print()
    print("⚠️  MISMATCHES FOUND - Backend needs more fixes")
