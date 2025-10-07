from pathlib import Path
import re
import textwrap

path = Path(r"d:\dev\casestrainer\src\unified_clustering_master.py")
text = path.read_text(encoding="utf-8")

replacements = {}

replacements['_detect_parallel_citations'] = """
def _detect_parallel_citations(self, citations: List[Any], text: str) -> List[List[Any]]:
    """Detect parallel citations using reporter heuristics and proximity analysis."""
    if not citations:
        return []

    parallel_groups: List[List[Any]] = []
    processed_ids: Set[int] = set()
    total = len(citations)

    adjacency = {i: set() for i in range(total)}
    for i in range(total):
        for j in range(i + 1, total):
            if self._are_citations_parallel_pair(citations[i], citations[j], text):
                adjacency[i].add(j)
                adjacency[j].add(i)

    visited = set()
    for idx in range(total):
        if idx in visited:
            continue
        stack = [idx]
        component = []
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            component.append(current)
            stack.extend(neighbor for neighbor in adjacency[current] if neighbor not in visited)

        if len(component) > 1:
            group = [citations[i] for i in component]
            parallel_groups.append(group)
            for citation in group:
                processed_ids.add(id(citation))

    remaining = [citation for citation in citations if id(citation) not in processed_ids]
    if remaining:
        proximity_groups = self._group_by_proximity(remaining, text)
        for group in proximity_groups:
            if len(group) >= 2 and self._are_parallel_citations(group, text):
                parallel_groups.append(group)
                for citation in group:
                    processed_ids.add(id(citation))

    for citation in citations:
        if id(citation) not in processed_ids:
            parallel_groups.append([citation])

    return parallel_groups
"""

replacements['_extract_and_propagate_metadata'] = """
def _extract_and_propagate_metadata(self, citations: List[Any], parallel_groups: List[List[Any]], text: str) -> List[Any]:
    """Extract metadata from clusters and propagate to all members."""
    enhanced_citations = []

    for group in parallel_groups:
        if not group:
            continue

        canonical_names: List[str] = []
        canonical_dates: List[str] = []
        for citation in group:
            if isinstance(citation, dict):
                verified = citation.get('verified', False)
                canonical_name = citation.get('canonical_name')
                canonical_date = citation.get('canonical_date')
            else:
                verified = getattr(citation, 'verified', False)
                canonical_name = getattr(citation, 'canonical_name', None)
                canonical_date = getattr(citation, 'canonical_date', None)

            if verified and canonical_name and canonical_name != 'N/A':
                canonical_names.append(canonical_name)
            if verified and canonical_date and canonical_date != 'N/A':
                canonical_dates.append(canonical_date)

        if canonical_names:
            case_name = max(canonical_names, key=self._score_case_name)
        else:
            case_name = self._select_best_case_name(group)

        if canonical_dates:
            from collections import Counter
            case_year = Counter(canonical_dates).most_common(1)[0][0]
        else:
            case_year = self._select_best_case_year(group)

        if not case_name:
            for citation in group:
                extracted_name = getattr(citation, 'extracted_case_name', None)
                fallback_name = getattr(citation, 'canonical_name', None)
                if extracted_name and extracted_name != 'N/A':
                    case_name = extracted_name
                    break
                if fallback_name and fallback_name != 'N/A':
                    case_name = fallback_name
                    break

        if not case_year:
            for citation in group:
                extracted_date = getattr(citation, 'extracted_date', None)
                fallback_date = getattr(citation, 'canonical_date', None)
                if extracted_date and extracted_date != 'N/A':
                    case_year = extracted_date
                    break
                if fallback_date and fallback_date != 'N/A':
                    case_year = fallback_date
                    break

        for citation in group:
            enhanced_citation = self._create_enhanced_citation(citation, case_name, case_year, group)
            enhanced_citations.append(enhanced_citation)

    return enhanced_citations
"""

