"""
Analysis of new 1031351.pdf results after Fix #1 (signal word removal)
Comparing to original results and identifying remaining issues.
"""

import json

# Key statistics comparison
print("=" * 80)
print("STATISTICS COMPARISON")
print("=" * 80)

old_stats = {
    "citations": 139,
    "clusters": 89,
    "verified": 125,
    "unverified": 14,
    "ratio": 1.56
}

new_stats = {
    "citations": 139,
    "clusters": 89,
    "verified": 128,
    "unverified": 11,
    "ratio": 1.56
}

print("\n📊 OVERALL COMPARISON:")
print(f"Citations:  {old_stats['citations']} → {new_stats['citations']} (no change)")
print(f"Clusters:   {old_stats['clusters']} → {new_stats['clusters']} (no change ❌)")
print(f"Verified:   {old_stats['verified']} → {new_stats['verified']} (+3 ✅)")
print(f"Unverified: {old_stats['unverified']} → {new_stats['unverified']} (-3 ✅)")
print(f"Ratio:      {old_stats['ratio']} → {new_stats['ratio']} (no change)")

print("\n" + "=" * 80)
print("FIX #1 IMPACT ANALYSIS")
print("=" * 80)

signal_word_examples = [
    {
        "citation": "11 Wn.2d 288",
        "old_extracted": "also Richardson v. Pac. Power & Light Co.",
        "new_extracted": "Richardson v. Pac. Power & Light Co.",
        "status": "✅ FIXED"
    },
    {
        "citation": "161 Wn.2d 676",
        "old_extracted": "We review choice of law questions de novo. Erwin v. Cotter Health Ctrs., Inc.",
        "new_extracted": "N/A",
        "status": "⚠️ WORSE (was contaminated, now N/A)"
    }
]

print("\n🔧 SIGNAL WORD REMOVAL RESULTS:")
for ex in signal_word_examples:
    print(f"\n{ex['citation']}: {ex['status']}")
    print(f"  OLD: '{ex['old_extracted']}'")
    print(f"  NEW: '{ex['new_extracted']}'")

print("\n" + "=" * 80)
print("CRITICAL ISSUE: PARALLEL CITATION CLUSTERING")
print("=" * 80)

parallel_not_clustered = [
    {
        "case": "Johnson v. Spider Staging Corp.",
        "date": "1976-10-21",
        "citations": ["87 Wn.2d 577", "555 P.2d 997"],
        "status": "Both verified, both have parallel_citations arrays, but NOT clustered",
        "evidence": "parallel_citations: ['555 P.2d 997'] and ['87 Wn.2d 577']"
    },
    {
        "case": "Frye v. United States",
        "date": "1923-12-03",
        "citations": ["54 App. D.C. 46", "293 F. 1013"],
        "status": "Both verified, both have parallel_citations arrays, but NOT clustered",
        "evidence": "parallel_citations: ['293 F. 1013'] and ['54 App. D.C. 46']"
    },
    {
        "case": "Erwin v. Cotter Health Centers",
        "date": "2007-09-20",
        "citations": ["161 Wn.2d 676", "167 P.3d 1112"],
        "status": "Both verified, both have parallel_citations arrays, but NOT clustered",
        "evidence": "Both show extracted_case_name: 'N/A'"
    },
    {
        "case": "Richardson v. Pacific Power & Light Co.",
        "date": "1941-11-21",
        "citations": ["11 Wn.2d 288", "118 P.2d 985"],
        "status": "Both verified, both have parallel_citations arrays, but NOT clustered",
        "evidence": "parallel_citations: ['118 P.2d 985'] and ['11 Wn.2d 288']"
    },
    {
        "case": "Hurtado v. Superior Court",
        "date": "1974-05-31",
        "citations": ["11 Cal. 3d 574", "522 P.2d 666", "114 Cal. Rptr. 106"],
        "status": "THREE citations all verified, all have parallel_citations, NOT clustered",
        "evidence": "All three showing same canonical data but separate clusters"
    }
]

print("\n🚨 PARALLEL CITATIONS NOT BEING CLUSTERED:")
print("\nDESPITE having `parallel_citations` arrays populated!")
print("\nExamples:")
for i, ex in enumerate(parallel_not_clustered, 1):
    print(f"\n{i}. {ex['case']} ({ex['date']})")
    print(f"   Citations: {', '.join(ex['citations'])}")
    print(f"   Status: {ex['status']}")
    print(f"   Evidence: {ex['evidence']}")

print("\n" + "=" * 80)
print("N/A EXTRACTION FAILURES")
print("=" * 80)

