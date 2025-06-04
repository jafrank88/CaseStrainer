import os
import sys

# Files and their import patterns to fix
FIXES = [
    (
        "src/vue_api_endpoints.py",
        "from config import DATABASE_FILE",
        "from src.config import DATABASE_FILE",
    ),
    (
        "src/vue_api.py",
        "from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS",
        "from src.config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS",
    ),
    (
        "src/verify_unconfirmed_citations.py",
        "from config import DATABASE_FILE",
        "from src.config import DATABASE_FILE",
    ),
    (
        "src/verify_database_citations.py",
        "from config import DATABASE_FILE",
        "from src.config import DATABASE_FILE",
    ),
    (
        "src/citation_utils.py",
        "from config import COURTLISTENER_API_KEY",
        "from src.config import COURTLISTENER_API_KEY",
    ),
]


def fix_imports():
    """Fix import statements in the specified files."""
    project_root = os.path.dirname(os.path.abspath(__file__))

    for rel_path, old_import, new_import in FIXES:
        file_path = os.path.join(project_root, rel_path)

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_import not in content:
            print(f"Import not found in {rel_path}: {old_import}")
            continue

        new_content = content.replace(old_import, new_import)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"Fixed import in {rel_path}")


if __name__ == "__main__":
    fix_imports()
