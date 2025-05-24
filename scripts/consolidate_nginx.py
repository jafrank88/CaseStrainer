#!/usr/bin/env python3
import os
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

    # Move nginx-1.27.5 to archive
    nginx_old = project_root / "nginx-1.27.5"
    if nginx_old.exists():
        try:
            target = archive_dir / "nginx-1.27.5"
            shutil.move(str(nginx_old), str(target))
            print(f"Moved nginx-1.27.5 to {target}")
        except Exception as e:
            print(f"Error moving nginx-1.27.5: {e}")

    # Rename nginx-1.24.0 to just nginx
    nginx_current = project_root / "nginx-1.24.0"
    nginx_new = project_root / "nginx"
    if nginx_current.exists():
        try:
            if nginx_new.exists():
                shutil.rmtree(str(nginx_new))
            shutil.move(str(nginx_current), str(nginx_new))
            print(f"Renamed nginx-1.24.0 to nginx")
        except Exception as e:
            print(f"Error renaming nginx-1.24.0: {e}")

    print(f"\nNginx consolidation complete. Old version archived in: {archive_dir}")


if __name__ == "__main__":
    consolidate_nginx()
