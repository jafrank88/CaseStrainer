"""
Test the exact URL from the user
"""

from src.progress_manager import fetch_url_content

url = "https://www.courtlistener.com/opinion/10320728/grace-v-perkins-restaurant/"

print("="*80)
print("TESTING EXACT URL")
print("="*80)
print(f"\nURL: {url}")
print("\nFetching content...")

try:
    content = fetch_url_content(url)
    
    print(f"\n✓ Success!")
    print(f"  Content length: {len(content):,} characters")
    print(f"\nFirst 500 characters:")
    print("-"*80)
    print(content[:500])
    print("\n" + "-"*80)
    print(f"\nLast 500 characters:")
    print("-"*80)
    print(content[-500:])
    
    # Check what we got
    print("\n" + "="*80)
    print("CONTENT ANALYSIS")
    print("="*80)
    
    # Is it JSON?
    import json
    try:
        data = json.loads(content)
        print(f"\n✓ Content is JSON")
        print(f"  Keys: {list(data.keys())[:10]}")
        
        if 'plain_text' in data:
            text_len = len(data['plain_text'])
            print(f"\n✓ Has 'plain_text' field: {text_len:,} characters")
            print(f"\nFirst 300 chars of plain_text:")
            print(data['plain_text'][:300])
            
        if 'html' in data:
            print(f"\n✓ Has 'html' field")
            
        if 'case_name' in data:
            print(f"\n✓ Case name: {data['case_name']}")
            
    except json.JSONDecodeError:
        print(f"\n✗ Content is NOT JSON (probably HTML)")
        
        # Check if it's the bot challenge
        if 'JavaScript is disabled' in content:
            print(f"  ⚠️  Got bot challenge page")
        elif '<html' in content.lower():
            print(f"  Content is HTML")
            
            # Try to extract some info
            import re
            title = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
            if title:
                print(f"  Page title: {title.group(1)}")
        else:
            print(f"  Content type unknown")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
