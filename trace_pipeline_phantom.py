import sys
sys.path.append('src')
from pdfminer.high_level import extract_text as pdfminer_extract_text

try:
    from eyecite import get_citations
    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False

try:
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    processor = UnifiedCitationProcessorV2()
    PROCESSOR_AVAILABLE = True
except ImportError:
    PROCESSOR_AVAILABLE = False
    print("⚠️ Could not import processor")

print('🔍 TRACING PIPELINE TO FIND PHANTOM CREATION')
print('=' * 60)

text = pdfminer_extract_text('1033940.pdf')

if PROCESSOR_AVAILABLE:
    print('📋 STEP-BY-STEP PIPELINE TRACE:')
    
    # Step 1: Test eyecite extraction directly
    print('\n1️⃣ EYECITE EXTRACTION:')
    if EYECITE_AVAILABLE:
        eyecite_citations = processor._extract_with_eyecite(text)
        print(f'   Found {len(eyecite_citations)} citations')
        
        for i, citation in enumerate(eyecite_citations):
            if hasattr(citation, 'citation') and '9 P.3d 655' in citation.citation:
                print(f'   🎯 PHANTOM FOUND IN EYECITE: {citation.citation}')
            elif hasattr(citation, 'citation') and '59 P.3d 655' in citation.citation:
                print(f'   ✅ Correct citation: {citation.citation} at {citation.start_index}-{citation.end_index}')
    
    # Step 2: Test regex extraction directly
    print('\n2️⃣ REGEX EXTRACTION:')
    try:
        regex_citations = processor._extract_with_regex(text)
        print(f'   Found {len(regex_citations)} citations')
        
        for citation in regex_citations:
            if hasattr(citation, 'citation') and '9 P.3d 655' in citation.citation:
                print(f'   🎯 PHANTOM FOUND IN REGEX: {citation.citation}')
            elif hasattr(citation, 'citation') and '59 P.3d 655' in citation.citation:
                print(f'   ✅ Correct citation: {citation.citation} at {citation.start_index}-{citation.end_index}')
    except Exception as e:
        print(f'   Error in regex extraction: {e}')
    
    # Step 3: Test unified extraction
    print('\n3️⃣ UNIFIED EXTRACTION:')
    try:
        unified_citations = processor._extract_citations_unified(text)
        print(f'   Found {len(unified_citations)} citations')
        
        for citation in unified_citations:
            if hasattr(citation, 'citation') and '9 P.3d 655' in citation.citation:
                print(f'   🎯 PHANTOM FOUND IN UNIFIED: {citation.citation} at {citation.start_index}-{citation.end_index}')
                print(f'      Method: {getattr(citation, "method", "unknown")}')
                # Show the actual text at those positions
                if hasattr(citation, 'start_index') and citation.start_index is not None:
                    actual_text = text[citation.start_index:citation.end_index]
                    print(f'      Actual text at position: "{actual_text}"')
            elif hasattr(citation, 'citation') and '59 P.3d 655' in citation.citation:
                print(f'   ✅ Correct citation: {citation.citation} at {citation.start_index}-{citation.end_index}')
    except Exception as e:
        print(f'   Error in unified extraction: {e}')
        import traceback
        traceback.print_exc()

print(f'\n💡 ANALYSIS:')
print('This will show us exactly which extraction method is creating the phantom.')
print('Once we find it, we can trace into that specific method to find the bug.')






