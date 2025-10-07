from pathlib import Path

FILE_PATH = Path(r"d:\dev\casestrainer\src\unified_clustering_master.py")
if not FILE_PATH.exists():
    raise SystemExit("unified_clustering_master.py not found")

text = FILE_PATH.read_text(encoding="utf-8")

old_are = '''    def _are_parallel_citations(self, citations: List[Any], text: str) -> bool:
        """Check if citations are parallel (refer to the same case)."""
        if len(citations) < 2:
            return False
        
        # Extract citation texts
        citation_texts = []
        for citation in citations:
            if hasattr(citation, 'citation'):
                citation_texts.append(citation.citation)
            elif isinstance(citation, dict):
                citation_texts.append(citation.get('citation', ''))
            else:
                citation_texts.append(str(citation))
        
        # Check for parallel patterns
        for pattern_name, pattern in self.patterns.items():
            if 'parallel' in pattern_name:
                for text_segment in citation_texts:
                    if pattern.search(text_segment):
                        return True
        
        # Check for similar case names (if available)
        case_names = []
        for citation in citations:
            case_name = getattr(citation, 'extracted_case_name', None) or getattr(citation, 'canonical_name', None)
            if case_name and case_name != 'N/A':
                case_names.append(case_name)
        
        if len(case_names) >= 2:
            # Check if case names are similar
            for i in range(len(case_names)):
                for j in range(i + 1, len(case_names)):
                    similarity = self._calculate_name_similarity(case_names[i], case_names[j])
                    if similarity >= self.case_name_similarity_threshold:
                        return True
        
        return False
'''

