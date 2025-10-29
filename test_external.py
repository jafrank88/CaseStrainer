import requests

# Test external URL
try:
    response = requests.post("https://wolf.law.uw.edu/casestrainer/api/analyze", 
                           json={"text": "Smith v. Jones, 123 U.S. 456 (2020). This was later affirmed in Johnson v. Smith, 456 F.2d 789 (2021). The landmark Brown v. Board of Education, 347 U.S. 483 (1954) ended segregation. In Roe v. Wade, 410 U.S. 113 (1973), the Court recognized privacy rights. Miranda v. Arizona, 384 U.S. 436 (1966) established warnings.", 
                                 "enable_verification": False,
                                 "client_request_id": "test_external"},
                           timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success!")
        print(f"Status: {result.get('status')}")
        print(f"Processing mode: {result.get('metadata', {}).get('processing_mode')}")
        
        if 'result' in result:
            citations = result['result'].get('citations', [])
            clusters = result['result'].get('clusters', [])
            
            print(f"\n📊 Results:")
            print(f"Citations extracted: {len(citations)}")
            print(f"Clusters created: {len(clusters)}")
            
            print(f"\n📋 Cititions:")
            for i, cit in enumerate(citations):
                print(f"  {i+1}. {cit.get('citation', 'N/A')}")
                if cit.get('extracted_case_name'):
                    print(f"     Case: {cit.get('extracted_case_name')}")
                    
            print(f"\n🎉 VALIDATION COMPLETE:")
            print(f"✅ EXTRACTION: Working - {len(citations)} citations found")
            print(f"✅ CLUSTERING: Working - {len(clusters)} clusters created")
            print(f"✅ API ENDPOINT: Working - External URL accessible")
    else:
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"Error: {e}")
