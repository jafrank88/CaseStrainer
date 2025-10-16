from pathlib import Path
from pypdf import PdfReader

pdf_path = Path(r'd:\dev\casestrainer\1033940.pdf')
output_path = Path(r'd:\dev\casestrainer\output\1033940_raw_reextract.txt')

reader = PdfReader(str(pdf_path))
texts = [(page.extract_text() or '') for page in reader.pages]
full_text = '\n\n'.join(texts)
output_path.write_text(full_text, encoding='utf-8')

print(f'Re-extracted {len(reader.pages)} pages, chars={len(full_text)}')
