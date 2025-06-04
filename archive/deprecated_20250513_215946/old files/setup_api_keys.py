#!/usr/bin/env python3
"""
CaseStrainer API Key Setup Utility

This script helps configure API keys for CaseStrainer by:
1. Setting up environment variables
2. Creating/updating a config.json file
3. Testing API connectivity

Usage:
    python setup_api_keys.py

The script will prompt for API keys and test them to ensure they work correctly.
"""

import os
import sys
import json
import argparse
from pathlib import Path
import time


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)


def get_input(prompt, default=None, password=False):
    """Get user input with a default value."""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "

    if password:
        import getpass

        value = getpass.getpass(prompt)
    else:
        value = input(prompt)

    return value if value else default


def load_config():
    """Load existing configuration if available."""
    config_path = Path("config.json")
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load existing config.json: {e}")
    return {}


def save_config(config):
    """Save configuration to config.json."""
    config_path = Path("config.json")
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Configuration saved to {config_path}")
        return True
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False


def test_courtlistener_api(api_key):
    """Test CourtListener API connectivity."""
    try:
        import requests

        print("Testing CourtListener API connection...")

        headers = {"Authorization": f"Token {api_key}"}

        # Try a simple API call
        response = requests.get(
            "https://www.courtlistener.com/api/rest/v3/citation-lookup/?citation=410+U.S.+113",
            headers=headers,
        )

        if response.status_code == 200:
            print("✓ CourtListener API connection successful!")
            return True
        else:
            print(
                f"✗ CourtListener API error: {response.status_code} - {response.text}"
            )
            return False
    except Exception as e:
        print(f"✗ CourtListener API test failed: {e}")
        return False


def test_langsearch_api(api_key):
    """Test LangSearch API connectivity."""
    try:
        import requests

        print("Testing LangSearch API connection...")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Try a simple API call - adjust endpoint as needed
        response = requests.post(
            "https://api.langsearch.ai/v1/search",
            headers=headers,
            json={"query": "test query", "limit": 1},
        )

        if response.status_code == 200:
            print("✓ LangSearch API connection successful!")
            return True
        else:
            print(f"✗ LangSearch API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ LangSearch API test failed: {e}")
        return False


def setup_environment_variables(config):
    """Set up environment variables for the current session."""
    for key, value in config.items():
        env_key = key.upper()
        if key.endswith("_api_key"):
            env_key = key[:-8].upper() + "_API_KEY"
        os.environ[env_key] = value

    print("Environment variables set for current session")


def generate_systemd_config(config):
    """Generate systemd service configuration with API keys."""
    try:
        with open("casestrainer.service", "r") as f:
            service_content = f.read()

        # Replace environment variables
        for key, value in config.items():
            env_key = key.upper()
            if key.endswith("_api_key"):
                env_key = key[:-8].upper() + "_API_KEY"

            # Replace commented environment line
            service_content = service_content.replace(
                f'# Environment="{env_key}=your_api_key_here"',
                f'Environment="{env_key}={value}"',
            )

            # Replace uncommented environment line
            service_content = service_content.replace(
                f'Environment="{env_key}=your_api_key_here"',
                f'Environment="{env_key}={value}"',
            )

        # Write updated service file
        with open("casestrainer.service.configured", "w") as f:
            f.write(service_content)

        print(
            "Updated systemd service configuration saved to casestrainer.service.configured"
        )
        print(
            "Review this file and copy it to /etc/systemd/system/casestrainer.service"
        )
    except Exception as e:
        print(f"Error generating systemd configuration: {e}")


def generate_secure_key():
    """Generate a secure random key."""
    import secrets

    return secrets.token_hex(32)


def encrypt_api_key(key: str, master_key: str) -> str:
    """Encrypt an API key using Fernet symmetric encryption."""
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64

    # Derive a key from the master key
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"casestrainer_salt",  # In production, use a unique salt per key
        iterations=100000,
    )
    key_bytes = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
    f = Fernet(key_bytes)

    # Encrypt the API key
    return f.encrypt(key.encode()).decode()


def decrypt_api_key(encrypted_key: str, master_key: str) -> str:
    """Decrypt an API key using Fernet symmetric encryption."""
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64

    # Derive the key from the master key
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"casestrainer_salt",  # Must match the salt used in encryption
        iterations=100000,
    )
    key_bytes = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
    f = Fernet(key_bytes)

    # Decrypt the API key
    return f.decrypt(encrypted_key.encode()).decode()


