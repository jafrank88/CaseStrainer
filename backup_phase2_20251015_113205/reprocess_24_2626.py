"""
Reprocess 24-2626.pdf using the fixed backend with strict context isolation.
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 100)
print("REPROCESSING 24-2626.pdf with STRICT CONTEXT ISOLATION FIX")
print("=" * 100)
print()

# Load the PDF text
try:
    import PyPDF2
    pdf_path = r'D:\dev\casestrainer\24-2626.pdf'
    pdf_reader = PyPDF2.PdfReader(pdf_path)
    full_text = '\n'.join([page.extract_text() for page in pdf_reader.pages])
    print(f"✅ Loaded PDF: {len(full_text)} characters, {len(pdf_reader.pages)} pages")
except Exception as e:
    print(f"❌ Failed to load PDF: {e}")
    sys.exit(1)

print()
print("Processing with UnifiedSyncProcessor...")
print()

try:
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    import asyncio
    
    processor = UnifiedCitationProcessorV2()
    
    # Use asyncio to run the async process_text method
    result = asyncio.run(processor.process_text(full_text))
    
    if result.get('success'):
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"✅ Processing complete:")
        print(f"   - Citations: {len(citations)}")
        print(f"   - Clusters: {len(clusters)}")
        print(f"   - Processing time: {result.get('processing_time', 0):.2f}s")
        
        # Save updated results
        output_path = r'D:\dev\casestrainer\24-2626_comprehensive_results_FIXED.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved results to: {output_path}")
        
        print()
        print("=" * 100)
        print("SAMPLE EXTRACTIONS (First 10 citations):")
        print("=" * 100)
        
        for i, cit in enumerate(citations[:10], 1):
            print(f"\n{i}. {cit.get('citation')}")
            print(f"   Case Name: {cit.get('extracted_case_name', 'N/A')}")
            print(f"   Year: {cit.get('extracted_date', 'N/A')}")
            if cit.get('context'):
                context = cit['context'][:100] + '...' if len(cit.get('context', '')) > 100 else cit.get('context', '')
                print(f"   Context: {context}")
        
    else:
        print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
        
except Exception as e:
    print(f"❌ Processing error: {e}")
    import traceback
    traceback.print_exc()
