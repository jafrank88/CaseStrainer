import requests
import json
from src.extract_case_name import get_citation_url
from src.document_processing_unified import process_document

# Citation to test
citation = "John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)"

# Get URL for the citation
url = get_citation_url(citation)
print(f"Generated URL for citation: {url}")

if url:
    # Process the URL through the document processing function
    result = process_document(url=url, extract_case_names=True)
    print(f"Processing result: {json.dumps(result, indent=2)}")
    
    # Check if case name and date are extracted
    citations = result.get('citations', [])
    for citation_data in citations:
        if citation_data.get('citation') == citation or citation in citation_data.get('citation', ''):
            print(f"Case Name: {citation_data.get('case_name', 'Not found')}")
            print(f"Canonical Date: {citation_data.get('canonical_date', 'Not found')}")
else:
    print("No URL could be generated for the citation.")
