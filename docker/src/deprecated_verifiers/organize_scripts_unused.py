"""
Organize CaseStrainer Python Scripts

This script organizes the Python scripts in the CaseStrainer project by moving
deprecated scripts to a 'deprecated_scripts' directory.
"""

import os
import shutil
from pathlib import Path

# Define the base directory
BASE_DIR = Path(__file__).resolve().parent

# Create the deprecated_scripts directory if it doesn't exist
deprecated_dir = BASE_DIR / "deprecated_scripts"
os.makedirs(deprecated_dir, exist_ok=True)

# List of essential scripts that should NOT be moved
essential_scripts = [
    "app_final_vue.py",
    "app_final.py",
    "fixed_multi_source_verifier.py",
    "landmark_cases.py",
    "citation_export.py",
    "citation_verification.py",
    "deploy_vue_frontend_updated.py",
    "citation_classifier.py",
    "citation_correction.py",
    "enhanced_citation_verifier.py",
    "organize_scripts.py",  # Don't move this script itself
]

# List of scripts that can be deprecated
deprecated_scripts = [
    "app_final_vue_simple.py",
    "app_nginx_compatible.py",
    "app_simple.py",
    "app_simple_landing.py",
    "app_vue.py",
    "app_vue_fixed.py",
    "deploy_vue_frontend.py",
    "fix_python_path.py",
    "run_directly.py",
    "run_production.py",
    "run_vue_frontend.py",
    "simple_server.py",
]

# Move deprecated scripts
moved_count = 0
for script in deprecated_scripts:
    script_path = BASE_DIR / script
    if script_path.exists():
        target_path = deprecated_dir / script
        print(f"Moving {script} to deprecated_scripts directory...")
        shutil.move(script_path, target_path)
        moved_count += 1

# Find all other .py files that aren't in the essential list and ask if they should be moved
other_scripts = []
for py_file in BASE_DIR.glob("*.py"):
    if py_file.name not in essential_scripts and py_file.name not in [
        os.path.basename(s) for s in deprecated_scripts
    ]:
        other_scripts.append(py_file.name)

if other_scripts:
    print("\nFound other Python scripts that may be deprecated:")
    for i, script in enumerate(other_scripts, 1):
        print(f"{i}. {script}")

    print(
        "\nDo you want to move any of these scripts to the deprecated_scripts directory?"
    )
    print(
        "Enter the numbers separated by commas, or 'all' to move all, or 'none' to keep all:"
    )
    choice = input("> ")

    if choice.lower() == "all":
        for script in other_scripts:
            script_path = BASE_DIR / script
            target_path = deprecated_dir / script
            print(f"Moving {script} to deprecated_scripts directory...")
            shutil.move(script_path, target_path)
            moved_count += 1
    elif choice.lower() != "none":
        try:
            indices = [int(idx.strip()) - 1 for idx in choice.split(",")]
            for idx in indices:
                if 0 <= idx < len(other_scripts):
                    script = other_scripts[idx]
                    script_path = BASE_DIR / script
                    target_path = deprecated_dir / script
                    print(f"Moving {script} to deprecated_scripts directory...")
                    shutil.move(script_path, target_path)
                    moved_count += 1
        except ValueError:
            print("Invalid input. No additional scripts moved.")

print(
    f"\nOrganization complete. Moved {moved_count} deprecated scripts to the deprecated_scripts directory."
)
print("Essential scripts remain in the main directory.")

# Create a README file in the deprecated_scripts directory
readme_content = """# Deprecated Scripts

This directory contains Python scripts that are no longer actively used in the CaseStrainer application.
They have been moved here to keep the main directory clean and focused on the essential functionality.

These scripts may still be useful for reference or in specific scenarios, but they are not part of the
core application flow with the Vue.js frontend.

## Scripts in this Directory

{}

Last updated: {}
""".format(
    "\n".join(
        f"- **{script}**"
        for script in os.listdir(deprecated_dir)
        if script.endswith(".py")
    ),
    __import__("datetime").datetime.now().strftime("%Y-%m-%d"),
)

with open(deprecated_dir / "README.md", "w") as f:
    f.write(readme_content)

print("Created README.md in the deprecated_scripts directory.")
