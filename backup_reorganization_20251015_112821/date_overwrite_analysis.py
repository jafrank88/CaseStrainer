#!/usr/bin/env python3
"""
Analysis of Date Overwrite Issues - Where Dates Get Replaced with Blanks

This identifies all places where a successfully extracted date could be
overwritten with None, empty string, or other blank values.
"""

import re
from typing import Dict, List, Any, Optional

class DateOverwriteAnalyzer:
    """Analyzes places where dates can be overwritten with blanks."""
    
    def __init__(self):
        self.overwrite_patterns = []
        
    def analyze_overwrite_risks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Identify all date overwrite risks."""
        
        risks = {
            'critical_overwrites': [],
            'logic_overwrites': [],
            'error_overwrites': [],
            'initialization_overwrites': [],
            'fallback_overwrites': []
        }
        
        # CRITICAL: Direct field overwriting
        risks['critical_overwrites'].extend([
            {
                'location': 'verify_citations() method',
                'risk': 'VERY HIGH',
                'problem': 'extracted_date gets overwritten by failed API call',
                'code_pattern': '''
# PROBLEM: API failure overwrites successful document extraction
canonical_result = get_canonical_case_name_with_date(citation.citation)
if canonical_result:
    citation.canonical_date = canonical_result.get('date', 'N/A')
else:
    citation.canonical_date = 'N/A'  # This is fine
    
# BUT THEN THIS HAPPENS:
citation.extracted_date = canonical_result.get('date', '')  # OVERWRITES with blank!
                ''',
                'consequence': 'Successfully extracted date from document gets replaced with empty string',
                'fix': 'Never assign canonical data to extracted fields'
            },
            
            {
                'location': 'format_for_frontend() assignment logic',
                'risk': 'HIGH', 
                'problem': 'Display logic overwrites with fallback None values',
                'code_pattern': '''
# PROBLEM: Fallback logic overwrites good data
'extracted_date': citation.extracted_date if getattr(citation, 'extracted_date', None) else 'N/A',
# If citation.extracted_date exists but is falsy ('', 0, False), it gets overwritten!
                ''',
                'consequence': 'Good extracted dates replaced with "N/A" in output',
                'fix': 'Use explicit None checks instead of falsy checks'
            },
            
            {
                'location': 'CitationResult field initialization',
                'risk': 'MEDIUM',
                'problem': 'Default field values overwrite during object creation',
                'code_pattern': '''
# PROBLEM: Object creation with default values
result = CitationResult(
    citation=citation_str,
    extracted_date=None,  # Overwrites any previously set value
    # ...
)
                ''',
                'consequence': 'Date extraction happens but then object recreation blanks it',
                'fix': 'Preserve existing values during object updates'
            }
        ])
        
        # LOGIC: Conditional overwriting
        risks['logic_overwrites'].extend([
            {
                'location': 'Enhanced extraction integration',
                'risk': 'HIGH',
                'problem': 'Multiple extraction attempts overwrite each other',
                'code_pattern': '''
# PROBLEM: Later extraction overwrites earlier success
extracted_info = extract_case_info_enhanced(text, citation.citation)
if extracted_info.get('year'):
    citation.extracted_date = extracted_info['year']  # Good
    
# BUT THEN:
fallback_info = extract_with_different_method(text, citation)
citation.extracted_date = fallback_info.get('date', '')  # Overwrites with blank!
                ''',
                'consequence': 'First successful extraction gets overwritten by failed second attempt',
                'fix': 'Only update if new value is better than existing'
            },
            
            {
                'location': 'Citation grouping merge logic',
                'risk': 'MEDIUM',
                'problem': 'Parallel citation merging overwrites dates',
                'code_pattern': '''
# PROBLEM: Primary citation has date, parallel citation doesn't
primary_citation.extracted_date = "2022"  # Good
parallel_citation.extracted_date = ""     # Blank

# During grouping:
if len(group) > 1:
    primary = group[0]
    for other in group[1:]:
        # This might overwrite primary's good date with parallel's blank date
        if not primary.extracted_date and other.extracted_date:
            primary.extracted_date = other.extracted_date  # Could be blank!
                ''',
                'consequence': 'Good date from primary citation replaced with blank from parallel',
                'fix': 'Only merge non-empty values'
            }
        ])
        
        # ERROR: Exception handling overwrites
        risks['error_overwrites'].extend([
            {
                'location': 'Exception handling in date extraction',
                'risk': 'MEDIUM',
                'problem': 'Error handling blanks out successful extractions',
                'code_pattern': '''
# PROBLEM: Exception resets field instead of preserving
try:
    extracted_date = DateExtractor.extract_date_from_context(text, start, end)
    citation.extracted_date = extracted_date  # Success!
except Exception as e:
    citation.extracted_date = ''  # OVERWRITES successful extraction!
    logger.warning(f"Date extraction failed: {e}")
                ''',
                'consequence': 'Successful date extraction gets wiped by later exception',
                'fix': 'Preserve existing values on exceptions'
            },
            
            {
                'location': 'API timeout/failure handling',
                'risk': 'LOW',
                'problem': 'API failures reset document-extracted dates',
                'code_pattern': '''
# PROBLEM: API failure affects document extraction
citation.extracted_date = "2022"  # From document
try:
    api_result = verify_with_api(citation)
    citation.extracted_date = api_result.get('date', None)  # API failed, overwrites!
except:
    citation.extracted_date = None  # Double overwrite!
                ''',
                'consequence': 'Document extraction success gets lost due to unrelated API failure',
                'fix': 'Keep API and document data completely separate'
            }
        ])
        
        # INITIALIZATION: Object/field initialization issues
        risks['initialization_overwrites'].extend([
            {
                'location': 'CitationResult.__post_init__',
                'risk': 'MEDIUM',
                'problem': 'Post-initialization resets fields',
                'code_pattern': '''
# PROBLEM: __post_init__ might reset fields
def __post_init__(self):
    if self.extracted_date is None:
        self.extracted_date = ""  # Converts None to empty string
    # This changes the field even if it was intentionally None
                ''',
                'consequence': 'None values get converted to empty strings, affecting logic',
                'fix': 'Avoid changing field values in __post_init__'
            },
            
            {
                'location': 'JSON serialization/deserialization',
                'risk': 'LOW',
                'problem': 'JSON conversion loses date types',
                'code_pattern': '''
# PROBLEM: JSON round-trip changes date values
citation.extracted_date = datetime(2022, 1, 1)  # datetime object
json_data = json.dumps(citation, default=str)
reloaded = json.loads(json_data)
# Now extracted_date might be string "None" or missing entirely
                ''',
                'consequence': 'Date objects become strings or disappear',
                'fix': 'Proper JSON serialization handlers'
            }
        ])
        
        # FALLBACK: Fallback logic overwrites
        risks['fallback_overwrites'].extend([
            {
                'location': 'Multi-method extraction with poor precedence',
                'risk': 'HIGH',
                'problem': 'Lower priority methods overwrite higher priority successes',
                'code_pattern': '''
# PROBLEM: Method order overwrites better results
# Method 1: Enhanced extraction (success)
citation.extracted_date = enhanced_extractor.extract_date(text, citation)  # "2022"

# Method 2: Fallback extraction (failure)  
if not citation.extracted_date:  # This check fails because "2022" is truthy
    fallback_date = simple_extractor.extract_date(text)  # Returns ""
    citation.extracted_date = fallback_date  # Overwrites "2022" with ""!
                ''',
                'consequence': 'Better extraction results overwritten by worse fallback methods',
                'fix': 'Use proper precedence and only update if value is better'
            },
            
            {
                'location': 'Context-based extraction priority',
                'risk': 'MEDIUM',
                'problem': 'Context extraction overwrites direct extraction',
                'code_pattern': '''
# PROBLEM: Multiple extraction contexts override each other
# Direct citation context (success)
citation.extracted_date = extract_from_citation_context(text, citation)  # "2022"

# Paragraph context (failure)
paragraph_date = extract_from_paragraph_context(text, citation)  # ""
if paragraph_date:  # This is falsy, so skipped - good
    citation.extracted_date = paragraph_date
else:
    citation.extracted_date = ""  # Wait, why are we setting this to blank?!
                ''',
                'consequence': 'Successful direct extraction replaced with blank from failed context',
                'fix': 'Never overwrite successful extraction with blanks'
            }
        ])
        
        return risks
    
    def generate_protection_patterns(self) -> List[Dict[str, str]]:
        """Generate patterns to protect against date overwrites."""
        
        patterns = [
            {
                'pattern_name': 'Safe Assignment Pattern',
                'before': '''
# DANGEROUS: Always overwrites
citation.extracted_date = new_value
                ''',
                'after': '''
# SAFE: Only updates if new value is better
if new_value and (not citation.extracted_date or len(str(new_value)) > len(str(citation.extracted_date))):
    citation.extracted_date = new_value
                ''',
                'description': 'Only update if new value is non-empty and better than existing'
            },
            
            {
                'pattern_name': 'Fallback Preservation Pattern',
                'before': '''
# DANGEROUS: Exception overwrites
try:
    citation.extracted_date = extract_date(text)
except:
    citation.extracted_date = ""  # Overwrites!
                ''',
                'after': '''
# SAFE: Exception preserves existing
try:
    new_date = extract_date(text)
    if new_date:  # Only update if successful
        citation.extracted_date = new_date
except Exception as e:
    # Don't overwrite existing value
    logger.warning(f"Date extraction failed: {e}")
                ''',
                'description': 'Preserve existing values when operations fail'
            },
            
            {
                'pattern_name': 'Multi-Method Protection Pattern',
                'before': '''
# DANGEROUS: Later methods overwrite earlier success
citation.extracted_date = method1()  # Success: "2022"
citation.extracted_date = method2()  # Failure: "" - overwrites!
                ''',
                'after': '''
# SAFE: Priority-based assignment
methods = [
    ('enhanced', lambda: enhanced_extract_date(text, citation)),
    ('context', lambda: context_extract_date(text, citation)), 
    ('fallback', lambda: simple_extract_date(text))
]

for method_name, method_func in methods:
    try:
        result = method_func()
        if result and not citation.extracted_date:  # Only if no existing value
            citation.extracted_date = result
            citation.extraction_method = method_name
            break  # Stop after first success
    except:
        continue  # Try next method
                ''',
                'description': 'Use priority order and stop after first success'
            },
            
            {
                'pattern_name': 'Conditional Update Pattern',
                'before': '''
# DANGEROUS: Overwrites with falsy values
if condition:
    citation.extracted_date = potentially_empty_value
                ''',
                'after': '''
# SAFE: Only updates with valid values
if condition and potentially_empty_value:
    citation.extracted_date = potentially_empty_value
elif condition:
    # Log that condition was met but value was empty
    logger.debug(f"Condition met but no valid date found for {citation.citation}")
                ''',
                'description': 'Guard against updating with empty/falsy values'
            },
            
            {
                'pattern_name': 'Field Separation Pattern',
                'before': '''
# DANGEROUS: Mixed field usage
canonical_result = api_call()
citation.extracted_date = canonical_result.get('date', '')  # Wrong field!
                ''',
                'after': '''
# SAFE: Strict field separation
canonical_result = api_call()
citation.canonical_date = canonical_result.get('date', '')  # Correct field

# extracted_date should only be set from document extraction
document_result = extract_from_document(text, citation)
if document_result and document_result.get('date'):
    citation.extracted_date = document_result['date']
                ''',
                'description': 'Never mix canonical and extracted field assignments'
            }
        ]
        
        return patterns
    
    def generate_debugging_checklist(self) -> List[str]:
        """Generate checklist for debugging date overwrites."""
        
        checklist = [
            "🔍 DATE OVERWRITE DEBUGGING CHECKLIST:",
            "",
            "1. TRACE FIELD ASSIGNMENTS:",
            "   □ Add logging before every extracted_date assignment",
            "   □ Log the source/method setting each date value", 
            "   □ Track the call stack when dates get overwritten",
            "",
            "2. CHECK EXTRACTION ORDER:",
            "   □ Verify extraction methods run in correct priority order",
            "   □ Ensure later methods don't overwrite earlier successes",
            "   □ Check if fallback methods are incorrectly triggering",
            "",
            "3. VALIDATE FIELD SEPARATION:",
            "   □ Ensure extracted_date only comes from document text",
            "   □ Verify canonical_date only comes from API calls",
            "   □ Check for incorrect field crossover",
            "",
            "4. TEST EXCEPTION HANDLING:",
            "   □ Verify exceptions don't blank out successful extractions",
            "   □ Check error recovery preserves existing values",
            "   □ Test timeout scenarios don't overwrite good data",
            "",
            "5. REVIEW OBJECT LIFECYCLE:",
            "   □ Check CitationResult initialization doesn't reset fields",
            "   □ Verify JSON serialization preserves date values",
            "   □ Test object copying/cloning preserves dates",
            "",
            "6. VALIDATE CONDITIONAL LOGIC:",
            "   □ Check if-statements use proper truthy/falsy checks",
            "   □ Verify fallback conditions don't incorrectly trigger",
            "   □ Test edge cases with empty strings vs None vs 0"
        ]
        
        return checklist
    
    def generate_quick_fixes(self) -> List[str]:
        """Generate immediate fixes for common overwrite issues."""
        
        fixes = [
            "🚀 IMMEDIATE FIXES FOR DATE OVERWRITES:",
            "",
            "1. ADD PROTECTION WRAPPER:",
            '''
def safe_set_extracted_date(citation, new_date, source="unknown"):
    """Safely set extracted_date, preserving existing good values."""
    if not new_date:  # Don't overwrite with empty values
        logger.debug(f"Skipping empty date from {source} for {citation.citation}")
        return False
        
    if citation.extracted_date and len(str(citation.extracted_date)) >= len(str(new_date)):
        logger.debug(f"Keeping existing date {citation.extracted_date} over {new_date}")
        return False
        
    logger.info(f"Setting extracted_date to {new_date} from {source}")
    citation.extracted_date = new_date
    return True
            ''',
            "",
            "2. GUARD ASSIGNMENT LOCATIONS:",
            "   Replace: citation.extracted_date = value",
            "   With: safe_set_extracted_date(citation, value, 'method_name')",
            "",
            "3. ADD FIELD VALIDATION:",
            '''
def validate_citation_dates(citation):
    """Validate date fields haven't been corrupted."""
    issues = []
    
    if hasattr(citation, 'extracted_date'):
        if citation.extracted_date == "":
            issues.append("extracted_date is empty string (should be None or valid date)")
        if citation.extracted_date == "N/A":
            issues.append("extracted_date is 'N/A' (should be None)")
            
    if issues:
        logger.warning(f"Date validation issues for {citation.citation}: {issues}")
    
    return len(issues) == 0
            ''',
            "",
            "4. TRACE ASSIGNMENT SOURCES:",
            '''
