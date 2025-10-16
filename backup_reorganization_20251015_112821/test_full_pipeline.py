#!/usr/bin/env python3
"""
Test the full pipeline to see where truncation happens
"""
import sys
import os

# Force UTF-8 encoding for output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Read the PDF
pdf_path = "25-2808.pdf"

print("Step 1: Extract text from PDF...")
from document_processing_unified import UnifiedDocumentProcessor
processor = UnifiedDocumentProcessor()
text = processor.extract_text_from_file(pdf_path)
print(f"  Extracted {len(text)} characters\n")

# Check if specific case names are in the text
print("Step 2: Verify case names in extracted text...")
test_cases = [
    "Department of Education v. California",
    "E. Palo Alto v. U.S.",
    "Tootle v. Sec'y of Navy"
]
for case in test_cases:
    found = case in text
    print(f"  {'✓' if found else '✗'} '{case}' in text: {found}")
print()

# Now process with the citation processor
print("Step 3: Process with UnifiedCitationProcessorV2...")
from unified_citation_processor_v2 import UnifiedCitationProcessorV2
import asyncio

async def process():
    processor = UnifiedCitationProcessorV2()
    result = await processor.process_text(text)
    return result

result = asyncio.run(process())
print(f"  Found {len(result['citations'])} citations\n")

# Check specific citations
print("Step 4: Check extracted case names...")
target_citations = ["604 U.S. 650", "780 F. Supp. 3d 897", "446 F.3d 167"]
for target in target_citations:
    matching = [c for c in result['citations'] if target in c.citation]
    if matching:
        c = matching[0]
        print(f"  Citation: {c.citation}")
        print(f"    Extracted: '{getattr(c, 'extracted_case_name', 'N/A')}'")
        print(f"    Method: {getattr(c, 'method', 'unknown')}")
    else:
        print(f"  ✗ Citation {target} not found")
    print()
