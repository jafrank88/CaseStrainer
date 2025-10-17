import PyPDF2
import re

pdf_path = r'D:\dev\casestrainer\1034300.pdf'
pdf = PyPDF2.PdfReader(open(pdf_path, 'rb'))
full_text = ''.join([page.extract_text() for page in pdf.pages])

# Find the "In re" citation with more context
citation = "197 Wn.2d 868"
pattern = re.escape(citation)
match = re.search(pattern, full_text)

if match:
    start = max(0, match.start() - 300)
    end = min(len(full_text), match.end() + 50)
    context = full_text[start:end]
    # Clean whitespace for readability
    context = re.sub(r'\s+', ' ', context)
    print(f"FULL CONTEXT ({len(context)} chars):")
    print(context)
    print("\n" + "="*80)
    
    # Check if "In re" is present
    if "In re" in context:
        in_re_match = re.search(r'(In re [^,]+)', context)
        if in_re_match:
            print(f"Found 'In re' pattern: {in_re_match.group(1)}")
    else:
        print("WARNING: 'In re' not found in context!")