# Add this at the top of verify_citations():
import inspect

original_setattr = CitationResult.__setattr__
def traced_setattr(self, name, value):
    if name == 'extracted_date':
        caller = inspect.stack()[1]
        logger.debug(f"Setting extracted_date to '{value}' from {caller.filename}:{caller.lineno}")
    return original_setattr(self, name, value)
CitationResult.__setattr__ = traced_setattr
            '''
        ]
        
        return fixes
    
    def print_analysis_report(self):
        """Print comprehensive overwrite analysis."""
        
        print("📅 DATE OVERWRITE ANALYSIS REPORT")
        print("=" * 60)
        
        risks = self.analyze_overwrite_risks()
        
        for category, risk_list in risks.items():
            if risk_list:
                print(f"\n{category.upper().replace('_', ' ')}:")
                for risk in risk_list:
                    print(f"\n📍 {risk['location']} ({risk['risk']} RISK)")
                    print(f"   Problem: {risk['problem']}")
                    print(f"   Impact: {risk['consequence']}")
                    print(f"   Solution: {risk['fix']}")
        
        print(f"\n🛡️ PROTECTION PATTERNS:")
        patterns = self.generate_protection_patterns()
        for pattern in patterns:
            print(f"\n{pattern['pattern_name']}:")
            print(f"   {pattern['description']}")
        
        print(f"\n✅ DEBUGGING CHECKLIST:")
        checklist = self.generate_debugging_checklist()
        for item in checklist:
            print(item)
        
        print(f"\n🔧 QUICK FIXES:")
        fixes = self.generate_quick_fixes()
        for fix in fixes:
            print(fix)

def main():
    """Run date overwrite analysis."""
    analyzer = DateOverwriteAnalyzer()
    analyzer.print_analysis_report()

if __name__ == "__main__":
    main() 