new_are = '''    def _are_parallel_citations(self, citations: List[Any], text: str) -> bool:
        """Check if citations are parallel (refer to the same case)."""
        if len(citations) < 2:
            return False

        citation_texts = []
        citation_lookup = {}
        for citation in citations:
            if hasattr(citation, 'citation'):
                citation_text = citation.citation
            elif isinstance(citation, dict):
                citation_text = citation.get('citation', '')
            else:
                citation_text = str(citation)
            citation_texts.append(citation_text)
            citation_lookup[citation_text] = citation

        # Respect explicit parallel_citations metadata when present
        for citation in citations:
            if isinstance(citation, dict):
                parallels = citation.get('parallel_citations', []) or []
            else:
                parallels = getattr(citation, 'parallel_citations', []) or []
            for parallel_text in parallels:
                if parallel_text in citation_lookup:
                    return True

        # Check for regex-based parallel patterns
        for pattern_name, pattern in self.patterns.items():
            if 'parallel' in pattern_name:
                for text_segment in citation_texts:
                    if pattern.search(text_segment):
                        return True

        # Reporter-based heuristic comparisons
        for i in range(len(citations)):
            for j in range(i + 1, len(citations)):
                if self._are_citations_parallel_pair(citations[i], citations[j], text):
                    return True

        # Fallback: compare available case names for similarity
        case_names = []
        for citation in citations:
            case_name = (
                getattr(citation, 'canonical_name', None)
                or getattr(citation, 'cluster_case_name', None)
                or getattr(citation, 'extracted_case_name', None)
            )
            if case_name and case_name != 'N/A':
                case_names.append(case_name)

        if len(case_names) >= 2:
            for i in range(len(case_names)):
                for j in range(i + 1, len(case_names)):
                    similarity = self._calculate_name_similarity(case_names[i], case_names[j])
                    if similarity >= self.case_name_similarity_threshold:
                        return True

        return False

    def _are_citations_parallel_pair(self, citation1: Any, citation2: Any, text: str) -> bool:
        """Determine if two citations are likely parallel citations."""
        # Extract citation text
        if isinstance(citation1, dict):
            citation1_text = citation1.get('citation', '')
        else:
            citation1_text = getattr(citation1, 'citation', str(citation1))

        if isinstance(citation2, dict):
            citation2_text = citation2.get('citation', '')
        else:
            citation2_text = getattr(citation2, 'citation', str(citation2))

        reporter1 = self._extract_reporter_type(citation1_text)
        reporter2 = self._extract_reporter_type(citation2_text)

        if reporter1 == reporter2 or 'unknown' in (reporter1, reporter2):
            return False

        if not self._match_parallel_patterns(citation1_text, citation2_text):
            return False

        # Washington-specific handling
        if 'wash' in reporter1 or 'wash' in reporter2:
            if not self._check_washington_parallel_patterns(citation1_text, citation2_text):
                return False

        def get_start_index(cit: Any) -> int:
            if isinstance(cit, dict):
                return cit.get('start_index', cit.get('start', 0))
            return getattr(cit, 'start_index', getattr(cit, 'start', 0))

        start1 = get_start_index(citation1)
        start2 = get_start_index(citation2)
        if abs(start1 - start2) > self.proximity_threshold:
            return False

        def get_case_name(cit: Any) -> Optional[str]:
            if isinstance(cit, dict):
                return (
                    cit.get('canonical_name')
                    or cit.get('cluster_case_name')
                    or cit.get('extracted_case_name')
                )
            return (
                getattr(cit, 'canonical_name', None)
                or getattr(cit, 'cluster_case_name', None)
                or getattr(cit, 'extracted_case_name', None)
            )

        name1 = get_case_name(citation1)
        name2 = get_case_name(citation2)
        if name1 and name2 and name1 != 'N/A' and name2 != 'N/A':
            similarity = self._calculate_name_similarity(name1, name2)
            if similarity < self.case_name_similarity_threshold:
                return False

        def get_year(cit: Any) -> Optional[str]:
            if isinstance(cit, dict):
                return cit.get('canonical_date') or cit.get('cluster_year') or cit.get('extracted_date')
            return (
                getattr(cit, 'canonical_date', None)
                or getattr(cit, 'cluster_year', None)
                or getattr(cit, 'extracted_date', None)
            )

        year1 = get_year(citation1)
        year2 = get_year(citation2)
        if year1 and year2 and year1 != 'N/A' and year2 != 'N/A' and year1 != year2:
            return False

        return True

    def _extract_reporter_type(self, citation_text: str) -> str:
        """Extract a simplified reporter type token from citation text."""
        normalized = citation_text.lower()
        if 'wn.2d' in normalized or 'wash. 2d' in normalized or 'wash.2d' in normalized:
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

    def _match_parallel_patterns(self, citation1: str, citation2: str) -> bool:
        """Check if two citation texts match known parallel citation reporter combinations."""
        reporter_pair = frozenset({self._extract_reporter_type(citation1), self._extract_reporter_type(citation2)})
        if 'unknown' in reporter_pair:
            return False

        valid_pairs = {
            frozenset({'wash', 'p3d'}),
            frozenset({'wash', 'p2d'}),
            frozenset({'us', 'sct'}),
            frozenset({'us', 'led'}),
            frozenset({'sct', 'led'}),
            frozenset({'f3d', 'us'}),
            frozenset({'f3d', 'sct'}),
            frozenset({'f', 'us'}),
            frozenset({'f', 'sct'}),
        }
        return reporter_pair in valid_pairs

    def _check_washington_parallel_patterns(self, citation1: str, citation2: str) -> bool:
        """Specifically validate Washington reporter pairings (Wn./Wash. with P. reporters)."""
        normalized1 = citation1.lower()
        normalized2 = citation2.lower()
        has_wash = any(token in normalized1 or token in normalized2 for token in ('wn.2d', 'wash.2d', 'wash.'))
        has_p = any(token in normalized1 or token in normalized2 for token in ('p.3d', 'p.2d'))
        return has_wash and has_p
'''

old_create = '''    def _create_enhanced_citation(self, citation: Any, case_name: Optional[str], case_year: Optional[str], group: List[Any]) -> Any:
        """Create an enhanced citation object with propagated metadata."""
        # Copy the original citation
        if hasattr(citation, '__dict__'):
            import copy
            enhanced = copy.copy(citation)
        elif isinstance(citation, dict):
            enhanced = citation.copy()
        else:
            enhanced = citation
        
        members = [getattr(c, 'citation', str(c)) for c in group]
        citation_text = getattr(citation, 'citation', str(citation))
        parallel = len(group) > 1
        
        if hasattr(enhanced, '__dict__'):
            enhanced.cluster_case_name = case_name
            enhanced.cluster_year = case_year
            enhanced.cluster_size = len(group)
            enhanced.is_in_cluster = parallel
            enhanced.cluster_members = members
            
            if case_name and case_name != 'N/A':
                current_name = getattr(enhanced, 'extracted_case_name', None)
                if self._should_replace_case_name(current_name, case_name):
                    enhanced.extracted_case_name = case_name
            if case_year and case_year != 'N/A':
                current_year = getattr(enhanced, 'extracted_date', None)
                if not current_year or current_year in ('', 'N/A', 'Unknown'):
                    enhanced.extracted_date = case_year
            
            enhanced.is_parallel = parallel
            enhanced.parallel_citations = [member for member in members if member != citation_text]
        elif isinstance(enhanced, dict):
            enhanced['cluster_case_name'] = case_name
            enhanced['cluster_year'] = case_year
            enhanced['cluster_size'] = len(group)
            enhanced['is_in_cluster'] = parallel
            enhanced['cluster_members'] = members
            
            if case_name and case_name != 'N/A':
                current_name = enhanced.get('extracted_case_name')
                if self._should_replace_case_name(current_name, case_name):
                    enhanced['extracted_case_name'] = case_name
            if case_year and case_year != 'N/A':
                current_year = enhanced.get('extracted_date')
                if not current_year or current_year in ('', 'N/A', 'Unknown'):
                    enhanced['extracted_date'] = case_year
            
            enhanced['is_parallel'] = parallel
            enhanced['parallel_citations'] = [member for member in members if member != enhanced.get('citation', str(enhanced))]
        
        return enhanced
'''

