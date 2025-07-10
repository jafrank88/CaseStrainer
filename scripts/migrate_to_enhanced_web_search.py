#!/usr/bin/env python3
"""
Migration script to update imports from old web search modules to EnhancedWebSearcher.
"""

import os
import re
import sys
from pathlib import Path

def migrate_file(file_path: str, dry_run: bool = False) -> bool:
    """Migrate a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Migration patterns
        patterns = [
            ("from src.optimized_web_searcher import OptimizedWebSearcher", 
             "from src.enhanced_web_searcher import EnhancedWebSearcher"),
            ("from src.web_search_extractor import WebSearchExtractor", 
             "from src.enhanced_web_searcher import EnhancedWebExtractor"),
            ("OptimizedWebSearcher", "EnhancedWebSearcher"),
            ("WebSearchExtractor", "EnhancedWebExtractor"),
        ]
        
        for old_pattern, new_pattern in patterns:
            content = content.replace(old_pattern, new_pattern)
        
        if content != original_content:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            return True
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return False

def main():
    """Main migration function."""
    dry_run = "--dry-run" in sys.argv
    
    print("🔄 Enhanced Web Search Migration Tool")
    print("=" * 50)
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
    
    # Find Python files (excluding common directories)
    python_files = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'venv', 'node_modules'}]
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"📁 Found {len(python_files)} Python files to scan")
    
    migrated_files = 0
    for file_path in python_files:
        if migrate_file(file_path, dry_run):
            migrated_files += 1
            print(f"✅ Migrated: {file_path}")
    
    print(f"\n📊 Summary: {migrated_files} files {'would be ' if dry_run else ''}migrated")
    print(f"📚 See docs/WEB_SEARCH_MIGRATION.md for usage examples")

if __name__ == "__main__":
    main() 