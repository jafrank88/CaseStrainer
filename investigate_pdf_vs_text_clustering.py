#!/usr/bin/env python3
"""
Investigation script to determine why clustering results differ between PDF and text versions
of the same document (60179-6.25).

This script will:
1. Process both the PDF and text versions
2. Compare the extracted citations
3. Analyze clustering differences
4. Identify potential causes
"""

import sys
import os
import json
import asyncio
from typing import Dict, List, Any, Tuple
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services import CitationExtractor, CitationVerifier, CitationClusterer
from src.models import ProcessingConfig
from src.quality import TestDataGenerator, handle_errors, error_tracker

class PDFvsTextInvestigator:
    """Investigate differences between PDF and text processing."""
    
    def __init__(self):
        self.config = ProcessingConfig(debug_mode=True)
        self.extractor = CitationExtractor(self.config)
        self.verifier = CitationVerifier(self.config)
        self.clusterer = CitationClusterer(self.config)
        
        # File paths
        self.pdf_file = "D:/dev/casestrainer/wa_briefs/60179-6.25.pdf"
        self.txt_file = "D:/dev/casestrainer/wa_briefs_txt/60179-6.25.txt"
        
        self.results = {}
    
    def read_text_file(self, filepath: str) -> str:
        """Read text file content."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return ""
    
    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            print("PyPDF2 not available, trying pdfplumber...")
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                    return text
            except ImportError:
                print("Neither PyPDF2 nor pdfplumber available. Cannot extract PDF text.")
                return ""
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return ""
    
    @handle_errors(operation="process_document", reraise=False, default_return={})
    async def process_document(self, text: str, source_type: str) -> Dict[str, Any]:
        """Process a document and return detailed results."""
        print(f"\nProcessing {source_type} document...")
        print(f"Text length: {len(text)} characters")
        
        # Step 1: Extract citations
        print("Step 1: Extracting citations...")
        citations = self.extractor.extract_citations(text)
        print(f"Found {len(citations)} citations")
        
        # Step 2: Verify citations (limit to avoid rate limits)
        print("Step 2: Verifying citations (first 5)...")
        citations_to_verify = citations[:5]
        verified_citations = await self.verifier.verify_citations(citations_to_verify)
        
        # Use all citations for clustering, but only some are verified
        all_citations_for_clustering = citations.copy()
        for i, verified in enumerate(verified_citations):
            if i < len(all_citations_for_clustering):
                all_citations_for_clustering[i] = verified
        
        print(f"Verified {sum(1 for c in verified_citations if c.verified)} citations")
        
        # Step 3: Detect parallel citations
        print("Step 3: Detecting parallel citations...")
        citations_with_parallels = self.clusterer.detect_parallel_citations(all_citations_for_clustering, text)
        parallel_count = sum(1 for c in citations_with_parallels if c.parallel_citations)
        print(f"Found {parallel_count} citations with parallels")
        
        # Step 4: Create clusters
        print("Step 4: Creating clusters...")
        clusters = self.clusterer.cluster_citations(citations_with_parallels)
        print(f"Created {len(clusters)} clusters")
        
        return {
            'source_type': source_type,
            'text_length': len(text),
            'text_preview': text[:500] + "..." if len(text) > 500 else text,
            'citations': [
                {
                    'citation': c.citation,
                    'extracted_case_name': c.extracted_case_name,
                    'extracted_date': c.extracted_date,
                    'canonical_name': c.canonical_name,
                    'canonical_date': c.canonical_date,
                    'verified': c.verified,
                    'confidence': c.confidence,
                    'method': c.method,
                    'start_index': c.start_index,
                    'end_index': c.end_index,
                    'parallel_citations': c.parallel_citations or []
                }
                for c in citations_with_parallels
            ],
            'clusters': clusters,
            'summary': {
                'total_citations': len(citations_with_parallels),
                'verified_citations': sum(1 for c in citations_with_parallels if c.verified),
                'citations_with_parallels': parallel_count,
                'total_clusters': len(clusters)
            }
        }
    
    def compare_results(self, pdf_results: Dict[str, Any], txt_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare results between PDF and text processing."""
        print("\n" + "="*60)
        print("COMPARISON ANALYSIS")
        print("="*60)
        
        comparison = {
            'text_length_difference': abs(pdf_results['text_length'] - txt_results['text_length']),
            'citation_count_difference': abs(len(pdf_results['citations']) - len(txt_results['citations'])),
            'cluster_count_difference': abs(len(pdf_results['clusters']) - len(txt_results['clusters'])),
            'differences_found': []
        }
        
        # Compare text lengths
        pdf_len = pdf_results['text_length']
        txt_len = txt_results['text_length']
        len_diff_pct = abs(pdf_len - txt_len) / max(pdf_len, txt_len) * 100
        
        print(f"Text Length Comparison:")
        print(f"  PDF: {pdf_len:,} characters")
        print(f"  TXT: {txt_len:,} characters")
        print(f"  Difference: {abs(pdf_len - txt_len):,} characters ({len_diff_pct:.1f}%)")
        
        if len_diff_pct > 5:
            comparison['differences_found'].append(f"Significant text length difference: {len_diff_pct:.1f}%")
        
        # Compare citation counts
        pdf_citations = len(pdf_results['citations'])
        txt_citations = len(txt_results['citations'])
        
        print(f"\nCitation Count Comparison:")
        print(f"  PDF: {pdf_citations} citations")
        print(f"  TXT: {txt_citations} citations")
        print(f"  Difference: {abs(pdf_citations - txt_citations)} citations")
        
        if pdf_citations != txt_citations:
            comparison['differences_found'].append(f"Citation count mismatch: PDF={pdf_citations}, TXT={txt_citations}")
        
        # Compare cluster counts
        pdf_clusters = len(pdf_results['clusters'])
        txt_clusters = len(txt_results['clusters'])
        
        print(f"\nCluster Count Comparison:")
        print(f"  PDF: {pdf_clusters} clusters")
        print(f"  TXT: {txt_clusters} clusters")
        print(f"  Difference: {abs(pdf_clusters - txt_clusters)} clusters")
        
        if pdf_clusters != txt_clusters:
            comparison['differences_found'].append(f"Cluster count mismatch: PDF={pdf_clusters}, TXT={txt_clusters}")
        
        # Compare specific citations
        print(f"\nCitation Detail Comparison:")
        pdf_citation_texts = {c['citation'] for c in pdf_results['citations']}
        txt_citation_texts = {c['citation'] for c in txt_results['citations']}
        
        only_in_pdf = pdf_citation_texts - txt_citation_texts
        only_in_txt = txt_citation_texts - pdf_citation_texts
        common_citations = pdf_citation_texts & txt_citation_texts
        
        print(f"  Common citations: {len(common_citations)}")
        print(f"  Only in PDF: {len(only_in_pdf)}")
        print(f"  Only in TXT: {len(only_in_txt)}")
        
        if only_in_pdf:
            print(f"  Citations only in PDF:")
            for citation in list(only_in_pdf)[:5]:  # Show first 5
                print(f"    - {citation}")
            comparison['differences_found'].append(f"{len(only_in_pdf)} citations only found in PDF")
        
        if only_in_txt:
            print(f"  Citations only in TXT:")
            for citation in list(only_in_txt)[:5]:  # Show first 5
                print(f"    - {citation}")
            comparison['differences_found'].append(f"{len(only_in_txt)} citations only found in TXT")
        
        # Compare clustering for common citations
        if common_citations:
            print(f"\nClustering Comparison for Common Citations:")
            self.compare_clustering_for_common_citations(pdf_results, txt_results, common_citations, comparison)
        
        return comparison
    
    def compare_clustering_for_common_citations(self, pdf_results: Dict[str, Any], txt_results: Dict[str, Any], 
                                              common_citations: set, comparison: Dict[str, Any]):
        """Compare how common citations are clustered differently."""
        
        # Build citation-to-cluster mapping for both sources
        pdf_citation_clusters = {}
        for i, cluster in enumerate(pdf_results['clusters']):
            for citation_data in cluster['citations']:
                pdf_citation_clusters[citation_data['citation']] = i
        
        txt_citation_clusters = {}
        for i, cluster in enumerate(txt_results['clusters']):
            for citation_data in cluster['citations']:
                txt_citation_clusters[citation_data['citation']] = i
        
        clustering_differences = 0
        
        for citation in common_citations:
            pdf_cluster = pdf_citation_clusters.get(citation, -1)
            txt_cluster = txt_citation_clusters.get(citation, -1)
            
            if pdf_cluster != txt_cluster:
                clustering_differences += 1
        
        print(f"  Citations with different clustering: {clustering_differences}")
        
        if clustering_differences > 0:
            comparison['differences_found'].append(f"{clustering_differences} common citations clustered differently")
    
    def analyze_text_differences(self, pdf_text: str, txt_text: str) -> Dict[str, Any]:
        """Analyze differences in the actual text content."""
        print("\n" + "="*60)
        print("TEXT CONTENT ANALYSIS")
        print("="*60)
        
        # Sample both texts for comparison
        pdf_sample = pdf_text[:1000]
        txt_sample = txt_text[:1000]
        
        print("PDF Text Sample (first 1000 chars):")
        print("-" * 40)
        print(repr(pdf_sample))
        
        print("\nTXT Text Sample (first 1000 chars):")
        print("-" * 40)
        print(repr(txt_sample))
        
        # Check for encoding issues
        pdf_non_ascii = sum(1 for c in pdf_text if ord(c) > 127)
        txt_non_ascii = sum(1 for c in txt_text if ord(c) > 127)
        
        print(f"\nEncoding Analysis:")
        print(f"  PDF non-ASCII characters: {pdf_non_ascii}")
        print(f"  TXT non-ASCII characters: {txt_non_ascii}")
        
        # Check for common PDF extraction issues
        pdf_issues = []
        if "�" in pdf_text:
            pdf_issues.append("Contains replacement characters (�)")
        if pdf_text.count("\n") < txt_text.count("\n") / 2:
            pdf_issues.append("Possible line break loss in PDF extraction")
        if len(pdf_text.split()) < len(txt_text.split()) * 0.8:
            pdf_issues.append("Possible word separation issues in PDF")
        
        if pdf_issues:
            print(f"\nPotential PDF Extraction Issues:")
            for issue in pdf_issues:
                print(f"  - {issue}")
        
        return {
            'pdf_length': len(pdf_text),
            'txt_length': len(txt_text),
            'pdf_non_ascii': pdf_non_ascii,
            'txt_non_ascii': txt_non_ascii,
            'pdf_issues': pdf_issues
        }
    
    def save_results(self, results: Dict[str, Any]):
        """Save investigation results to file."""
        output_file = "pdf_vs_txt_investigation_results.json"
        
        # Convert any non-serializable objects to strings
        serializable_results = json.loads(json.dumps(results, default=str))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_file}")
    
    async def run_investigation(self):
        """Run the complete investigation."""
        print("PDF vs Text Clustering Investigation")
        print("=" * 60)
        print(f"Investigating: {os.path.basename(self.pdf_file)} vs {os.path.basename(self.txt_file)}")
        
        # Check if files exist
        if not os.path.exists(self.pdf_file):
            print(f"❌ PDF file not found: {self.pdf_file}")
            return
        
        if not os.path.exists(self.txt_file):
            print(f"❌ Text file not found: {self.txt_file}")
            return
        
        try:
            # Read both files
            print("\nReading files...")
            txt_content = self.read_text_file(self.txt_file)
            pdf_content = self.extract_pdf_text(self.pdf_file)
            
            if not txt_content:
                print("❌ Failed to read text file")
                return
            
            if not pdf_content:
                print("❌ Failed to extract PDF content")
                return
            
            # Analyze text differences
            text_analysis = self.analyze_text_differences(pdf_content, txt_content)
            
            # Process both documents
            pdf_results = await self.process_document(pdf_content, "PDF")
            txt_results = await self.process_document(txt_content, "TXT")
            
            # Compare results
            comparison = self.compare_results(pdf_results, txt_results)
            
            # Compile final results
            investigation_results = {
                'investigation_info': {
                    'pdf_file': self.pdf_file,
                    'txt_file': self.txt_file,
                    'timestamp': str(asyncio.get_event_loop().time())
                },
                'text_analysis': text_analysis,
                'pdf_results': pdf_results,
                'txt_results': txt_results,
                'comparison': comparison,
                'recommendations': self.generate_recommendations(comparison, text_analysis)
            }
            
            # Save results
            self.save_results(investigation_results)
            
            # Print summary
            self.print_summary(comparison)
            
        except Exception as e:
            print(f"❌ Investigation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def generate_recommendations(self, comparison: Dict[str, Any], text_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on the investigation."""
        recommendations = []
        
        if text_analysis.get('pdf_issues'):
            recommendations.append("Consider improving PDF text extraction method")
            recommendations.append("Investigate PDF-specific text preprocessing")
        
        if comparison['citation_count_difference'] > 0:
            recommendations.append("Review citation extraction patterns for PDF vs text differences")
            recommendations.append("Check for encoding-related citation parsing issues")
        
        if comparison['cluster_count_difference'] > 0:
            recommendations.append("Investigate clustering algorithm sensitivity to text formatting")
            recommendations.append("Consider normalizing text before clustering")
        
        if not recommendations:
            recommendations.append("No major issues found - differences may be within expected variance")
        
        return recommendations
    
    def print_summary(self, comparison: Dict[str, Any]):
        """Print investigation summary."""
        print("\n" + "="*60)
        print("INVESTIGATION SUMMARY")
        print("="*60)
        
        if comparison['differences_found']:
            print("🔍 Differences Found:")
            for diff in comparison['differences_found']:
                print(f"  - {diff}")
        else:
            print("✅ No significant differences found")
        
        print(f"\nKey Metrics:")
        print(f"  Text length difference: {comparison['text_length_difference']:,} characters")
        print(f"  Citation count difference: {comparison['citation_count_difference']}")
        print(f"  Cluster count difference: {comparison['cluster_count_difference']}")


async def main():
    """Main investigation function."""
    investigator = PDFvsTextInvestigator()
    await investigator.run_investigation()


if __name__ == "__main__":
    asyncio.run(main())
