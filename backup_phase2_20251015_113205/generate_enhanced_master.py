from pathlib import Path

base_path = Path(r"d:\dev\casestrainer\src\unified_clustering_master.py")
if not base_path.exists():
    raise SystemExit("Base unified_clustering_master.py not found")

text = base_path.read_text(encoding="utf-8")

old_extract = """    def _extract_and_propagate_metadata(self, citations: List[Any], parallel_groups: List[List[Any]], text: str) -> List[Any]:
        \"\"\"Extract metadata from clusters and propagate to all members.\"\"\"
        enhanced_citations = []
        
        for group in parallel_groups:
            if not group:
                continue
            
            # Extract case name from first citation with a name
            case_name = None
            case_year = None
            
            for citation in group:
                extracted_name = getattr(citation, 'extracted_case_name', None)
                canonical_name = getattr(citation, 'canonical_name', None)
                
                if extracted_name and extracted_name != 'N/A':
                    case_name = extracted_name
                    break
                elif canonical_name and canonical_name != 'N/A':
                    case_name = canonical_name
                    break
            
            # Extract year from any citation with a year
            for citation in group:
                extracted_date = getattr(citation, 'extracted_date', None)
                canonical_date = getattr(citation, 'canonical_date', None)
                
                if extracted_date and extracted_date != 'N/A':
                    case_year = extracted_date
                    break
                elif canonical_date and canonical_date != 'N/A':
                    case_year = canonical_date
                    break
            
            # Propagate metadata to all citations in the group
            for citation in group:
                # Create enhanced citation object
                enhanced_citation = self._create_enhanced_citation(citation, case_name, case_year, group)
                enhanced_citations.append(enhanced_citation)
        
        return enhanced_citations
"""

new_extract = """    def _extract_and_propagate_metadata(self, citations: List[Any], parallel_groups: List[List[Any]], text: str) -> List[Any]:
        \"\"\"Extract metadata from clusters and propagate to all members.\"\"\"
        enhanced_citations = []
        
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
        
        return enhanced_citations
"""

old_create = """    def _create_enhanced_citation(self, citation: Any, case_name: Optional[str], case_year: Optional[str], group: List[Any]) -> Any:
        \"\"\"Create an enhanced citation object with propagated metadata.\"\"\"
        # Copy the original citation
        if hasattr(citation, '__dict__'):
            # Use copy.copy() to properly copy the object instead of creating empty instance
            import copy
            enhanced = copy.copy(citation)
        elif isinstance(citation, dict):
            enhanced = citation.copy()
        else:
            enhanced = citation
        
        # Add cluster metadata
        if hasattr(enhanced, '__dict__'):
            enhanced.cluster_case_name = case_name
            enhanced.cluster_year = case_year
            enhanced.cluster_size = len(group)
            enhanced.is_in_cluster = len(group) > 1
            enhanced.cluster_members = [getattr(c, 'citation', str(c)) for c in group]
            if case_name and case_name != 'N/A':
                current_name = getattr(enhanced, 'extracted_case_name', None)
                if not current_name or current_name in ('', 'N/A'):
                    enhanced.extracted_case_name = case_name
            if case_year and case_year != 'N/A':
                current_year = getattr(enhanced, 'extracted_date', None)
                if not current_year or current_year in ('', 'N/A'):
                    enhanced.extracted_date = case_year
        elif isinstance(enhanced, dict):
            enhanced['cluster_case_name'] = case_name
            enhanced['cluster_year'] = case_year
            enhanced['cluster_size'] = len(group)
            enhanced['is_in_cluster'] = len(group) > 1
            enhanced['cluster_members'] = [getattr(c, 'citation', str(c)) for c in group]
            if case_name and case_name != 'N/A':
                current_name = enhanced.get('extracted_case_name')
                if not current_name or current_name in ('', 'N/A'):
                    enhanced['extracted_case_name'] = case_name
            if case_year and case_year != 'N/A':
                current_year = enhanced.get('extracted_date')
                if not current_year or current_year in ('', 'N/A'):
                    enhanced['extracted_date'] = case_year
        
        return enhanced
"""

new_create = """    def _create_enhanced_citation(self, citation: Any, case_name: Optional[str], case_year: Optional[str], group: List[Any]) -> Any:
        \"\"\"Create an enhanced citation object with propagated metadata.\"\"\"
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
"""

