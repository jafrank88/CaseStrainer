#!/usr/bin/env python3
"""
Analyze Pylance errors in the CaseStrainer codebase
"""

import os
import re
import ast
from typing import List, Dict, Any, Set
from collections import defaultdict

class PylanceErrorAnalyzer:
    def __init__(self):
        self.errors = []
        self.error_categories = defaultdict(list)
        
    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze a single Python file for common Pylance issues"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for common import issues
            import_issues = self._check_import_issues(content, file_path)
            issues.extend(import_issues)
            
            # Check for type annotation issues
            type_issues = self._check_type_annotations(content, file_path)
            issues.extend(type_issues)
            
            # Check for attribute access issues
            attribute_issues = self._check_attribute_access(content, file_path)
            issues.extend(attribute_issues)
            
            # Check for function call issues
            call_issues = self._check_function_calls(content, file_path)
            issues.extend(call_issues)
            
        except Exception as e:
            issues.append({
                "type": "parse_error",
                "message": f"Failed to parse file: {e}",
                "file": file_path,
                "line": 0
            })
        
        return issues
    
    def _check_import_issues(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Check for import-related issues"""
        issues = []
        lines = content.split('\n')
        
        # Check for imports of non-existent modules/functions
        import_patterns = [
            r'from\s+src\.case_name_extraction_core\s+import\s+extract_case_name_and_date_comprehensive',
            r'from\s+case_name_extraction_core\s+import\s+extract_case_name_and_date_comprehensive',
            r'from\s+src\.case_name_extraction_core\s+import\s+extract_case_name_improved',
            r'from\s+src\.case_name_extraction_core\s+import\s+extract_year_improved',
            r'from\s+src\.case_name_extraction_core\s+import\s+date_extractor',
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in import_patterns:
                if re.search(pattern, line):
                    issues.append({
                        "type": "import_error",
                        "message": f"Importing non-existent function: {line.strip()}",
                        "file": file_path,
                        "line": i,
                        "severity": "high"
                    })
        
        return issues
    
    def _check_type_annotations(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Check for missing type annotations"""
        issues = []
        lines = content.split('\n')
        
        # Look for function definitions without type annotations
        for i, line in enumerate(lines, 1):
            if re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*->\s*None:', line):
                # Function with return type annotation but no parameter annotations
                continue
            elif re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*:', line):
                # Function without return type annotation
                func_name = re.search(r'def\s+(\w+)', line)
                if func_name and not func_name.group(1).startswith('_'):
                    issues.append({
                        "type": "missing_type_annotation",
                        "message": f"Function '{func_name.group(1)}' missing return type annotation",
                        "file": file_path,
                        "line": i,
                        "severity": "medium"
                    })
        
        return issues
    
    def _check_attribute_access(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Check for attribute access issues"""
        issues = []
        lines = content.split('\n')
        
        # Check for common attribute access patterns that might cause issues
        attribute_patterns = [
            r'\.verify_citations\s*=',  # Setting non-existent attribute
            r'\.citations\s*\.',  # Accessing .citations on list
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in attribute_patterns:
                if re.search(pattern, line):
                    issues.append({
                        "type": "attribute_access_error",
                        "message": f"Potential attribute access issue: {line.strip()}",
                        "file": file_path,
                        "line": i,
                        "severity": "high"
                    })
        
        return issues
    
    def _check_function_calls(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Check for function call issues"""
        issues = []
        lines = content.split('\n')
        
        # Check for calls to non-existent functions
        function_patterns = [
            r'extract_case_name_and_date_comprehensive\s*\(',
            r'extract_case_name_improved\s*\(',
            r'extract_year_improved\s*\(',
            r'extract_case_name_triple_comprehensive\s*\(',
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in function_patterns:
                if re.search(pattern, line):
                    issues.append({
                        "type": "function_call_error",
                        "message": f"Calling non-existent function: {line.strip()}",
                        "file": file_path,
                        "line": i,
                        "severity": "high"
                    })
        
        return issues
    
    def analyze_directory(self, directory: str) -> Dict[str, Any]:
        """Analyze all Python files in a directory"""
        all_issues = []
        
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    issues = self.analyze_file(file_path)
                    all_issues.extend(issues)
        
        # Categorize issues
        for issue in all_issues:
            self.error_categories[issue["type"]].append(issue)
        
        return {
            "total_issues": len(all_issues),
            "categories": dict(self.error_categories),
            "files_with_issues": len(set(issue["file"] for issue in all_issues))
        }
    
    def print_report(self, analysis: Dict[str, Any]):
        """Print a comprehensive report of the analysis"""
        print("🔍 PYLANCE ERROR ANALYSIS REPORT")
        print("=" * 60)
        print(f"Total Issues Found: {analysis['total_issues']}")
        print(f"Files with Issues: {analysis['files_with_issues']}")
        print()
        
        for category, issues in analysis['categories'].items():
            print(f"📋 {category.upper().replace('_', ' ')} ({len(issues)} issues):")
            for issue in issues[:5]:  # Show first 5 issues per category
                print(f"  {issue['file']}:{issue['line']} - {issue['message']}")
            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more")
            print()
        
        # Show high severity issues first
        high_severity = []
        for category, issues in analysis['categories'].items():
            for issue in issues:
                if issue.get('severity') == 'high':
                    high_severity.append(issue)
        
        if high_severity:
            print("🚨 HIGH SEVERITY ISSUES:")
            for issue in high_severity[:10]:
                print(f"  {issue['file']}:{issue['line']} - {issue['message']}")
            print()

def main():
    analyzer = PylanceErrorAnalyzer()
    
    # Analyze the src directory
    print("Analyzing src directory for Pylance errors...")
    analysis = analyzer.analyze_directory("src")
    
    # Print the report
    analyzer.print_report(analysis)
    
    # Provide recommendations
    print("💡 RECOMMENDATIONS:")
    print("1. Fix import issues in unified_citation_processor_v2.py")
    print("2. Update function calls to use new API")
    print("3. Add type annotations to public functions")
    print("4. Fix attribute access issues")
    print("5. Consider deprecating legacy files")

if __name__ == "__main__":
    main() 