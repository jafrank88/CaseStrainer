#!/usr/bin/env python3
"""
Script to integrate cleaned Wikipedia case names into the case trainer system
for context analysis and testing.
"""

import csv
import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Optional

# Add the src directory to the path so we can import case trainer modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def load_cleaned_case_names(csv_file: str) -> List[Dict]:
    """Load cleaned case names from CSV file."""
    cases = []
    
    with open(csv_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cases.append({
                'case_name': row['case_name'],
                'source_url': row['source_url'],
                'confidence': float(row['confidence']),
                'extraction_method': row['extraction_method']
            })
    
    return cases

def create_test_paragraphs(cases: List[Dict], num_paragraphs: int = 10) -> List[str]:
    """Create test paragraphs using the case names for context analysis."""
    test_paragraphs = []
    
    # Group cases by confidence level
    high_confidence = [case for case in cases if case['confidence'] >= 0.8]
    medium_confidence = [case for case in cases if 0.6 <= case['confidence'] < 0.8]
    
    # Use high confidence cases for better test paragraphs
    selected_cases = high_confidence if high_confidence else medium_confidence
    
    if not selected_cases:
        print("No high-confidence cases found. Using all cases.")
        selected_cases = cases
    
    # Create test paragraphs
    for i in range(min(num_paragraphs, len(selected_cases))):
        case = selected_cases[i]
        case_name = case['case_name']
        
        # Create different types of test paragraphs
        if i % 3 == 0:
            # Standard citation format
            paragraph = f"The court in {case_name} established important precedent regarding constitutional rights. This case, decided in the early 19th century, continues to influence modern jurisprudence. The holding in {case_name} has been cited in numerous subsequent decisions."
        elif i % 3 == 1:
            # Multiple citations format
            paragraph = f"Several landmark cases have shaped our understanding of federal jurisdiction. {case_name} represents a key moment in the development of constitutional law. The principles established in {case_name} have been reaffirmed in later decisions."
        else:
            # Complex legal analysis format
            paragraph = f"In analyzing the constitutional issues presented, the court must consider the precedent set forth in {case_name}. The reasoning in {case_name} provides a framework for understanding the scope of federal authority. This case demonstrates the evolution of legal doctrine over time."
        
        test_paragraphs.append({
            'paragraph': paragraph,
            'case_name': case_name,
            'confidence': case['confidence'],
            'source_url': case['source_url']
        })
    
    return test_paragraphs

def test_case_name_extraction(paragraphs: List[Dict]) -> None:
    """Test case name extraction on the generated paragraphs."""
    try:
        # Import case trainer modules
        from case_name_extraction_core import extract_case_name_triple_comprehensive
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
        
        print("\n=== Testing Case Name Extraction ===")
        
        for i, test_data in enumerate(paragraphs[:5]):  # Test first 5 paragraphs
            paragraph = test_data['paragraph']
            expected_case = test_data['case_name']
            
            print(f"\nTest {i+1}:")
            print(f"Expected case: {expected_case}")
            print(f"Paragraph: {paragraph[:100]}...")
            
            # Test with comprehensive extraction
            try:
                extracted_name, extracted_date, confidence = extract_case_name_triple_comprehensive(paragraph)
                print(f"Extracted name: {extracted_name}")
                print(f"Extracted date: {extracted_date}")
                print(f"Confidence: {confidence}")
                
                # Check if extraction was successful
                if extracted_name and extracted_name != "N/A":
                    print("✓ Extraction successful")
                else:
                    print("✗ Extraction failed")
                    
            except Exception as e:
                print(f"✗ Extraction error: {e}")
            
            print("-" * 50)
    
    except ImportError as e:
        print(f"Could not import case trainer modules: {e}")
        print("Make sure you're running this from the correct directory.")

def create_context_analysis_dataset(paragraphs: List[Dict], output_file: str = None) -> str:
    """Create a dataset for context analysis."""
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/context_analysis_dataset_{timestamp}.json"
    
    # Ensure the data directory exists
    os.makedirs('data', exist_ok=True)
    
    dataset = {
        'metadata': {
            'created_date': datetime.now().isoformat(),
            'total_paragraphs': len(paragraphs),
            'source': 'Wikipedia Supreme Court cases',
            'description': 'Test paragraphs for case name extraction and context analysis'
        },
        'paragraphs': paragraphs
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"Created context analysis dataset: {output_file}")
    return output_file

def create_csv_for_batch_processing(paragraphs: List[Dict], output_file: str = None) -> str:
    """Create a CSV file for batch processing in the case trainer system."""
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/batch_test_paragraphs_{timestamp}.csv"
    
    # Ensure the data directory exists
    os.makedirs('data', exist_ok=True)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['text', 'expected_case_name', 'confidence', 'source_url', 'test_id']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, test_data in enumerate(paragraphs):
            writer.writerow({
                'text': test_data['paragraph'],
                'expected_case_name': test_data['case_name'],
                'confidence': test_data['confidence'],
                'source_url': test_data['source_url'],
                'test_id': f"wiki_test_{i+1:03d}"
            })
    
    print(f"Created batch processing CSV: {output_file}")
    return output_file

def main():
    """Main function to integrate case names for context analysis."""
    print("Integrating Wikipedia case names for context analysis...")
    
    # Find the most recent cleaned CSV file
    data_dir = 'data'
    if not os.path.exists(data_dir):
        print("No data directory found. Please run the cleaning script first.")
        return
    
    csv_files = [f for f in os.listdir(data_dir) if f.startswith('cleaned_wikipedia_case_names_') and f.endswith('.csv')]
    
    if not csv_files:
        print("No cleaned Wikipedia case names CSV files found. Please run the cleaning script first.")
        return
    
    # Use the most recent file
    latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(data_dir, x)))
    input_file = os.path.join(data_dir, latest_file)
    
    print(f"Using input file: {input_file}")
    
    # Load cleaned case names
    cases = load_cleaned_case_names(input_file)
    print(f"Loaded {len(cases)} cleaned case names")
    
    # Create test paragraphs
    print("Creating test paragraphs...")
    test_paragraphs = create_test_paragraphs(cases, num_paragraphs=20)
    print(f"Created {len(test_paragraphs)} test paragraphs")
    
    # Test case name extraction
    test_case_name_extraction(test_paragraphs)
    
    # Create datasets
    context_dataset = create_context_analysis_dataset(test_paragraphs)
    batch_csv = create_csv_for_batch_processing(test_paragraphs)
    
    print(f"\nIntegration complete!")
    print(f"Context analysis dataset: {context_dataset}")
    print(f"Batch processing CSV: {batch_csv}")
    print(f"\nYou can now use these files to test your case trainer system with real case names.")

if __name__ == "__main__":
    main() 