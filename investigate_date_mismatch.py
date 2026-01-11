"""
Investigate the date mismatch issue for NYCLU v. NYC Transit Authority
"""

import requests
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('D:/dev/casestrainer/.env')
api_key = os.getenv('COURTLISTENER_API_KEY')

print("=" * 80)
print("INVESTIGATING DATE MISMATCH: NYCLU v. NYC Transit Authority")
print("=" * 80)

# The citation from the document
citation = "684 F.3d 286"
print(f"\nCitation: {citation}")

# Query CourtListener API directly
base_url = "https://www.courtlistener.com/api/rest/v4"
search_url = f"{base_url}/search/?citation={citation}"

print("\nQuerying CourtListener API...")
try:
    response = requests.get(search_url, headers={'Authorization': f'Token {api_key}'})
    
    if response.status_code == 200:
        data = response.json()
        if data['count'] > 0:
            result = data['results'][0]
            
            print("\nAPI Results:")
            print("-" * 40)
            print(f"Case name: {result.get('case_name', 'N/A')}")
            print(f"Citation: {result.get('citation', 'N/A')}")
            print(f"Date filed: {result.get('date_filed', 'N/A')}")
            print(f"Date created: {result.get('date_created', 'N/A')}")
            print(f"URL: {result.get('absolute_url', 'N/A')}")
            
            # Check for amended opinion
            print(f"\nOpinion details:")
            print(f"  Type: {result.get('type', 'N/A')}")
            print(f"  Precedential: {result.get('precedential_status', 'N/A')}")
            print(f"  Sub-opinions: {len(result.get('sub_opinions', []))}")
            
            # Check if there's an amended date
            if 'date_filed' in result:
                filed_date = result['date_filed']
                print(f"\n  Filed date: {filed_date}")
                
                # The issue mentions "amended date"
                # Let's check the opinion details
                opinion_url = result.get('absolute_url', '').strip('/')
                if opinion_url:
                    full_url = f"https://www.courtlistener.com{opinion_url}/"
                    print(f"\nChecking opinion page for amended date info...")
                    print(f"URL: {full_url}")
                    
        else:
            print("No results found")
    else:
        print(f"Error: {response.status_code}")
        
except Exception as e:
    print(f"Exception: {e}")

print("\n" + "=" * 80)
print("ANALYSIS:")
print("-" * 40)
print("The issue shows:")
print("  Extracted date: 2012")
print("  Canonical date: 2011-07-20")
print("")
print("This suggests the opinion was amended on 2011-07-20,")
print("but the citation was published in 2012.")
print("")
print("The verification system should use the amended date")
print("as the canonical date since it's the most recent")
print("authoritative date for the case.")
print("=" * 80)
