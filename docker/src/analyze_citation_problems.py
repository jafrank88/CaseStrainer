"""
Script to analyze unconfirmed citations by type and identify common problems.

This script organizes citations by format type, identifies patterns in unconfirmed citations,
and generates a report to help understand where verification problems occur.
"""

import json
import os
import re
import traceback
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

# Citation format patterns (same as in scan_and_categorize_citations.py)
CITATION_PATTERNS = {
    "us_reports": r"^(\d+)\s+U\.?\s?S\.?\s+(\d+)$",
    "federal_reporter": r"^(\d+)\s+F\.(\d+)d\s+(\d+)$",
    "federal_supplement": r"^(\d+)\s+F\.Supp\.(\d+)d\s+(\d+)$",
    "supreme_court_reporter": r"^(\d+)\s+S\.?\s?Ct\.?\s+(\d+)$",
    "washington_reports": r"^(\d+)\s+(Wn|Wash)\.(\d+)d\s+(\d+)$",
    "washington_app_reports": r"^(\d+)\s+(Wn\.|Wash\.|Wash|Wn)\s+App\.\s+(\d+)$",
    "lawyers_edition": r"^(\d+)\s+L\.?\s?Ed\.?\s?(\d+)d\s+(\d+)$",
    "westlaw": r"^(\d{4})\s+WL\s+(\d+)$",
    "pacific_reporter": r"^(\d+)\s+P\.(\d+)d\s+(\d+)$",
    "atlantic_reporter": r"^(\d+)\s+A\.(\d+)d\s+(\d+)$",
    "north_eastern_reporter": r"^(\d+)\s+N\.E\.(\d+)d\s+(\d+)$",
    "new_york_reports": r"^(\d+)\s+N\.Y\.(\d+)d\s+(\d+)$",
    "california_reports": r"^(\d+)\s+Cal\.(\d+)th\s+(\d+)$"
}

