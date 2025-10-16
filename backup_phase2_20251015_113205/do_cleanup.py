"""
Execute Phase 1 cleanup - Delete backup files
"""
import os

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

print("=" * 80)
print("PHASE 1 CLEANUP: DELETING BACKUP FILES")
print("=" * 80)

total_size = 0
deleted = []
not_found = []
errors = []

for filepath in FILES_TO_DELETE:
    if not os.path.exists(filepath):
        print(f"⚠️  Not found: {filepath}")
        not_found.append(filepath)
        continue
    
    try:
        size = os.path.getsize(filepath) / 1024  # KB
        os.remove(filepath)
        total_size += size
        deleted.append(filepath)
        print(f"✅ Deleted: {filepath} ({size:.1f} KB)")
    except Exception as e:
        print(f"❌ Error: {filepath} - {e}")
        errors.append((filepath, str(e)))

print("\n" + "=" * 80)
print("CLEANUP SUMMARY")
print("=" * 80)
print(f"\n✅ Successfully deleted: {len(deleted)} files")
print(f"💾 Space reclaimed: {total_size:.1f} KB")

if not_found:
    print(f"\n⚠️  Files not found: {len(not_found)}")
    for f in not_found:
        print(f"   - {f}")

if errors:
    print(f"\n❌ Errors: {len(errors)}")
    for filepath, error in errors:
        print(f"   - {filepath}: {error}")

if deleted and not errors:
    print("\n🎉 Phase 1 cleanup completed successfully!")
    print("\n📝 Next steps:")
    print("   1. Verify tests still pass: python -m pytest tests/")
    print("   2. Commit changes: git add -A && git commit -m 'Phase 1: Remove backup files'")
    print("   3. See PRODUCTION_READINESS_ANALYSIS.md for Phase 2")
elif not deleted:
    print("\n⚠️  No files were deleted. They may have already been removed.")
