"""
Production Cleanup Script - Phase 1: Safe Deletions
Removes backup and experimental files that are safe to delete
"""
import os
import shutil

# Files to delete (backup/experimental files)
FILES_TO_DELETE = [
    'src/unified_citation_processor_v2.py.backup',
    'src/unified_clustering_master_before_tmp.py',
    'src/unified_clustering_master_pre_parallel.py',
    'src/unified_clustering_master_original_restore.py',
    'src/unified_clustering_master_regressed.py',
    'src/unified_citation_processor_v2_optimized.py',
    'src/enhanced_sync_processor_refactored.py',
    'src/pdf_extraction_optimized.py',
    'src/unified_citation_processor_v2_refactored.py',
    'src/document_processing_optimized.py',
]

def delete_files(files, dry_run=True):
    """Delete files with safety checks."""
    total_size = 0
    deleted = []
    errors = []
    
    for filepath in files:
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filepath}")
            continue
        
        size = os.path.getsize(filepath) / 1024  # KB
        total_size += size
        
        if dry_run:
            print(f"🔍 Would delete: {filepath} ({size:.1f} KB)")
            deleted.append(filepath)
        else:
            try:
                os.remove(filepath)
                print(f"✅ Deleted: {filepath} ({size:.1f} KB)")
                deleted.append(filepath)
            except Exception as e:
                print(f"❌ Error deleting {filepath}: {e}")
                errors.append((filepath, str(e)))
    
    return deleted, errors, total_size

if __name__ == '__main__':
    print("=" * 80)
    print("PRODUCTION CLEANUP - PHASE 1: SAFE DELETIONS")
    print("=" * 80)
    print("\nThis script will delete backup and experimental files.")
    print("These files are safe to delete as they are:")
    print("  - Backup copies (*.backup)")
    print("  - Old versions (*_before_*, *_original_*, *_regressed_*)")
    print("  - Experimental versions (*_optimized, *_refactored)")
    print("\n" + "=" * 80)
    
    # Dry run first
    print("\n🔍 DRY RUN - No files will be deleted\n")
    deleted, errors, total_size = delete_files(FILES_TO_DELETE, dry_run=True)
    
    print(f"\n📊 Summary:")
    print(f"   - Files to delete: {len(deleted)}")
    print(f"   - Total space to reclaim: {total_size:.1f} KB")
    print(f"   - Errors: {len(errors)}")
    
    if errors:
        print("\n⚠️  Errors encountered:")
        for filepath, error in errors:
            print(f"   - {filepath}: {error}")
    
    # Ask for confirmation
    print("\n" + "=" * 80)
    response = input("\n⚠️  Proceed with deletion? (yes/no): ").strip().lower()
    
    if response == 'yes':
        print("\n🗑️  Deleting files...\n")
        deleted, errors, total_size = delete_files(FILES_TO_DELETE, dry_run=False)
        
        print(f"\n✅ Cleanup complete!")
        print(f"   - Files deleted: {len(deleted)}")
        print(f"   - Space reclaimed: {total_size:.1f} KB")
        
        if errors:
            print(f"\n⚠️  {len(errors)} errors occurred:")
            for filepath, error in errors:
                print(f"   - {filepath}: {error}")
        else:
            print("\n🎉 All files deleted successfully!")
            print("\n📝 Next steps:")
            print("   1. Run tests: python -m pytest tests/")
            print("   2. Commit changes: git add -A && git commit -m 'Remove backup files'")
            print("   3. Continue with Phase 2: Update imports (see PRODUCTION_READINESS_ANALYSIS.md)")
    else:
        print("\n❌ Cleanup cancelled. No files were deleted.")
        print("   Run this script again when ready.")