new_create = '''    def _create_enhanced_citation(self, citation: Any, case_name: Optional[str], case_year: Optional[str], group: List[Any]) -> Any:
        """Create an enhanced citation object with propagated metadata."""
        if hasattr(citation, '__dict__'):
            import copy
            enhanced = copy.copy(citation)
        elif isinstance(citation, dict):
            enhanced = citation.copy()
        else:
            enhanced = citation

        # Incorporate canonical data when available
        if isinstance(citation, dict):
            canonical_name = citation.get('canonical_name')
            canonical_date = citation.get('canonical_date')
            verified_flag = citation.get('verified', False)
        else:
            canonical_name = getattr(citation, 'canonical_name', None)
            canonical_date = getattr(citation, 'canonical_date', None)
            verified_flag = getattr(citation, 'verified', False)

        if not case_name and canonical_name and canonical_name != 'N/A':
            case_name = canonical_name
        if not case_year and canonical_date and canonical_date != 'N/A':
            case_year = canonical_date

        members = [getattr(c, 'citation', str(c)) for c in group]
        citation_text = getattr(citation, 'citation', str(citation))
        parallel = len(group) > 1

        if hasattr(enhanced, '__dict__'):
            enhanced.cluster_case_name = case_name
            enhanced.cluster_year = case_year
            enhanced.cluster_size = len(group)
            enhanced.is_in_cluster = parallel
            enhanced.cluster_members = members

            if case_name and case_name != 'N/A':
                current_name = getattr(enhanced, 'extracted_case_name', None)
                if self._should_replace_case_name(current_name, case_name):
                    enhanced.extracted_case_name = case_name
            if verified_flag and canonical_name and canonical_name != 'N/A':
                current_name = getattr(enhanced, 'extracted_case_name', None)
                if self._should_replace_case_name(current_name, canonical_name):
                    enhanced.extracted_case_name = canonical_name
            if case_year and case_year != 'N/A':
                current_year = getattr(enhanced, 'extracted_date', None)
                if not current_year or current_year in ('', 'N/A', 'Unknown'):
                    enhanced.extracted_date = case_year
            if verified_flag and canonical_date and canonical_date != 'N/A':
                current_year = getattr(enhanced, 'extracted_date', None)
                if not current_year or current_year in ('', 'N/A', 'Unknown'):
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
            if verified_flag and canonical_name and canonical_name != 'N/A':
                current_name = enhanced.get('extracted_case_name')
                if self._should_replace_case_name(current_name, canonical_name):
                    enhanced['extracted_case_name'] = canonical_name

            current_year = enhanced.get('extracted_date')
            if case_year and case_year != 'N/A' and (not current_year or current_year in ('', 'N/A', 'Unknown')):
                enhanced['extracted_date'] = case_year
            if verified_flag and canonical_date and canonical_date != 'N/A':
                current_year = enhanced.get('extracted_date')
                if not current_year or current_year in ('', 'N/A', 'Unknown'):
                    enhanced['extracted_date'] = canonical_date

            enhanced['is_parallel'] = parallel
            enhanced['parallel_citations'] = [member for member in members if member != enhanced.get('citation', str(enhanced))]

        return enhanced
'''

if old_are not in text:
    raise SystemExit("Original _are_parallel_citations block not found")
if old_create not in text:
    raise SystemExit("Original _create_enhanced_citation block not found")

text = text.replace(old_are, new_are)
text = text.replace(old_create, new_create)

output_path = Path(r"d:\dev\casestrainer\src\unified_clustering_master_updated.py")
if output_path.exists():
    raise SystemExit("unified_clustering_master_updated.py already exists")

output_path.write_text(text, encoding="utf-8")
print("Updated file written to unified_clustering_master_updated.py")
