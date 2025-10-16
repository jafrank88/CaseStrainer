"""
Test URL content extraction from CourtListener
"""

from src.progress_manager import fetch_url_content

url = "https://www.courtlistener.com/opinion/10320728/"

print(f"Fetching content from: {url}")
print("="*80)

try:
    content = fetch_url_content(url)
    
    print(f"Content length: {len(content)} characters")
    print("="*80)
    print("\nFirst 500 characters:")
    print(content[:500])
    print("\n" + "="*80)
    print("\nLast 500 characters:")
    print(content[-500:])
    print("\n" + "="*80)
    
    # Check for citations
    import re
    federal_pattern = r'\d+\s+F\.\s*(?:2d|3d|4th|Supp\.|App\'x)\s+\d+'
    us_pattern = r'\d+\s+U\.S\.\s+\d+'
    
    federal_citations = re.findall(federal_pattern, content)
    us_citations = re.findall(us_pattern, content)
    
    print(f"\nFederal citations found: {len(federal_citations)}")
    if federal_citations[:5]:
        print(f"  Examples: {federal_citations[:5]}")
    
    print(f"\nU.S. citations found: {len(us_citations)}")
    if us_citations[:5]:
        print(f"  Examples: {us_citations[:5]}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
