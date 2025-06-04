import os
import sys
import subprocess
import shutil
from pathlib import Path


def print_step(step):
    print(f"\n{'='*50}")
    print(f" {step}")
    print(f"{'='*50}")


def run_command(command, cwd=None, shell=True):
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command, cwd=cwd, shell=shell, check=True, text=True, capture_output=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def main():
    # Define paths
    base_dir = Path(__file__).parent.absolute()
    vue_dir = base_dir / "casestrainer-vue"
    static_vue_dir = base_dir / "static" / "vue"

    # Step 1: Install dependencies
    print_step("Installing Vue.js dependencies")
    if not run_command("npm install", cwd=vue_dir):
        print("Failed to install Vue.js dependencies")
        return False

    # Step 2: Build the Vue.js app
    print_step("Building Vue.js application")
    if not run_command("npm run build", cwd=vue_dir):
        print("Failed to build Vue.js application")
        return False

    # Step 3: Clean up existing static/vue directory
    print_step("Preparing static directory")
    if static_vue_dir.exists():
        print(f"Removing existing directory: {static_vue_dir}")
        shutil.rmtree(static_vue_dir)

    # Step 4: Copy built files to static/vue
    print_step("Copying built files")
    dist_dir = vue_dir / "dist"
    if not dist_dir.exists():
        print(f"Error: Build output directory not found: {dist_dir}")
        return False

    print(f"Copying from {dist_dir} to {static_vue_dir}")
    shutil.copytree(dist_dir, static_vue_dir)

    print("\nBuild and setup completed successfully!")
    print("You can now start the server with:")
    print("  python app_final_vue.py")

    return True


if __name__ == "__main__":
    main()
