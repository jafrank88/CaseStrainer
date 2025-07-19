#!/usr/bin/env python3
"""
Analyze confidence scores from adaptive learning results.
Compare confidence scores to extraction success and identify optimal thresholds.
"""

import json
import os
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import numpy as np

def load_adaptive_results():
    """Load the adaptive learning results."""
    results_file = "adaptive_results/adaptive_processing_results.json"
    if not os.path.exists(results_file):
        print(f"Results file not found: {results_file}")
        return []
    
    with open(results_file, 'r') as f:
        return json.load(f)

def analyze_confidence_distribution():
    """Analyze the distribution of confidence scores and their relationship to success."""
    results = load_adaptive_results()
    
    if not results:
        print("No results to analyze")
        return
    
    # Collect data for analysis
    confidence_data = []
    extraction_success = []
    case_name_success = []
    citation_success = []
    year_success = [] # Added missing variable
    
    for doc_result in results:
        filename = doc_result.get('filename', 'Unknown')
        citations_count = doc_result.get('citations_count', 0)
        
        # Get comparison results
        comparison_results = doc_result.get('comparison_results', [])
        
        for comp in comparison_results:
            extracted = comp.get('extracted', {})
            match_status = comp.get('match_status', {})
            
            # Extract confidence indicators
            case_name = extracted.get('case_name', '')
            citation = extracted.get('citation', '')
            year = extracted.get('year', '')
            
            # Determine success based on whether we extracted meaningful data
            case_name_success.append(len(case_name.strip()) > 0)
            citation_success.append(len(citation.strip()) > 0)
            year_success.append(len(year.strip()) > 0)
            
            # Overall extraction success (if we got any meaningful data)
            overall_success = any([len(case_name.strip()) > 0, len(citation.strip()) > 0, len(year.strip()) > 0])
            extraction_success.append(overall_success)
            
            # Calculate a simple confidence score based on data quality
            confidence_score = 0.0
            if len(case_name.strip()) > 0:
                confidence_score += 0.4
            if len(citation.strip()) > 0:
                confidence_score += 0.4
            if len(year.strip()) > 0:
                confidence_score += 0.2
            
            confidence_data.append(confidence_score)
    
    # Analyze the data
    print("=" * 60)
    print("CONFIDENCE SCORE ANALYSIS")
    print("=" * 60)
    
    print(f"Total extractions analyzed: {len(confidence_data)}")
    print(f"Average confidence score: {np.mean(confidence_data):.3f}")
    print(f"Median confidence score: {np.median(confidence_data):.3f}")
    print(f"Standard deviation: {np.std(confidence_data):.3f}")
    
    # Success rates by confidence level
    confidence_ranges = [
        (0.0, 0.2, "Very Low (0.0-0.2)"),
        (0.2, 0.4, "Low (0.2-0.4)"),
        (0.4, 0.6, "Medium (0.4-0.6)"),
        (0.6, 0.8, "High (0.6-0.8)"),
        (0.8, 1.0, "Very High (0.8-1.0)")
    ]
    
    print("\nSuccess Rates by Confidence Level:")
    print("-" * 40)
    
    for min_conf, max_conf, label in confidence_ranges:
        mask = [(min_conf <= conf < max_conf) for conf in confidence_data]
        if sum(mask) > 0:
            success_rate = np.mean([extraction_success[i] for i, m in enumerate(mask) if m])
            count = sum(mask)
            print(f"{label:15} | Count: {count:4d} | Success Rate: {success_rate:.3f}")
    
    # Overall success rates
    print(f"\nOverall Success Rates:")
    print(f"Case Name Extraction: {np.mean(case_name_success):.3f}")
    print(f"Citation Extraction: {np.mean(citation_success):.3f}")
    print(f"Year Extraction: {np.mean(year_success):.3f}")
    print(f"Any Data Extracted: {np.mean(extraction_success):.3f}")
    
    # Find optimal confidence threshold
    print(f"\nOptimal Confidence Threshold Analysis:")
    print("-" * 40)
    
    thresholds = np.arange(0.0, 1.0, 0.05)
    precision_scores = []
    recall_scores = []
    
    for threshold in thresholds:
        high_conf_mask = [conf >= threshold for conf in confidence_data]
        if sum(high_conf_mask) > 0:
            precision = np.mean([extraction_success[i] for i, m in enumerate(high_conf_mask) if m])
            recall = sum([extraction_success[i] and m for i, m in enumerate(high_conf_mask)]) / sum(extraction_success)
            precision_scores.append(precision)
            recall_scores.append(recall)
        else:
            precision_scores.append(0.0)
            recall_scores.append(0.0)
    
    # Find threshold with best F1 score
    f1_scores = []
    for p, r in zip(precision_scores, recall_scores):
        if p + r > 0:
            f1 = 2 * (p * r) / (p + r)
        else:
            f1 = 0.0
        f1_scores.append(f1)
    
    best_idx = np.argmax(f1_scores)
    best_threshold = thresholds[best_idx]
    best_f1 = f1_scores[best_idx]
    best_precision = precision_scores[best_idx]
    best_recall = recall_scores[best_idx]
    
    print(f"Best F1 Score: {best_f1:.3f} at threshold {best_threshold:.2f}")
    print(f"  Precision: {best_precision:.3f}")
    print(f"  Recall: {best_recall:.3f}")
    
    # Recommendations
    print(f"\nRECOMMENDATIONS:")
    print("-" * 40)
    
    current_low_conf_count = sum(1 for conf in confidence_data if conf < 0.4)
    current_high_conf_count = sum(1 for conf in confidence_data if conf >= 0.4)
    
    print(f"Current low confidence extractions (< 0.4): {current_low_conf_count}")
    print(f"Current high confidence extractions (>= 0.4): {current_high_conf_count}")
    
    if current_low_conf_count > current_high_conf_count:
        print("⚠️  Most extractions are low confidence. Consider:")
        print("   - Improving case name extraction patterns")
        print("   - Enhancing context analysis")
        print("   - Adjusting confidence calculation")
    else:
        print("✅ Good balance of confidence scores")
    
    print(f"\nSuggested confidence threshold: {best_threshold:.2f}")
    print(f"This would classify {sum(1 for conf in confidence_data if conf >= best_threshold)} extractions as high confidence")

if __name__ == "__main__":
    analyze_confidence_distribution() 