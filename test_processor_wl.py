from src.document_processing_unified import extract_text_from_file
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

# Extract text from the file
text = extract_text_from_file(r'D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf')
print(f"Text length: {len(text)}")

# Create processor with WL patterns enabled
config = ProcessingConfig(
    use_eyecite=False,
    use_regex=True,
    extract_case_names=True,
    extract_dates=True,
    enable_clustering=False,
    enable_verification=False,
    debug_mode=True
)

processor = UnifiedCitationProcessorV2(config)

# Process the text
print("Processing text with UnifiedCitationProcessorV2...")
results = processor.process_text(text)

print(f"Found {len(results)} total citations")

# Filter for WL citations
wl_citations = [r for r in results if 'WL' in r.citation]
print(f"Found {len(wl_citations)} WL citations:")

for i, citation in enumerate(wl_citations[:10]):
    print(f"  {i+1}. {citation.citation}")
    print(f"     Pattern: {citation.pattern}")
    print(f"     Method: {citation.method}")
    print(f"     Confidence: {citation.confidence}")
    print() 