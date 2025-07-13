#!/usr/bin/env python3
"""
Analyze case names in the database to find those with more than 3 capitalized words before "v."
"""

import sqlite3
import re
import os
from collections import Counter

def connect_to_database():
    """Connect to the citations database."""
    db_path = os.path.join('data', 'citations.db')
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def analyze_case_names():
    """Analyze case names in the database."""
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Get all case names from the database
        cursor.execute("""
            SELECT DISTINCT case_name 
            FROM citations 
            WHERE case_name IS NOT NULL 
              AND case_name != 'N/A'
              AND case_name != ''
        """)
        
        results = cursor.fetchall()
        
        print(f"Found {len(results)} unique case names in database")
        print("=" * 80)
        
        # Analyze each case name
        long_case_names = []
        case_name_stats = {
            'total': 0,
            'with_v': 0,
            'more_than_3_words': 0,
            'word_count_distribution': Counter()
        }
        
        for (case_name,) in results:
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
                
                if word_count > 3:
                    case_name_stats['more_than_3_words'] += 1
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
        print(f"Case names with >3 capitalized words before 'v.': {case_name_stats['more_than_3_words']}")
        print()
        
        print("WORD COUNT DISTRIBUTION (capitalized words before 'v.'):")
        for word_count in sorted(case_name_stats['word_count_distribution'].keys()):
            count = case_name_stats['word_count_distribution'][word_count]
            percentage = (count / case_name_stats['with_v']) * 100 if case_name_stats['with_v'] > 0 else 0
            print(f"  {word_count} words: {count} cases ({percentage:.1f}%)")
        print()
        
        # Print detailed results for cases with >3 words
        if long_case_names:
            print(f"DETAILED RESULTS - {len(long_case_names)} CASES WITH >3 CAPITALIZED WORDS BEFORE 'v.':")
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
            print("No cases found with more than 3 capitalized words before 'v.'")
        
        # Additional analysis: Show some examples of different word counts
        print("EXAMPLES BY WORD COUNT:")
        print("=" * 80)
        
        examples_by_count = {}
        for case in long_case_names:
            count = case['word_count']
            if count not in examples_by_count:
                examples_by_count[count] = []
            examples_by_count[count].append(case['name'])
        
        for count in sorted(examples_by_count.keys(), reverse=True):
            print(f"\n{count} capitalized words before 'v.':")
            for example in examples_by_count[count][:5]:  # Show first 5 examples
                print(f"  - {example}")
            if len(examples_by_count[count]) > 5:
                print(f"  ... and {len(examples_by_count[count]) - 5} more")
        
        # Print 10 random case names if any exist
        import random
        if results:
            print("\n10 RANDOM CASE NAMES:")
            print("=" * 80)
            sample = random.sample([row[0] for row in results], min(10, len(results)))
            for i, name in enumerate(sample, 1):
                print(f"{i:2d}. {name}")
        else:
            print("No case names available to sample.")
        
    except Exception as e:
        print(f"Error analyzing database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_case_names() 