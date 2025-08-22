"""
Enhanced search strategy for legal citations with better query generation
and result filtering specifically for legal content.
"""

import re
from typing import List, Dict, Any
from urllib.parse import quote_plus

class EnhancedLegalSearchEngine:
    """Enhanced legal citation search with better query strategies."""
    
    def __init__(self):
        # Legal-specific domains that should be prioritized
        self.legal_domains = {
            'justia.com': 95,
            'caselaw.findlaw.com': 90, 
            'findlaw.com': 85,
            'courtlistener.com': 100,
            'leagle.com': 85,
            'casetext.com': 80,
            'law.cornell.edu': 80,
            'google.com/scholar': 75,
            'vlex.com': 70
        }
        
        # Washington state specific patterns
        self.washington_patterns = [
            r'(\d+)\s+Wn\.?\s*2d\s+(\d+)',
            r'(\d+)\s+Wn\.?\s*3d\s+(\d+)', 
            r'(\d+)\s+Wn\.?\s*App\.?\s*2d\s+(\d+)',
            r'(\d+)\s+Wash\.?\s*2d\s+(\d+)',
            r'(\d+)\s+Washington\s+2d\s+(\d+)'
        ]

    def generate_enhanced_legal_queries(self, citation: str) -> List[Dict[str, Any]]:
        """Generate legal-specific search queries with context, for all major citation variants."""
        queries = []
        
        # Clean and normalize the citation first
        normalized_citation = self.normalize_citation(citation)
        
        # Generate all major variants (including the original citation)
        variants = set([citation.strip(), normalized_citation])
        if self.is_washington_citation(citation):
            variants.update(self.generate_washington_variants(citation))
        
        # For each variant, generate all query strategies
        for variant in variants:
            # Strategy 1: Exact citation with legal context keywords
            legal_contexts = [
                f'"{variant}" case law',
                f'"{variant}" court decision', 
                f'"{variant}" legal opinion',
                f'"{variant}" judgment',
                f'"{variant}" Washington Supreme Court',
                f'"{variant}" Washington Court of Appeals'
            ]
            for context_query in legal_contexts:
                queries.append({
                    'query': context_query,
                    'priority': 1,
                    'type': 'legal_context',
                    'citation': variant
                })
            # Strategy 2: Site-specific searches on legal databases
            legal_sites = [
                'site:justia.com',
                'site:caselaw.findlaw.com', 
                'site:courtlistener.com',
                'site:leagle.com',
                'site:casetext.com',
                'site:law.cornell.edu'
            ]
            for site in legal_sites:
                queries.append({
                    'query': f'{site} "{variant}"',
                    'priority': 2,
                    'type': 'site_specific',
                    'citation': variant,
                    'site': site
                })
            # Strategy 3: Washington-specific context (if applicable)
            if self.is_washington_citation(variant):
                queries.append({
                    'query': f'"{variant}" Washington state court',
                    'priority': 3,
                    'type': 'washington_variant',
                    'citation': variant
                })
            # Strategy 4: Broader legal database searches
            broad_queries = [
                f'"{variant}" filetype:pdf',
                f'"{variant}" "Wn.2d" OR "Wash.2d"',
                f'legal citation "{variant}"'
            ]
            for broad_query in broad_queries:
                queries.append({
                    'query': broad_query,
                    'priority': 4, 
                    'type': 'broad_legal',
                    'citation': variant
                })
        return queries

    def normalize_citation(self, citation: str) -> str:
        """Normalize citation for better search results."""
        # Clean whitespace
        citation = re.sub(r'\s+', ' ', citation.strip())
        
        # Ensure proper periods in Washington citations
        citation = re.sub(r'Wn\s+(\d+d)', r'Wn. \1', citation)
        citation = re.sub(r'Wn(\d+d)', r'Wn. \1', citation)
        
        # Standardize "2d" vs "2nd"
        citation = re.sub(r'\b2nd\b', '2d', citation)
        citation = re.sub(r'\b3rd\b', '3d', citation) 
        
        return citation

    def generate_washington_variants(self, citation: str) -> List[str]:
        """Generate Washington-specific citation variants."""
        variants = []
        
        # Match Washington citation pattern
        match = re.search(r'(\d+)\s+Wn\.?\s*(\d+d)\s+(\d+)', citation, re.IGNORECASE)
        if match:
            volume, series, page = match.groups()
            
            # Generate multiple formats
            variants.extend([
                f"{volume} Wn. {series} {page}",
                f"{volume} Wash. {series} {page}", 
                f"{volume} Washington {series} {page}",
                f"{volume} Wn.{series} {page}",
                f"{volume} Wash.{series} {page}"
            ])
        
        return variants

    def is_washington_citation(self, citation: str) -> bool:
        """Check if citation is from Washington state."""
        washington_indicators = [
            r'\bWn\.?\s*\d+d\b',
            r'\bWash\.?\s*\d+d\b', 
            r'\bWashington\s*\d+d\b'
        ]
        
        for pattern in washington_indicators:
            if re.search(pattern, citation, re.IGNORECASE):
                return True
        return False

    def filter_legal_results(self, results: List[Dict]) -> List[Dict]:
        """Filter results to only include those from approved legal domains."""
        approved_domains = [
            'justia.com',
            'caselaw.findlaw.com',
            'findlaw.com',
            'courtlistener.com',
            'leagle.com',
            'casetext.com',
            'law.cornell.edu',
            'vlex.com',
            'scholar.google.com',
            'cetient.com',
            'openjurist.org',
            'supremecourt.gov',
            'uscourts.gov',
            'law.duke.edu',
            'westlaw.com',
            'lexis.com'
        ]
        legal_results = []
        for result in results:
            url = result.get('url', '').lower()
            # Only include if from an approved domain
            if any(domain in url for domain in approved_domains):
                result['legal_relevance_score'] = 100  # Max score for approved domain
                legal_results.append(result)
        # Sort by score if needed
        legal_results.sort(key=lambda x: x.get('legal_relevance_score', 0), reverse=True)
        return legal_results

    def search_with_enhanced_strategy(self, citation: str, max_results: int = 10) -> List[Dict]:
        """
        Search using enhanced legal-specific strategy.
        This would integrate with the existing search infrastructure.
        """
        # Generate legal-focused queries
        queries = self.generate_enhanced_legal_queries(citation)
        
        all_results = []
        seen_urls = set()
        
        # Execute top priority queries first
        priority_queries = sorted(queries, key=lambda x: x['priority'])[:15]
        
        for query_info in priority_queries:
            query = query_info['query']
            
            # Here you would call the existing search engines
            # results = self.search_with_engine(query, 'google', num_results=3)
            # results.extend(self.search_with_engine(query, 'bing', num_results=3))
            
            # For demo purposes, showing the query structure
            print(f"Priority {query_info['priority']}: {query}")
            
            # In real implementation, filter and add results
            # for result in results:
            #     if result['url'] not in seen_urls:
            #         seen_urls.add(result['url'])
            #         all_results.append(result)
        
        # Filter for legal content
        legal_results = self.filter_legal_results(all_results)
        
        return legal_results[:max_results]

# Example usage
def test_enhanced_search():
    """Test the enhanced legal search strategy."""
    engine = EnhancedLegalSearchEngine()
    
    # Test citation
    citation = "200 Wn. 2d 72"
    
    print(f"Testing enhanced search for: {citation}")
    print(f"Is Washington citation: {engine.is_washington_citation(citation)}")
    print(f"Normalized: {engine.normalize_citation(citation)}")
    
    print("\nWashington variants:")
    variants = engine.generate_washington_variants(citation)
    for i, variant in enumerate(variants, 1):
        print(f"  {i}. {variant}")
    
    print("\nGenerated queries:")
    queries = engine.generate_enhanced_legal_queries(citation)
    for i, query in enumerate(queries[:10], 1):  # Show first 10
        print(f"  {i}. Priority {query['priority']}: {query['query']}")

if __name__ == "__main__":
    test_enhanced_search() 