"""
Test 60 different citation types for extraction and fallback verification
"""

# Create test text with 60 different citation formats
test_text = """
COMPREHENSIVE CITATION FORMAT TEST DOCUMENT

This document contains 60 different legal citation formats to test extraction coverage.

=== FEDERAL REPORTERS ===

1. Supreme Court Cases:
Brown v. Board of Education, 347 U.S. 483 (1954).
Roe v. Wade, 410 U.S. 113 (1973).
Miranda v. Arizona, 384 U.S. 436 (1966).

2. Federal Appellate Courts:
Smith v. Jones, 123 F.3d 456 (9th Cir. 1997).
Williams v. Brown, 456 F.2d 789 (2d Cir. 1985).
Johnson v. Smith, 789 F.4th 123 (5th Cir. 2020).
Davis v. Miller, 234 F. 567 (8th Cir. 1922).

3. Federal District Courts:
Anderson v. Liberty Lobby, 477 F. Supp. 615 (D.D.C. 1979).
United States v. Smith, 234 F. Supp. 2d 567 (S.D.N.Y. 2002).
Jones v. County, 567 F. Supp. 3d 890 (N.D. Cal. 2021).

=== STATE REPORTERS ===

4. California:
People v. Anderson, 6 Cal. 3d 628 (1972).
Smith v. Jones, 100 Cal. 2d 200 (1960).
Williams v. State, 234 Cal. 4th 567 (2015).
Garcia v. County, 456 Cal. 5th 789 (2022).

5. New York:
Matter of Jacob, 86 N.Y.2d 651 (1995).
People v. Smith, 123 N.Y.3d 456 (2014).
Jones v. Williams, 234 N.Y. 567 (1922).

6. Texas:
Brown v. State, 123 Tex. 456 (1980).
Smith v. Jones, 234 S.W.3d 567 (Tex. 2008).
Williams v. County, 456 S.W.2d 789 (Tex. App. 1995).

7. Florida:
State v. Johnson, 123 Fla. 456 (1990).
Smith v. Jones, 234 So. 3d 567 (Fla. 2016).
Williams v. State, 456 So. 2d 789 (Fla. Dist. Ct. App. 2002).

8. Illinois:
People v. Smith, 123 Ill. 2d 456 (1988).
Jones v. Williams, 234 Ill. 567 (1925).
Brown v. County, 456 N.E.3d 789 (Ill. 2019).

9. Ohio:
State v. Johnson, 2025 Ohio 213 (2025).
Smith v. Jones, 123 Ohio St. 3d 456 (2009).
Williams v. State, 234 Ohio St. 2d 567 (1995).
Brown v. County, 456 Ohio App. 789 (1988).

=== REGIONAL REPORTERS ===

10. Pacific Reporter:
State v. Smith, 123 P.3d 456 (Wash. 2005).
Jones v. Williams, 234 P.2d 567 (Cal. 1951).
Brown v. County, 456 P. 789 (Or. 1915).

11. Atlantic Reporter:
State v. Johnson, 123 A.3d 456 (N.J. 2015).
Smith v. Jones, 234 A.2d 567 (Pa. 1967).
Williams v. State, 456 A. 789 (Md. 1905).

12. North Eastern Reporter:
People v. Smith, 123 N.E.3d 456 (Ill. 2018).
Jones v. Williams, 234 N.E.2d 567 (Ohio 1968).
Brown v. County, 456 N.E. 789 (Mass. 1910).

13. South Eastern Reporter:
State v. Johnson, 123 S.E.2d 456 (N.C. 1962).
Smith v. Jones, 234 S.E. 567 (Va. 1920).

14. Southern Reporter:
Williams v. State, 123 So. 3d 456 (Ala. 2013).
Brown v. County, 234 So. 2d 567 (Miss. 1970).

15. North Western Reporter:
State v. Smith, 123 N.W.2d 456 (Minn. 1963).
Jones v. Williams, 234 N.W. 567 (Wis. 1918).

=== SPECIALTY REPORTERS ===

16. Washington State:
Bostain v. Food Express, Inc., 159 Wn.2d 700 (2007).
State v. Johnson, 183 Wn.2d 649 (2015).
Smith v. Jones, 123 Wash. App. 456 (2004).

17. Bankruptcy:
In re Smith, 123 B.R. 456 (Bankr. D. Del. 2000).

18. Federal Claims:
Jones v. United States, 123 Fed. Cl. 456 (2015).

=== ONLINE/UNREPORTED ===

19. Westlaw:
Smith v. Jones, 2020 WL 1234567 (D. Mass. Mar. 15, 2020).
Williams v. State, 2019 WL 9876543 (S.D.N.Y. Dec. 1, 2019).

20. LEXIS:
Brown v. County, 2021 U.S. Dist. LEXIS 12345 (N.D. Cal. Jan. 20, 2021).
Johnson v. Smith, 2018 U.S. App. LEXIS 67890 (9th Cir. June 15, 2018).

=== SPECIAL CASE TYPES ===

21. In re Cases:
In re Marriage of Smith, 123 Cal. App. 4th 456 (2004).
In re Estate of Johnson, 234 N.Y.2d 567 (2010).

22. Ex rel Cases:
State ex rel. Attorney General v. Smith, 123 Ohio St. 3d 456 (2009).
People ex rel. Bryant v. Holladay, 234 Ill. 2d 567 (2008).

23. Administrative:
Smith v. Commissioner, 123 T.C. 456 (2004).

END OF TEST DOCUMENT
"""

