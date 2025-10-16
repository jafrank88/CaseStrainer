#!/usr/bin/env python
"""Test URL processing inside Docker"""
from src.unified_input_processor import UnifiedInputProcessor

url = "https://www.courts.wa.gov/opinions/pdf/1034300.pdf"
request_id = "docker-test"

print(f"Testing URL: {url}")
print("=" * 60)

processor = UnifiedInputProcessor()
result = processor.process_any_input(url, 'url', request_id)

print(f"\n📊 RESULTS:")
print(f"  Success: {result.get('success')}")
print(f"  Error: {result.get('error', 'None')}")
print(f"  Citations: {len(result.get('citations', []))}")
print(f"  Clusters: {len(result.get('clusters', []))}")

# Check what metadata says
metadata = result.get('metadata', {})
print(f"\n📋 METADATA:")
print(f"  Text length: {metadata.get('text_length', 'N/A')}")
print(f"  Content length: {metadata.get('content_length', 'N/A')}")
print(f"  Input type: {metadata.get('input_type', 'N/A')}")
print(f"  URL domain: {metadata.get('url_domain', 'N/A')}")

if result.get('citations'):
    print(f"\n✅ First 3 citations:")
    for i, cit in enumerate(result['citations'][:3], 1):
        print(f"  {i}. {cit.get('citation', 'N/A')}")
