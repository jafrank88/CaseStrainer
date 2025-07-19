#!/usr/bin/env python3
"""
Simple code analyzer to find common Pylance issues
"""

import ast
import os
from typing import List, Dict, Set, Any

class CodeAnalyzer:
    def __init__(self) -> None:
        super().__init__()
        self.issues: List[Dict[str, Any]] = []
        self.imports: Dict[str, str] = {}
        self.used_names: Set[str] = set()
        
    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze a single Python file for common issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            analyzer = FileAnalyzer(file_path)
            analyzer.visit(tree)
            return analyzer.issues
        except Exception as e:
            return [{"type": "error", "message": f"Failed to parse {file_path}: {e}", "line": 0}]
    
    def analyze_directory(self, directory: str) -> List[Dict[str, Any]]:
        """Analyze all Python files in a directory"""
        all_issues: List[Dict[str, Any]] = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    issues = self.analyze_file(file_path)
                    all_issues.extend(issues)
        return all_issues

class FileAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path: str) -> None:
        super().__init__()
        self.file_path = file_path
        self.issues: List[Dict[str, Any]] = []
        self.imports: Dict[str, str] = {}
        self.used_names: Set[str] = set()
        self.function_defs: Set[str] = set()
        self.class_defs: Set[str] = set()
        
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.asname:
                self.imports[alias.asname] = alias.name
            else:
                self.imports[alias.name] = alias.name
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.names:
            for alias in node.names:
                if alias.asname:
                    self.imports[alias.asname] = f"{node.module}.{alias.name}"
                else:
                    self.imports[alias.name] = f"{node.module}.{alias.name}"
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name) -> None:
        self.used_names.add(node.id)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_defs.add(node.name)
        # Check for missing type annotations
        if node.args.args:
            for arg in node.args.args:
                if arg.annotation is None and arg.arg != 'self':
                    self.issues.append({
                        "type": "missing_type_annotation",
                        "message": f"Missing type annotation for parameter '{arg.arg}'",
                        "line": node.lineno,
                        "file": self.file_path
                    })
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_defs.add(node.name)
        # Check for missing super() call in __init__
        if node.name == '__init__':
            has_super_call = False
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Attribute) and child.func.attr == '__init__':
                        if isinstance(child.func.value, ast.Call):
                            if isinstance(child.func.value.func, ast.Name) and child.func.value.func.id == 'super':
                                has_super_call = True
                                break
            if not has_super_call:
                self.issues.append({
                    "type": "missing_super_call",
                    "message": "Missing super().__init__() call in __init__ method",
                    "line": node.lineno,
                    "file": self.file_path
                })
        self.generic_visit(node)
    
    def visit_Module(self, node: ast.Module) -> None:
        self.generic_visit(node)
        # Check for unused imports
        for import_name in self.imports:
            if import_name not in self.used_names and import_name not in self.function_defs and import_name not in self.class_defs:
                self.issues.append({
                    "type": "unused_import",
                    "message": f"Import '{import_name}' is not accessed",
                    "line": 0,  # We don't track line numbers for imports in this simple version
                    "file": self.file_path
                })

def main() -> None:
    analyzer = CodeAnalyzer()
    src_dir = "src"
    
    if not os.path.exists(src_dir):
        print(f"Directory {src_dir} not found")
        return
    
    print(f"Analyzing {src_dir} directory...")
    issues: List[Dict[str, Any]] = analyzer.analyze_directory(src_dir)
    
    if not issues:
        print("No issues found!")
        return
    
    print(f"\nFound {len(issues)} issues:")
    print("=" * 50)
    
    for issue in issues:
        print(f"{issue['file']}:{issue['line']} - {issue['type']}: {issue['message']}")

if __name__ == "__main__":
    main() 