replacements['_create_enhanced_citation'] = """
def _create_enhanced_citation(self, citation: Any, case_name: Optional[str], case_year: Optional[str], group: List[Any]) -> Any:
    """Create an enhanced citation object with propagated metadata."""
    if hasattr(citation, '__dict__'):
        import copy
        enhanced = copy.copy(citation)
    elif isinstance(citation, dict):
        enhanced = citation.copy()
    else:
        enhanced = citation

    if isinstance(citation, dict):
        canonical_name = citation.get('canonical_name')
        canonical_date = citation.get('canonical_date')
        verified_flag = citation.get('verified', False)
    else:
        canonical_name = getattr(citation, 'canonical_name', None)
        canonical_date = getattr(citation, 'canonical_date', None)
        verified_flag = getattr(citation, 'verified', False)

    if verified_flag and canonical_name and canonical_name != 'N/A':
        case_name = case_name or canonical_name
    if verified_flag and canonical_date and canonical_date != 'N/A':
        case_year = case_year or canonical_date

    members = [getattr(c, 'citation', str(c)) for c in group]
    citation_text = getattr(citation, 'citation', str(citation))
    parallel = len(group) > 1

    if hasattr(enhanced, '__dict__'):
        enhanced.cluster_case_name = case_name
        enhanced.cluster_year = case_year
        enhanced.cluster_size = len(group)
        enhanced.is_in_cluster = parallel
        enhanced.cluster_members = members

        current_name = getattr(enhanced, 'extracted_case_name', None)
        if case_name and case_name != 'N/A' and self._should_replace_case_name(current_name, case_name):
            enhanced.extracted_case_name = case_name
        if verified_flag and canonical_name and canonical_name != 'N/A' and self._should_replace_case_name(current_name, canonical_name):
            enhanced.extracted_case_name = canonical_name

        current_year = getattr(enhanced, 'extracted_date', None)
        if case_year and case_year != 'N/A' and (not current_year or current_year in ('', 'N/A', 'Unknown')):
            enhanced.extracted_date = case_year
        if verified_flag and canonical_date and canonical_date != 'N/A' and (not current_year or current_year in ('', 'N/A', 'Unknown')):
            enhanced.extracted_date = canonical_date

        enhanced.is_parallel = parallel
        enhanced.parallel_citations = [member for member in members if member != citation_text]
    elif isinstance(enhanced, dict):
        enhanced['cluster_case_name'] = case_name
        enhanced['cluster_year'] = case_year
        enhanced['cluster_size'] = len(group)
        enhanced['is_in_cluster'] = parallel
        enhanced['cluster_members'] = members

        current_name = enhanced.get('extracted_case_name')
        if case_name and case_name != 'N/A' and self._should_replace_case_name(current_name, case_name):
            enhanced['extracted_case_name'] = case_name
        if verified_flag and canonical_name and canonical_name != 'N/A' and self._should_replace_case_name(current_name, canonical_name):
            enhanced['extracted_case_name'] = canonical_name

        current_year = enhanced.get('extracted_date')
        if case_year and case_year != 'N/A' and (not current_year or current_year in ('', 'N/A', 'Unknown')):
            enhanced['extracted_date'] = case_year
        if verified_flag and canonical_date and canonical_date != 'N/A' and (not current_year or current_year in ('', 'N/A', 'Unknown')):
            enhanced['extracted_date'] = canonical_date

        enhanced['is_parallel'] = parallel
        enhanced['parallel_citations'] = [member for member in members if member != enhanced.get('citation', str(enhanced))]

    return enhanced
"""

replacements['_extract_reporter_type'] = """
def _extract_reporter_type(self, citation_text: str) -> str:
    """Extract a simplified reporter type token from citation text."""
    normalized = citation_text.lower()
    if 'wn. app.' in normalized or 'wash. app.' in normalized:
        return 'wash_app'
    if 'wn.2d' in normalized or 'wash. 2d' in normalized or 'wash.2d' in normalized or 'wn.2d' in normalized:
        return 'wash'
    if 'wash.' in normalized and 'wn.' not in normalized:
        return 'wash'
    if 'p.3d' in normalized:
        return 'p3d'
    if 'p.2d' in normalized:
        return 'p2d'
    if 'u.s.' in normalized:
        return 'us'
    if 's. ct.' in normalized or 's.ct.' in normalized:
        return 'sct'
    if 'l. ed.' in normalized or 'l.ed.' in normalized:
        return 'led'
    if 'f.3d' in normalized:
        return 'f3d'
    if 'f.2d' in normalized:
        return 'f2d'
    if 'f.' in normalized:
        return 'f'
    if 'wl' in normalized:
        return 'wl'
    return 'unknown'
"""

replacements['_match_parallel_patterns'] = """
def _match_parallel_patterns(self, citation1: str, citation2: str) -> bool:
    """Check if two citation texts match known parallel citation reporter combinations."""
    reporter1 = self._extract_reporter_type(citation1)
    reporter2 = self._extract_reporter_type(citation2)
    reporter_pair = frozenset({reporter1, reporter2})
    if 'unknown' in reporter_pair:
        return False

    valid_pairs = {
        frozenset({'wash', 'p3d'}),
        frozenset({'wash', 'p2d'}),
        frozenset({'wash_app', 'p3d'}),
        frozenset({'wash_app', 'p2d'}),
        frozenset({'us', 'sct'}),
        frozenset({'us', 'led'}),
        frozenset({'sct', 'led'}),
        frozenset({'f3d', 'us'}),
        frozenset({'f3d', 'sct'}),
        frozenset({'f', 'us'}),
        frozenset({'f', 'sct'}),
    }
    return reporter_pair in valid_pairs
"""

for name, body in replacements.items():
    pattern = re.compile(rf"    def {name}\([\s\S]*?(?=    def |\Z)")
    new_body = textwrap.dedent(body).strip('\n') + '\n'
    new_body = textwrap.indent(new_body, '    ')
    result, count = pattern.subn(new_body, text, count=1)
    if count != 1:
        raise SystemExit(f"Failed to replace function {name}")
    text = result

output_path = Path(r"d:\dev\casestrainer\src\unified_clustering_master_parallel_tmp.py")
if output_path.exists():
    raise SystemExit("Temporary output file already exists")

output_path.write_text(text, encoding="utf-8")
print("Updated clustering master written to unified_clustering_master_parallel_tmp.py")
