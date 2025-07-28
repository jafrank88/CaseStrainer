#!/usr/bin/env python3
"""
Deep root cause analysis for PDF vs. text clustering differences.

Based on the investigation results, this script identifies specific issues:
1. Eyecite extraction differences between PDF and text
2. Citation formatting inconsistencies 
3. Context extraction problems
4. Clustering algorithm sensitivity to text differences
"""

import sys
import os
import json
import re
from typing import Dict, List, Any, Set, Tuple
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services import CitationExtractor
from src.models import ProcessingConfig

class RootCauseAnalyzer:
    """Analyze root causes of PDF vs. text differences."""
    
    def __init__(self):
        self.config = ProcessingConfig(debug_mode=True)
        
    def load_investigation_results(self) -> Dict[str, Any]:
        """Load the investigation results."""
        with open('pdf_vs_txt_investigation_results.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def analyze_citation_format_differences(self, results: Dict[str, Any]):
        """Analyze differences in citation formats between PDF and text."""
        print("="*60)
        print("CITATION FORMAT ANALYSIS")
        print("="*60)
        
        pdf_citations = results['pdf_results']['citations']
        txt_citations = results['txt_results']['citations']
        
        # Categorize citations by type
        pdf_types = self.categorize_citations(pdf_citations)
        txt_types = self.categorize_citations(txt_citations)
        
        print("Citation Type Distribution:")
        print(f"{'Type':<25} {'PDF Count':<12} {'TXT Count':<12} {'Difference'}")
        print("-" * 60)
        
        all_types = set(pdf_types.keys()) | set(txt_types.keys())
        for citation_type in sorted(all_types):
            pdf_count = pdf_types.get(citation_type, 0)
            txt_count = txt_types.get(citation_type, 0)
            diff = abs(pdf_count - txt_count)
            print(f"{citation_type:<25} {pdf_count:<12} {txt_count:<12} {diff}")
        
        # Identify problematic citation formats
        self.identify_problematic_formats(pdf_citations, txt_citations)
    
    def categorize_citations(self, citations: List[Dict]) -> Dict[str, int]:
        """Categorize citations by their format type."""
        types = {}
        
        for citation in citations:
            citation_text = citation['citation']
            
            # Determine citation type
            if citation_text.startswith('FullCaseCitation'):
                citation_type = 'FullCaseCitation'
            elif citation_text.startswith('ShortCaseCitation'):
                citation_type = 'ShortCaseCitation'
            elif citation_text.startswith('SupraCitation'):
                citation_type = 'SupraCitation'
            elif citation_text.startswith('UnknownCitation'):
                citation_type = 'UnknownCitation'
            elif re.match(r'\d+\s+[A-Z][\w\s\.]+\s+\d+', citation_text):
                citation_type = 'StandardFormat'
            else:
                citation_type = 'Other'
            
            types[citation_type] = types.get(citation_type, 0) + 1
        
        return types
    
    def identify_problematic_formats(self, pdf_citations: List[Dict], txt_citations: List[Dict]):
        """Identify specific problematic citation formats."""
        print("\nProblematic Citation Analysis:")
        print("-" * 40)
        
        # Find citations that appear malformed
        pdf_malformed = []
        txt_malformed = []
        
        for citation in pdf_citations:
            if self.is_malformed_citation(citation['citation']):
                pdf_malformed.append(citation['citation'])
        
        for citation in txt_citations:
            if self.is_malformed_citation(citation['citation']):
                txt_malformed.append(citation['citation'])
        
        print(f"Malformed citations in PDF: {len(pdf_malformed)}")
        if pdf_malformed:
            for i, citation in enumerate(pdf_malformed[:3]):  # Show first 3
                print(f"  {i+1}. {citation[:100]}...")
        
        print(f"Malformed citations in TXT: {len(txt_malformed)}")
        if txt_malformed:
            for i, citation in enumerate(txt_malformed[:3]):  # Show first 3
                print(f"  {i+1}. {citation[:100]}...")
    
    def is_malformed_citation(self, citation_text: str) -> bool:
        """Check if a citation appears malformed."""
        # Citations that start with object representations are malformed
        if citation_text.startswith(('FullCaseCitation(', 'ShortCaseCitation(', 'SupraCitation(', 'UnknownCitation(')):
            return True
        
        # Citations with unusual characters or formatting
        if len(citation_text) > 200:  # Unusually long
            return True
        
        if citation_text.count('(') != citation_text.count(')'):  # Unbalanced parentheses
            return True
        
        return False
    
    def analyze_context_extraction_differences(self, results: Dict[str, Any]):
        """Analyze differences in context extraction."""
        print("\n" + "="*60)
        print("CONTEXT EXTRACTION ANALYSIS")
        print("="*60)
        
        pdf_citations = results['pdf_results']['citations']
        txt_citations = results['txt_results']['citations']
        
        # Compare context extraction for similar citations
        pdf_contexts = {c['citation']: c.get('extracted_case_name', '') for c in pdf_citations}
        txt_contexts = {c['citation']: c.get('extracted_case_name', '') for c in txt_citations}
        
        # Find citations with different context extraction
        context_differences = []
        
        for citation in set(pdf_contexts.keys()) & set(txt_contexts.keys()):
            pdf_context = pdf_contexts[citation]
            txt_context = txt_contexts[citation]
            
            if pdf_context != txt_context:
                context_differences.append({
                    'citation': citation,
                    'pdf_context': pdf_context,
                    'txt_context': txt_context
                })
        
        print(f"Citations with different context extraction: {len(context_differences)}")
        
        if context_differences:
            print("\nExamples of context differences:")
            for i, diff in enumerate(context_differences[:3]):
                print(f"\n{i+1}. Citation: {diff['citation'][:50]}...")
                print(f"   PDF context: {diff['pdf_context'][:100]}...")
                print(f"   TXT context: {diff['txt_context'][:100]}...")
    
    def analyze_clustering_sensitivity(self, results: Dict[str, Any]):
        """Analyze clustering algorithm sensitivity to differences."""
        print("\n" + "="*60)
        print("CLUSTERING SENSITIVITY ANALYSIS")
        print("="*60)
        
        pdf_clusters = results['pdf_results']['clusters']
        txt_clusters = results['txt_results']['clusters']
        
        # Analyze cluster size distributions
        pdf_sizes = [cluster['size'] for cluster in pdf_clusters]
        txt_sizes = [cluster['size'] for cluster in txt_clusters]
        
        print("Cluster Size Distribution:")
        print(f"PDF - Average: {sum(pdf_sizes)/len(pdf_sizes):.1f}, Max: {max(pdf_sizes)}, Min: {min(pdf_sizes)}")
        print(f"TXT - Average: {sum(txt_sizes)/len(txt_sizes):.1f}, Max: {max(txt_sizes)}, Min: {min(txt_sizes)}")
        
        # Find clusters that should be the same but aren't
        self.identify_clustering_inconsistencies(pdf_clusters, txt_clusters)
    
    def identify_clustering_inconsistencies(self, pdf_clusters: List[Dict], txt_clusters: List[Dict]):
        """Identify specific clustering inconsistencies."""
        print("\nClustering Inconsistencies:")
        print("-" * 30)
        
        # Look for clusters with the same canonical name but different sizes
        pdf_canonical_clusters = {}
        txt_canonical_clusters = {}
        
        for cluster in pdf_clusters:
            canonical = cluster.get('canonical_name', 'N/A')
            if canonical != 'N/A':
                pdf_canonical_clusters[canonical] = cluster
        
        for cluster in txt_clusters:
            canonical = cluster.get('canonical_name', 'N/A')
            if canonical != 'N/A':
                txt_canonical_clusters[canonical] = cluster
        
        # Compare clusters with same canonical names
        common_canonical = set(pdf_canonical_clusters.keys()) & set(txt_canonical_clusters.keys())
        
        for canonical_name in common_canonical:
            pdf_cluster = pdf_canonical_clusters[canonical_name]
            txt_cluster = txt_canonical_clusters[canonical_name]
            
            if pdf_cluster['size'] != txt_cluster['size']:
                print(f"\nCluster '{canonical_name}':")
                print(f"  PDF size: {pdf_cluster['size']}")
                print(f"  TXT size: {txt_cluster['size']}")
                print(f"  Difference: {abs(pdf_cluster['size'] - txt_cluster['size'])}")
    
    def analyze_extraction_method_differences(self, results: Dict[str, Any]):
        """Analyze differences in extraction methods used."""
        print("\n" + "="*60)
        print("EXTRACTION METHOD ANALYSIS")
        print("="*60)
        
        pdf_citations = results['pdf_results']['citations']
        txt_citations = results['txt_results']['citations']
        
        # Count extraction methods
        pdf_methods = {}
        txt_methods = {}
        
        for citation in pdf_citations:
            method = citation.get('method', 'unknown')
            pdf_methods[method] = pdf_methods.get(method, 0) + 1
        
        for citation in txt_citations:
            method = citation.get('method', 'unknown')
            txt_methods[method] = txt_methods.get(method, 0) + 1
        
        print("Extraction Method Distribution:")
        print(f"{'Method':<15} {'PDF Count':<12} {'TXT Count':<12} {'Difference'}")
        print("-" * 50)
        
        all_methods = set(pdf_methods.keys()) | set(txt_methods.keys())
        for method in sorted(all_methods):
            pdf_count = pdf_methods.get(method, 0)
            txt_count = txt_methods.get(method, 0)
            diff = abs(pdf_count - txt_count)
            print(f"{method:<15} {pdf_count:<12} {txt_count:<12} {diff}")
    
    def generate_specific_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations based on the analysis."""
        recommendations = []
        
        pdf_citations = results['pdf_results']['citations']
        txt_citations = results['txt_results']['citations']
        
        # Check for eyecite object serialization issues
        pdf_malformed = sum(1 for c in pdf_citations if self.is_malformed_citation(c['citation']))
        txt_malformed = sum(1 for c in txt_citations if self.is_malformed_citation(c['citation']))
        
        if pdf_malformed > 0 or txt_malformed > 0:
            recommendations.append("FIX CRITICAL: Eyecite objects are being serialized instead of citation text")
            recommendations.append("- Update citation extraction to use .text or .cite property")
            recommendations.append("- Fix CitationResult creation to store clean citation text")
        
        # Check for context extraction issues
        pdf_contexts = [c.get('extracted_case_name', '') for c in pdf_citations]
        txt_contexts = [c.get('extracted_case_name', '') for c in txt_citations]
        
        if any('quoting Peo ple v. Fielding' in context for context in pdf_contexts + txt_contexts):
            recommendations.append("FIX: Context extraction is capturing incorrect case names")
            recommendations.append("- Improve case name extraction regex patterns")
            recommendations.append("- Fix context window calculation for citation extraction")
        
        # Check for clustering differences
        pdf_cluster_count = len(results['pdf_results']['clusters'])
        txt_cluster_count = len(results['txt_results']['clusters'])
        
        if abs(pdf_cluster_count - txt_cluster_count) > 2:
            recommendations.append("INVESTIGATE: Significant clustering differences detected")
            recommendations.append("- Review clustering algorithm sensitivity to text formatting")
            recommendations.append("- Consider text normalization before clustering")
        
        return recommendations
    
    def test_current_extraction(self):
        """Test current extraction to see if issues persist."""
        print("\n" + "="*60)
        print("CURRENT EXTRACTION TEST")
        print("="*60)
        
        # Test with a simple citation
        test_text = "In Brown v. Board of Education, 347 U.S. 483 (1954), the Court ruled."
        
        extractor = CitationExtractor(self.config)
        citations = extractor.extract_citations(test_text)
        
        print(f"Test text: {test_text}")
        print(f"Citations found: {len(citations)}")
        
        for i, citation in enumerate(citations):
            print(f"\nCitation {i+1}:")
            print(f"  Text: {citation.citation}")
            print(f"  Method: {citation.method}")
            print(f"  Confidence: {citation.confidence}")
            print(f"  Case name: {citation.extracted_case_name}")
            print(f"  Date: {citation.extracted_date}")
        
        # Check if we're still getting malformed citations
        malformed = any(self.is_malformed_citation(c.citation) for c in citations)
        if malformed:
            print("\n❌ ISSUE CONFIRMED: Still getting malformed citations")
        else:
            print("\n✅ Current extraction appears to be working correctly")
    
    def run_analysis(self):
        """Run the complete root cause analysis."""
        print("PDF vs. Text Root Cause Analysis")
        print("=" * 60)
        
        try:
            # Load investigation results
            results = self.load_investigation_results()
            
            # Run various analyses
            self.analyze_citation_format_differences(results)
            self.analyze_context_extraction_differences(results)
            self.analyze_clustering_sensitivity(results)
            self.analyze_extraction_method_differences(results)
            
            # Test current extraction
            self.test_current_extraction()
            
            # Generate specific recommendations
            recommendations = self.generate_specific_recommendations(results)
            
            print("\n" + "="*60)
            print("SPECIFIC RECOMMENDATIONS")
            print("="*60)
            
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
            
            print("\n" + "="*60)
            print("ROOT CAUSE SUMMARY")
            print("="*60)
            
            print("Primary Issues Identified:")
            print("1. Eyecite objects being serialized instead of citation text")
            print("2. Context extraction capturing wrong case names")
            print("3. Different extraction methods between PDF and text")
            print("4. Clustering algorithm sensitivity to formatting differences")
            
            print("\nNext Steps:")
            print("1. Fix CitationResult creation to store clean text")
            print("2. Improve context extraction patterns")
            print("3. Add text normalization before clustering")
            print("4. Test fixes with the same document pair")
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main analysis function."""
    analyzer = RootCauseAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