print("="*80)
print("TESTING 60 CITATION TYPES")
print("="*80)

print(f"\nTest document length: {len(test_text):,} characters")
print(f"Test document lines: {len(test_text.split(chr(10)))}")

# Count expected citations manually
import re
expected_patterns = [
    r'\d+\s+U\.S\.\s+\d+',           # U.S. Reports
    r'\d+\s+F\.\d*(?:d|th)?\s+\d+',   # Federal Reporters
    r'\d+\s+F\.\s*Supp\.\s*\d*d?\s+\d+', # F. Supp
    r'\d+\s+Cal\.\s*\d*(?:d|th)?\s+\d+',  # California
    r'\d+\s+N\.Y\.\d*d?\s+\d+',       # New York
    r'\d+\s+Tex\.\s+\d+',             # Texas
    r'\d+\s+S\.W\.\d*d?\s+\d+',       # South Western
    r'\d+\s+Fla\.\s+\d+',             # Florida
    r'\d+\s+So\.\s*\d*d?\s+\d+',      # Southern
    r'\d+\s+Ill\.\s*\d*d?\s+\d+',     # Illinois
    r'\d+\s+N\.E\.\d*d?\s+\d+',       # North Eastern
    r'\d+\s+Ohio',                    # Ohio
    r'\d+\s+P\.\d*d?\s+\d+',          # Pacific
    r'\d+\s+A\.\d*d?\s+\d+',          # Atlantic
    r'\d+\s+S\.E\.\d*d?\s+\d+',       # South Eastern
    r'\d+\s+N\.W\.\d*d?\s+\d+',       # North Western
    r'\d+\s+Wn\.\d*d?\s+\d+',         # Washington
    r'\d+\s+Wash\.\s*App\.\s+\d+',    # Washington Appellate
    r'\d+\s+B\.R\.\s+\d+',            # Bankruptcy
    r'\d+\s+Fed\.\s*Cl\.\s+\d+',      # Federal Claims
    r'\d+\s+WL\s+\d+',                # Westlaw
    r'\d+\s+U\.S\.\s*(?:Dist\.|App\.)\s*LEXIS\s+\d+', # LEXIS
    r'\d+\s+T\.C\.\s+\d+',            # Tax Court
]

total_expected = 0
for pattern in expected_patterns:
    matches = re.findall(pattern, test_text)
    if matches:
        total_expected += len(matches)
        print(f"  Pattern {pattern[:30]:30} found {len(matches):2} citations")

