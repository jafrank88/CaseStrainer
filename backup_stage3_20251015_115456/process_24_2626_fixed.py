"""
Process 24-2626.pdf with the fixed strict context isolation.
"""

import sys
import os
import json
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 100)
print("PROCESSING 24-2626.pdf WITH STRICT CONTEXT ISOLATION")
print("=" * 100)
print()

# Load PDF
try:
    import PyPDF2
    pdf_path = r'D:\dev\casestrainer\24-2626.pdf'
    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        text = '\n'.join([page.extract_text() for page in pdf.pages])
    print(f"OK Loaded PDF: {len(text)} chars, {len(pdf.pages)} pages")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

print()

# Process
async def process():
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    
    processor = UnifiedCitationProcessorV2()
    result = await processor.process_text(text)
    return result

try:
    result = asyncio.run(process())
    
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f"OK Complete: {len(citations)} citations, {len(clusters)} clusters")
    print()
    
    # Save results
    output_path = r'D:\dev\casestrainer\24-2626_FIXED.json'
    
    # Convert citation objects to dicts
    citations_dicts = []
    for cit in citations:
        if hasattr(cit, '__dict__'):
            cit_dict = {k: v for k, v in cit.__dict__.items() if not k.startswith('_')}
        elif isinstance(cit, dict):
            cit_dict = cit
        else:
            cit_dict = {'citation': str(cit)}
        citations_dicts.append(cit_dict)
    
    result['citations'] = citations_dicts
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"✅ Saved: {output_path}")
    print()
    
    # Show samples
    print("=" * 100)
    print("FIRST 10 EXTRACTIONS:")
    print("=" * 100)
    for i, cit in enumerate(citations_dicts[:10], 1):
        print(f"\n{i}. {cit.get('citation')}")
        print(f"   Extracted: {cit.get('extracted_case_name', 'N/A')}")
        print(f"   Year: {cit.get('extracted_date', 'N/A')}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
