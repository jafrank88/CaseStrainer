#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
from datetime import datetime


def archive_deprecated_folders():
    """
    Move deprecated folders to the archive directory with a timestamp.
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    # Create archive directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = project_root / "archive" / f"deprecated_{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Folders to archive
    folders_to_archive = ["deprecated_scripts", "old files"]

    # Move each folder
    for folder in folders_to_archive:
        source = project_root / folder
        if source.exists():
            try:
                # Create a subdirectory in archive with the original folder name
                target = archive_dir / folder
                shutil.move(str(source), str(target))
                print(f"Moved {folder} to {target}")
            except Exception as e:
                print(f"Error moving {folder}: {e}")

    print(f"\nArchive complete. Folders moved to: {archive_dir}")


if __name__ == "__main__":
    archive_deprecated_folders()