print(f"\n  Approximate expected citations: {total_expected}")

# Now test with our system
print(f"\n{'='*80}")
print("RUNNING CASESTRAINER EXTRACTION")
print("="*80)

from src.citation_extraction_endpoint import extract_citations_with_clustering

print("\n[DEBUG] Calling extraction with enable_verification=True")
result = extract_citations_with_clustering(test_text, enable_verification=True)
print(f"[DEBUG] Result keys: {list(result.keys())}")

citations = result.get('citations', [])
clusters = result.get('clusters', [])

print(f"\nExtraction Results:")
print(f"  Citations found: {len(citations)}")
print(f"  Clusters: {len(clusters)}")
print(f"  Match rate: {len(citations)/total_expected*100:.1f}%")

# Analyze verification
verified_count = sum(1 for c in citations if c.get('verified', False))
unverified_count = len(citations) - verified_count

print(f"\nVerification Results:")
print(f"  Verified: {verified_count} ({verified_count/len(citations)*100:.1f}%)")
print(f"  Unverified: {unverified_count} ({unverified_count/len(citations)*100:.1f}%)")

# Check verification sources
verification_sources = {}
for c in citations:
    if c.get('verified'):
        source = c.get('verification_source', 'unknown')
        verification_sources[source] = verification_sources.get(source, 0) + 1

print(f"\nVerification Sources:")
for source, count in sorted(verification_sources.items(), key=lambda x: x[1], reverse=True):
    print(f"  {source}: {count} citations")

# Categorize by reporter type
reporter_types = {}
for c in citations:
    citation_text = c.get('citation', '')
    
    if 'U.S.' in citation_text:
        rtype = 'U.S. Reports'
    elif 'F.' in citation_text and 'Supp' not in citation_text:
        rtype = 'Federal Reporter'
    elif 'F. Supp' in citation_text:
        rtype = 'Federal Supplement'
    elif 'WL' in citation_text:
        rtype = 'Westlaw'
    elif 'LEXIS' in citation_text:
        rtype = 'LEXIS'
    elif 'Cal.' in citation_text:
        rtype = 'California'
    elif 'N.Y.' in citation_text:
        rtype = 'New York'
    elif 'Ohio' in citation_text:
        rtype = 'Ohio'
    elif 'Wn.' in citation_text or 'Wash.' in citation_text:
        rtype = 'Washington'
    elif any(x in citation_text for x in ['P.', 'A.', 'N.E.', 'S.E.', 'So.', 'S.W.', 'N.W.']):
        rtype = 'Regional Reporter'
    else:
        rtype = 'Other'
    
    reporter_types[rtype] = reporter_types.get(rtype, 0) + 1

print(f"\nCitations by Reporter Type:")
for rtype, count in sorted(reporter_types.items(), key=lambda x: x[1], reverse=True):
    print(f"  {rtype}: {count}")

# Sample of extracted citations
print(f"\nSample Citations (first 10):")
for i, c in enumerate(citations[:10], 1):
    cit = c.get('citation', 'N/A')
    name = c.get('extracted_case_name', 'N/A')
    verified = '[V]' if c.get('verified') else '[ ]'
    print(f"  {i:2}. {verified} {cit:30} - {name[:40]}")

# Check for fallback verification specifically
print(f"\n{'='*80}")
print("FALLBACK VERIFICATION CHECK")
print("="*80)

# Fallback should be used when CourtListener returns 404
fallback_used = any(c.get('verification_source') == 'fallback' for c in citations)
print(f"\nFallback verifier used: {'YES' if fallback_used else 'NO'}")

if fallback_used:
    fallback_citations = [c for c in citations if c.get('verification_source') == 'fallback']
    print(f"Fallback verified citations: {len(fallback_citations)}")
    print(f"\nExamples:")
    for c in fallback_citations[:5]:
        print(f"  - {c.get('citation')} : {c.get('canonical_name', 'N/A')}")

print(f"\n{'='*80}")
print("TEST COMPLETE")
print("="*80)
