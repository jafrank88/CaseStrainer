#!/usr/bin/env python3
import shutil
from pathlib import Path
from datetime import datetime


def consolidate_nginx():
    """
    Consolidate nginx versions by keeping 1.24.0 and removing 1.27.5.
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    # Create archive directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = project_root / "archive" / f"nginx_{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Move nginx to archive
    nginx_old = project_root / "nginx"
    if nginx_old.exists():
        try:
            target = archive_dir / "nginx"
            shutil.move(str(nginx_old), str(target))
            print(f"Moved nginx to {target}")
        except Exception as e:
            print(f"Error moving nginx: {e}")

    # (Removed nginx-1.24.0 logic; only current nginx folder is relevant)

    print(f"\nNginx consolidation complete. Old version archived in: {archive_dir}")


if __name__ == "__main__":
    consolidate_nginx()
