#!/usr/bin/env python3
"""
CaseStrainer Codebase Cleanup Script

This script helps organize and deprecate redundant files in the CaseStrainer codebase.
It moves files to appropriate directories and marks deprecated files.

Usage:
    python cleanup_codebase.py --dry-run    # Preview changes without making them
    python cleanup_codebase.py --execute    # Actually perform the cleanup
"""

import os
import shutil
import argparse
import sys
from pathlib import Path
from datetime import datetime

class CodebaseCleanup:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.project_root = Path(__file__).parent
        self.src_dir = self.project_root / "src"
        self.tests_dir = self.project_root / "tests"
        self.scripts_dir = self.project_root / "scripts"
        self.config_dir = self.project_root / "config"
        self.data_dir = self.project_root / "data"
        self.deprecated_dir = self.src_dir / "deprecated"
        
        # Track operations
        self.operations = []
        self.errors = []
        
    def log_operation(self, operation, source, destination=None):
        """Log an operation for reporting."""
        op = {
            'operation': operation,
            'source': str(source),
            'destination': str(destination) if destination else None,
            'timestamp': datetime.now().isoformat()
        }
        self.operations.append(op)
        
        if self.dry_run:
            print(f"[DRY RUN] {operation}: {source}")
            if destination:
                print(f"  -> {destination}")
        else:
            print(f"[EXECUTED] {operation}: {source}")
            if destination:
                print(f"  -> {destination}")
    
    def ensure_directory(self, directory):
        """Ensure a directory exists."""
        if not directory.exists():
            if not self.dry_run:
                directory.mkdir(parents=True, exist_ok=True)
                self.log_operation("Created directory", directory)
            else:
                self.log_operation("Would create directory", directory)
    
    def move_file(self, source, destination):
        """Move a file from source to destination."""
        source_path = Path(source)
        dest_path = Path(destination)
        
        if not source_path.exists():
            self.errors.append(f"Source file not found: {source_path}")
            return False
            
        # Ensure destination directory exists
        self.ensure_directory(dest_path.parent)
        
        if not self.dry_run:
            try:
                shutil.move(str(source_path), str(dest_path))
                self.log_operation("Moved file", source_path, dest_path)
                return True
            except Exception as e:
                self.errors.append(f"Error moving {source_path}: {e}")
                return False
        else:
            self.log_operation("Would move file", source_path, dest_path)
            return True
    
    def delete_file(self, file_path):
        """Delete a file."""
        path = Path(file_path)
        if not path.exists():
            return False
            
        if not self.dry_run:
            try:
                path.unlink()
                self.log_operation("Deleted file", path)
                return True
            except Exception as e:
                self.errors.append(f"Error deleting {path}: {e}")
                return False
        else:
            self.log_operation("Would delete file", path)
            return True
    
    def cleanup_deprecated_app_files(self):
        """Move deprecated app files to deprecated directory."""
        print("\n=== Cleaning up deprecated app files ===")
        
        deprecated_app_files = [
            "src/app.py",
            "src/enhanced_multi_source_verifier.py.backup",
            "debug_app.py",
            "minimal_app.py", 
            "minimal_app_5001.py",
            "run_minimal_5000.py",
            "simple_app.py"
        ]
        
        for file_path in deprecated_app_files:
            if Path(file_path).exists():
                dest_path = self.deprecated_dir / Path(file_path).name
                self.move_file(file_path, dest_path)
    
    def cleanup_test_files(self):
        """Move test files to tests directory."""
        print("\n=== Moving test files to tests/ directory ===")
        
        # Ensure tests directory exists
        self.ensure_directory(self.tests_dir)
        
        # Find all test files in src/
        test_patterns = [
            "src/test_*.py",
            "src/debug_*.py", 
            "src/check_*.py",
            "src/verify_*.py"
        ]
        
        for pattern in test_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    dest_path = self.tests_dir / file_path.name
                    self.move_file(file_path, dest_path)
    
    def cleanup_processing_scripts(self):
        """Move processing scripts to scripts directory."""
        print("\n=== Moving processing scripts to scripts/ directory ===")
        
        # Ensure scripts directory exists
        self.ensure_directory(self.scripts_dir)
        
        # Find all processing scripts in src/
        processing_patterns = [
            "src/process_*.py",
            "src/extract_*.py",
            "src/analyze_*.py",
            "src/find_more_citations.py",
            "src/update_citation_json_files.py",
            "src/sample_citation_*.py",
            "src/eyecite_*.py",
            "src/legal_database_scraper.py",
            "src/enhanced_legal_scraper.py",
            "src/enhanced_case_name_extractor.py",
            "src/extract_case_name.py",
            "src/citation_extractor.py"
        ]
        
        for pattern in processing_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    dest_path = self.scripts_dir / file_path.name
                    self.move_file(file_path, dest_path)
    
    def cleanup_config_files(self):
        """Move configuration files to config directory."""
        print("\n=== Moving configuration files to config/ directory ===")
        
        # Ensure config directory exists
        self.ensure_directory(self.config_dir)
        
        config_files = [
            "src/config.json",
            "src/config_prod.py",
            "src/config_dev.py", 
            "src/logging_config.py"
        ]
        
        for file_path in config_files:
            if Path(file_path).exists():
                dest_path = self.config_dir / Path(file_path).name
                self.move_file(file_path, dest_path)
    
    def cleanup_data_files(self):
        """Move data files to data directory."""
        print("\n=== Moving data files to data/ directory ===")
        
        # Ensure data directory exists
        self.ensure_directory(self.data_dir)
        
        data_files = [
            "src/citations.db",
            "src/langsearch_cache.db"
        ]
        
        for file_path in data_files:
            if Path(file_path).exists():
                dest_path = self.data_dir / Path(file_path).name
                self.move_file(file_path, dest_path)
    
    def cleanup_log_files(self):
        """Clean up log files."""
        print("\n=== Cleaning up log files ===")
        
        log_files = [
            "src/case_name_debug.log",
            "*.log"  # Root level log files
        ]
        
        for pattern in log_files:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and file_path.name.endswith('.log'):
                    # Move to logs directory instead of deleting
                    logs_dir = self.project_root / "logs"
                    self.ensure_directory(logs_dir)
                    dest_path = logs_dir / file_path.name
                    self.move_file(file_path, dest_path)
    
    def cleanup_temp_files(self):
        """Clean up temporary and debug files."""
        print("\n=== Cleaning up temporary files ===")
        
        temp_files = [
            "src/citation_verification_result.json",
            "*.tmp",
            "*.temp",
            "*.bak",
            "*.backup"
        ]
        
        for pattern in temp_files:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    self.delete_file(file_path)
    
    def create_cleanup_report(self):
        """Create a report of all operations."""
        report_path = self.project_root / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        if not self.dry_run:
            with open(report_path, 'w') as f:
                f.write("CaseStrainer Codebase Cleanup Report\n")
                f.write("=" * 50 + "\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"Dry run: {self.dry_run}\n\n")
                
                f.write("Operations:\n")
                f.write("-" * 20 + "\n")
                for op in self.operations:
                    f.write(f"{op['operation']}: {op['source']}\n")
                    if op['destination']:
                        f.write(f"  -> {op['destination']}\n")
                
                if self.errors:
                    f.write("\nErrors:\n")
                    f.write("-" * 10 + "\n")
                    for error in self.errors:
                        f.write(f"ERROR: {error}\n")
                
                f.write(f"\nTotal operations: {len(self.operations)}\n")
                f.write(f"Total errors: {len(self.errors)}\n")
            
            print(f"\nCleanup report saved to: {report_path}")
    
    def run_cleanup(self):
        """Run the complete cleanup process."""
        print("CaseStrainer Codebase Cleanup")
        print("=" * 40)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        print(f"Project root: {self.project_root}")
        print()
        
        # Ensure required directories exist
        self.ensure_directory(self.deprecated_dir)
        
        # Run cleanup operations
        self.cleanup_deprecated_app_files()
        self.cleanup_test_files()
        self.cleanup_processing_scripts()
        self.cleanup_config_files()
        self.cleanup_data_files()
        self.cleanup_log_files()
        self.cleanup_temp_files()
        
        # Create report
        self.create_cleanup_report()
        
        # Summary
        print(f"\n=== Cleanup Summary ===")
        print(f"Total operations: {len(self.operations)}")
        print(f"Total errors: {len(self.errors)}")
        
        if self.errors:
            print("\nErrors encountered:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.dry_run:
            print("\nThis was a dry run. No files were actually moved.")
            print("Run with --execute to perform the actual cleanup.")

def main():
    parser = argparse.ArgumentParser(description="Clean up CaseStrainer codebase")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Preview changes without making them (default)")
    parser.add_argument("--execute", action="store_true", 
                       help="Actually perform the cleanup")
    
    args = parser.parse_args()
    
    # Determine if this is a dry run
    dry_run = not args.execute
    
    if args.execute:
        print("WARNING: This will actually move and delete files!")
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() != 'yes':
            print("Cleanup cancelled.")
            return
    
    # Run cleanup
    cleanup = CodebaseCleanup(dry_run=dry_run)
    cleanup.run_cleanup()

if __name__ == "__main__":
    main() 