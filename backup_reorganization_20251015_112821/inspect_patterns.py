import re
from pathlib import Path

context = Path('surrounding_debug.txt').read_text(encoding='utf-8')
citation = '521 U.S. 811'

def clean_candidate(raw: str) -> str:
    candidate = raw.strip()
    candidate = re.sub(r'\s+', ' ', candidate)
    candidate = re.sub(r'^(?:quoting|citing|see\s+also|see|accord|but\s+see|but\s+cf\.?|cf\.?|compare)\s+', '', candidate, flags=re.IGNORECASE)
    candidate = candidate.strip(',;: ')
    candidate = candidate.split(',', 1)[0].strip()
    candidate = re.sub(r'\d{1,4}', '', candidate)
    candidate = re.sub(r'\s+', ' ', candidate)
    return candidate

patterns = [
    ("targeted_parenthetical", rf'(?:quoting|citing|see\s+also|see|accord|but\s+see|but\s+cf\.?|cf\.?|compare)?\s*([A-Z][^,()]+?\bv\.\s+[^,()]+?)\s*,\s*(?:\d+\s+[A-Za-z\.]+\s+\d+(?:,\s*\d+\s+[A-Za-z\.]+\s+\d+)*)\s*\({re.escape(citation)}[^)]*\)'),
    ("immediate_before", rf'([A-Z][^()]+?\bv\.\s+[^()]+?)\s*,\s*{re.escape(citation)}'),
    ("reporter_before", rf'([A-Z][^()]+?\bv\.\s+[^()]+?)\s*,\s*(?:\d+\s+[A-Za-z\.]+\s+\d+(?:,\s*\d+\s+[A-Za-z\.]+\s+\d+)*)\s*(?:,\s*\d+\s+[A-Za-z\.]+\s+\d+|\s*[\,\w\.]+?)*\s*(?:\([^)]*\)\s*)?{re.escape(citation)}'),
    ("prefix_case", rf'(?:quoting|citing|see|accord|but\s+see|cf\.?|compare)\s+([A-Z][^()]+?\bv\.\s+[^()]+?)\s*,\s*(?:\d+\s+[A-Za-z\.]+\s+\d+(?:,\s*\d+\s+[A-Za-z\.]+\s+\d+)*)\s*(?:\s*,\s*[^()]*?)*\s*\({re.escape(citation)}[^)]*\)'),
    ("broad_multiline", rf'([A-Z][\s\S]{0,300}?\bv\.\s+[A-Z][\s\S]{0,200}?)\s*,\s*(?:[\s\S]{0,400}?)?{re.escape(citation)}'),
]

for name, pattern in patterns:
    match = re.search(pattern, context, re.IGNORECASE | re.DOTALL)
    print(f"Pattern '{name}' matched: {bool(match)}")
    if match:
        raw = match.group(1)
        cleaned = clean_candidate(raw)
        print(f"  Raw: {raw!r}")
        print(f"  Cleaned: {cleaned!r}")

citation_index = context.lower().find(citation.lower())
print('Citation index:', citation_index)
pre_segment = context[max(0, citation_index - 400):citation_index]
print('Pre segment tail:\n', pre_segment[-200:])

quoting_pattern = re.compile(r'(?:quoting|citing|see\s+also|see|accord|but\s+see|but\s+cf\.?|cf\.?|compare)\s+([A-Z][\s\S]{0,200}?\bv\.?\s+[A-Z][\s\S]{0,200}?)(?=,)', re.IGNORECASE)
quoting_matches = [m for m in quoting_pattern.finditer(context) if m.end() <= citation_index]
print('Quoting matches count:', len(quoting_matches))
for m in quoting_matches[-5:]:
    print('  quoting raw:', repr(m.group(1)))
    print('  quoting cleaned:', clean_candidate(m.group(1)))
v_matches = list(re.finditer(r'([A-Z][A-Za-z0-9\'’&\.,\-\s]+?\s+v\.?\s+[A-Z][A-Za-z0-9\'’&\.,\-\s]+)', pre_segment, re.IGNORECASE))
print("Found", len(v_matches), "'v.' matches")
for m in v_matches[-5:]:
    print('  ->', m.group(1))
