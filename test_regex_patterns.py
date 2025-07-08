#!/usr/bin/env python3
"""
Test the main regex patterns from the extractor against the context window for a failing test case (misspelled party name).
"""
import re

# Test input
text = 'In Doe v. Wdae, 123 U.S. 456 (1973), the court ruled...'
citation = '123 U.S. 456'

# Simulate context window
citation_index = text.find(citation)
context_before = text[max(0, citation_index - 100):citation_index]
context_after = text[citation_index:min(len(text), citation_index + 100)]
full_context = context_before + context_after
print(f"Context before: '{context_before}'")
print(f"Context after: '{context_after}'")
print(f"Full context: '{full_context}'\n")

# Patterns from extract_case_name_from_complex_citation
complex_citation_patterns = [
    r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
    r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?,\s*\d+.*?\(\d{4}\)',
    r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+\s*\(\d{4}\)',
    r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?,\s*\d+',
    r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
    r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
    r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
    r'(People\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
    r'(United\s+States\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
]

print("Testing complex_citation_patterns:")
for i, pattern in enumerate(complex_citation_patterns, 1):
    matches = list(re.finditer(pattern, full_context, re.IGNORECASE))
    print(f"Pattern {i}: {pattern}")
    for match in matches:
        print(f"  Match: '{match.group(1)}'")
    if not matches:
        print("  No match.")
print()

# Patterns from extract_case_name_with_date_adjacency
adjacent_patterns = [
    r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
    r'([A-Z][A-Za-z\s,\.\'-]+?\s+vs\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
    r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
    r'([A-Z][A-Za-z\s,\.\'-]+?\s+vs\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
    r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
    r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
    r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
    r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
    r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
    r'(People\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
    r'(United\s+States\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
]

print("Testing adjacent_patterns:")
for i, pattern in enumerate(adjacent_patterns, 1):
    matches = list(re.finditer(pattern, context_before, re.IGNORECASE))
    print(f"Pattern {i}: {pattern}")
    for match in matches:
        print(f"  Match: '{match.group(1)}'")
    if not matches:
        print("  No match.") 