import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

print("Testing direct verification of citation: 534 F.3d 1290\n")

try:
    from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
    config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=False,
        enable_deduplication=False,
        debug_mode=True
    )
    processor = UnifiedCitationProcessorV2(config)
    results = processor.process_text('534 F.3d 1290')
    if results:
        citation = results[0]
        print("[Unified Processor]")
        print(f"Verified: {getattr(citation, 'verified', None)}")
        print(f"Canonical Name: {getattr(citation, 'canonical_name', None)}")
        print(f"Canonical Date: {getattr(citation, 'canonical_date', None)}")
        print(f"URL: {getattr(citation, 'url', None)}")
        print(f"Error: {getattr(citation, 'error', None)}")
    else:
        print("No citation found by unified processor.")
except ImportError:
    print("Unified processor not available, trying enhanced processor...")
    try:
        from app_final_vue import verify_citation_with_extraction
        result = verify_citation_with_extraction('534 F.3d 1290')
        print("[Enhanced Processor]")
        print(f"Verified: {result.get('verified')}")
        print(f"Canonical Name: {result.get('canonical_name')}")
        print(f"Canonical Date: {result.get('canonical_date')}")
        print(f"URL: {result.get('url')}")
        print(f"Error: {result.get('error')}")
    except ImportError:
        print("No citation processor available.") 