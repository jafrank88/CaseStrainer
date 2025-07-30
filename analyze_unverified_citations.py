#!/usr/bin/env python3
"""
Analyze citations from the 50 briefs processing to identify:
1. Citations not found in CourtListener
2. Citations that were not verified
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add the project root to the Python path
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def analyze_existing_results():
    """Analyze existing results files and log files for unverified citations"""
    
    print("Analyzing Citations from 50 Briefs Processing")
    print("=" * 60)
    
    # Look for existing results files
    results_files = list(Path(".").glob("50_briefs_results_*.json"))
    log_files = list(Path(".").glob("brief_processing_*.log"))
    
    print(f"Found {len(results_files)} results files")
    print(f"Found {len(log_files)} log files")
    
    # Analyze results files if they exist
    if results_files:
        latest_results = max(results_files, key=os.path.getctime)
        print(f"\nAnalyzing latest results file: {latest_results}")
        
        try:
            with open(latest_results, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            analyze_results_data(data)
            return True
        except Exception as e:
            print(f"Error reading results file: {e}")
    
    # If no results files, analyze log files
    if log_files:
        latest_log = max(log_files, key=os.path.getctime)
        print(f"\nAnalyzing latest log file: {latest_log}")
        
        try:
            analyze_log_file(latest_log)
            return True
        except Exception as e:
            print(f"Error reading log file: {e}")
    
    # If no existing files, run a quick analysis on a few briefs
    print("\nNo existing results found. Running quick analysis on first 3 briefs...")
    return run_quick_analysis()

def analyze_results_data(data):
    """Analyze structured results data"""
    
    processing_stats = data.get('processing_stats', {})
    brief_results = data.get('brief_results', [])
    
    print(f"\nProcessing Statistics:")
    print(f"  Total briefs: {processing_stats.get('total_briefs', 0)}")
    print(f"  Successfully processed: {processing_stats.get('successfully_processed', 0)}")
    print(f"  Total citations: {processing_stats.get('total_citations', 0)}")
    print(f"  Total verified: {processing_stats.get('total_verified', 0)}")
    print(f"  Overall verification rate: {processing_stats.get('overall_verification_rate', 0):.1f}%")
    
    # Collect unverified citations
    unverified_citations = []
    non_courtlistener_citations = []
    
    for brief in brief_results:
        if brief.get('success') and 'citations' in brief:
            for citation in brief['citations']:
                citation_text = citation.get('citation', '')
                verified = citation.get('verified', False)
                source = citation.get('source', '')
                
                if not verified:
                    unverified_citations.append({
                        'citation': citation_text,
                        'brief': brief.get('filename', ''),
                        'extracted_name': citation.get('extracted_case_name', ''),
                        'canonical_name': citation.get('canonical_name', '')
                    })
                
                if verified and 'CourtListener' not in str(source):
                    non_courtlistener_citations.append({
                        'citation': citation_text,
                        'brief': brief.get('filename', ''),
                        'source': source,
                        'canonical_name': citation.get('canonical_name', '')
                    })
    
    print_citation_analysis(unverified_citations, non_courtlistener_citations)

def analyze_log_file(log_file):
    """Analyze log file for citation information"""
    
    print(f"Analyzing log file: {log_file}")
    
    unverified_citations = []
    non_courtlistener_citations = []
    current_brief = ""
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                # Track current brief
                if "Processing Brief" in line and ".pdf" in line:
                    parts = line.split(":")
                    if len(parts) > 2:
                        current_brief = parts[2].strip()
                
                # Look for verification failures
                if "UNVERIFIED" in line or "not verified" in line.lower():
                    citation_match = extract_citation_from_log_line(line)
                    if citation_match:
                        unverified_citations.append({
                            'citation': citation_match,
                            'brief': current_brief,
                            'log_line': line.strip()
                        })
                
                # Look for non-CourtListener sources
                if "fallback" in line.lower() or "verified" in line and "CourtListener" not in line:
                    citation_match = extract_citation_from_log_line(line)
                    if citation_match:
                        non_courtlistener_citations.append({
                            'citation': citation_match,
                            'brief': current_brief,
                            'log_line': line.strip()
                        })
    
    except Exception as e:
        print(f"Error reading log file: {e}")
        return
    
    print_citation_analysis(unverified_citations, non_courtlistener_citations)

def extract_citation_from_log_line(line):
    """Extract citation from a log line"""
    import re
    
    # Look for common citation patterns in log lines
    patterns = [
        r'(\d+\s+[A-Za-z.]+\s+\d+)',  # Basic citation pattern
        r'(\d+\s+[A-Za-z.]+\d*\s+\d+)',  # With numbers in reporter
        r'(\d{4}\s+WL\s+\d+)',  # Westlaw citations
    ]
    
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            return match.group(1).strip()
    
    return None

def run_quick_analysis():
    """Run a quick analysis on a few briefs to demonstrate the enhanced verification"""
    
    print("Running quick analysis on first 3 briefs...")
    
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    
    briefs_dir = Path("wa_briefs")
    if not briefs_dir.exists():
        print("Briefs directory not found")
        return False
    
    pdf_files = list(briefs_dir.glob("*.pdf"))[:3]  # Just first 3 briefs
    
    processor = UnifiedCitationProcessorV2()
    
    unverified_citations = []
    non_courtlistener_citations = []
    
    for brief_file in pdf_files:
        print(f"\nProcessing: {brief_file.name}")
        
        try:
            # Extract text from PDF
            import PyPDF2
            with open(brief_file, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            # Process with enhanced verification
            result = processor.process_text(text)
            citations = result.get('citations', [])
            
            print(f"  Found {len(citations)} citations")
            
            for citation in citations:
                citation_text = getattr(citation, 'citation', '')
                verified = getattr(citation, 'verified', False)
                source = getattr(citation, 'source', '')
                
                if not verified:
                    unverified_citations.append({
                        'citation': citation_text,
                        'brief': brief_file.name,
                        'extracted_name': getattr(citation, 'extracted_case_name', ''),
                        'canonical_name': getattr(citation, 'canonical_name', '')
                    })
                
                if verified and 'CourtListener' not in str(source):
                    non_courtlistener_citations.append({
                        'citation': citation_text,
                        'brief': brief_file.name,
                        'source': source,
                        'canonical_name': getattr(citation, 'canonical_name', '')
                    })
        
        except Exception as e:
            print(f"  Error processing {brief_file.name}: {e}")
    
    print_citation_analysis(unverified_citations, non_courtlistener_citations)
    return True

def print_citation_analysis(unverified_citations, non_courtlistener_citations):
    """Print detailed analysis of citations"""
    
    print(f"\n{'='*80}")
    print(f"CITATION ANALYSIS RESULTS")
    print(f"{'='*80}")
    
    # Unverified Citations
    print(f"\n🔍 CITATIONS NOT VERIFIED ({len(unverified_citations)} total):")
    print(f"{'='*60}")
    
    if unverified_citations:
        # Group by citation pattern
        citation_patterns = defaultdict(list)
        for item in unverified_citations:
            citation = item['citation']
            if 'WL' in citation:
                pattern = 'Westlaw (WL)'
            elif any(x in citation.upper() for x in ['F.3D', 'F.2D', 'F.SUPP']):
                pattern = 'Federal'
            elif any(x in citation.upper() for x in ['P.3D', 'P.2D']):
                pattern = 'Pacific Reporter'
            elif any(x in citation.upper() for x in ['S.E.', 'N.E.', 'S.W.', 'N.W.']):
                pattern = 'Regional Reporter'
            else:
                pattern = 'Other'
            
            citation_patterns[pattern].append(item)
        
        for pattern, items in citation_patterns.items():
            print(f"\n📋 {pattern} Citations ({len(items)} citations):")
            for i, item in enumerate(items[:10], 1):  # Show first 10 of each type
                print(f"  {i:2d}. {item['citation']}")
                if item.get('extracted_name'):
                    print(f"      Extracted name: {item['extracted_name']}")
                print(f"      From brief: {item['brief']}")
            
            if len(items) > 10:
                print(f"      ... and {len(items) - 10} more {pattern} citations")
    else:
        print("✅ All citations were successfully verified!")
    
    # Non-CourtListener Citations
    print(f"\n🌐 CITATIONS NOT FROM COURTLISTENER ({len(non_courtlistener_citations)} total):")
    print(f"{'='*60}")
    
    if non_courtlistener_citations:
        # Group by source
        source_groups = defaultdict(list)
        for item in non_courtlistener_citations:
            source = item.get('source', 'Unknown')
            source_groups[source].append(item)
        
        for source, items in source_groups.items():
            print(f"\n📚 {source} ({len(items)} citations):")
            for i, item in enumerate(items[:5], 1):  # Show first 5 of each source
                print(f"  {i}. {item['citation']}")
                if item.get('canonical_name'):
                    print(f"     Canonical: {item['canonical_name']}")
                print(f"     From brief: {item['brief']}")
            
            if len(items) > 5:
                print(f"     ... and {len(items) - 5} more from {source}")
    else:
        print("ℹ️  All verified citations came from CourtListener")
    
    # Summary Statistics
    total_analyzed = len(unverified_citations) + len(non_courtlistener_citations)
    print(f"\n📊 SUMMARY:")
    print(f"{'='*40}")
    print(f"Total unverified citations: {len(unverified_citations)}")
    print(f"Total non-CourtListener citations: {len(non_courtlistener_citations)}")
    print(f"Total citations needing attention: {total_analyzed}")
    
    if unverified_citations:
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"  • Review unverified citations for potential database additions")
        print(f"  • Check if Westlaw citations can be converted to official reporters")
        print(f"  • Verify extracted case names for accuracy")

if __name__ == "__main__":
    success = analyze_existing_results()
    if success:
        print(f"\n✅ Citation analysis completed!")
    else:
        print(f"\n❌ Citation analysis failed!")
    
    sys.exit(0 if success else 1)
