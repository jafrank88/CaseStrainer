"""
Test the backend API to verify extraction results are correct.
Tests case names, years, and citations.
"""

import requests
import json
import time

BASE_URL = "https://wolf.law.uw.edu/casestrainer/api"

# Test text with known citations
TEST_TEXT = """
In Smith v. Jones, 500 U.S. 123 (1991), the Supreme Court held that federal courts
have jurisdiction over such matters. This principle was reaffirmed in Johnson v. 
Texas, 509 U.S. 350 (1993), where the Court emphasized the importance of due process.

The Ninth Circuit addressed similar issues in Brown v. California, 123 F.3d 456 
(9th Cir. 1997). See also Garcia v. United States, 469 U.S. 70 (1984), which 
established the foundational framework.

In Washington state courts, the holding in State v. Gregory, 192 Wn.2d 1 (2018)
is particularly relevant. The court cited Bostain v. Food Express, Inc., 159 Wn.2d 
700, 153 P.3d 846 (2007), as precedent.
"""

# Expected extractions for validation
EXPECTED_CITATIONS = [
    {"citation": "500 U.S. 123", "expected_year": "1991", "expected_name_contains": "Smith"},
    {"citation": "509 U.S. 350", "expected_year": "1993", "expected_name_contains": "Johnson"},
    {"citation": "123 F.3d 456", "expected_year": "1997", "expected_name_contains": "Brown"},
    {"citation": "469 U.S. 70", "expected_year": "1984", "expected_name_contains": "Garcia"},
    {"citation": "192 Wn.2d 1", "expected_year": "2018", "expected_name_contains": "Gregory"},
    {"citation": "159 Wn.2d 700", "expected_year": "2007", "expected_name_contains": "Bostain"},
    {"citation": "153 P.3d 846", "expected_year": "2007", "expected_name_contains": "Bostain"},
]

def submit_text(text):
    """Submit text to the API and return task_id."""
    url = f"{BASE_URL}/analyze"
    data = {"text": text, "type": "text"}
    
    print(f"Submitting text ({len(text)} chars) to {url}...")
    response = requests.post(url, data=data, timeout=30)
    
    if response.status_code != 200:
        print(f"Error: HTTP {response.status_code}")
        print(response.text)
        return None
    
    result = response.json()
    task_id = result.get("task_id")
    print(f"Task ID: {task_id}")
    return task_id


def poll_for_result(task_id, max_wait=180):
    """Poll for task completion."""
    url = f"{BASE_URL}/task_status/{task_id}"
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"Poll error: HTTP {response.status_code}")
            time.sleep(2)
            continue
        
        result = response.json()
        status = result.get("status", "")
        is_finished = result.get("is_finished", False)
        
        if is_finished or status == "completed":
            return result
        
        # Check for errors
        metadata = result.get("metadata", {})
        pipeline_meta = metadata.get("pipeline_metadata", {})
        if pipeline_meta.get("status") == "failed":
            print(f"Pipeline failed: {pipeline_meta.get('error')}")
            return result
        
        elapsed = int(time.time() - start_time)
        print(f"  Waiting... ({elapsed}s) status={status}")
        time.sleep(3)
    
    print(f"Timeout after {max_wait}s")
    return None


def validate_results(result):
    """Validate extraction results against expected values."""
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    
    # Check for errors first
    metadata = result.get("metadata", {})
    pipeline_meta = metadata.get("pipeline_metadata", {})
    
    if pipeline_meta.get("status") == "failed":
        print(f"\n[FAIL] Pipeline failed with error: {pipeline_meta.get('error')}")
        errors = pipeline_meta.get("errors", [])
        for err in errors:
            print(f"  - {err}")
        return False
    
    citations = result.get("citations", [])
    clusters = result.get("clusters", [])
    
    print(f"\nFound {len(citations)} citations, {len(clusters)} clusters")
    
    if len(citations) == 0:
        print("[FAIL] No citations extracted!")
        return False
    
    # Build a lookup for extracted citations
    extracted = {}
    for cit in citations:
        cit_text = cit.get("citation", "")
        extracted[cit_text] = cit
    
    all_passed = True
    
    print("\n--- Citation Validation ---\n")
    
    for expected in EXPECTED_CITATIONS:
        cit_text = expected["citation"]
        expected_year = expected["expected_year"]
        expected_name = expected["expected_name_contains"]
        
        # Find matching citation
        found = None
        for key in extracted:
            if cit_text in key or key in cit_text:
                found = extracted[key]
                break
        
        if not found:
            print(f"[FAIL] Citation not found: {cit_text}")
            all_passed = False
            continue
        
        # Check extracted data
        ext_name = found.get("extracted_case_name") or found.get("case_name") or "N/A"
        ext_year = found.get("extracted_year") or found.get("extracted_date") or found.get("year") or "N/A"
        canonical_name = found.get("canonical_name")
        canonical_date = found.get("canonical_date")
        
        print(f"Citation: {cit_text}")
        print(f"  Extracted Name: {ext_name}")
        print(f"  Extracted Year: {ext_year}")
        print(f"  Canonical Name: {canonical_name}")
        print(f"  Canonical Date: {canonical_date}")
        
        # Validate year
        year_ok = str(expected_year) in str(ext_year) if ext_year and ext_year != "N/A" else False
        if year_ok:
            print(f"  [OK] Year matches expected ({expected_year})")
        else:
            print(f"  [FAIL] Year mismatch - expected {expected_year}, got {ext_year}")
            all_passed = False
        
        # Validate name contains expected party
        name_ok = expected_name.lower() in str(ext_name).lower() if ext_name and ext_name != "N/A" else False
        if name_ok:
            print(f"  [OK] Name contains '{expected_name}'")
        else:
            print(f"  [FAIL] Name '{ext_name}' doesn't contain '{expected_name}'")
            all_passed = False
        
        # Check for contamination (canonical should differ from extracted or be None)
        if canonical_name and canonical_name == ext_name:
            source = found.get("source", "")
            verified = found.get("verified", False)
            if not verified and source in ["extraction_only", "fallback"]:
                print(f"  [WARN] Potential contamination: canonical equals extracted")
        
        print()
    
    # Print summary
    print("=" * 70)
    if all_passed:
        print("[PASS] All validations passed!")
    else:
        print("[FAIL] Some validations failed - see above")
    print("=" * 70)
    
    return all_passed


def main():
    print("=" * 70)
    print("BACKEND EXTRACTION TEST")
    print("=" * 70)
    
    # Submit text
    task_id = submit_text(TEST_TEXT)
    if not task_id:
        print("[FAIL] Failed to submit text")
        return False
    
    # Poll for result
    print("\nPolling for results...")
    result = poll_for_result(task_id)
    
    if not result:
        print("[FAIL] Failed to get result")
        return False
    
    # Save raw result for debugging
    with open("test_backend_result.json", "w") as f:
        json.dump(result, f, indent=2, default=str)
    print("\nRaw result saved to test_backend_result.json")
    
    # Validate
    return validate_results(result)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