na_extractions = [
    {
        "citation": "161 Wn.2d 676",
        "canonical": "Erwin v. Cotter Health Centers, Inc.",
        "verified": True,
        "parallel": "167 P.3d 1112",
        "issue": "Extraction completely failed despite verification success"
    },
    {
        "citation": "167 P.3d 1112",
        "canonical": "Erwin v. Cotter Health Centers",
        "verified": True,
        "parallel": "161 Wn.2d 676",
        "issue": "Extraction completely failed despite verification success"
    },
    {
        "citation": "548 P.3d 226",
        "canonical": "Erickson v. Pharmacia LLC",
        "verified": True,
        "parallel": "31 Wn. App. 2d 100",
        "issue": "Extraction failed, but verification found it (via CaseMine)"
    },
    {
        "citation": "31 Wn. App. 2d 100",
        "canonical": None,
        "verified": False,
        "parallel": "548 P.3d 226",
        "issue": "Extraction failed, verification also failed"
    },
    {
        "citation": "2 Wn.3d 430",
        "canonical": "United States v. Alexander Sittenfeld aka P.G. Sittenfeld",
        "verified": "true_by_parallel",
        "parallel": "539 P.3d 361",
        "issue": "Verified by parallel but extraction still N/A"
    }
]

print("\n⚠️ CITATIONS WITH N/A EXTRACTION:")
print("\nTotal N/A extractions found: 6+")
print("\nDetailed examples:")
for i, na in enumerate(na_extractions, 1):
    print(f"\n{i}. {na['citation']}")
    print(f"   Extracted: N/A")
    print(f"   Canonical: {na['canonical']}")
    print(f"   Verified: {na['verified']}")
    print(f"   Parallel: {na['parallel']}")
    print(f"   Issue: {na['issue']}")

print("\n" + "=" * 80)
print("DATE MISMATCH ANALYSIS")
print("=" * 80)

date_mismatches = [
    {
        "citation": "87 Wn.2d 577",
        "extracted_date": "2024",
        "canonical_date": "1976-10-21",
        "diff_years": 48,
        "case": "Johnson v. Spider Staging Corp."
    },
    {
        "citation": "161 Wn.2d 676",
        "extracted_date": "2024",
        "canonical_date": "2007-09-20",
        "diff_years": 17,
        "case": "Erwin v. Cotter Health Centers, Inc."
    },
    {
        "citation": "11 Wn.2d 288",
        "extracted_date": "2024",
        "canonical_date": "1941-11-21",
        "diff_years": 83,
        "case": "Richardson v. Pacific Power & Light Co."
    }
]

print("\n📅 DATES STILL SHOWING '2024' FOR OLD CASES:")
print("\nThese are NOT code fallbacks - document likely contains '2024' text")
print("\nExamples:")
for dm in date_mismatches:
    print(f"\n{dm['citation']}: {dm['case']}")
    print(f"  Extracted: {dm['extracted_date']}")
    print(f"  Canonical: {dm['canonical_date']}")
    print(f"  Difference: {dm['diff_years']} years")

print("\n" + "=" * 80)
print("CASE NAME MISMATCH ANALYSIS")
print("=" * 80)

mismatch_types = {
    "extraction_failure": [
        {
            "citation": "161 Wn.2d 676",
            "extracted": "N/A",
            "canonical": "Erwin v. Cotter Health Centers, Inc.",
            "type": "Complete extraction failure",
            "root_cause": "Pattern matching or context isolation issue"
        },
        {
            "citation": "167 P.3d 1112",
            "extracted": "N/A",
            "canonical": "Erwin v. Cotter Health Centers",
            "type": "Complete extraction failure",
            "root_cause": "Pattern matching or context isolation issue"
        }
    ],
    "wrong_case_extracted": [
        {
            "citation": "60 P.3d 145",
            "extracted": "Act I, LLC v. Davis",
            "canonical": "ACT I, LLC v. Davis",
            "type": "Capitalization difference",
            "root_cause": "Extraction vs verification data formatting"
        },
        {
            "citation": "130 Wn.2d 244",
            "extracted": "L.M. v. Hamilton",
            "canonical": "State v. Copeland",
            "type": "WRONG CASE NAME extracted",
            "root_cause": "Extracted name from different citation in vicinity"
        },
        {
            "citation": "539 P.3d 361",
            "extracted": "Bennett v. United States",
            "canonical": "United States v. Alexander Sittenfeld aka P.G. Sittenfeld",
            "type": "WRONG CASE NAME extracted",
            "root_cause": "Extracted name from different citation in vicinity"
        }
    ],
    "truncation": [
        {
            "citation": "11 Cal. 3d 574",
            "extracted": "Hurtado v. Superior C",
            "canonical": "Hurtado v. Superior Court",
            "type": "Truncated at word boundary",
            "root_cause": "Pattern capture ended too early"
        }
    ]
}

print("\n🔍 CASE NAME MISMATCHES BY TYPE:")

print("\n1. EXTRACTION FAILURES (N/A):")
for item in mismatch_types["extraction_failure"]:
    print(f"\n   {item['citation']}")
    print(f"   Extracted: {item['extracted']}")
    print(f"   Canonical: {item['canonical']}")
    print(f"   Root Cause: {item['root_cause']}")

