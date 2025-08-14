import requests
import json

def test_analyze_endpoint():
    url = "http://localhost:5000/casestrainer/api/analyze"
    headers = {"Content-Type": "application/json"}
    
    # Test with a realistic legal text that includes citations
    test_text = """
    IN THE UNITED STATES COURT OF APPEALS
    FOR THE NINTH CIRCUIT
    
    JOHN DOE, 
    Plaintiff-Appellant,
    
    v. 
    
    JANE SMITH, 
    Defendant-Appellee.
    
    No. 20-12345
    
    Appeal from the United States District Court
    for the Northern District of California
    D.C. No. 3:19-cv-01234-JD
    
    Argued and Submitted: January 15, 2020
    
    Before: THOMAS, Chief Judge, and WARDLAW and HURWITZ, Circuit Judges.
    
    OPINION
    
    HURWITZ, Circuit Judge:
    
    This appeal presents the question of whether the district court properly granted summary judgment to the defendant. 
    
    The Supreme Court has long recognized that "the very essence of civil liberty certainly consists in the right of every individual to claim the protection of the laws, whenever he receives an injury." Marbury v. Madison, 5 U.S. (1 Cranch) 137, 163 (1803). As we explained in Smith v. City of Oakland, 846 F.3d 1010, 1015 (9th Cir. 2017), the standard for summary judgment requires that we view the evidence in the light most favorable to the non-moving party.
    
    The plaintiff relies heavily on our decision in Johnson v. City of Seattle, 474 F.3d 634 (9th Cir. 2007), but that case is readily distinguishable. In Johnson, we held that...
    
    For the foregoing reasons, we AFFIRM the judgment of the district court.
    """
    
    data = {
        "text": test_text,
        "type": "text"
    }
    
    try:
        print("Testing /api/analyze endpoint...")
        response = requests.post(url, json=data, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\nAPI Response:")
            print(json.dumps(result, indent=2))
            
            if 'citations' in result:
                print(f"\nFound {len(result['citations'])} citations:")
                for i, citation in enumerate(result['citations'][:5], 1):  # Show first 5 citations
                    print(f"{i}. {citation.get('citation', 'N/A')} - {citation.get('status', 'N/A')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing API: {str(e)}")

if __name__ == "__main__":
    test_analyze_endpoint()
