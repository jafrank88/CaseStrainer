#!/usr/bin/env python3
"""
Debug Docker cache behavior to understand why rebuilds weren't triggered.
"""

import os
import hashlib
import json
from datetime import datetime

def calculate_file_hash(filepath):
    """Calculate SHA256 hash of a file."""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        return f"Error: {e}"

def get_file_info(filepath):
    """Get comprehensive file information."""
    try:
        stat = os.stat(filepath)
        return {
            'path': filepath,
            'size': stat.st_size,
            'mtime': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'ctime': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'hash': calculate_file_hash(filepath)
        }
    except Exception as e:
        return {'path': filepath, 'error': str(e)}

def analyze_docker_cache_issue():
    """Analyze why Docker cache wasn't invalidated."""
    
    print("🔍 Docker Cache Analysis")
    print("=" * 60)
    
    # Key files that should trigger rebuild
    key_files = [
        "d:/dev/casestrainer/casestrainer-vue-new/src/views/EnhancedValidator.vue",
        "d:/dev/casestrainer/casestrainer-vue-new/package.json",
        "d:/dev/casestrainer/casestrainer-vue-new/package-lock.json",
        "d:/dev/casestrainer/casestrainer-vue-new/Dockerfile.prod",
        "d:/dev/casestrainer/casestrainer-vue-new/.dockerignore"
    ]
    
    print("📋 Key File Analysis:")
    print("-" * 40)
    
    for filepath in key_files:
        info = get_file_info(filepath)
        if 'error' not in info:
            print(f"📄 {os.path.basename(info['path'])}:")
            print(f"   Size: {info['size']:,} bytes")
            print(f"   Modified: {info['mtime']}")
            print(f"   Created: {info['ctime']}")
            print(f"   Hash: {info['hash'][:16]}...")
        else:
            print(f"❌ {os.path.basename(filepath)}: {info['error']}")
        print()
    
    # Check Docker build context
    print("🐳 Docker Build Context Analysis:")
    print("-" * 40)
    
    build_context = "d:/dev/casestrainer/casestrainer-vue-new"
    
    # Check if .dockerignore is excluding important files
    dockerignore_path = os.path.join(build_context, ".dockerignore")
    if os.path.exists(dockerignore_path):
        print("📄 .dockerignore contents:")
        with open(dockerignore_path, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    print(f"   {i:2d}: {line}")
        print()
    
    # Check src directory structure
    src_dir = os.path.join(build_context, "src")
    if os.path.exists(src_dir):
        print("📁 Source Directory Structure:")
        for root, dirs, files in os.walk(src_dir):
            level = root.replace(src_dir, '').count(os.sep)
            indent = '  ' * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = '  ' * (level + 1)
            for file in files[:5]:  # Limit to first 5 files per directory
                filepath = os.path.join(root, file)
                stat = os.stat(filepath)
                mtime = datetime.fromtimestamp(stat.st_mtime)
                print(f"{subindent}{file} ({mtime.strftime('%m/%d %H:%M')})")
            if len(files) > 5:
                print(f"{subindent}... and {len(files) - 5} more files")
        print()
    
    # Analyze potential cache issues
    print("🔍 Potential Cache Issues:")
    print("-" * 40)
    
    issues = []
    
    # Check if package.json changed (would invalidate npm install cache)
    package_json = os.path.join(build_context, "package.json")
    if os.path.exists(package_json):
        stat = os.stat(package_json)
        mtime = datetime.fromtimestamp(stat.st_mtime)
        if mtime < datetime(2025, 9, 19, 16, 0):  # Before our changes
            issues.append("package.json hasn't changed - npm install layer cached")
    
    # Check if Dockerfile changed
    dockerfile = os.path.join(build_context, "Dockerfile.prod")
    if os.path.exists(dockerfile):
        stat = os.stat(dockerfile)
        mtime = datetime.fromtimestamp(stat.st_mtime)
        if mtime < datetime(2025, 9, 19, 16, 0):  # Before our changes
            issues.append("Dockerfile.prod hasn't changed - build instructions cached")
    
    # Check Docker layer caching behavior
    issues.append("Docker BuildKit uses content-based caching")
    issues.append("COPY commands create layers based on file content hashes")
    issues.append("If file content doesn't change, layer is reused")
    
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    
    print()
    
    # Recommendations
    print("💡 Cache Invalidation Strategies:")
    print("-" * 40)
    
    strategies = [
        "Use --no-cache flag to force complete rebuild",
        "Remove existing images: docker rmi <image>",
        "Clear build cache: docker builder prune",
        "Use .dockerignore properly to include only necessary files",
        "Order Dockerfile commands from least to most likely to change",
        "Use specific COPY commands instead of COPY . .",
        "Add build ARGs that change to invalidate cache"
    ]
    
    for i, strategy in enumerate(strategies, 1):
        print(f"   {i}. {strategy}")
    
    print()
    
    # Docker BuildKit analysis
    print("🔧 Docker BuildKit Behavior:")
    print("-" * 40)
    print("   • BuildKit uses content-addressable storage")
    print("   • Each layer has a hash based on its content")
    print("   • If content doesn't change, layer is reused")
    print("   • COPY src/ src/ creates layer based on src/ directory hash")
    print("   • File timestamps don't affect layer hashing")
    print("   • Only file content and permissions matter")
    
    return True

def main():
    """Run Docker cache analysis."""
    
    print("🚀 Docker Cache Issue Analysis")
    print("=" * 80)
    
    analyze_docker_cache_issue()
    
    print("=" * 80)
    print("📋 ANALYSIS COMPLETE")
    print("=" * 80)
    
    print("🎯 Key Findings:")
    print("   • Docker uses content-based caching, not timestamp-based")
    print("   • File changes should trigger rebuild, but cache can be aggressive")
    print("   • BuildKit may reuse layers even when files change")
    print("   • Manual cache clearing was needed to force rebuild")
    
    return True

if __name__ == "__main__":
    main()
