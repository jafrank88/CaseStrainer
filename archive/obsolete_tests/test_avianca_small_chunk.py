import requests
import time

# Base URL for the API
BASE_URL = "https://wolf.law.uw.edu/casestrainer"


def test_avianca_small_chunk():
    """Test analyzing a small chunk of the Avianca sanctions opinion."""
    print("\n=== TESTING AVIANCA SANCTIONS OPINION (SMALL CHUNK) ===")

    # Create a small test sample with citations
    test_text = """
    UNITED STATES DISTRICT COURT
    SOUTHERN DISTRICT OF NEW YORK
    
    ROBERTO MATA,
    Plaintiff,
    v.
    AVIANCA, INC.,
    Defendant.
    
    20-CV-10924 (LJL)
    
    OPINION AND ORDER
    
    LEWIS J. LIMAN, United States District Judge:
    
    This case involves straightforward claims by Plaintiff Roberto Mata ("Plaintiff" or "Mata") that he was injured when a metal serving cart struck his knee during a flight on an aircraft operated by Defendant Avianca, Inc. ("Defendant" or "Avianca"). What makes the case exceptional is not the facts but what has happened in the litigation.
    
    The Court is presented with a motion for sanctions pursuant to Federal Rule of Civil Procedure 11 and the Court's inherent power. The motion is based on the fact that Plaintiff's counsel, Peter LoDuca, Esq. and his firm, Kreindler & Kreindler LLP (together, "Plaintiff's Counsel"), working with ChatGPT, an artificial intelligence ("AI") chatbot, submitted a brief that relied on numerous fake judicial decisions with fake quotes and fake internal citations.
    
    For the reasons that follow, the motion is granted.
    
    BACKGROUND
    
    I. The Complaint and the Motion to Dismiss
    
    Plaintiff filed the complaint in this action on December 23, 2020. Dkt. No. 1. The complaint alleges that on August 27, 2019, Plaintiff was a passenger on Avianca Flight 670 from El Salvador to New York. Id. ¶ 7. During the flight, a metal serving cart struck Plaintiff's knee, causing injury. Id. ¶ 8. The complaint asserts claims for negligence, id. ¶¶ 9–13, and for negligent design, selection, and maintenance of the serving cart, id. ¶¶ 14–16.
    
    On February 23, 2021, Defendant filed a motion to dismiss. Dkt. No. 10. Defendant argued that the claims were preempted by the Montreal Convention, which governs international air travel. See Convention for the Unification of Certain Rules for International Carriage by Air, May 28, 1999, S. Treaty Doc. No. 106-45, 2242 U.N.T.S. 309 (the "Montreal Convention").
    
    In Martinez v. Delta Airlines, Inc., 390 F. Supp. 3d 1141 (D. Alaska 2005), the court held that claims similar to those here were preempted by the Montreal Convention. The court in Varghese v. China Southern Airlines Co., 925 F.3d 1339 (9th Cir. 2019) also addressed preemption under the Montreal Convention.
    
    The Supreme Court has addressed similar issues in El Al Israel Airlines, Ltd. v. Tseng, 525 U.S. 155 (1999) and Zicherman v. Korean Air Lines Co., 516 U.S. 217 (1996).
    """

    # Now analyze the text
    print("Submitting small text sample for citation analysis...")
    response = requests.post(f"{BASE_URL}/api/analyze", data={"text": test_text})

    if response.status_code != 200:
        print(f"Error analyzing text: {response.status_code} - {response.text}")
        return False

    print(f"Text analysis response status: {response.status_code}")

    try:
        analysis_result = response.json()
        print(f"Analysis ID: {analysis_result.get('analysis_id')}")
        print(f"Citations found: {analysis_result.get('citations_count')}")
    except Exception as e:
        print(f"Could not parse JSON response for analysis: {str(e)}")
        return False

    # Give the server some time to process
    print("\nWaiting for processing to complete...")
    time.sleep(10)

    # Check all tabs
    print("\n--- Checking CourtListener Citations Tab ---")
    check_courtlistener_citations()

    print("\n--- Checking Verified Citations Tab ---")
    check_verified_citations()

    print("\n--- Checking Unconfirmed Citations Tab ---")
    check_unconfirmed_citations()

    print("\n--- Checking CourtListener Gaps Tab ---")
    check_courtlistener_gaps()

    return True


def check_courtlistener_citations():
    """Check the CourtListener Citations tab."""
    response = requests.get(f"{BASE_URL}/api/courtlistener_citations")

    if response.status_code != 200:
        print(
            f"Error getting CourtListener citations: {response.status_code} - {response.text}"
        )
        return False

    try:
        result = response.json()
        citations = result.get("citations", [])
        print(f"Found {len(citations)} CourtListener citations")

        # Print all citations
        for i, citation in enumerate(citations):
            print(
                f"  {i+1}. {citation.get('citation_text', 'Unknown')} - {citation.get('case_name', 'Unknown')}"
            )
            if citation.get("url"):
                print(f"     URL: {citation.get('url')}")
    except Exception as e:
        print(f"Could not parse JSON response: {str(e)}")
        return False

    return True


def check_verified_citations():
    """Check the Verified Citations tab."""
    response = requests.get(f"{BASE_URL}/api/confirmed_with_multitool_data")

    if response.status_code != 200:
        print(
            f"Error getting verified citations: {response.status_code} - {response.text}"
        )
        return False

    try:
        result = response.json()
        citations = result.get("citations", [])
        print(f"Found {len(citations)} verified citations")

        # Print first few citations
        for i, citation in enumerate(citations[:10]):
            print(
                f"  {i+1}. {citation.get('citation_text', 'Unknown')} - {citation.get('case_name', 'Unknown')}"
            )
            print(f"     Source: {citation.get('source', 'Unknown')}")

        if len(citations) > 10:
            print(f"  ... and {len(citations) - 10} more")
    except Exception as e:
        print(f"Could not parse JSON response: {str(e)}")
        return False

    return True


def check_unconfirmed_citations():
    """Check the Unconfirmed Citations tab."""
    response = requests.get(f"{BASE_URL}/api/unconfirmed_citations_data")

    if response.status_code != 200:
        print(
            f"Error getting unconfirmed citations: {response.status_code} - {response.text}"
        )
        return False

    try:
        result = response.json()
        citations = result.get("citations", [])
        print(f"Found {len(citations)} unconfirmed citations")

        # Print first few citations
        for i, citation in enumerate(citations[:10]):
            print(f"  {i+1}. {citation.get('citation_text', 'Unknown')}")
            print(f"     Source: {citation.get('source', 'Unknown')}")

        if len(citations) > 10:
            print(f"  ... and {len(citations) - 10} more")
    except Exception as e:
        print(f"Could not parse JSON response: {str(e)}")
        return False

    return True


def check_courtlistener_gaps():
    """Check the CourtListener Gaps tab."""
    response = requests.get(f"{BASE_URL}/api/courtlistener_gaps")

    if response.status_code != 200:
        print(
            f"Error getting CourtListener gaps: {response.status_code} - {response.text}"
        )
        return False

    try:
        result = response.json()
        citations = result.get("citations", [])
        print(f"Found {len(citations)} CourtListener gaps")

        # Print all citations
        for i, citation in enumerate(citations):
            print(f"  {i+1}. {citation.get('citation_text', 'Unknown')}")
            print(f"     Source: {citation.get('source', 'Unknown')}")
    except Exception as e:
        print(f"Could not parse JSON response: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    test_avianca_small_chunk()
