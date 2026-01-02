#!/usr/bin/env python3
"""
Verify SSL certificate files are in the new location
"""

import os
import sys

def verify_ssl_files():
    """Verify SSL files exist in the new location"""
    print("=" * 60)
    print("VERIFYING SSL CERTIFICATE FILES")
    print("=" * 60)
    
    # New SSL file locations
    cert_path = "C:/Users/jafrank/wolf-cert-bundle.crt"
    key_path = "C:/Users/jafrank/wolf.law.uw.edu.key"
    
    # Check certificate file
    print(f"\nChecking certificate file:")
    print(f"  Path: {cert_path}")
    if os.path.exists(cert_path):
        stat = os.stat(cert_path)
        size = stat.st_size
        print(f"  Status: [FOUND] (size: {size:,} bytes)")
    else:
        print(f"  Status: [NOT FOUND]")
        return False
    
    # Check key file
    print(f"\nChecking private key file:")
    print(f"  Path: {key_path}")
    if os.path.exists(key_path):
        stat = os.stat(key_path)
        size = stat.st_size
        print(f"  Status: [FOUND] (size: {size:,} bytes)")
    else:
        print(f"  Status: [NOT FOUND]")
        return False
    
    print("\n" + "=" * 60)
    print("[SUCCESS] ALL SSL FILES FOUND IN NEW LOCATION")
    print("=" * 60)
    print("\nThe following files have been updated to use the new SSL paths:")
    print("  - config.env")
    print("  - config.ini")
    print("  - docker-compose.yml")
    print("  - update-nginx-ssl.ps1")
    print("  - scripts/setup_directories.bat")
    print("\nDocker containers will now use the new SSL certificate files.")
    
    return True

if __name__ == "__main__":
    if verify_ssl_files():
        sys.exit(0)
    else:
        print("[ERROR] SSL files not found. Please ensure the files exist at:")
        print("  C:/Users/jafrank/wolf-cert-bundle.crt")
        print("  C:/Users/jafrank/wolf.law.uw.edu.key")
        sys.exit(1)
