import re

test_text = """We review statutory interpretation de novo. DeSean v. Sanger, 2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023). 
"The goal of statutory interpretation is to give effect to the legislature's intentions." DeSean, 2 Wn.3d at 335. 
In determining the plain meaning of a statute, we look to the text of the statute, as well as its No. 87675-9-I/14 14 
broader context and the statutory scheme as a whole. State v. Ervin, 169 Wn.2d 815, 820, 239 P.3d 354 (2010). 
Only if the plain text is susceptible to more than one interpretation do we turn to statutory construction, 
legislative history, and relevant case law to determine legislative intent. Ervin, 169 Wn.2d at 820."""

def extract_case_name(text, citation):
    # Look for case name before the citation
    pattern = r'([A-Z][^.!?]*?\b(?:v\.?|vs\.?|in\s+re|ex\s+rel\.|ex\s+parte)\b[^.!?]*?)[,.]\s*' + re.escape(citation)
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    
    if match:
        case_name = match.group(1).strip()
        # Clean up the case name
        case_name = re.sub(r'\s+', ' ', case_name)
        case_name = re.sub(r'^[^A-Za-z]+', '', case_name)
        return case_name
    return None

# Test cases
test_cases = [
    "2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023)",
    "DeSean, 2 Wn.3d at 335",
    "169 Wn.2d 815, 820, 239 P.3d 354 (2010)",
    "Ervin, 169 Wn.2d at 820"
]

print("Case Name Extraction Test\n" + "="*50)
for i, citation in enumerate(test_cases, 1):
    case_name = extract_case_name(test_text, citation)
    print(f"Test {i}:")
    print(f"Citation: {citation}")
    print(f"Extracted Case Name: {case_name or 'Not found'}")
    print("-" * 50)
