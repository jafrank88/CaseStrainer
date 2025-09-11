"""
Migration Script: Unified Extraction Architecture

This script helps migrate the existing codebase to use the new unified
extraction service and enforce data separation between extracted and canonical names.

Usage:
    python src/migration_to_unified_extraction.py --validate
    python src/migration_to_unified_extraction.py --migrate
"""

import os
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import re
import argparse
import logging
from typing import List, Dict, Any, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExtractionMigration:
    """Handles migration to unified extraction architecture"""
    
    def __init__(self):
        self.src_dir = "src"
        self.duplicate_functions = [
            "_extract_citation_blocks",
            "_extract_citations_from_text",
            "extract_citations",
            "extract_case_name_from_context"
        ]
        
        self.contamination_patterns = [
            r'extracted_case_name\s*=\s*canonical_name',
            r'case_name\s*=\s*canonical_name',
            r'extracted_case_name\s*=.*canonical.*name',
        ]
    
    def find_duplicate_functions(self) -> Dict[str, List[str]]:
        """Find all duplicate extraction functions across the codebase"""
        duplicates = {func: [] for func in self.duplicate_functions}
        
        for root, dirs, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for func_name in self.duplicate_functions:
                            pattern = rf'def\s+{re.escape(func_name)}\s*\('
                            if re.search(pattern, content):
                                duplicates[func_name].append(file_path)
                                
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
        
        return duplicates
    
    def find_contamination_patterns(self) -> List[Tuple[str, int, str]]:
        """Find patterns where canonical names might overwrite extracted names"""
        contaminations = []
        
        for root, dirs, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            
                        for line_num, line in enumerate(lines, 1):
                            for pattern in self.contamination_patterns:
                                if re.search(pattern, line):
                                    contaminations.append((file_path, line_num, line.strip()))
                                    
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
        
        return contaminations
    
    def validate_current_state(self) -> Dict[str, Any]:
        """Validate the current state of the codebase"""
        logger.info("🔍 Validating current codebase state...")
        
        duplicates = self.find_duplicate_functions()
        contaminations = self.find_contamination_patterns()
        
        total_duplicates = sum(len(files) for files in duplicates.values())
        
        validation_report = {
            'duplicate_functions': duplicates,
            'total_duplicates': total_duplicates,
            'contamination_patterns': contaminations,
            'total_contaminations': len(contaminations),
            'needs_migration': total_duplicates > 0 or len(contaminations) > 0
        }
        
        return validation_report
    
    def generate_migration_plan(self) -> List[Dict[str, Any]]:
        """Generate a step-by-step migration plan"""
        validation = self.validate_current_state()
        
        migration_steps = []
        
        if validation['total_duplicates'] > 0:
            migration_steps.append({
                'step': 1,
                'title': 'Replace Duplicate Extraction Functions',
                'description': 'Replace all duplicate _extract_citation_blocks functions with unified service',
                'files_affected': list(set(sum(validation['duplicate_functions'].values(), []))),
                'priority': 'HIGH',
                'risk': 'MEDIUM'
            })
        
        if validation['total_contaminations'] > 0:
            affected_files = list(set(item[0] for item in validation['contamination_patterns']))
            migration_steps.append({
                'step': 2,
                'title': 'Fix Data Contamination Patterns',
                'description': 'Remove code that overwrites extracted names with canonical names',
                'files_affected': affected_files,
                'priority': 'CRITICAL',
                'risk': 'LOW'
            })
        
        migration_steps.append({
            'step': 3,
            'title': 'Add Data Separation Validation',
            'description': 'Integrate data separation validator into processing pipeline',
            'files_affected': ['src/enhanced_sync_processor.py', 'src/vue_api_endpoints.py'],
            'priority': 'HIGH',
            'risk': 'LOW'
        })
        
        return migration_steps
    
    def create_replacement_code(self, function_name: str) -> str:
        """Generate replacement code for duplicate functions"""
        
        if function_name == "_extract_citation_blocks":
            return '''
    def _extract_citation_blocks(self, text: str):
        """MIGRATED: Use unified extraction service"""
        from src.unified_extraction_service import extract_citations_unified
        
        results = extract_citations_unified(text)
        citations = []
        
        for result in results:
            citation = CitationResult(
                citation=result['citation'],
                extracted_case_name=result['extracted_case_name'],
                extracted_date=result['extracted_date'],
                start_index=result['start_index'],
                end_index=result['end_index'],
                confidence=result['confidence'],
                method=result['extraction_method']
            )
            citations.append(citation)
        
        return citations
'''
        
        return f"    # TODO: Replace {function_name} with unified extraction service\n"
    
    def print_validation_report(self, validation: Dict[str, Any]):
        """Print a detailed validation report"""
        print("\n" + "="*80)
        print("="*80)
        
        print(f"\n📊 DUPLICATE FUNCTIONS FOUND: {validation['total_duplicates']}")
        for func_name, files in validation['duplicate_functions'].items():
            if files:
                print(f"  • {func_name}: {len(files)} duplicates")
                for file_path in files:
                    print(f"    - {file_path}")
        
        print(f"\n⚠️ CONTAMINATION PATTERNS FOUND: {validation['total_contaminations']}")
        for file_path, line_num, line in validation['contamination_patterns']:
            print(f"  • {file_path}:{line_num} - {line}")
        
        if validation['needs_migration']:
            print(f"\n🚨 MIGRATION NEEDED: YES")
            print("   The codebase has duplicate functions and/or contamination patterns")
        else:
            print(f"\n✅ MIGRATION NEEDED: NO")
            print("   The codebase is clean")
    
    def print_migration_plan(self, plan: List[Dict[str, Any]]):
        """Print the migration plan"""
        print("\n" + "="*80)
        print("🔧 MIGRATION PLAN")
        print("="*80)
        
        for step in plan:
            print(f"\n📋 STEP {step['step']}: {step['title']}")
            print(f"   Priority: {step['priority']} | Risk: {step['risk']}")
            print(f"   Description: {step['description']}")
            print(f"   Files affected: {len(step['files_affected'])}")
            for file_path in step['files_affected'][:5]:  # Show first 5 files
                print(f"     - {file_path}")
            if len(step['files_affected']) > 5:
                print(f"     ... and {len(step['files_affected']) - 5} more")

def main():
    """Main migration script"""
    parser = argparse.ArgumentParser(description='Migration to Unified Extraction Architecture')
    parser.add_argument('--validate', action='store_true', help='Validate current codebase state')
    parser.add_argument('--migrate', action='store_true', help='Perform migration (not implemented)')
    parser.add_argument('--plan', action='store_true', help='Show migration plan')
    
    args = parser.parse_args()
    
    migration = ExtractionMigration()
    
    if args.validate or not any([args.validate, args.migrate, args.plan]):
        validation = migration.validate_current_state()
        migration.print_validation_report(validation)
        
        if validation['needs_migration']:
            plan = migration.generate_migration_plan()
            migration.print_migration_plan(plan)
    
    elif args.plan:
        validation = migration.validate_current_state()
        plan = migration.generate_migration_plan()
        migration.print_migration_plan(plan)
    
    elif args.migrate:
        print("🚧 Automatic migration not implemented yet.")
        print("   Please apply changes manually based on the migration plan.")
        print("   Run with --plan to see the detailed migration steps.")

if __name__ == "__main__":
    main()

