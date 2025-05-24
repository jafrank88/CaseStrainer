#!/usr/bin/env python3
import os
import shutil
from pathlib import Path


def cleanup_pycache():
    """
    Recursively find and remove all __pycache__ directories in the project.
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    # Counter for removed directories
    removed_count = 0

    # Walk through all directories
    for root, dirs, files in os.walk(project_root):
        if "__pycache__" in dirs:
            pycache_path = Path(root) / "__pycache__"
            try:
                shutil.rmtree(pycache_path)
                print(f"Removed: {pycache_path}")
                removed_count += 1
            except Exception as e:
                print(f"Error removing {pycache_path}: {e}")

    print(f"\nCleanup complete. Removed {removed_count} __pycache__ directories.")


if __name__ == "__main__":
    cleanup_pycache()
