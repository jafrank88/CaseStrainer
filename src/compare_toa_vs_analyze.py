#!/usr/bin/env python3
"""
Compare ToA parser vs unified citation processor on ToA lines from 10 briefs.
Show only cases where the extracted name or date differ.
"""
import os
import logging
from toa_parser import ToAParser
from unified_citation_processor_v2 import UnifiedCitationProcessorV2

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BRIEFS_DIR = '../wa_briefs_text/'
MAX_BRIEFS = 10

def normalize(s):
    if not s:
        return ''
    return str(s).strip().lower()

toa_parser = ToAParser()
citation_processor = UnifiedCitationProcessorV2()

brief_files = sorted([f for f in os.listdir(BRIEFS_DIR) if f.endswith('.txt')])[:MAX_BRIEFS]

def extract_toa_section(text):
    # Use ToAParser's section extraction logic if available, else simple heuristic
    if hasattr(toa_parser, 'extract_toa_section'):
        return toa_parser.extract_toa_section(text)
    # Fallback: look for 'table of authorities' and next blank line
    lines = text.splitlines()
    start, end = None, None
    for i, line in enumerate(lines):
        if 'table of authorities' in line.lower():
            start = i
            break
    if start is not None:
        for j in range(start+1, len(lines)):
            if lines[j].strip() == '':
                end = j
                break
    if start is not None and end is not None:
        return '\n'.join(lines[start:end])
    return ''

logger.info("Cases where ToA parser and unified processor differ (name or date):\n")
for brief_file in brief_files:
    with open(os.path.join(BRIEFS_DIR, brief_file), encoding='utf-8') as f:
        text = f.read()
    toa_section = extract_toa_section(text)
    if not toa_section.strip():
        continue
    toa_lines = [l for l in toa_section.split('\n') if l.strip() and not l.strip().lower().startswith('table of authorities')]
    for i, line in enumerate(toa_lines, 1):
        toa_entry = toa_parser._parse_toa_line_flexible(line)
        toa_name = getattr(toa_entry, 'case_name', None)
        toa_year = None
        if getattr(toa_entry, 'years', None):
            toa_year = toa_entry.years[0]
        # Clean line for processor
        clean_line = line.split('.....................')[0].strip()
        results = citation_processor.process_text(clean_line)
        # Compare each extracted citation
        if results and hasattr(results, 'citations'):
            for citation in results.citations:
                proc_name = getattr(citation, 'canonical_name', None) or getattr(citation, 'extracted_case_name', None)
                proc_date = getattr(citation, 'canonical_date', None) or getattr(citation, 'extracted_date', None)
                if normalize(toa_name) != normalize(proc_name) or str(toa_year) != str(proc_date):
                    logger.info(f"{brief_file} | ToA line: {line}")
                    logger.info(f"   ToA parser:   name='{toa_name}'  year='{toa_year}'")
                    logger.info(f"   Processor:    name='{proc_name}'  date='{proc_date}'\n") 