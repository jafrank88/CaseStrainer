"""
Check the specific cases from the user's frontend against the network response
"""

# From the network response provided, let me extract the relevant cases

# Case 1: Erickson v. Pharmacia (548 P.3d 226)
print("=" * 80)
print("Case 1: Erickson v. Pharmacia")
print("=" * 80)
print("""
From network response - Citation: 548 P.3d 226
{
    "canonical_date": null,
    "canonical_name": null,
    "canonical_url": null,
    "case_name": "Erickson v. Pharmacia",
    "citation": "548 P.3d 226",
    "extracted_case_name": "N/A",
    "extracted_date": "2024",
    "name_mismatch": false,  # ← Backend says FALSE!
    "verified": false
}

And from the clusters section:
{
    "cluster_case_name": "N/A",
    "has_name_mismatch": false,  # ← Cluster level also FALSE!
}

❓ QUESTION: Why is frontend showing "⚠️ Different name" when backend says false?
""")

# Case 2: Singh v. Edwards Lifesciences Corp. (151 Wn. App. 137)
print("\n" + "=" * 80)
print("Case 2: Singh v. Edwards Lifesciences Corp.")
print("=" * 80)
print("""
This case is NOT in the provided network response JSON!
The response contains 139 citations but Singh v. Edwards is not one of them.

This suggests the user is looking at a DIFFERENT document/response than the
network response JSON they provided.
""")

# Case 3: Kammerer v. Western Gear (96 Wn.2d 416) 
print("\n" + "=" * 80)
print("Case 3: Kammerer v. Western Gear")
print("=" * 80)
print("""
This case is also NOT in the provided network response JSON!
""")

# Case 4: Erwin v. Cotter Health Centers (161 Wn.2d 676)
print("\n" + "=" * 80)
print("Case 4: Erwin v. Cotter Health Centers")
print("=" * 80)
print("""
From network response - Citation: 161 Wn.2d 676
{
    "canonical_date": "2007-09-20",
    "canonical_name": "Erwin v. Cotter Health Centers, Inc.",
    "case_name": "Erwin v. Cotter Health Centers, Inc.",
    "citation": "161 Wn.2d 676",
    "extracted_case_name": "N/A",  # ← Extraction FAILED!
    "extracted_date": "2007",
    "name_mismatch": true,  # ← Backend says TRUE (because extracted is N/A)
    "possible_match": true,
    "verified": true
}

✅ Backend is CORRECT to flag this:
   - Canonical name: "Erwin v. Cotter Health Centers, Inc."
   - Extracted name: "N/A" (extraction failed)
   - This is a legitimate mismatch

But the frontend display shows:
   "Extracted from Document: Erwin v. Cotter Health Centers, Inc., 2007"
   
❓ QUESTION: Where is the frontend getting this extracted name if backend says "N/A"?
""")

print("\n" + "=" * 80)
print("CRITICAL DISCOVERY")
print("=" * 80)
print("""
The frontend display of "Extracted from Document: [case name]" does NOT match
what the backend is actually sending in extracted_case_name field!

HYPOTHESIS 1: Frontend is displaying CLUSTER_CASE_NAME instead of individual
citation extracted_case_name

HYPOTHESIS 2: Frontend is doing its own name extraction/display logic separate
from backend processing

HYPOTHESIS 3: User is looking at a different response than the JSON provided

NEXT STEP: Need to see the actual frontend code that displays these warnings
to understand where it's getting the "Extracted from Document" text.
""")
