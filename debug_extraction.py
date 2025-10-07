import logging
from pathlib import Path

from src.unified_extraction_architecture import UnifiedExtractionArchitecture

logging.basicConfig(level=logging.WARNING, format='%(levelname)s:%(message)s')

text = Path(r'd:\dev\casestrainer\output\1033940_raw_reextract.txt').read_text(encoding='utf-8')

citation = '521 U.S. 811'
start = text.index(citation)
end = start + len(citation)

reference = 'Spokeo, Inc. v. Robins'
if reference in text:
    ref_index = text.index(reference)
    print(f"Reference '{reference}' is {start - ref_index} chars before target citation")
else:
    print(f"Reference '{reference}' not found in text")

slice_start = max(0, start - 2000)
slice_end = min(len(text), end + 500)
print('--- Surrounding Text ---')
print(text[slice_start:slice_end])
print('------------------------')
Path('surrounding_debug.txt').write_text(text[slice_start:slice_end], encoding='utf-8')

extractor = UnifiedExtractionArchitecture()
result = extractor.extract_case_name_and_year(text, citation, start_index=start, end_index=end, debug=True)
print('\nRESULT:', result)
