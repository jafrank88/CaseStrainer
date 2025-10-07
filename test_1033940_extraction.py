import sys
import os
import asyncio
import json
from pathlib import Path
import PyPDF2
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime

# Add parent directory to path to allow importing from src
sys.path.insert(0, str(Path(__file__).parent))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.unified_extraction_architecture import UnifiedExtractionArchitecture

@dataclass
class ExtractionStats:
    """Class to track extraction statistics."""
    total: int = 0
    with_case_name: int = 0
    with_year: int = 0
    with_both: int = 0
    case_name_lengths: List[int] = field(default_factory=list)
    case_name_examples: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_result(self, citation: Dict[str, Any]):
        """Add a citation result to the statistics."""
        self.total += 1
        has_case_name = bool(citation.get('extracted_case_name'))
        has_year = bool(citation.get('extracted_date'))
        
        if has_case_name:
            self.with_case_name += 1
            case_name = citation['extracted_case_name']
            self.case_name_lengths.append(len(case_name))
            
            # Store example case names (first few)
            if len(self.case_name_examples) < 5:
                self.case_name_examples.append({
                    'citation': citation.get('citation', ''),
                    'case_name': case_name,
                    'year': citation.get('extracted_date', '')
                })
        
        if has_year:
            self.with_year += 1
        
        if has_case_name and has_year:
            self.with_both += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to a dictionary."""
        avg_length = sum(self.case_name_lengths) / len(self.case_name_lengths) if self.case_name_lengths else 0
        return {
            'total': self.total,
            'with_case_name': self.with_case_name,
            'with_year': self.with_year,
            'with_both': self.with_both,
            'case_name_percentage': round(self.with_case_name / self.total * 100, 2) if self.total > 0 else 0,
            'year_percentage': round(self.with_year / self.total * 100, 2) if self.total > 0 else 0,
            'both_percentage': round(self.with_both / self.total * 100, 2) if self.total > 0 else 0,
            'avg_case_name_length': round(avg_length, 2),
            'case_name_examples': self.case_name_examples
        }

def analyze_extraction_results(result, debug: bool = False) -> Dict[str, Any]:
    """Analyze the extraction results and count issues.
    
    Args:
        result: The extraction result object or dict
        debug: Whether to print debug information
        
    Returns:
        Dictionary with detailed analysis of the extraction results
    """
    # Handle both dict and object access
    if hasattr(result, 'citations'):
        citations = result.citations
    else:
        citations = result.get('citations', [])
    
    # Initialize statistics
    stats = ExtractionStats()
    
    # Process each citation
    for citation in citations:
        # Convert to dict if it's an object
        if not isinstance(citation, dict):
            citation_dict = {k: getattr(citation, k, None) for k in dir(citation) if not k.startswith('_')}
        else:
            citation_dict = citation
        
        stats.add_result(citation_dict)
        
        if debug and len(stats.case_name_examples) <= 5:
            print(f"Example citation: {citation_dict.get('citation')}")
            print(f"  Year: {citation_dict.get('extracted_date', 'N/A')}")
            print()
    
    return stats.to_dict()

async def run_extraction(text: str, processor: UnifiedCitationProcessorV2, name: str) -> Dict[str, Any]:
    """Run extraction and return analysis results."""
    print(f"\n=== Running {name} extraction ===")
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Process the text
        result = await processor.process_text(text)
        
        # Analyze the results
        analysis = analyze_extraction_results(result, debug=True)
        
        # Add timing information
        analysis['extraction_time'] = asyncio.get_event_loop().time() - start_time
        analysis['name'] = name
        
        return analysis
        
    except Exception as e:
        print(f"Error during {name} extraction: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

async def main():
    # Initialize the processors
    standard_processor = UnifiedCitationProcessorV2()
    
    # Create a processor with enhanced context windows
    class EnhancedExtractionArchitecture(UnifiedExtractionArchitecture):
        def _extract_case_name_intelligent(self, *args, **kwargs):
            # Force debug mode to see detailed logs
            kwargs['debug'] = True
            return super()._extract_case_name_intelligent(*args, **kwargs)
    
    enhanced_processor = UnifiedCitationProcessorV2()
    enhanced_processor.extractor = EnhancedExtractionArchitecture()
    
    # Get the path to the PDF file
    pdf_path = Path('1033940.pdf')
    
    # Check if the file exists
    if not pdf_path.exists():
        print(f"Error: File '{pdf_path}' not found.")
        return
    
    print(f"Processing PDF: {pdf_path}")
    
    # Extract text from PDF
    try:
        text = ""
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""

        if not text.strip():
            print("Error: No text could be extracted from the PDF")
            return
            
        print(f"Extracted {len(text)} characters from PDF")
        
        # Run standard extraction
        standard_result = await run_extraction(text, standard_processor, "Standard Extraction")
        
        # Run enhanced extraction
        enhanced_result = await run_extraction(text, enhanced_processor, "Enhanced Context Extraction")
        
        # Print comparison
        print("\n=== Extraction Results Comparison ===")
        print(f"{'Metric':<30} {'Standard':<15} {'Enhanced':<15} {'Improvement':<15}")
        print("-" * 70)
        
        # Compare key metrics
        metrics = [
            ('Case Name Extraction', 'case_name_percentage'),
            ('Year Extraction', 'year_percentage'),
            ('Complete Extraction', 'both_percentage'),
            ('Avg Case Name Length', 'avg_case_name_length'),
            ('Extraction Time (s)', 'extraction_time')
        ]
        
        for label, key in metrics:
            std_val = standard_result.get(key, 0)
            enh_val = enhanced_result.get(key, 0)
            
            if isinstance(std_val, (int, float)) and isinstance(enh_val, (int, float)):
                if std_val != 0:
                    improvement = ((enh_val - std_val) / std_val) * 100
                    imp_str = f"{improvement:+.1f}%"
                else:
                    imp_str = "N/A"
                
                if key == 'extraction_time':
                    print(f"{label:<30} {std_val:<15.2f} {enh_val:<15.2f} {imp_str:<15}")
                else:
                    print(f"{label:<30} {std_val:<15.2f}% {enh_val:<15.2f}% {imp_str:<15}")
        
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