def load_enhanced_citations(filename='downloaded_briefs/enhanced_unconfirmed_citations.json'):
    """Load enhanced unconfirmed citations from the JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading enhanced citations: {e}")
        return {}

def analyze_citation_format(citation_text):
    """Analyze a citation format and determine its type."""
    # Strip whitespace
    citation = citation_text.strip()
    
    # Check against each pattern
    for format_type, pattern in CITATION_PATTERNS.items():
        if re.match(pattern, citation):
            return format_type
    
    return "unknown"

def analyze_citations_by_type():
    """Analyze unconfirmed citations by type and identify common problems."""
    # Load enhanced citations
    enhanced_citations = load_enhanced_citations()
    
    if not enhanced_citations:
        print("No enhanced citations found. Please run scan_and_categorize_citations.py first.")
        return
    
    # Flatten the citations list
    flat_citations = []
    for document, citations in enhanced_citations.items():
        for citation in citations:
            citation['document_name'] = document
            flat_citations.append(citation)
    
    print(f"Analyzing {len(flat_citations)} unconfirmed citations...")
    
    # Group citations by format type
    citations_by_type = defaultdict(list)
    for citation in flat_citations:
        format_type = citation.get('format_type', 'unknown')
        citations_by_type[format_type].append(citation)
    
    # Analyze each format type
    type_stats = {}
    for format_type, citations in citations_by_type.items():
        # Count valid formats and volumes
        valid_format_count = sum(1 for c in citations if c.get('is_valid_format', False))
        valid_volume_count = sum(1 for c in citations if c.get('is_valid_volume', False))
        
        # Calculate average likelihood
        avg_likelihood = sum(c.get('likelihood_of_being_real', 0) for c in citations) / len(citations)
        
        # Collect jurisdictions
        jurisdictions = Counter(c.get('jurisdiction', 'Unknown') for c in citations)
        
        # Collect common problems
        problems = []
        if valid_format_count < len(citations):
            problems.append("Invalid format")
        if valid_volume_count < valid_format_count:
            problems.append("Invalid volume number")
        
        # Store statistics
        type_stats[format_type] = {
            'count': len(citations),
            'valid_format_count': valid_format_count,
            'valid_format_percent': valid_format_count / len(citations) * 100,
            'valid_volume_count': valid_volume_count,
            'valid_volume_percent': valid_volume_count / len(citations) * 100,
            'avg_likelihood': avg_likelihood,
            'jurisdictions': dict(jurisdictions),
            'problems': problems,
            'examples': [c['citation_text'] for c in citations[:3]]  # First 3 examples
        }
    
    # Generate report
    generate_report(type_stats, flat_citations)
    
    # Generate visualizations
    try:
        generate_visualizations(type_stats, flat_citations)
    except Exception as e:
        print(f"Error generating visualizations: {e}")
        print("Continuing with text report...")
    
    return type_stats

def generate_report(type_stats, flat_citations):
    """Generate a text report of citation analysis."""
    # Create report directory if it doesn't exist
    os.makedirs('reports', exist_ok=True)
    
    # Generate report filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"reports/citation_analysis_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write("=== CITATION ANALYSIS REPORT ===\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Citations Analyzed: {len(flat_citations)}\n\n")
        
        # Overall statistics
        valid_format_count = sum(1 for c in flat_citations if c.get('is_valid_format', False))
        valid_volume_count = sum(1 for c in flat_citations if c.get('is_valid_volume', False))
        
        f.write("=== OVERALL STATISTICS ===\n")
        f.write(f"Valid Formats: {valid_format_count} ({valid_format_count/len(flat_citations)*100:.1f}%)\n")
        f.write(f"Valid Volumes: {valid_volume_count} ({valid_volume_count/len(flat_citations)*100:.1f}%)\n\n")
        
        # Sort types by count (descending)
        sorted_types = sorted(type_stats.items(), key=lambda x: x[1]['count'], reverse=True)
        
        f.write("=== CITATION TYPES ===\n")
        for format_type, stats in sorted_types:
            f.write(f"\n--- {format_type.upper()} ---\n")
            f.write(f"Count: {stats['count']} ({stats['count']/len(flat_citations)*100:.1f}%)\n")
            f.write(f"Valid Formats: {stats['valid_format_count']} ({stats['valid_format_percent']:.1f}%)\n")
            f.write(f"Valid Volumes: {stats['valid_volume_count']} ({stats['valid_volume_percent']:.1f}%)\n")
            f.write(f"Average Likelihood: {stats['avg_likelihood']:.2f}\n")
            
            f.write("Jurisdictions:\n")
            for jurisdiction, count in stats['jurisdictions'].items():
                f.write(f"  - {jurisdiction}: {count}\n")
            
            if stats['problems']:
                f.write("Common Problems:\n")
                for problem in stats['problems']:
                    f.write(f"  - {problem}\n")
            
            f.write("Examples:\n")
            for example in stats['examples']:
                f.write(f"  - {example}\n")
    
    print(f"Report generated: {report_file}")
    
    # Also generate CSV file for easier analysis
    csv_file = f"reports/citation_analysis_{timestamp}.csv"
    
    # Prepare data for CSV
    rows = []
    for citation in flat_citations:
        row = {
            'citation_text': citation.get('citation_text', ''),
            'case_name': citation.get('case_name', ''),
            'format_type': citation.get('format_type', 'unknown'),
            'is_valid_format': citation.get('is_valid_format', False),
            'is_valid_volume': citation.get('is_valid_volume', False),
            'likelihood_of_being_real': citation.get('likelihood_of_being_real', 0),
            'jurisdiction': citation.get('jurisdiction', 'Unknown'),
            'document_name': citation.get('document_name', '')
        }
        rows.append(row)
    
    # Write to CSV
    try:
        df = pd.DataFrame(rows)
        df.to_csv(csv_file, index=False)
        print(f"CSV file generated: {csv_file}")
    except Exception as e:
        print(f"Error generating CSV file: {e}")

def generate_visualizations(type_stats, flat_citations):
    """Generate visualizations of citation analysis."""
    # Create visualizations directory if it doesn't exist
    os.makedirs('reports/visualizations', exist_ok=True)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Citation Types Pie Chart
    plt.figure(figsize=(12, 8))
    labels = []
    sizes = []
    for format_type, stats in sorted(type_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        if stats['count'] > 3:  # Only include types with more than 3 citations
            labels.append(format_type)
            sizes.append(stats['count'])
    
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title('Distribution of Unconfirmed Citations by Type')
    plt.savefig(f'reports/visualizations/citation_types_pie_{timestamp}.png')
    plt.close()
    
    # 2. Valid Format vs. Valid Volume Bar Chart
    plt.figure(figsize=(14, 8))
    format_types = []
    valid_format_pcts = []
    valid_volume_pcts = []
    
    for format_type, stats in sorted(type_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        if stats['count'] > 3:  # Only include types with more than 3 citations
            format_types.append(format_type)
            valid_format_pcts.append(stats['valid_format_percent'])
            valid_volume_pcts.append(stats['valid_volume_percent'])
    
    x = range(len(format_types))
    width = 0.35
    
    plt.bar([i - width/2 for i in x], valid_format_pcts, width, label='Valid Format')
    plt.bar([i + width/2 for i in x], valid_volume_pcts, width, label='Valid Volume')
    
    plt.xlabel('Citation Type')
    plt.ylabel('Percentage')
    plt.title('Valid Format vs. Valid Volume by Citation Type')
    plt.xticks(x, format_types, rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'reports/visualizations/valid_format_volume_{timestamp}.png')
    plt.close()
    
    # 3. Likelihood Distribution Histogram
    plt.figure(figsize=(10, 6))
    likelihoods = [c.get('likelihood_of_being_real', 0) for c in flat_citations]
    plt.hist(likelihoods, bins=10, alpha=0.7, color='blue')
    plt.xlabel('Likelihood of Being Real')
    plt.ylabel('Number of Citations')
    plt.title('Distribution of Citation Likelihood Scores')
    plt.grid(True, alpha=0.3)
    plt.savefig(f'reports/visualizations/likelihood_distribution_{timestamp}.png')
    plt.close()
    
    print(f"Visualizations generated in reports/visualizations/")

def main():
    """Main function to analyze citations by type."""
    try:
        print("Analyzing unconfirmed citations by type...")
        type_stats = analyze_citations_by_type()
        
        if type_stats:
            print("\nSummary of Citation Types:")
            for format_type, stats in sorted(type_stats.items(), key=lambda x: x[1]['count'], reverse=True):
                print(f"  {format_type}: {stats['count']} citations, {stats['valid_format_percent']:.1f}% valid format, {stats['valid_volume_percent']:.1f}% valid volume")
            
            print("\nCheck the reports directory for detailed analysis.")
    except Exception as e:
        print(f"Error analyzing citations: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
