#!/usr/bin/env python
"""
Script to fix Python path issues and start CaseStrainer
"""
import os
import sys
import subprocess
import shutil


def main():
    """Fix Python path issues and start CaseStrainer"""
    print("CaseStrainer Python Path Fixer")
    print("==============================")

    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Check if D:\Python\python.exe is expected
    if os.path.exists("D:\\Python\\python.exe"):
        print("D:\\Python\\python.exe exists, using it")
        python_exe = "D:\\Python\\python.exe"
    else:
        # Find Python in the virtual environment
        venv_python = os.path.join(script_dir, ".venv", "Scripts", "python.exe")
        if os.path.exists(venv_python):
            print(f"Using Python from virtual environment: {venv_python}")
            python_exe = venv_python
        else:
            # Find Python in the system PATH
            python_exe = shutil.which("python")
            if python_exe:
                print(f"Using Python from PATH: {python_exe}")
            else:
                print("Python not found. Please install Python and try again.")
                return 1

    # Get the path to app_final_vue.py
    app_path = os.path.join(script_dir, "app_final_vue.py")
    if not os.path.exists(app_path):
        print(f"Error: {app_path} not found")
        return 1

    print(f"Starting CaseStrainer from: {app_path}")
    print("Using Python executable:", python_exe)

    # Set environment variables
    os.environ["HOST"] = "0.0.0.0"
    os.environ["PORT"] = "5000"
    os.environ["USE_CHEROOT"] = "True"

    # Create a temporary directory to simulate D:\Python if it doesn't exist
    if not os.path.exists("D:\\Python"):
        try:
            os.makedirs("D:\\Python", exist_ok=True)
            print("Created D:\\Python directory")
        except (PermissionError, OSError):
            print("Could not create D:\\Python directory (permission denied)")

    # Start the application
    try:
        # Use subprocess.call to run the application with the correct Python executable
        subprocess.call([python_exe, app_path, "--host", "0.0.0.0", "--port", "5000"])
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
