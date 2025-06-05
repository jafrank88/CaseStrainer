#!/usr/bin/env python3
"""
Copy LangSearch API key from config.json to .env file.
"""

import json
from pathlib import Path


def main():
    # Define paths
    project_root = Path(__file__).parent

    # Define the citations config path
    config_path = project_root / "data" / "citations" / "config.json"
    env_path = project_root / ".env"

    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}")
        return 1

    print(f"Found config file at: {config_path}")

    try:
        # Read the API key from config.json
        with open(config_path, "r") as f:
            config = json.load(f)

        api_key = config.get("langsearch_api_key")

        if not api_key or api_key == "YOUR_LANGSEARCH_API_KEY_HERE":
            print(f"Error: No valid LangSearch API key found in {config_path}")
            return 1

        # Create or update .env file
        env_vars = {}

        # Read existing .env file if it exists
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        try:
                            key, value = line.split("=", 1)
                            env_vars[key.strip()] = value.strip()
                        except ValueError:
                            continue

        # Update the LANGSEARCH_API_KEY
        env_vars["LANGSEARCH_API_KEY"] = api_key

        # Write back to .env
        with open(env_path, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

        print(f"✅ Successfully copied LangSearch API key to {env_path}")

        # Add .env to .gitignore if not already there
        gitignore_path = project_root / ".gitignore"
        ignore_line = ".env\n"

        if gitignore_path.exists():
            with open(gitignore_path, "r+") as f:
                content = f.read()
                if ".env" not in content:
                    f.write(ignore_line)
        else:
            with open(gitignore_path, "w") as f:
                f.write(ignore_line)
            print(f"✅ Created {gitignore_path} and added .env")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
