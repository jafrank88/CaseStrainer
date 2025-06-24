import re
from PyPDF2 import PdfReader
from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

PDF_PATH = "1028814.pdf"

# Regex patterns for case names and citations
CASE_CITATION_PATTERN = re.compile(r"([A-Z][A-Za-z0-9.,'’\- ]+? v\. [A-Z][A-Za-z0-9.,'’\- ]+?),? ([0-9]{1,4} [A-Za-z.]+ ?[0-9]{1,5})", re.MULTILINE)
IN_RE_PATTERN = re.compile(r"(In re [A-Z][A-Za-z0-9.,'’\- ]+),? ([0-9]{1,4} [A-Za-z.]+ ?[0-9]{1,5})", re.MULTILINE)

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_case_citations(text):
    pairs = set()
    for match in CASE_CITATION_PATTERN.finditer(text):
        case_name, citation = match.groups()
        pairs.add((case_name.strip(), citation.strip()))
    for match in IN_RE_PATTERN.finditer(text):
        case_name, citation = match.groups()
        pairs.add((case_name.strip(), citation.strip()))
    return list(pairs)

def main():
    print("Extracting case names and citations from PDF...")
    text = extract_text_from_pdf(PDF_PATH)
    pairs = extract_case_citations(text)
    print(f"Found {len(pairs)} (case name, citation) pairs.")
    print("\nRunning verification on up to 10 pairs:\n" + "-"*60)
    verifier = EnhancedMultiSourceVerifier()
    for i, (case_name, citation) in enumerate(pairs[:10]):
        print(f"\n{i+1}. Citation: {citation}")
        print(f"   Extracted case name: {case_name}")
        result = verifier.verify_citation(citation, extracted_case_name=case_name)
        print(f"   Verified: {result.get('verified', False)}")
        print(f"   Source case name: {result.get('case_name', 'N/A')}")
        print(f"   URL: {result.get('url', 'N/A')}")
        print(f"   Similarity: {result.get('case_name_similarity', 'N/A')}")
        print(f"   Case name mismatch: {result.get('case_name_mismatch', 'N/A')}")
        if result.get('note'):
            print(f"   Note: {result['note']}")
        print("-"*40)

if __name__ == "__main__":
    main() 