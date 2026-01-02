#!/usr/bin/env python3
"""
Force rebuild frontend with latest Vue changes
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None, shell=True):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, cwd=cwd, shell=shell, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ SUCCESS: {cmd}")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ FAILED: {cmd}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ ERROR running {cmd}: {e}")
        return False

def main():
    """Force rebuild frontend"""
    print("🔧 Force rebuilding Vue frontend with latest changes...")
    
    # Get project root
    project_root = Path(__file__).parent
    vue_dir = project_root / "casestrainer-vue-new"
    
    if not vue_dir.exists():
        print(f"❌ Vue directory not found: {vue_dir}")
        return False
    
    print(f"📁 Vue directory: {vue_dir}")
    
    # Step 1: Clean old build
    print("\n🧹 Cleaning old build...")
    dist_dir = vue_dir / "dist"
    if dist_dir.exists():
        import shutil
        shutil.rmtree(dist_dir)
        print("✅ Removed old dist directory")
    
    # Step 2: Install dependencies (just in case)
    print("\n📦 Installing dependencies...")
    if not run_command("npm install", cwd=str(vue_dir)):
        print("❌ Failed to install dependencies")
        return False
    
    # Step 3: Build Vue frontend
    print("\n🏗️ Building Vue frontend...")
    if not run_command("npm run build", cwd=str(vue_dir)):
        print("❌ Failed to build Vue frontend")
        return False
    
    # Step 4: Rebuild Docker frontend container
    print("\n🐳 Rebuilding Docker frontend container...")
    if not run_command("docker-compose -f docker-compose.prod.yml build --no-cache frontend-prod"):
        print("❌ Failed to rebuild frontend container")
        return False
    
    # Step 5: Restart frontend container
    print("\n🔄 Restarting frontend container...")
    if not run_command("docker-compose -f docker-compose.prod.yml up -d frontend-prod"):
        print("❌ Failed to restart frontend container")
        return False
    
    # Step 6: Restart nginx to pick up new files
    print("\n🔄 Restarting nginx...")
    if not run_command("docker-compose -f docker-compose.prod.yml restart nginx"):
        print("❌ Failed to restart nginx")
        return False
    
    print("\n✅ Frontend rebuild complete!")
    print("🌐 Application: https://wolf.law.uw.edu/casestrainer/")
    print("🔗 Local access: http://localhost:8080")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