print("\n2. WRONG CASE EXTRACTED:")
for item in mismatch_types["wrong_case_extracted"]:
    print(f"\n   {item['citation']}")
    print(f"   Extracted: {item['extracted']}")
    print(f"   Canonical: {item['canonical']}")
    print(f"   Root Cause: {item['root_cause']}")

print("\n3. TRUNCATION:")
for item in mismatch_types["truncation"]:
    print(f"\n   {item['citation']}")
    print(f"   Extracted: {item['extracted']}")
    print(f"   Canonical: {item['canonical']}")
    print(f"   Root Cause: {item['root_cause']}")

print("\n" + "=" * 80)
print("TRUE_BY_PARALLEL / VERIFIED_BY_PARALLEL ANALYSIS")
print("=" * 80)

parallel_verification_examples = [
    {
        "citation": "2 Wn.3d 430",
        "verified": "true_by_parallel",
        "true_by_parallel": True,
        "parallel_citation": "539 P.3d 361 (verified: True)",
        "status": "✅ WORKING - Boolean set correctly"
    },
    {
        "citation": "717 P.3d 1353",
        "canonical": "State v. Johnson",
        "note": "Shows in 'Verified by Parallel' section in UI",
        "status": "✅ WORKING - UI shows parallel verification"
    }
]

print("\n✅ PARALLEL VERIFICATION STATUS:")
print("\nThe 'true_by_parallel' mechanism IS working:")
for ex in parallel_verification_examples:
    print(f"\n{ex['citation']}")
    if 'verified' in ex:
        print(f"  verified: {ex['verified']}")
    if 'true_by_parallel' in ex:
        print(f"  true_by_parallel: {ex['true_by_parallel']}")
    if 'parallel_citation' in ex:
        print(f"  Parallel: {ex['parallel_citation']}")
    print(f"  Status: {ex['status']}")

print("\n⚠️ HOWEVER: Parallel detection is NOT being used for CLUSTERING!")
print("Citations are verified by parallel but remain in separate clusters.")

print("\n" + "=" * 80)
print("SUMMARY OF FINDINGS")
print("=" * 80)

print("""
✅ IMPROVEMENTS FROM FIX #1:
- Signal word "also" removal working: Richardson case now extracts correctly
- Verification rate improved: 125 → 128 verified (+3)
- Unverified count decreased: 14 → 11 (-3)

❌ REMAINING ISSUES:

1. CLUSTERING NOT WORKING (CRITICAL):
   - Still 89 clusters instead of expected ~55-65
   - parallel_citations arrays ARE populated
   - But is_parallel = false and is_in_cluster = false
   - Parallel citations NOT being grouped into single clusters
   - Root Cause: Clustering logic not using parallel_citations metadata

2. N/A EXTRACTIONS (HIGH PRIORITY):
   - Multiple cases: 161 Wn.2d 676, 167 P.3d 1112, etc.
   - Root Cause: Pattern matching not covering all citation contexts
   - Some are in header/footer areas, others are complex formats

3. DATE MISMATCHES (HIGH PRIORITY):
   - Many showing extracted_date="2024" for old cases
   - Root Cause: Document likely written/filed in 2024, extraction picks up year from document header/footer rather than near specific citation

4. WRONG CASE NAME EXTRACTION (MEDIUM):
   - Examples: "130 Wn.2d 244" extracts "L.M. v. Hamilton" but canonical is "State v. Copeland"
   - Root Cause: Context window including nearby citations, extracting wrong name

5. CASE NAME MISMATCHES:
   - Type 1: Extraction failures (N/A) - 6+ cases
   - Type 2: Wrong case extracted - 3+ cases
   - Type 3: Truncation - 2+ cases
   - Root Causes: Mix of extraction issues, not verification issues

✅ PARALLEL VERIFICATION WORKING:
- true_by_parallel boolean correctly set
- UI showing "Verified by Parallel" section
- Metadata properly populated

🔧 PRIORITY FIXES NEEDED:

1. IMMEDIATE: Fix clustering to use parallel_citations metadata
   - Should reduce cluster count from 89 to ~55-60
   - Logic exists to detect parallels but not to cluster them

2. HIGH: Fix N/A extractions
   - Improve pattern matching coverage
   - Reduce aggressive filtering
   - Add fallback extraction patterns

3. HIGH: Fix date extraction accuracy
   - Narrow search window to immediate citation vicinity
   - Don't search broadly across document

4. MEDIUM: Fix wrong case name extraction
   - Improve context isolation
   - Validate extracted name matches citation location
""")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("""
1. Implement clustering fix to use parallel_citations arrays
2. Investigate N/A extraction failures (pattern matching)
3. Narrow date extraction search window
4. Add validation to prevent wrong case name extraction
""")
