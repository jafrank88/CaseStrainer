import os
import shutil

# List of files and directories to include (relative to project root)
INCLUDE_PATHS = [
    "src/app",
    "src/api",
    "src/citation_utils.py",
    "src/citation_extractor.py",
    "src/citation_patterns.py",
    "src/citation_classifier.py",
    "src/citation_api.py",
    "src/citation_services.py",
    "src/case_name_extraction_core.py",
    "src/file_utils.py",
    "src/document_processing_unified.py",
    "src/unified_citation_processor.py",
    "src/unified_citation_extractor.py",
    "src/unified_citation_processor_v2.py",
    "src/cache_manager.py",
    "src/rq_worker.py",
    "src/progress_manager.py",
    "src/config.py",
    "src/__init__.py",
    "src/canonical_case_name_service.py",
    "src/enhanced_validator_production.py",
    "src/enhanced_web_searcher.py",
    "src/websearch_utils.py",
    "src/citation_correction.py",
    "src/citation_format_utils.py",
    "src/standalone_citation_parser.py",
    "src/enhanced_extraction_utils.py",
    "src/database_manager.py",
    "src/healthcheck_robust.py",
    "src/healthcheck_rq.py",
    "src/pdf_handler.py",
    "src/vue_api_endpoints.py",
    "src/citation_normalizer.py",
    "src/citation_verification.py",
    "src/citation_grouping.py",
    "src/citation_correction_engine.py",
    "src/app_final_vue.py",
    "config",
    "requirements.txt",
    "casestrainer-vue-new",
    "docker",
    "nginx",
    "redis.conf",
    "cslaunch.ps1",
]

DEST_ROOT = r"D:/dev/casestrainer-minimal"


def copy_item(src_path, dest_root):
    if not os.path.exists(src_path):
        print(f"Warning: {src_path} does not exist, skipping.")
        return
    dest_path = os.path.join(dest_root, src_path)
    if os.path.isdir(src_path):
        shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
    else:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)

def main():
    if os.path.exists(DEST_ROOT):
        print(f"Removing existing {DEST_ROOT} ...")
        shutil.rmtree(DEST_ROOT)
    os.makedirs(DEST_ROOT, exist_ok=True)
    for path in INCLUDE_PATHS:
        copy_item(path, DEST_ROOT)
    print(f"\nExport complete! Minimal project is in: {DEST_ROOT}")

if __name__ == "__main__":
    main() 