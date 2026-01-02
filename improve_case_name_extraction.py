#!/usr/bin/env python3
"""
Improve case name extraction accuracy by analyzing and fixing common patterns
"""

import sys
import os
import requests
import re
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def analyze_extraction_errors():
    """Analyze the extraction errors to identify patterns"""
    
    print("🔍 ANALYZING CASE NAME EXTRACTION ERRORS")
    print("=" * 50)
    
    # Get production API results to analyze
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    pdf_url = "http://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"
    
    try:
        response = requests.post(
            api_url,
            json={"url": pdf_url},
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            # Analyze extraction patterns
            print("Analyzing extraction patterns...")
            
            abbreviation_errors = []
            missing_words = []
            formatting_issues = []
            major_errors = []
            
            for cit in citations:
                citation_text = cit.get('citation', '')
                extracted = cit.get('extracted_case_name', 'N/A')
                canonical = cit.get('canonical_name', 'N/A')
                verified = cit.get('verified', False)
                
                if extracted != 'N/A' and canonical != 'N/A' and verified:
                    # Categorize the error type
                    if _is_abbreviation_error(extracted, canonical):
                        abbreviation_errors.append((citation_text, extracted, canonical))
                    elif _is_missing_words_error(extracted, canonical):
                        missing_words.append((citation_text, extracted, canonical))
                    elif _is_formatting_issue(extracted, canonical):
                        formatting_issues.append((citation_text, extracted, canonical))
                    elif _is_major_error(extracted, canonical):
                        major_errors.append((citation_text, extracted, canonical))
            
            print(f"\n📊 ERROR CATEGORIES:")
            print("-" * 25)
            print(f"📝 Abbreviation errors: {len(abbreviation_errors)}")
            print(f"🔤 Missing words: {len(missing_words)}")
            print(f"🎨 Formatting issues: {len(formatting_issues)}")
            print(f"💥 Major errors: {len(major_errors)}")
            
            # Show examples of each category
            if abbreviation_errors:
                print(f"\n📝 ABBREVIATION ERRORS:")
                print("-" * 30)
                for citation, extracted, canonical in abbreviation_errors[:3]:
                    print(f"  {citation}:")
                    print(f"    Extracted: '{extracted}'")
                    print(f"    Canonical: '{canonical}'")
                    print()
            
            if missing_words:
                print(f"\n🔤 MISSING WORDS ERRORS:")
                print("-" * 30)
                for citation, extracted, canonical in missing_words[:3]:
                    print(f"  {citation}:")
                    print(f"    Extracted: '{extracted}'")
                    print(f"    Canonical: '{canonical}'")
                    print()
            
            if major_errors:
                print(f"\n💥 MAJOR ERRORS:")
                print("-" * 20)
                for citation, extracted, canonical in major_errors[:3]:
                    print(f"  {citation}:")
                    print(f"    Extracted: '{extracted}'")
                    print(f"    Canonical: '{canonical}'")
                    print()
            
            return {
                'abbreviation_errors': abbreviation_errors,
                'missing_words': missing_words,
                'formatting_issues': formatting_issues,
                'major_errors': major_errors
            }
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def _is_abbreviation_error(extracted: str, canonical: str) -> bool:
    """Check if error is due to abbreviations"""
    abbreviations = [
        ('Dep\'t', 'Department'),
        ('Dept', 'Department'),
        ('Co', 'Company'),
        ('Inc', 'Incorporated'),
        ('Corp', 'Corporation'),
        ('Ltd', 'Limited'),
        ('LLC', 'Limited Liability Company'),
        ('Bd', 'Board'),
        ('Colls', 'Colleges'),
        ('Dev', 'Development'),
        ('Indus', 'Industries'),
        ('Corr', 'Corrections')
    ]
    
    for abbrev, full in abbreviations:
        if abbrev in extracted and full in canonical:
            return True
    return False

def _is_missing_words_error(extracted: str, canonical: str) -> bool:
    """Check if error is due to missing words"""
    # Common missing words
    missing_patterns = [
        ('City of', 'Bellevue'),  # Missing "City of"
        ('County', 'Snohomish'),  # Missing "County"
        ('State', 'Washington'),  # Missing "State"
    ]
    
    for missing_word, indicator in missing_patterns:
        if missing_word in canonical and missing_word not in extracted:
            if indicator in extracted and indicator in canonical:
                return True
    return False

def _is_formatting_issue(extracted: str, canonical: str) -> bool:
    """Check if error is minor formatting issue"""
    # Remove punctuation and compare
    extracted_clean = re.sub(r'[^\w\s]', '', extracted.lower())
    canonical_clean = re.sub(r'[^\w\s]', '', canonical.lower())
    
    # If they're very similar after cleaning, it's a formatting issue
    if extracted_clean in canonical_clean or canonical_clean in extracted_clean:
        return True
    
    # Check for minor word order differences
    extracted_words = extracted_clean.split()
    canonical_words = canonical_clean.split()
    
    # If most words match, it's formatting
    common_words = set(extracted_words) & set(canonical_words)
    if len(common_words) >= min(len(extracted_words), len(canonical_words)) * 0.8:
        return True
    
    return False

def _is_major_error(extracted: str, canonical: str) -> bool:
    """Check if this is a major error (completely different case name)"""
    extracted_clean = re.sub(r'[^\w\s]', '', extracted.lower())
    canonical_clean = re.sub(r'[^\w\s]', '', canonical.lower())
    
    # If very few words match, it's a major error
    extracted_words = set(extracted_clean.split())
    canonical_words = set(canonical_clean.split())
    
    common_words = extracted_words & canonical_words
    similarity = len(common_words) / max(len(extracted_words), len(canonical_words))
    
    return similarity < 0.3

def create_improvement_strategies(error_analysis):
    """Create improvement strategies based on error analysis"""
    
    if not error_analysis:
        return
    
    print("\n🔧 IMPROVEMENT STRATEGIES")
    print("=" * 30)
    
    strategies = []
    
    # Strategy 1: Abbreviation expansion
    if error_analysis['abbreviation_errors']:
        print("📝 STRATEGY 1: Abbreviation Expansion")
        print("-" * 40)
        print("Create abbreviation mapping to expand common abbreviations")
        
        # Collect abbreviations from errors
        abbrev_map = {}
        for _, extracted, canonical in error_analysis['abbreviation_errors']:
            # Find abbreviations in extracted
            for word in extracted.split():
                if len(word) <= 5 and '.' in word or word.endswith("'t"):
                    # Try to find full version in canonical
                    for full_word in canonical.split():
                        if word.lower() in full_word.lower() and len(full_word) > len(word):
                            abbrev_map[word] = full_word
                            break
        
        print("Abbreviation mappings to add:")
        for abbrev, full in abbrev_map.items():
            print(f"  '{abbrev}' → '{full}'")
        
        strategies.append(('abbreviation_expansion', abbrev_map))
    
    # Strategy 2: Missing words detection
    if error_analysis['missing_words']:
        print("\n🔤 STRATEGY 2: Missing Words Detection")
        print("-" * 40)
        print("Add logic to detect missing common words like 'City of', 'County'")
        
        strategies.append(('missing_words', {}))
    
    # Strategy 3: Context boundary improvement
    if error_analysis['major_errors']:
        print("\n💥 STRATEGY 3: Context Boundary Improvement")
        print("-" * 45)
        print("Improve strict context isolation to prevent case name bleeding")
        
        strategies.append(('context_boundaries', {}))
    
    return strategies

if __name__ == "__main__":
    error_analysis = analyze_extraction_errors()
    strategies = create_improvement_strategies(error_analysis)
    
    print(f"\n🎯 NEXT STEPS:")
    print("-" * 15)
    print("1. Implement abbreviation expansion")
    print("2. Add missing words detection")
    print("3. Improve context boundary detection")
    print("4. Test improvements with production data")
