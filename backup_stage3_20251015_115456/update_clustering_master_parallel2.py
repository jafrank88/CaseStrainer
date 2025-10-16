from pathlib import Path
from textwrap import dedent

FILE_PATH = Path(r"d:\dev\casestrainer\src\unified_clustering_master.py")
if not FILE_PATH.exists():
    raise SystemExit("unified_clustering_master.py not found")

text = FILE_PATH.read_text(encoding="utf-8")

old_detect = dedent('''
    def _detect_parallel_citations(self, citations: List[Any], text: str) -> List[List[Any]]:
        """Detect parallel citations using proximity and pattern analysis."""
        if not citations:
            return []
        
        parallel_groups = []
        processed_citations = set()
        
        # Group by proximity first
        proximity_groups = self._group_by_proximity(citations, text)
        
        for group in proximity_groups:
            if len(group) < 2:
                continue
                
            # Check if citations in this group are actually parallel
            if self._are_parallel_citations(group, text):
                parallel_groups.append(group)
                for citation in group:
                    processed_citations.add(id(citation))
        
        # Add remaining unprocessed citations as single-citation groups
        for citation in citations:
            if id(citation) not in processed_citations:
                parallel_groups.append([citation])
        
        return parallel_groups
''')

new_detect = dedent('''
    def _detect_parallel_citations(self, citations: List[Any], text: str) -> List[List[Any]]:
        """Detect parallel citations using both proximity and reporter-based analysis."""
        if not citations:
            return []

        parallel_groups: List[List[Any]] = []
        processed_ids: Set[int] = set()
        total = len(citations)

        # Build adjacency graph using reporter heuristics for robust detection
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
                for neighbor in adjacency[current]:
                    if neighbor not in visited:
                        stack.append(neighbor)

            if len(component) > 1:
                group = [citations[i] for i in component]
                parallel_groups.append(group)
                for citation in group:
                    processed_ids.add(id(citation))

        # For any citations not yet processed, fall back to proximity-based grouping
        remaining_citations = [citation for citation in citations if id(citation) not in processed_ids]
        if remaining_citations:
            proximity_groups = self._group_by_proximity(remaining_citations, text)
            for group in proximity_groups:
                if len(group) >= 2 and self._are_parallel_citations(group, text):
                    parallel_groups.append(group)
                    for citation in group:
                        processed_ids.add(id(citation))

        # Add any remaining single citations
        for citation in citations:
            if id(citation) not in processed_ids:
                parallel_groups.append([citation])

        return parallel_groups
''')

if old_detect not in text:
    raise SystemExit("Original _detect_parallel_citations block not found")

text = text.replace(old_detect, new_detect)

old_extract = dedent('''
        for group in parallel_groups:
            if not group:
                continue
            
            # Prefer scored selection but fall back to original heuristic
            case_name = self._select_best_case_name(group)
            case_year = self._select_best_case_year(group)
            
            if not case_name:
                for citation in group:
                    extracted_name = getattr(citation, 'extracted_case_name', None)
                    canonical_name = getattr(citation, 'canonical_name', None)
                    
                    if extracted_name and extracted_name != 'N/A':
                        case_name = extracted_name
                        break
                    if canonical_name and canonical_name != 'N/A':
                        case_name = canonical_name
                        break
            
            if not case_year:
                for citation in group:
                    extracted_date = getattr(citation, 'extracted_date', None)
                    canonical_date = getattr(citation, 'canonical_date', None)
                    
                    if extracted_date and extracted_date != 'N/A':
                        case_year = extracted_date
                        break
                    if canonical_date and canonical_date != 'N/A':
                        case_year = canonical_date
                        break
            
            # Propagate metadata to all citations in the group
            for citation in group:
                enhanced_citation = self._create_enhanced_citation(citation, case_name, case_year, group)
                enhanced_citations.append(enhanced_citation)
''')

new_extract = dedent('''
        for group in parallel_groups:
            if not group:
                continue

            # Prefer canonical data from verified citations when available
            canonical_candidates: List[str] = []
            canonical_years: List[str] = []
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
                    canonical_candidates.append(canonical_name)
                if verified and canonical_date and canonical_date != 'N/A':
                    canonical_years.append(canonical_date)

            case_name = None
            case_year = None

            if canonical_candidates:
                case_name = max(canonical_candidates, key=self._score_case_name)
            else:
                case_name = self._select_best_case_name(group)

            if canonical_years:
                from collections import Counter
                case_year = Counter(canonical_years).most_common(1)[0][0]
            else:
                case_year = self._select_best_case_year(group)

            if not case_name:
                for citation in group:
                    extracted_name = getattr(citation, 'extracted_case_name', None)
                    canonical_name = getattr(citation, 'canonical_name', None)

                    if extracted_name and extracted_name != 'N/A':
                        case_name = extracted_name
                        break
                    if canonical_name and canonical_name != 'N/A':
                        case_name = canonical_name
                        break

            if not case_year:
                for citation in group:
                    extracted_date = getattr(citation, 'extracted_date', None)
                    canonical_date = getattr(citation, 'canonical_date', None)

                    if extracted_date and extracted_date != 'N/A':
                        case_year = extracted_date
                        break
                    if canonical_date and canonical_date != 'N/A':
                        case_year = canonical_date
                        break

            for citation in group:
                enhanced_citation = self._create_enhanced_citation(citation, case_name, case_year, group)
                enhanced_citations.append(enhanced_citation)
''')

if old_extract not in text:
    raise SystemExit("Original metadata propagation block not found")

text = text.replace(old_extract, new_extract)

output_path = Path(r"d:\dev\casestrainer\src\unified_clustering_master_parallel_tmp.py")
if output_path.exists():
    raise SystemExit("Temporary output file already exists")

output_path.write_text(text, encoding="utf-8")
print("Wrote updated clustering master to unified_clustering_master_parallel_tmp.py")
