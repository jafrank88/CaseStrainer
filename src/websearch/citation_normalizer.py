"""
Citation Normalization Module
Handles citation normalization and variant generation.
"""

import re
from typing import Dict, List, Any


class EnhancedCitationNormalizer:
    """Advanced citation normalization with ML-enhanced variant generation."""
    
    def __init__(self):
        self.citation_patterns = {
            'washington': [
                r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)',
                r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)',
                r'(\d+)\s+Wash\.?\s*(\d+[a-z]?)\s+(\d+)',
                r'(\d+)\s+Washington\s+(\d+[a-z]?)\s+(\d+)',
            ],
            'federal': [
                r'(\d+)\s+U\.?S\.?\s+(\d+)',
                r'(\d+)\s+F\.?\s*(\d+[a-z]?)\s+(\d+)',
                r'(\d+)\s+F\.?\s*Supp\.?\s*(\d+[a-z]?)\s+(\d+)',
                r'(\d+)\s+Fed\.?\s*(\d+[a-z]?)\s+(\d+)',
            ],
            'pacific': [
                r'(\d+)\s+P\.?\s*(\d+[a-z]?)\s+(\d+)',
                r'(\d+)\s+Pac\.?\s*(\d+[a-z]?)\s+(\d+)',
                r'(\d+)\s+Pacific\s+(\d+[a-z]?)\s+(\d+)',
            ]
        }
        
        # Common abbreviation mappings
        self.abbreviation_map = {
            'Wn.': ['Wash.', 'Washington'],
            'Wash.': ['Wn.', 'Washington'],
            'Washington': ['Wn.', 'Wash.'],
            'P.': ['Pac.', 'Pacific'],
            'Pac.': ['P.', 'Pacific'],
            'Pacific': ['P.', 'Pac.'],
            'F.': ['Fed.', 'Federal'],
            'Fed.': ['F.', 'Federal'],
            'U.S.': ['US', 'United States'],
            'App.': ['Ct. App.', 'Court of Appeals'],
        }
    
    def normalize_citation(self, citation: str) -> str:
        """Normalize a citation to standard format."""
        if not citation:
            return ""
        
        # Clean up whitespace
        citation = re.sub(r'\s+', ' ', citation.strip())
        
        # Standardize common patterns
        citation = re.sub(r'(\d+)\s*Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3', citation)
        citation = re.sub(r'(\d+)\s*P\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 P. \2 \3', citation)
        citation = re.sub(r'(\d+)\s*U\.?\s*S\.?\s+(\d+)', r'\1 U.S. \2', citation)
        citation = re.sub(r'(\d+)\s*F\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 F. \2 \3', citation)
        
        return citation.strip()
    
    def generate_variants(self, citation: str) -> List[str]:
        """Generate comprehensive citation variants using enhanced algorithms."""
        if not citation:
            return []
        
        variants = set([citation])
        normalized = self.normalize_citation(citation)
        if normalized != citation:
            variants.add(normalized)
        
        # Generate variants based on abbreviation mappings
        for abbrev, replacements in self.abbreviation_map.items():
            if abbrev in citation:
                for replacement in replacements:
                    variant = citation.replace(abbrev, replacement)
                    variants.add(variant)
                    # Also try with the normalized version
                    variant_norm = self.normalize_citation(variant)
                    variants.add(variant_norm)
        
        # Generate spacing variants
        for variant in list(variants):
            # Try with different spacing
            spaced = re.sub(r'(\d+)([A-Za-z])', r'\1 \2', variant)
            variants.add(spaced)
            
            # Try without spaces
            nospaces = re.sub(r'(\d+)\s+([A-Za-z])', r'\1\2', variant)
            variants.add(nospaces)
        
        # Generate ordinal variants (2d vs 2nd, 3d vs 3rd)
        for variant in list(variants):
            ordinal_variant = re.sub(r'(\d+)(d)\b', r'\1\2', variant)
            variants.add(ordinal_variant)
            
            full_ordinal = re.sub(r'(\d+)d\b', lambda m: f"{m.group(1)}{'nd' if m.group(1).endswith('2') else 'rd' if m.group(1).endswith('3') else 'th'}", variant)
            variants.add(full_ordinal)
        
        return list(variants)
    
    def extract_citation_components(self, citation: str) -> Dict[str, Any]:
        """Extract structured components from a citation."""
        components: Dict[str, Any] = {
            'volume': None,
            'reporter': None,
            'page': None,
            'year': None,
            'court': None,
            'series': None
        }
        
        # Try different patterns
        patterns = [
            r'(\d+)\s+([A-Za-z\.]+)\s*(\d+[a-z]?)\s+(\d+)\s*\(([^)]+)\s*(\d{4})\)',
            r'(\d+)\s+([A-Za-z\.]+)\s*(\d+[a-z]?)\s+(\d+)\s*\((\d{4})\)',
            r'(\d+)\s+([A-Za-z\.]+)\s*(\d+[a-z]?)\s+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, citation)
            if match:
                components['volume'] = match.group(1)
                components['reporter'] = match.group(2)
                components['series'] = match.group(3) if len(match.groups()) >= 3 else None
                components['page'] = match.group(4) if len(match.groups()) >= 4 else match.group(3)
                
                if len(match.groups()) >= 6:
                    components['court'] = match.group(5)
                    components['year'] = match.group(6)
                elif len(match.groups()) >= 5:
                    components['year'] = match.group(5)
                
                break
        
        return components 