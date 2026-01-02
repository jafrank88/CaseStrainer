"""
Parse the specific Karpenski citation from user's response to understand the issue.
"""

# From user's response - the Karpenski citation
karpenski_citation = {
    "canonical_date": "2014-04-02",
    "canonical_name": "Karpenski v. American General Life Companies, LLC",
    "canonical_url": "https://www.courtlistener.com/opinion/2730965/karpenski-v-american-general-life-companies-llc/",
    "case_history": [],
    "case_name": "Karpenski v. American General Life Companies, LLC",
    "citation": "999 F. Supp. 2d 1235",
    "cluster_case_name": "Karpenski v. American General Life Companies, LLC",
    "extracted_case_name": "Karpenski v. American General Life Companies, LLC",
    "extracted_date": "2014",
    "verified": True,
    "name_mismatch": True,  # <-- This is the issue!
    "date_mismatch": False,
    "possible_match": True,
}

print("=" * 100)
print("KARPENSKI CITATION ANALYSIS")
print("=" * 100)
print()

print("Extracted Case Name: ", karpenski_citation["extracted_case_name"])
print("Canonical Name:      ", karpenski_citation["canonical_name"])
print("Are they identical? ", karpenski_citation["extracted_case_name"] == karpenski_citation["canonical_name"])
print()
print("name_mismatch flag: ", karpenski_citation["name_mismatch"])
print("possible_match flag:", karpenski_citation["possible_match"])
print()

print("=" * 100)
print("HYPOTHESIS: The issue is NOT with similarity calculation")
print("=" * 100)
print()
print("The names are IDENTICAL but name_mismatch=True")
print("This suggests the flag is being set incorrectly in _annotate_mismatch_flags()")
print()
print("Looking at citation_extraction_endpoint.py lines 273-276:")
print("  if (not extracted or extracted == 'N/A') and canonical:")
print("      name_mismatch = True")
print()
print("This would flag mismatch if extracted is 'N/A' even when canonical exists.")
print("But in this case, extracted is NOT 'N/A', it's a valid name!")
print()
print("Let me check if there's another condition...")
print()

# Simulate the logic from _annotate_mismatch_flags
extracted = karpenski_citation["extracted_case_name"]
canonical = karpenski_citation["canonical_name"]
verified = karpenski_citation["verified"]
canonical_url = karpenski_citation["canonical_url"]

# The logic from citation_extraction_endpoint.py
if (not extracted or extracted == 'N/A') and canonical:
    name_mismatch = True
    reason = "N/A extracted but canonical exists"
else:
    # This is where _names_equivalent would be called
    # But we need to import the actual function to test
    reason = "Would call _names_equivalent"
    name_mismatch = None  # Unknown without calling the function

print(f"Based on code logic:")
print(f"  Would set name_mismatch due to N/A check: {(not extracted or extracted == 'N/A') and canonical}")
print(f"  Reason: {reason}")
print()

print("=" * 100)
print("POSSIBLE BUG")
print("=" * 100)
print()
print("If _names_equivalent is returning False for identical names, there may be a bug in:")
print("  1. The function itself")
print("  2. How the parameters are being passed")
print("  3. Some preprocessing that's changing the names before comparison")
print()
print("ACTION: Check _names_equivalent function with actual identical names")
