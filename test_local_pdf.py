#!/usr/bin/env python
"""Test local PDF processing"""
import sys
sys.path.insert(0, 'd:/dev/casestrainer')

from src.unified_input_processor import UnifiedInputProcessor

pdf_path = r"D:\dev\casestrainer\1034300.pdf"
request_id = "test-local-pdf"

print(f"Testing local PDF: {pdf_path}")
print("=" * 60)

processor = UnifiedInputProcessor()

# Read the PDF as binary
with open(pdf_path, 'rb') as f:
    pdf_data = f.read()
    print(f"✅ PDF loaded: {len(pdf_data)} bytes")

# Process as file input
print("\n🔄 Processing PDF...")
result = processor.process_any_input(pdf_data, 'file', request_id, source_name='1034300.pdf')

print("\n📊 RESULTS:")
print(f"  Success: {result.get('success', False)}")
print(f"  Citations found: {len(result.get('citations', []))}")
print(f"  Clusters found: {len(result.get('clusters', []))}")
print(f"  Processing mode: {result.get('processing_mode', 'unknown')}")

if result.get('citations'):
    print(f"\n✅ First 5 citations:")
    for i, cit in enumerate(result['citations'][:5], 1):
        print(f"  {i}. {cit.get('citation', 'N/A')}")
else:
    print("\n❌ NO CITATIONS FOUND")
    if result.get('error'):
        print(f"  Error: {result['error']}")
