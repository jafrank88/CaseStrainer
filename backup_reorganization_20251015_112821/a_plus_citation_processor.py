import re
from typing import List, Optional

# --- Robust Regex Patterns ---
CUSTOM_PATTERNS = [
    # Washington Supreme Court and Appellate
    re.compile(r'\b(\d+)\s+Wn\.2d\s+(\d+)\b', re.IGNORECASE),
    re.compile(r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
    re.compile(r'\b(\d+)\s+Wash\.2d\s+(\d+)\b', re.IGNORECASE),
    re.compile(r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
    # Pacific Reporter
    re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)\b', re.IGNORECASE),
    re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)\b', re.IGNORECASE),
    # Parallel/clustered
    re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b', re.IGNORECASE),
    re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+))?\b', re.IGNORECASE),
    re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+))?\b', re.IGNORECASE),
]

# --- Parallel Citation Clustering Logic ---
def find_parallel_citation_clusters(citations: List[dict]) -> List[List[dict]]:
    """Group citations that are within 100 chars and comma-separated."""
    groups = []
    processed = set()
    sorted_citations = sorted(
        [c for c in citations if c.get('start_position') is not None],
        key=lambda c: c['start_position']
    )
    for i, citation in enumerate(sorted_citations):
        if i in processed:
            continue
        group = [citation]
        processed.add(i)
        for j, other in enumerate(sorted_citations):
            if j != i and j not in processed:
                # Check proximity and comma separation
                if (abs(citation['start_position'] - other['start_position']) < 100 and
                    ',' in citation.get('context', '')):
                    group.append(other)
                    processed.add(j)
        if len(group) > 1:
            groups.append(group)
    return groups

# --- Case Name and Year Extraction Helpers ---
def extract_case_name_from_context(text: str, citation_start: int) -> Optional[str]:
    """Look back 150 chars for a valid case name pattern, only after sentence-ending punctuation or start of string.
    If the match contains sentence-ending punctuation, only return the part after the last such punctuation that contains 'v.' or 'In re'."""
    context = text[max(0, citation_start-150):citation_start]
    patterns = [
        r'([A-Z][A-Za-z0-9&.,\'\s\-]+ v\. [A-Z][A-Za-z0-9&.,\'\s\-]+)',
        r'(Dep[’\'`’]t of [A-Za-z0-9&.,\'\s\-]+ v\. [A-Z][A-Za-z0-9&.,\'\s\-]+)',
        r'(In re [A-Za-z0-9&.,\'\s\-]+)'
    ]
    for pattern in patterns:
        matches = list(re.finditer(pattern, context))
        if matches:
            raw = matches[-1].group(1).strip()
            # Split on sentence-ending punctuation, take the last part with 'v.' or 'In re'
            for sep in ['.', ';', '!', '?']:
                if sep in raw:
                    parts = [p.strip() for p in raw.split(sep) if 'v.' in p or 'In re' in p]
                    if parts:
                        return parts[-1]
            return raw
    return None

def extract_year_after_citation(text: str, citation_end: int) -> Optional[str]:
    """Look for a 4-digit year immediately after the citation."""
    context = text[citation_end: min(len(text), citation_end+10)]
    match = re.search(r'\((19|20)\d{2}\)', context)
    if match:
        return match.group(0).strip('()')
    match = re.search(r'(19|20)\d{2}', context)
    if match:
        return match.group(0)
    return None

def extract_case_name_from_toa_context(text: str, citation_start: int) -> Optional[str]:
    """Extract case name from ToA context where case name is immediately before citation.
    Pattern: Case Name, Citation (Year)"""
    
    # Look backwards from the citation start to find the case name
    # Start from the citation and go backwards up to 300 characters
    search_start = max(0, citation_start - 300)
    search_text = text[search_start:citation_start]
    
    # Look for case name patterns that end with a comma, followed by the citation
    patterns = [
        # Standard case name: "Plaintiff v. Defendant, Citation" (with optional space before v.)
        r'([A-Z][A-Za-z0-9&.,\'\s\-]+?\s*v\.?\s*[A-Z][A-Za-z0-9&.,\'\s\-]+?)\s*,',
        # In re cases: "In re Case Name, Citation"
        r'(In\s+re\s+[A-Za-z0-9&.,\'\s\-]+?)\s*,',
        # Department cases: "Dep't of ... v. ..., Citation"
        r'(Dep[\'`]t of [A-Za-z0-9&.,\'\s\-]+?\s*v\.\s*[A-Za-z0-9&.,\'\s\-]+?)\s*,',
    ]
    
    # Find all matches and take the one closest to the citation
    all_matches = []
    for pattern in patterns:
        matches = list(re.finditer(pattern, search_text, re.IGNORECASE))
        for match in matches:
            # Calculate the distance from the citation start
            match_end = match.end()
            distance_from_citation = len(search_text) - match_end
            all_matches.append((distance_from_citation, match.group(1).strip()))
    
    if all_matches:
        # Sort by distance from citation (closest first) and take the closest
        all_matches.sort(key=lambda x: x[0])
        return all_matches[0][1]
    
    return None

def extract_year_from_toa_context(text: str, citation_end: int) -> Optional[str]:
    """Extract year from ToA context where year is in parentheses after citation.
    Pattern: Citation (Year)"""
    # Look for year in parentheses after the citation - look further ahead
    context_after = text[citation_end:min(len(text), citation_end+100)]
    match = re.search(r'\((\d{4})\)', context_after)
    if match:
        return match.group(1)
    return None

# --- Example usage in extraction pipeline ---
def extract_citations_with_custom_logic(text: str) -> List[dict]:
    citations = []
    seen = set()
    
    # Check if this looks like a ToA section
    is_toa_section = any(keyword in text.upper() for keyword in 
                        ['TABLE OF AUTHORITIES', 'AUTHORITIES CITED', 'CASES CITED'])
    
    for pattern in CUSTOM_PATTERNS:
        for match in pattern.finditer(text):
            citation_str = match.group(0).strip()
            if not citation_str or citation_str in seen:
                continue
            seen.add(citation_str)
            start_pos = match.start()
            end_pos = match.end()
            context = text[max(0, start_pos-50):min(len(text), end_pos+50)]
            
            # Use specialized ToA extraction if we're in a ToA section
            if is_toa_section:
                case_name = extract_case_name_from_toa_context(text, start_pos)
                year = extract_year_from_toa_context(text, end_pos)
            else:
                case_name = extract_case_name_from_context(text, start_pos)
                year = extract_year_after_citation(text, end_pos)
            
            citations.append({
                'citation': citation_str,
                'start_position': start_pos,
                'end_position': end_pos,
                'context': context,
                'case_name': case_name,
                'year': year
            })
    # Order preservation
    citations = sorted(citations, key=lambda c: c['start_position'])
    return citations

# --- Example usage for clustering ---
def cluster_and_display(text: str):
    citations = extract_citations_with_custom_logic(text)
    clusters = find_parallel_citation_clusters(citations)
    for idx, cluster in enumerate(clusters):
        best_name = next((c['case_name'] for c in cluster if c['case_name']), 'N/A')
        best_year = next((c['year'] for c in cluster if c['year']), 'N/A')
        print(f"Cluster {idx+1}: {best_name} ({best_year})")
        for c in cluster:
            print(f"  - {c['citation']}")
        print('---') 