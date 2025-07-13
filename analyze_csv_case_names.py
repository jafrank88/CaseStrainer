#!/usr/bin/env python3
"""
Analyze case names in the CSV file to find those with more than 4 capitalized words before "v."
"""

import csv
import re
import random
from collections import Counter

def analyze_csv_case_names():
    """Analyze case names in the CSV file."""
    csv_path = 'data/cleaned_wikipedia_case_names_20250710_083545.csv'
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            case_names = [row['case_name'] for row in reader]
        
        print(f"Found {len(case_names)} case names in CSV")
        print("=" * 80)
        
        # Analyze each case name
        long_case_names = []
        case_name_stats = {
            'total': 0,
            'with_v': 0,
            'more_than_4_words': 0,
            'word_count_distribution': Counter()
        }
        
        for case_name in case_names:
            if not case_name or case_name == 'N/A':
                continue
                
            case_name_stats['total'] += 1
            
            # Look for "v." pattern
            v_match = re.search(r'(.+?)\s+(?:v\.|vs\.|versus)\s+(.+)', case_name, re.IGNORECASE)
            if v_match:
                case_name_stats['with_v'] += 1
                before_v = v_match.group(1).strip()
                
                # Count capitalized words before "v."
                words = before_v.split()
                capitalized_words = [word for word in words if word and word[0].isupper()]
                
                word_count = len(capitalized_words)
                case_name_stats['word_count_distribution'][word_count] += 1
                
                if word_count > 4:
                    case_name_stats['more_than_4_words'] += 1
                    long_case_names.append({
                        'name': case_name,
                        'before_v': before_v,
                        'word_count': word_count,
                        'capitalized_words': capitalized_words
                    })
        
        # Print statistics
        print("CASE NAME ANALYSIS STATISTICS:")
        print(f"Total case names analyzed: {case_name_stats['total']}")
        print(f"Case names with 'v.' pattern: {case_name_stats['with_v']}")
        print(f"Case names with >4 capitalized words before 'v.': {case_name_stats['more_than_4_words']}")
        print()
        
        print("WORD COUNT DISTRIBUTION (capitalized words before 'v.'):")
        for word_count in sorted(case_name_stats['word_count_distribution'].keys()):
            count = case_name_stats['word_count_distribution'][word_count]
            percentage = (count / case_name_stats['with_v']) * 100 if case_name_stats['with_v'] > 0 else 0
            print(f"  {word_count} words: {count} cases ({percentage:.1f}%)")
        print()
        
        # Print detailed results for cases with >4 words
        if long_case_names:
            print(f"DETAILED RESULTS - {len(long_case_names)} CASES WITH >4 CAPITALIZED WORDS BEFORE 'v.':")
            print("=" * 80)
            
            # Sort by word count (highest first)
            long_case_names.sort(key=lambda x: x['word_count'], reverse=True)
            
            for i, case in enumerate(long_case_names, 1):
                print(f"{i:3d}. {case['name']}")
                print(f"     Before 'v.': '{case['before_v']}'")
                print(f"     Word count: {case['word_count']}")
                print(f"     Capitalized words: {case['capitalized_words']}")
                print()
        else:
            print("No cases found with more than 4 capitalized words before 'v.'")
        
        # Show 10 random case names
        print("10 RANDOM CASE NAMES:")
        print("=" * 80)
        sample = random.sample(case_names, min(10, len(case_names)))
        for i, name in enumerate(sample, 1):
            print(f"{i:2d}. {name}")
        
    except Exception as e:
        print(f"Error analyzing CSV: {e}")

if __name__ == "__main__":
    analyze_csv_case_names() 