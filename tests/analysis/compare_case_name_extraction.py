"""
Compare case name extraction quality: eyecite vs internal tools
NO VERIFICATION - pure extraction comparison only
"""
import requests
import tempfile
import os

# Download the PDF
print("=" * 80)
print("CASE NAME EXTRACTION COMPARISON (NO VERIFICATION)")
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
from src.optimized_pdf_processor import OptimizedPDFProcessor
pdf_processor = OptimizedPDFProcessor()
result = pdf_processor.process_pdf(temp_path)
text = result.text if result else ""

print(f"✅ Extracted {len(text)} characters")

# Clean up temp file
os.remove(temp_path)

# Test 1: Eyecite extraction
print("\n" + "=" * 80)
print("METHOD 1: EYECITE")
print("=" * 80)

try:
    import eyecite
    
    eyecite_citations = eyecite.get_citations(text)
    print(f"\n✅ Found {len(eyecite_citations)} citations with eyecite")
    
    # Eyecite doesn't extract case names - it only finds citation strings
    print(f"\nℹ️  Note: Eyecite finds citations but does NOT extract case names")
    print(f"   It only identifies citation strings like '159 Wn.2d 700'")
    
    print(f"\nFirst 10 citations:")
    for i, cite in enumerate(eyecite_citations[:10], 1):
        print(f"  {i}. {cite} ({type(cite).__name__})")
        
except Exception as e:
    print(f"❌ Eyecite extraction failed: {e}")

# Test 2: Our internal case name extractor
print("\n" + "=" * 80)
print("METHOD 2: OUR INTERNAL CASE NAME EXTRACTOR")
print("=" * 80)

try:
    from src.unified_extraction_architecture import UnifiedExtractionArchitecture
    
    extractor = UnifiedExtractionArchitecture()
    
    # Extract citations with case names (NO VERIFICATION)
    extracted = extractor.extract_citations_with_context(text)
    
    print(f"\n✅ Found {len(extracted)} citations with case names")
    
    # Count how many have case names
    with_names = sum(1 for c in extracted if c.get('extracted_case_name') not in [None, '', 'N/A'])
    print(f"   {with_names}/{len(extracted)} have case names ({with_names/len(extracted)*100:.1f}%)")
    
    print(f"\nFirst 20 citations with case names:")
    for i, cite in enumerate(extracted[:20], 1):
        citation = cite.get('citation', 'N/A')
        case_name = cite.get('extracted_case_name', 'N/A')
        
        # Mark quality
        quality = "✅" if case_name not in [None, '', 'N/A'] else "❌"
        
        print(f"  {i}. {quality} {citation}")
        print(f"      Case: {case_name}")
        print()
        
except Exception as e:
    print(f"❌ Internal extraction failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Compare specific examples
print("\n" + "=" * 80)
print("QUALITY ANALYSIS")
print("=" * 80)

if 'extracted' in locals():
    print(f"\nCase Name Extraction Quality:")
    
    # Analyze quality
    good_names = []
    poor_names = []
    no_names = []
    
    for cite in extracted[:30]:
        case_name = cite.get('extracted_case_name', '')
        citation = cite.get('citation', '')
        
        if not case_name or case_name == 'N/A':
            no_names.append(citation)
        elif len(case_name) < 5 or ' v. ' not in case_name.lower():
            poor_names.append((citation, case_name))
        else:
            good_names.append((citation, case_name))
    
    print(f"\n✅ Good extractions: {len(good_names)}/30 ({len(good_names)/30*100:.1f}%)")
    if good_names:
        print(f"   Examples:")
        for citation, case_name in good_names[:3]:
            print(f"   - {citation} → {case_name}")
    
    print(f"\n⚠️  Poor quality: {len(poor_names)}/30 ({len(poor_names)/30*100:.1f}%)")
    if poor_names:
        print(f"   Examples:")
        for citation, case_name in poor_names[:3]:
            print(f"   - {citation} → {case_name}")
    
    print(f"\n❌ No name extracted: {len(no_names)}/30 ({len(no_names)/30*100:.1f}%)")
    if no_names:
        print(f"   Examples:")
        for citation in no_names[:3]:
            print(f"   - {citation}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print(f"\nEyecite:")
print(f"  - Finds citation strings accurately")
print(f"  - Does NOT extract case names")
print(f"  - Good for: Citation detection")

print(f"\nOur Internal Extractor:")
print(f"  - Finds citations AND extracts case names")
print(f"  - Quality varies by citation complexity")
print(f"  - Good for: Full citation metadata extraction")

print(f"\nℹ️  This comparison ran WITHOUT calling CourtListener API")
print(f"   (No verification - pure extraction only)")

print("\n" + "=" * 80)
