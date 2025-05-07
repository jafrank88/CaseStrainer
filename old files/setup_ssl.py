#!/usr/bin/env python3
"""
SSL Certificate and Nginx Configuration Setup Script

This script helps set up SSL certificates and Nginx configuration for the CaseStrainer web application.
"""

import os
import sys
import shutil
from pathlib import Path

def setup_ssl():
    """Set up SSL certificates and Nginx configuration."""
    # Create SSL directory if it doesn't exist
    ssl_dir = Path("ssl")
    ssl_dir.mkdir(exist_ok=True)
    
    # Check if certificates exist
    cert_path = ssl_dir / "cert.pem"
    key_path = ssl_dir / "key.pem"
    
    if not cert_path.exists() or not key_path.exists():
        print("SSL certificates not found. Please place your certificates in the ssl directory:")
        print(f"  - Certificate: {cert_path}")
        print(f"  - Private key: {key_path}")
        return False
    
    # Update Nginx configuration
    nginx_conf = Path("nginx-1.27.5/conf/nginx.conf")
    if not nginx_conf.exists():
        print(f"Nginx configuration file not found: {nginx_conf}")
        return False
    
    # Read current configuration
    with open(nginx_conf, "r") as f:
        config = f.read()
    
    # Update SSL certificate paths
    config = config.replace(
        "ssl_certificate C:/Users/jafrank/OneDrive - UW/Documents/GitHub/CaseStrainer/ssl/cert.pem;",
        "ssl_certificate ../ssl/cert.pem;"
    )
    config = config.replace(
        "ssl_certificate_key C:/Users/jafrank/OneDrive - UW/Documents/GitHub/CaseStrainer/ssl/key.pem;",
        "ssl_certificate_key ../ssl/key.pem;"
    )
    
    # Write updated configuration
    with open(nginx_conf, "w") as f:
        f.write(config)
    
    print("SSL and Nginx configuration updated successfully!")
    return True

def main():
    """Main function."""
    print("Setting up SSL certificates and Nginx configuration...")
    
    if setup_ssl():
        print("\nSetup complete! You can now:")
        print("1. Start Nginx with: nginx-1.27.5/nginx.exe")
        print("2. Start the Python application with: python app.py")
        print("\nThe application will be available at: https://wolf.law.uw.edu:5000")
    else:
        print("\nSetup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 