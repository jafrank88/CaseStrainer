#!/usr/bin/env python3
"""
Comprehensive Analysis of Crosscontamination Points in Citation Processing Pipeline

This identifies all spots where canonical/database data might contaminate
document extraction, causing extracted_* fields to be incorrectly populated.
"""

import re
from typing import Dict, List, Any

class CrosscontaminationAnalyzer:
    """Analyzes potential crosscontamination points in citation processing."""
    
    def __init__(self):
        self.contamination_points = []
        self.field_mappings = {
            'extracted_case_name': 'Should come from USER DOCUMENT only',
            'case_name': 'Display field - can be extracted or canonical',
            'canonical_name': 'Should come from API/DATABASE only',
            'extracted_date': 'Should come from USER DOCUMENT only', 
            'canonical_date': 'Should come from API/DATABASE only',
            'year': 'Can be from either source',
            'court': 'Usually from API/DATABASE',
            'url': 'Always from API/DATABASE'
        }
    
    def analyze_contamination_points(self) -> Dict[str, List[str]]:
        """Identify all potential crosscontamination points."""
        
        contamination_risks = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': [],
            'safe_zones': []
        }
        
        # HIGH RISK: Direct field copying/overwriting
        contamination_risks['high_risk'].extend([
            "🚨 verify_citations() method: extracted_case_name might be overwritten by canonical_name",
            "🚨 format_for_frontend() method: case_name assignment logic mixes extracted and canonical",
            "🚨 CitationResult.__post_init__: field initialization might use wrong source",
            "🚨 Eyecite integration: eyecite metadata might overwrite document extraction",
            "🚨 Complex citation parsing: parallel citation logic might merge different cases"
        ])
        
        # MEDIUM RISK: Indirect contamination through shared objects
        contamination_risks['medium_risk'].extend([
            "⚠️ Citation grouping: similar case names might cause data mixing",
            "⚠️ Cache system: cached results might have mixed data sources",
            "⚠️ Citation normalization: normalized citations lose original context",
            "⚠️ Method prioritization: high-confidence API results might override document extraction",
            "⚠️ Batch processing: citations processed together might cross-pollinate"
        ])
        
        # LOW RISK: Edge cases and timing issues
        contamination_risks['low_risk'].extend([
            "⚙️ Concurrent processing: race conditions in parallel citation verification",
            "⚙️ Error handling: fallback logic might use wrong data source",
            "⚙️ Regex pattern conflicts: overlapping patterns might extract wrong context",
            "⚙️ Text cleaning: preprocessing might affect extraction accuracy"
        ])
        
        # SAFE ZONES: Properly isolated functions
        contamination_risks['safe_zones'].extend([
            "✅ DateExtractor.extract_date_from_context(): Uses only text and positions",
            "✅ EnhancedCaseNameExtractor: Uses only document text",
            "✅ CitationParser.extract_from_text(): Standalone document extraction",
            "✅ Individual API calls: Pure canonical data retrieval"
        ])
        
        return contamination_risks
    
    def analyze_code_sections(self) -> List[Dict[str, Any]]:
        """Analyze specific code sections for contamination risks."""
        
        sections = [
            {
                'section': 'verify_citations() method',
                'risk_level': 'HIGH',
                'contamination_type': 'Direct field overwriting',
                'problem_code': '''
# PROBLEM: This might overwrite extracted data with canonical data
if citation.extracted_case_name and citation.extracted_case_name != 'N/A':
    citation.case_name = citation.extracted_case_name
elif citation.canonical_name and citation.canonical_name != 'N/A':
    citation.case_name = citation.canonical_name  # CONTAMINATION!
                ''',
                'fixed_code': '''
# SOLUTION: Keep extracted and canonical data completely separate
citation.extracted_case_name = extract_from_document(text, citation)
citation.canonical_name = get_from_api(citation)
# Display logic should be in format_for_frontend(), not here
                ''',
                'issues': [
                    'extracted_case_name can be overwritten by canonical_name',
                    'Logic mixes document and API data in same method',
                    'No clear separation of data sources'
                ]
            },
            
            {
                'section': 'Eyecite Integration',
                'risk_level': 'HIGH', 
                'contamination_type': 'Metadata mixing',
                'problem_code': '''
# PROBLEM: Eyecite metadata might overwrite document extraction
if hasattr(citation, 'metadata') and citation.metadata:
    if hasattr(citation.metadata, 'plaintiff') and hasattr(citation.metadata, 'defendant'):
        citation.case_name = f"{plaintiff} v. {defendant}"  # CONTAMINATION!
                ''',
                'fixed_code': '''
# SOLUTION: Store eyecite data separately
citation.eyecite_case_name = f"{plaintiff} v. {defendant}"
citation.eyecite_metadata = citation_metadata
# Keep document extraction separate
citation.extracted_case_name = extract_from_document_context(text, citation)
                ''',
                'issues': [
                    'Eyecite metadata overwrites document extraction',
                    'No distinction between eyecite and document sources',
                    'Mixed data sources in same field'
                ]
            },
            
            {
                'section': 'Citation Grouping',
                'risk_level': 'MEDIUM',
                'contamination_type': 'Cross-citation data bleeding',
                'problem_code': '''
# PROBLEM: Grouping might mix data from different citations
if self._are_same_case(citation1, citation2):
    group.append(other)  # Data from citation2 might contaminate citation1
                ''',
                'fixed_code': '''
# SOLUTION: Keep individual citation data isolated
grouped_citations = self.group_citations(citations)
for group in grouped_citations:
    primary = group[0]
    primary.parallel_citations = [c.citation for c in group[1:]]
    # Don't copy case names or dates - each citation keeps its own extracted data
                ''',
                'issues': [
                    'Case names from different citations might be mixed',
                    'Grouping logic might prioritize wrong data source',
                    'Parallel citations might overwrite primary citation data'
                ]
            },
            
            {
                'section': 'format_for_frontend()',
                'risk_level': 'MEDIUM',
                'contamination_type': 'Display logic contamination',
                'problem_code': '''
# PROBLEM: Display logic mixes sources and might overwrite extracted data
'case_name': citation.case_name if citation.case_name else 'N/A',
'extracted_case_name': citation.extracted_case_name if getattr(citation, 'extracted_case_name', None) else 'N/A',
                ''',
                'fixed_code': '''
# SOLUTION: Always show both sources clearly
'case_name_display': citation.extracted_case_name or citation.canonical_name or 'N/A',
'extracted_case_name': citation.extracted_case_name or 'N/A',
'canonical_case_name': citation.canonical_name or 'N/A',
'data_source_priority': 'extracted' if citation.extracted_case_name else 'canonical'
                ''',
                'issues': [
                    'Display logic might hide data source contamination',
                    'Frontend gets mixed data without knowing source',
                    'Debugging becomes impossible'
                ]
            },
            
            {
                'section': 'Cache System',
                'risk_level': 'MEDIUM',
                'contamination_type': 'Cached data mixing',
                'problem_code': '''
# PROBLEM: Cache might store mixed data from different processing runs
cached_result = self._check_cache(citation)
if cached_result:
    return cached_result  # Might have contaminated data from previous run
                ''',
                'fixed_code': '''
# SOLUTION: Cache keys should include document context hash
cache_key = f"{citation}_{document_hash}_{extraction_method}"
cached_result = self._check_cache(cache_key)
# Cache should only store canonical data, not document-extracted data
                ''',
                'issues': [
                    'Cache might return results from different documents',
                    'Document-specific extraction gets cached globally',
                    'No separation between canonical and document cache'
                ]
            },
            
            {
                'section': 'Error Handling',
                'risk_level': 'LOW',
                'contamination_type': 'Fallback contamination',
                'problem_code': '''
# PROBLEM: Error fallbacks might use wrong data source
except Exception as e:
    citation.extracted_case_name = citation.canonical_name  # CONTAMINATION!
                ''',
                'fixed_code': '''
# SOLUTION: Keep error fallbacks clean
except Exception as e:
    citation.extracted_case_name = None  # Don't fallback to canonical
    citation.extraction_error = str(e)
    # Log the error but don't contaminate data
                ''',
                'issues': [
                    'Error handling contaminates extracted fields',
                    'Fallback logic uses wrong data source',
                    'Errors hide data source problems'
                ]
            }
        ]
        
        return sections
    
    def generate_contamination_checklist(self) -> List[str]:
        """Generate a checklist to prevent contamination."""
        
        checklist = [
            "✅ FIELD SEPARATION:",
            "   - extracted_* fields only from document text",
            "   - canonical_* fields only from API/database", 
            "   - Display fields use clear priority logic",
            "",
            "✅ METHOD ISOLATION:",
            "   - Document extraction methods never call API",
            "   - API methods never use document text",
            "   - Verification combines both but keeps separate",
            "",
            "✅ DATA FLOW VALIDATION:",
            "   - Each field has single, clear data source",
            "   - No field assignment from multiple sources",
            "   - Clear precedence rules documented",
            "",
            "✅ TESTING VALIDATION:",
            "   - Test document extraction with no API access", 
            "   - Test API extraction with empty document",
            "   - Verify each field comes from expected source",
            "",
            "✅ ERROR HANDLING:",
            "   - Failures don't fallback to wrong data source",
            "   - Null values preferred over contaminated data",
            "   - Clear error messages about data source failures"
        ]
        
        return checklist
    
    def generate_debugging_guide(self) -> List[str]:
        """Generate debugging guide for contamination issues."""
        
        guide = [
            "🔍 DEBUGGING CONTAMINATION:",
            "",
            "1. CHECK FIELD SOURCES:",
            "   - Add debug prints showing where each field gets set",
            "   - Trace extracted_* fields back to document extraction only", 
            "   - Trace canonical_* fields back to API calls only",
            "",
            "2. ISOLATION TESTING:",
            "   - Run document extraction with API disabled",
            "   - Run API extraction with empty document text",
            "   - Compare results to identify cross-contamination",
            "",
            "3. TIMELINE ANALYSIS:",
            "   - Log order of field assignments",
            "   - Check if canonical data overwrites extracted data",
            "   - Look for late assignment in format_for_frontend()",
            "",
            "4. CACHE VALIDATION:",
            "   - Clear all caches and retest",
            "   - Check if cache keys include document context",
            "   - Verify cache doesn't mix document-specific data",
            "",
            "5. INTEGRATION POINTS:",
            "   - Check eyecite integration for metadata mixing",
            "   - Verify citation grouping doesn't cross-pollinate",
            "   - Test concurrent processing for race conditions"
        ]
        
        return guide
    
    def print_analysis_report(self):
        """Print comprehensive contamination analysis."""
        
        print("🧪 CITATION CROSSCONTAMINATION ANALYSIS")
        print("=" * 60)
        
        # Risk levels
        risks = self.analyze_contamination_points()
        for risk_level, items in risks.items():
            if items:
                print(f"\n{risk_level.upper().replace('_', ' ')}:")
                for item in items:
                    print(f"  {item}")
        
        # Code sections
        print(f"\n📋 DETAILED CODE ANALYSIS:")
        sections = self.analyze_code_sections()
        for section in sections:
            print(f"\n{section['section']} ({section['risk_level']} RISK):")
            print(f"  Type: {section['contamination_type']}")
            for issue in section['issues']:
                print(f"  • {issue}")
        
        # Checklist
        print(f"\n📝 PREVENTION CHECKLIST:")
        checklist = self.generate_contamination_checklist()
        for item in checklist:
            print(f"{item}")
        
        # Debugging guide
        print(f"\n🔧 DEBUGGING GUIDE:")
        guide = self.generate_debugging_guide()
        for item in guide:
            print(f"{item}")

def main():
    """Run contamination analysis."""
    analyzer = CrosscontaminationAnalyzer()
    analyzer.print_analysis_report()

if __name__ == "__main__":
    main() 