"""
Compare case name extraction quality: eyecite vs internal tools
Using the test PDF: https://www.courts.wa.gov/opinions/pdf/1034300.pdf
"""
import requests
import tempfile
import os
from src.optimized_pdf_processor import OptimizedPDFProcessor

# Download the PDF
print("=" * 80)
print("CASE NAME EXTRACTION QUALITY COMPARISON")
print("=" * 80)

url = "https://www.courts.wa.gov/opinions/pdf/1034300.pdf"
print(f"\n📥 Downloading PDF from: {url}")

response = requests.get(url, timeout=30)
response.raise_for_status()

# Save to temp file
with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
    temp_file.write(response.content)
    temp_path = temp_file.name

print(f"✅ Downloaded {len(response.content)} bytes")

# Extract text
print(f"\n📄 Extracting text from PDF...")
pdf_processor = OptimizedPDFProcessor()
result = pdf_processor.process_pdf(temp_path)
text = result.text if result else ""

print(f"✅ Extracted {len(text)} characters")

# Clean up temp file
os.remove(temp_path)

# Test 1: Extract citations with eyecite
print("\n" + "=" * 80)
print("METHOD 1: EYECITE EXTRACTION")
print("=" * 80)

try:
    import eyecite
    
    eyecite_citations = eyecite.get_citations(text)
    print(f"\n✅ Found {len(eyecite_citations)} citations with eyecite")
    
    # Show first 10 with case names
    print(f"\nFirst 10 citations with case names:")
    for i, cite in enumerate(eyecite_citations[:10], 1):
        case_name = getattr(cite, 'metadata', {}).get('plaintiff', 'N/A') if hasattr(cite, 'metadata') else 'N/A'
        if not case_name or case_name == 'N/A':
            # Try to get case name from corrected_citation_full
            full_cite = getattr(cite, 'corrected_citation_full', str(cite))
            # Try to extract case name before citation
            case_name = "N/A (eyecite doesn't extract case names)"
        
        print(f"  {i}. {cite}")
        print(f"     Case name: {case_name}")
        print(f"     Type: {type(cite).__name__}")
        if hasattr(cite, '__dict__'):
            print(f"     Attributes: {list(cite.__dict__.keys())}")
        print()
        
except Exception as e:
    print(f"❌ Eyecite extraction failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Extract with our internal tools
print("\n" + "=" * 80)
print("METHOD 2: INTERNAL EXTRACTION (UnifiedCitationProcessorV2)")
print("=" * 80)

try:
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    import asyncio
    
    processor = UnifiedCitationProcessorV2()
    
    # Run async extraction
    internal_result = asyncio.run(processor.process_text(text))
    
    internal_citations = internal_result.get('citations', [])
    print(f"\n✅ Found {len(internal_citations)} citations with internal tools")
    
    # Show first 10 with case names
    print(f"\nFirst 10 citations with case names:")
    for i, cite in enumerate(internal_citations[:10], 1):
        citation_text = cite.get('citation') if isinstance(cite, dict) else getattr(cite, 'citation', str(cite))
        case_name = cite.get('extracted_case_name') if isinstance(cite, dict) else getattr(cite, 'extracted_case_name', 'N/A')
        method = cite.get('method') if isinstance(cite, dict) else getattr(cite, 'method', 'unknown')
        
        print(f"  {i}. {citation_text}")
        print(f"     Case name: {case_name}")
        print(f"     Method: {method}")
        print()
        
except Exception as e:
    print(f"❌ Internal extraction failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Extract with clean pipeline
print("\n" + "=" * 80)
print("METHOD 3: CLEAN EXTRACTION PIPELINE")
print("=" * 80)

try:
    from src.citation_extraction_endpoint import extract_citations_production
    
    clean_result = extract_citations_production(text)
    
    clean_citations = clean_result.get('citations', [])
    print(f"\n✅ Found {len(clean_citations)} citations with clean pipeline")
    print(f"   Accuracy: {clean_result.get('accuracy', 'N/A')}")
    print(f"   Method: {clean_result.get('method', 'N/A')}")
    
    # Show first 10 with case names
    print(f"\nFirst 10 citations with case names:")
    for i, cite in enumerate(clean_citations[:10], 1):
        citation_text = cite.get('citation', 'N/A')
        case_name = cite.get('extracted_case_name', 'N/A')
        method = cite.get('method', 'unknown')
        
        print(f"  {i}. {citation_text}")
        print(f"     Case name: {case_name}")
        print(f"     Method: {method}")
        print()
        
except Exception as e:
    print(f"❌ Clean pipeline extraction failed: {e}")
    import traceback
    traceback.print_exc()

# Summary comparison
print("\n" + "=" * 80)
print("SUMMARY COMPARISON")
print("=" * 80)

try:
    print(f"\nCitation Counts:")
    print(f"  Eyecite: {len(eyecite_citations) if 'eyecite_citations' in locals() else 'N/A'}")
    print(f"  Internal: {len(internal_citations) if 'internal_citations' in locals() else 'N/A'}")
    print(f"  Clean Pipeline: {len(clean_citations) if 'clean_citations' in locals() else 'N/A'}")
    
    # Count how many have case names
    if 'internal_citations' in locals():
        internal_with_names = sum(1 for c in internal_citations[:20] if (c.get('extracted_case_name') if isinstance(c, dict) else getattr(c, 'extracted_case_name', None)) not in [None, '', 'N/A'])
        print(f"\nCase Name Extraction (first 20):")
        print(f"  Internal: {internal_with_names}/20 ({internal_with_names/20*100:.1f}%)")
    
    if 'clean_citations' in locals():
        clean_with_names = sum(1 for c in clean_citations[:20] if c.get('extracted_case_name') not in [None, '', 'N/A'])
        print(f"  Clean Pipeline: {clean_with_names}/20 ({clean_with_names/20*100:.1f}%)")
    
except Exception as e:
    print(f"Summary calculation error: {e}")

print("\n" + "=" * 80)
