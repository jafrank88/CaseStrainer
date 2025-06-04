#!/usr/bin/env python3
"""
Test script to verify environment variable configuration.
"""
import os
import sys
from pathlib import Path


def check_env():
    """Check if required environment variables are set."""
    print("=== Environment Variable Check ===\n")

    # Check if .env exists
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found. Please run 'scripts\\setup_env.bat' first.")
        return False

    print(f"✅ Found .env file at {env_path.absolute()}")

    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    # Check required variables
    required_vars = [
        "SECRET_KEY",
        "DATABASE_FILE",
        "UPLOAD_FOLDER",
        "COURTLISTENER_API_KEY",
    ]

    all_ok = True
    print("\nChecking required environment variables:")

    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith("your-"):
            print(f"❌ {var}: Not set or using default value")
            all_ok = False
        else:
            # Don't print the actual values of sensitive variables
            display_value = (
                "[SET]" if var in ["SECRET_KEY", "COURTLISTENER_API_KEY"] else value
            )
            print(f"✅ {var}: {display_value}")

    # Check optional variables
    print("\nOptional environment variables:")
    optional_vars = ["LANGSEARCH_API_KEY", "SENTRY_DSN"]

    for var in optional_vars:
        value = os.getenv(var)
        if value and not value.startswith("your-"):
            display_value = "[SET]" if var == "LANGSEARCH_API_KEY" else value
            print(f"ℹ️  {var}: {display_value}")
        else:
            print(f"ℹ️  {var}: Not set (optional)")

    return all_ok


if __name__ == "__main__":
    try:
        success = check_env()
        if success:
            print("\n✅ Environment is properly configured!")
        else:
            print("\n❌ Some required environment variables are missing or invalid.")
            print("   Please update your .env file and try again.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)
