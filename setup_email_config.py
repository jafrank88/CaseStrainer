"""
Helper script to set up email configuration for CaseStrainer.
"""

import os
import sys
from getpass import getpass


def main():
    print("CaseStrainer Email Configuration Setup")
    print("-" * 40)

    # Get email configuration from user
    config = {
        "MAIL_SERVER": input("SMTP Server [smtp.gmail.com]: ") or "smtp.gmail.com",
        "MAIL_PORT": input("SMTP Port [587]: ") or "587",
        "MAIL_USE_TLS": input("Use TLS? [y/N]: ").lower() in ("y", "yes"),
        "MAIL_USE_SSL": False,
        "MAIL_USERNAME": input("Email Username: "),
        "MAIL_PASSWORD": getpass("Email Password (or App Password for Gmail): "),
        "MAIL_DEFAULT_SENDER": input("Default Sender [noreply@casestrainer.uw.edu]: ")
        or "noreply@casestrainer.uw.edu",
        "MAIL_RECIPIENT": input("Feedback Recipient Email: ") or "jafrank@uw.edu",
        "MAIL_DEBUG": input("Enable debug mode? [y/N]: ").lower() in ("y", "yes"),
    }

    # Create .env file content
    env_content = "\n".join([f"{key}={value}" for key, value in config.items()])

    # Write to .env file
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        with open(env_path, "w") as f:
            f.write(f"# Email Configuration\n{env_content}")
        print(f"\n✅ Configuration saved to {env_path}")
        print(
            "\nNote: Make sure to keep this file secure and never commit it to version control!"
        )
    except Exception as e:
        print(f"\n❌ Failed to save configuration: {e}")
        print("\nHere's your configuration. Please add it to your .env file manually:")
        print("\n# Email Configuration")
        print(env_content)


if __name__ == "__main__":
    main()