old_format = """    def _format_clusters_for_output(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        \"\"\"Format clusters for final output and update citation objects with cluster IDs.\"\"\"
        formatted_clusters = []
        
        for cluster in clusters:
            cluster_id = cluster.get('cluster_id', 'unknown')
            formatted_cluster = {
                'cluster_id': cluster_id,
                'cluster_case_name': cluster.get('case_name', 'N/A'),
                'cluster_year': cluster.get('case_year', 'N/A'),
                'cluster_size': cluster.get('size', 0),
                'citations': cluster.get('citations', []),
                'confidence': cluster.get('confidence', 0.0),
                'verification_status': cluster.get('verification_status', 'not_verified'),
                'verification_source': cluster.get('verification_source', None),
                'metadata': cluster.get('metadata', {}),
                'cluster_members': []
            }
            
            # Add cluster members and update citation objects with cluster info
            citations = cluster.get('citations', [])
            for citation in citations:
                citation_text = getattr(citation, 'citation', str(citation))
                formatted_cluster['cluster_members'].append(citation_text)
                
                # CRITICAL: Update citation object with cluster information
                if hasattr(citation, 'cluster_id'):
                    citation.cluster_id = cluster_id
                if hasattr(citation, 'is_cluster'):
                    citation.is_cluster = len(citations) > 1
                if hasattr(citation, 'cluster_case_name'):
                    citation.cluster_case_name = cluster.get('case_name', 'N/A')
            
            formatted_clusters.append(formatted_cluster)
        
        return formatted_clusters
"""

new_format = """    def _format_clusters_for_output(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        \"\"\"Format clusters for final output and update citation objects with cluster IDs.\"\"\"
        formatted_clusters = []
        
        for cluster in clusters:
            cluster_id = cluster.get('cluster_id', 'unknown')
            citations = cluster.get('citations', [])
            
            best_name = cluster.get('case_name', 'N/A')
            if best_name in (None, '', 'N/A', 'Unknown', 'Unknown Case'):
                inferred_name = self._select_best_case_name(citations)
                if inferred_name:
                    best_name = inferred_name
            
            best_year = cluster.get('case_year', 'N/A')
            if best_year in (None, '', 'N/A', 'Unknown'):
                inferred_year = self._select_best_case_year(citations)
                if inferred_year:
                    best_year = inferred_year
            
            formatted_cluster = {
                'cluster_id': cluster_id,
                'cluster_case_name': best_name or 'N/A',
                'cluster_year': best_year or 'N/A',
                'cluster_size': cluster.get('size', 0),
                'citations': citations,
                'confidence': cluster.get('confidence', 0.0),
                'verification_status': cluster.get('verification_status', 'not_verified'),
                'verification_source': cluster.get('verification_source', None),
                'metadata': cluster.get('metadata', {}),
                'cluster_members': []
            }
            
            for citation in citations:
                citation_text = getattr(citation, 'citation', str(citation))
                formatted_cluster['cluster_members'].append(citation_text)
                
                if hasattr(citation, 'cluster_id'):
                    citation.cluster_id = cluster_id
                if hasattr(citation, 'is_cluster'):
                    citation.is_cluster = len(citations) > 1
                if hasattr(citation, 'cluster_case_name'):
                    citation.cluster_case_name = best_name or 'N/A'
                if hasattr(citation, 'cluster_year'):
                    citation.cluster_year = best_year or 'N/A'
                
                if isinstance(citation, dict):
                    citation['cluster_case_name'] = best_name or 'N/A'
                    citation['cluster_year'] = best_year or 'N/A'
            
            formatted_clusters.append(formatted_cluster)
        
        return formatted_clusters
"""

for original, replacement in (
    (old_extract, new_extract),
    (old_create, new_create),
    (old_format, new_format),
):
    if original not in text:
        raise SystemExit("Failed to locate block for replacement")
    text = text.replace(original, replacement)

enhanced_path = Path(r"d:\dev\casestrainer\src\unified_clustering_master_enhanced.py")
if enhanced_path.exists():
    raise SystemExit("Enhanced file already exists")

enhanced_path.write_text(text, encoding="utf-8")
print("Created unified_clustering_master_enhanced.py")
