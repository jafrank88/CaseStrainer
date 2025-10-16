#!/usr/bin/env python3
"""
Cache clearing utility for CaseStrainer

This script provides various options to clear different types of cache:
1. File cache (citation verification results)
2. Memory cache (in-memory LRU cache)
3. Unverified citations cache
4. All cache
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def clear_file_cache(cache_dir=None):
    """Clear the file-based citation cache."""
    if cache_dir is None:
        # Try to find the cache directory
        cache_locations = [
            os.path.join(os.path.expanduser("~"), ".casestrainer_cache"),
            os.path.join(os.getcwd(), "cache"),
            os.path.join(project_root, "cache"),
            os.path.join(project_root, "src", "citation_cache"),
        ]
        
        for location in cache_locations:
            if os.path.exists(location):
                cache_dir = location
                break
    
    if not cache_dir or not os.path.exists(cache_dir):
        print("❌ No cache directory found")
        return False
    
    try:
        # Count files before deletion
        cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.json')]
        count = len(cache_files)
        
        if count == 0:
            print("ℹ️  No cache files found to clear")
            return True
        
        # Delete all .json files
        for cache_file in cache_files:
            file_path = os.path.join(cache_dir, cache_file)
            os.remove(file_path)
        
        print(f"✅ Cleared {count} cache files from {cache_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing file cache: {e}")
        return False

def clear_memory_cache():
    """Clear the in-memory LRU cache by restarting the citation verifier."""
    try:
        from src.citation_verification import CitationVerifier
        
        # Create a new instance to clear memory cache
        verifier = CitationVerifier()
        verifier._lru_cache.clear()
        print("✅ Cleared in-memory LRU cache")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing memory cache: {e}")
        return False

def clear_unverified_cache():
    """Clear only unverified citations from cache."""
    cache_locations = [
        os.path.join(os.path.expanduser("~"), ".casestrainer_cache"),
        os.path.join(os.getcwd(), "cache"),
        os.path.join(project_root, "cache"),
        os.path.join(project_root, "src", "citation_cache"),
    ]
    
    cleared_count = 0
    
    for cache_dir in cache_locations:
        if not os.path.exists(cache_dir):
            continue
            
        try:
            cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.json')]
            
            for cache_file in cache_files:
                file_path = os.path.join(cache_dir, cache_file)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Check if this is an unverified citation
                    result = data.get('result', {})
                    if not result.get('verified', True) or not result.get('found', False):
                        os.remove(file_path)
                        cleared_count += 1
                        
                except Exception as e:
                    print(f"⚠️  Error reading cache file {cache_file}: {e}")
                    continue
                    
        except Exception as e:
            print(f"⚠️  Error accessing cache directory {cache_dir}: {e}")
            continue
    
    if cleared_count > 0:
        print(f"✅ Cleared {cleared_count} unverified citations from cache")
    else:
        print("ℹ️  No unverified citations found in cache")
    
    return True

def clear_all_cache():
    """Clear all types of cache."""
    print("🧹 Clearing all cache...")
    
    # Clear file cache
    file_success = clear_file_cache()
    
    # Clear memory cache
    memory_success = clear_memory_cache()
    
    # Clear any other cache directories
    other_cache_dirs = [
        os.path.join(project_root, "cache"),
        os.path.join(project_root, "citation_cache"),
        os.path.join(project_root, "temp"),
        os.path.join(project_root, "logs"),
    ]
    
    for cache_dir in other_cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ Cleared directory: {cache_dir}")
            except Exception as e:
                print(f"⚠️  Could not clear directory {cache_dir}: {e}")
    
    return file_success and memory_success

def show_cache_info():
    """Show information about current cache usage."""
    cache_locations = [
        os.path.join(os.path.expanduser("~"), ".casestrainer_cache"),
        os.path.join(os.getcwd(), "cache"),
        os.path.join(project_root, "cache"),
        os.path.join(project_root, "src", "citation_cache"),
    ]
    
    print("📊 Cache Information:")
    print("=" * 50)
    
    total_files = 0
    verified_count = 0
    unverified_count = 0
    
    for cache_dir in cache_locations:
        if not os.path.exists(cache_dir):
            continue
            
        print(f"\n📁 Cache Directory: {cache_dir}")
        
        try:
            cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.json')]
            dir_count = len(cache_files)
            total_files += dir_count
            
            if dir_count == 0:
                print("   ℹ️  No cache files")
                continue
            
            # Analyze cache files
            dir_verified = 0
            dir_unverified = 0
            
            for cache_file in cache_files[:10]:  # Sample first 10 files
                try:
                    with open(os.path.join(cache_dir, cache_file), 'r') as f:
                        data = json.load(f)
                    
                    result = data.get('result', {})
                    if result.get('verified', True) and result.get('found', False):
                        dir_verified += 1
                    else:
                        dir_unverified += 1
                        
                except Exception:
                    continue
            
            verified_count += dir_verified
            unverified_count += dir_unverified
            
            print(f"   📄 Total files: {dir_count}")
            print(f"   ✅ Verified: {dir_verified}")
            print(f"   ❌ Unverified: {dir_unverified}")
            
            if dir_count > 10:
                print(f"   ... and {dir_count - 10} more files")
                
        except Exception as e:
            print(f"   ❌ Error reading directory: {e}")
    
    print("\n" + "=" * 50)
    print(f"📈 Summary:")
    print(f"   📄 Total cache files: {total_files}")
    print(f"   ✅ Total verified: {verified_count}")
    print(f"   ❌ Total unverified: {unverified_count}")

def main():
    parser = argparse.ArgumentParser(description="Clear CaseStrainer cache")
    parser.add_argument("--type", choices=["file", "memory", "unverified", "all", "info"], 
                       default="info", help="Type of cache to clear")
    parser.add_argument("--cache-dir", help="Specific cache directory to clear")
    parser.add_argument("--force", action="store_true", help="Force clearing without confirmation")
    
    args = parser.parse_args()
    
    if args.type == "info":
        show_cache_info()
        return
    
    if not args.force:
        if args.type == "all":
            confirm = input("⚠️  This will clear ALL cache. Are you sure? (y/N): ")
        else:
            confirm = input(f"⚠️  This will clear {args.type} cache. Are you sure? (y/N): ")
        
        if confirm.lower() != 'y':
            print("❌ Operation cancelled")
            return
    
    print(f"🧹 Clearing {args.type} cache...")
    
    if args.type == "file":
        success = clear_file_cache(args.cache_dir)
    elif args.type == "memory":
        success = clear_memory_cache()
    elif args.type == "unverified":
        success = clear_unverified_cache()
    elif args.type == "all":
        success = clear_all_cache()
    else:
        print(f"❌ Unknown cache type: {args.type}")
        return
    
    if success:
        print("✅ Cache clearing completed successfully")
    else:
        print("❌ Cache clearing failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 