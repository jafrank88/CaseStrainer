"""
Check how Grace v. Perkins Restaurant should be cited
vs what citations it contains
"""

import requests
from src.config import COURTLISTENER_API_KEY

print("="*80)
print("GRACE V. PERKINS - CITATION FORMAT CHECK")
print("="*80)

# Get the opinion cluster (case metadata)
opinion_id = "10320728"

# First, get the opinion to find its cluster
print(f"\n1. Getting opinion {opinion_id}...")
headers = {
    'Authorization': f'Token {COURTLISTENER_API_KEY}',
    'Accept': 'application/json'
}

opinion_url = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"
response = requests.get(opinion_url, headers=headers, timeout=30)
data = response.json()

cluster_url = data.get('cluster')
print(f"   Cluster URL: {cluster_url}")

# Get the cluster to see all citations for this case
if cluster_url:
    print(f"\n2. Getting cluster data...")
    # Extract cluster ID from URL
    import re
    cluster_match = re.search(r'/clusters/(\d+)/', cluster_url)
    if cluster_match:
        cluster_id = cluster_match.group(1)
        cluster_api_url = f"https://www.courtlistener.com/api/rest/v4/clusters/{cluster_id}/"
        
        response = requests.get(cluster_api_url, headers=headers, timeout=30)
        cluster_data = response.json()
        
        print(f"   Case Name: {cluster_data.get('case_name', 'N/A')}")
        print(f"   Date Filed: {cluster_data.get('date_filed', 'N/A')}")
        print(f"   Court: {cluster_data.get('court', 'N/A')}")
        
        # Get all citations for this case
        citations = cluster_data.get('citations', [])
        print(f"\n3. How to cite this case (parallel citations):")
        print(f"   Total citation formats: {len(citations)}")
        
        for cit in citations:
            cit_type = cit.get('type', 'N/A')
            volume = cit.get('volume', '')
            reporter = cit.get('reporter', '')
            page = cit.get('page', '')
            
            # Show both the structured data and how it appears
            print(f"\n   Type: {cit_type}")
            print(f"     Volume: {volume}")
            print(f"     Reporter: {reporter}")
            print(f"     Page: {page}")
            print(f"     Format: {volume} {reporter} {page}")
            
        # Check if any use dash format
        print(f"\n4. Checking for dash-separated format in CourtListener data...")
        has_dash = any('-' in str(c.get('reporter', '')) or '-' in str(c.get('volume', '')) for c in citations)
        print(f"   Uses dashes: {has_dash}")
        
        # The actual web URL for this case
        absolute_url = cluster_data.get('absolute_url', '')
        if absolute_url:
            web_url = f"https://www.courtlistener.com{absolute_url}"
            print(f"\n5. Web URL: {web_url}")
            
            # Fetch the HTML page to see how it displays
            print(f"\n6. Checking web page HTML...")
            web_response = requests.get(web_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
            html_content = web_response.text
            
            # Look for citation patterns in the HTML
            import re
            dash_cits = re.findall(r'\b\d{1,5}-[A-Z][A-Za-z\.]+(?:\s*\d[a-z]{0,2})?-\d{1,12}\b', html_content)
            space_ohio = re.findall(r'\b\d{1,5}\s+Ohio\s+St\.[^\d]*\d{1,12}\b', html_content)
            
            print(f"   Dash-separated citations in HTML: {len(dash_cits)}")
            if dash_cits:
                for d in dash_cits[:5]:
                    print(f"     - {d}")
                    
            print(f"   Space-separated Ohio in HTML: {len(space_ohio)}")
            if space_ohio:
                for s in space_ohio[:5]:
                    print(f"     - {s}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
