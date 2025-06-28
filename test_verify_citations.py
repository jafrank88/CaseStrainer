from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
from src.unified_citation_extractor import extract_all_citations
import pdfminer.high_level

text = pdfminer.high_level.extract_text('test_1029764.pdf')
citations = extract_all_citations(text)

# Create verifier instance
verifier = EnhancedMultiSourceVerifier()

for c in citations:
    result = verifier.verify_citation_unified_workflow(
        c['citation'], 
        full_text=text  # Pass the full text for case name extraction
    )
    print('Citation: {}'.format(c['citation']))
    print('  Canonical: {}'.format(result.get('canonical_citation')))
    print('  URL: {}'.format(result.get('url')))
    print('  Case Name: {}'.format(result.get('case_name')))
    print('  Extracted Case Name: {}'.format(result.get('extracted_case_name')))
    print('  Hinted Case Name: {}'.format(result.get('hinted_case_name')))
    print('  Extracted Date: {}'.format(result.get('extracted_date')))
    print('  Canonical Date: {}'.format(result.get('canonical_date')))
    print('  Verified: {}'.format(result.get('verified')))
    print('---') 