def rotate_api_key(api_name: str, config: dict) -> bool:
    """Rotate an API key by generating a new one and updating the configuration."""
    try:
        # Generate new key
        new_key = generate_secure_key()

        # Get master key from environment or prompt user
        master_key = os.environ.get("MASTER_KEY")
        if not master_key:
            master_key = get_input("Enter master key for encryption", password=True)

        # Encrypt the new key
        encrypted_key = encrypt_api_key(new_key, master_key)

        # Update config
        config[f"{api_name}_api_key"] = encrypted_key
        config[f"{api_name}_key_rotation_date"] = time.strftime("%Y-%m-%d %H:%M:%S")

        # Save config
        if save_config(config):
            print(f"Successfully rotated {api_name} API key")
            return True
        return False
    except Exception as e:
        print(f"Error rotating {api_name} API key: {e}")
        return False


def main():
    """Main function to set up API keys."""
    parser = argparse.ArgumentParser(description="CaseStrainer API Key Setup Utility")
    parser.add_argument(
        "--no-test", action="store_true", help="Skip API connectivity tests"
    )
    parser.add_argument(
        "--rotate",
        choices=["courtlistener", "langsearch", "openai", "all"],
        help="Rotate specified API key(s)",
    )
    args = parser.parse_args()

    print_header("CaseStrainer API Key Setup Utility")

    # Load existing configuration
    config = load_config()

    # Handle key rotation if requested
    if args.rotate:
        if args.rotate == "all":
            for api in ["courtlistener", "langsearch", "openai"]:
                rotate_api_key(api, config)
        else:
            rotate_api_key(args.rotate, config)
        return

    # Get master key for encryption
    master_key = os.environ.get("MASTER_KEY")
    if not master_key:
        master_key = get_input("Enter master key for encryption", password=True)

    # Get CourtListener API key
    print("\nCourtListener API Key")
    print("---------------------")
    print(
        "The CourtListener API key is used for citation lookup and case data retrieval."
    )
    print(
        "You can register for an API key at: https://www.courtlistener.com/help/api/rest/"
    )

    courtlistener_key = get_input(
        "Enter your CourtListener API key",
        default=config.get("courtlistener_api_key", None),
        password=True,
    )

    if courtlistener_key:
        # Encrypt the key before storing
        encrypted_key = encrypt_api_key(courtlistener_key, master_key)
        config["courtlistener_api_key"] = encrypted_key
        config["courtlistener_key_rotation_date"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if not args.no_test:
            test_courtlistener_api(courtlistener_key)
    else:
        print(
            "Warning: No CourtListener API key provided. Some features will be limited."
        )

    # Get LangSearch API key
    print("\nLangSearch API Key")
    print("-----------------")
    print("The LangSearch API key is used for advanced case summary generation.")
    print("Contact the LangSearch provider for API access.")

    langsearch_key = get_input(
        "Enter your LangSearch API key",
        default=config.get("langsearch_api_key", None),
        password=True,
    )

    if langsearch_key:
        # Encrypt the key before storing
        encrypted_key = encrypt_api_key(langsearch_key, master_key)
        config["langsearch_api_key"] = encrypted_key
        config["langsearch_key_rotation_date"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if not args.no_test:
            test_langsearch_api(langsearch_key)
    else:
        print("Warning: No LangSearch API key provided. Some features will be limited.")

    # Get SSL certificate paths
    print("\nSSL Certificate Paths")
    print("-------------------")
    print("SSL certificates are required for HTTPS support.")

    ssl_cert_path = get_input(
        "Enter path to SSL certificate (cert.pem)",
        default=config.get("ssl_cert_path", "ssl/cert.pem"),
    )

    ssl_key_path = get_input(
        "Enter path to SSL key (key.pem)",
        default=config.get("ssl_key_path", "ssl/key.pem"),
    )

    config["ssl_cert_path"] = ssl_cert_path
    config["ssl_key_path"] = ssl_key_path

    # Generate a secret key if not present
    if "secret_key" not in config:
        import secrets

        config["secret_key"] = secrets.token_hex(24)
        print("\nGenerated a new secret key for session management")

    # Save configuration
    if save_config(config):
        # Set environment variables
        setup_environment_variables(config)

        # Generate systemd configuration
        generate_systemd_config(config)

        print("\nAPI key setup complete!")
        print("\nTo use these keys in your current terminal session:")
        for key, value in config.items():
            if key.endswith("_api_key"):
                env_key = key[:-8].upper() + "_API_KEY"
                print(f"export {env_key}='{value}'")

        print("\nTo start CaseStrainer with these keys:")
        print(
            "python run_server.py --threads 8 --workers 2 --channel-timeout 300 --connection-limit 2000 --timeout 300"
        )
    else:
        print("API key setup failed. Please try again.")


if __name__ == "__main__":
    main()
