#!/usr/bin/env python3
"""
Check for truncated case names in the results
"""
import requests
import sys
import io

# Force UTF-8 encoding for output
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

pdf_path = r"D:\dev\casestrainer\25-2808.pdf"
url = "http://localhost:5000/casestrainer/api/analyze"

print("Uploading PDF and checking for truncations...\n")

with open(pdf_path, 'rb') as f:
    files = {'file': ('25-2808.pdf', f, 'application/pdf')}
    data = {'force_mode': 'sync'}
    
    response = requests.post(url, files=files, data=data, timeout=120)
    result = response.json()
    
    citations = result.get('citations', [])
    
    print(f"Total citations: {len(citations)}\n")
    
    # Check for truncations
    truncated = []
    suspicious = []
    good = []
    
    for i, cit in enumerate(citations, 1):
        name = cit.get('extracted_case_name', 'N/A')
        citation_text = cit.get('citation', '')
        
        # Check for truncation indicators
        is_truncated = False
        is_suspicious = False
        
        # Truncation patterns
        if name and name != 'N/A':
            # Check if ends with single letter (like "U." or "Se")
            if name.strip().endswith(' v. U.') or name.strip().endswith(' v. Se'):
                is_truncated = True
            # Check if very short (< 10 chars)
            elif len(name) < 10:
                is_suspicious = True
            # Check if missing common words
            elif 'Department' in name and 'of' not in name:
                is_suspicious = True
            # Check if ends with abbreviation without period
            elif name.strip().endswith(' v. U') or name.strip().endswith(' v. Se'):
                is_truncated = True
        
        if is_truncated:
            truncated.append((i, citation_text, name))
        elif is_suspicious:
            suspicious.append((i, citation_text, name))
        else:
            good.append((i, citation_text, name))
    
    print("=" * 80)
    print(f"TRUNCATED NAMES ({len(truncated)}):")
    print("=" * 80)
    for i, cit, name in truncated:
        print(f"{i}. {cit}")
        print(f"   Name: '{name}'")
        print()
    
    print("=" * 80)
    print(f"SUSPICIOUS NAMES ({len(suspicious)}):")
    print("=" * 80)
    for i, cit, name in suspicious[:10]:  # Show first 10
        print(f"{i}. {cit}")
        print(f"   Name: '{name}'")
        print()
    
    print("=" * 80)
    print(f"GOOD NAMES ({len(good)}):")
    print("=" * 80)
    for i, cit, name in good[:10]:  # Show first 10
        print(f"{i}. {cit}")
        print(f"   Name: '{name}'")
        print()
    
    print("=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print(f"✅ Good: {len(good)}/{len(citations)} ({len(good)*100//len(citations)}%)")
    print(f"⚠️  Suspicious: {len(suspicious)}/{len(citations)} ({len(suspicious)*100//len(citations)}%)")
    print(f"❌ Truncated: {len(truncated)}/{len(citations)} ({len(truncated)*100//len(citations)}%)")
