"""
Get detailed opinion information for the date mismatch issue
"""

import requests
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('D:/dev/casestrainer/.env')
api_key = os.getenv('COURTLISTENER_API_KEY')

print("=" * 80)
print("GETTING DETAILED OPINION INFORMATION")
print("=" * 80)

# The opinion ID from the URL
opinion_id = 8441217

# Get detailed opinion info
detail_url = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"

print(f"\nFetching opinion details for ID: {opinion_id}")

try:
    response = requests.get(detail_url, headers={'Authorization': f'Token {api_key}'})
    
    if response.status_code == 200:
        opinion = response.json()
        
        print("\nDetailed Opinion Information:")
        print("-" * 40)
        print(f"Case name: {opinion.get('case_name', 'N/A')}")
        print(f"Date filed: {opinion.get('date_filed', 'N/A')}")
        print(f"Date created: {opinion.get('date_created', 'N/A')}")
        print(f"Date modified: {opinion.get('date_modified', 'N/A')}")
        print(f"Author: {opinion.get('author', 'N/A')}")
        print(f"Type: {opinion.get('type', 'N/A')}")
        print(f"Precedential: {opinion.get('precedential_status', 'N/A')}")
        
        # Check citations
        citations = opinion.get('citations', [])
        print(f"\nCitations ({len(citations)}):")
        for cit in citations:
            print(f"  - {cit.get('volume', '')} {cit.get('reporter', '')} {cit.get('page', '')} ({cit.get('date_created', 'N/A')})")
        
        # Check cluster info
        cluster_url = opinion.get('cluster')
        if cluster_url:
            print(f"\nFetching cluster information...")
            cluster_response = requests.get(cluster_url, headers={'Authorization': f'Token {api_key}'})
            
            if cluster_response.status_code == 200:
                cluster = cluster_response.json()
                print(f"Cluster date filed: {cluster.get('date_filed', 'N/A')}")
                print(f"Scdb decision date: {cluster.get('scdb_decision_date', 'N/A')}")
                print(f"Other dates: {cluster.get('other_dates', 'N/A')}")
                
    else:
        print(f"Error fetching opinion: {response.status_code}")
        
except Exception as e:
    print(f"Exception: {e}")

print("\n" + "=" * 80)
print("KEY FINDINGS:")
print("-" * 40)
print("1. The opinion has multiple citations including '2012 WL 10972'")
print("2. The main opinion date is 2012, but there might be an amendment")
print("3. Need to check if there's an amended opinion with a different date")
print("=" * 80)
