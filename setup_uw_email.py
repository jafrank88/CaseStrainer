"""
Helper script to set up UW SMTP email configuration for CaseStrainer.
"""

import os
import sys
from getpass import getpass


def main():
    print("CaseStrainer UW SMTP Setup")
    print("-" * 50)
    print(
        "This script will help you set up email functionality using UW's SMTP server."
    )
    print("\nYou'll need your UW NetID and password for authentication.")

    # Get UW email configuration from user
    netid = input("\nEnter your UW NetID (without @uw.edu): ").strip()
    email = f"{netid}@uw.edu"
    password = getpass("Enter your UW NetID password: ")
    recipient = (
        input("Enter the recipient email address [jafrank@uw.edu]: ").strip()
        or "jafrank@uw.edu"
    )

    # Create environment variables
    env_vars = {
        "MAIL_SERVER": "smtp.uw.edu",
        "MAIL_PORT": "587",
        "MAIL_USE_TLS": "True",  # UW requires STARTTLS
        "MAIL_USE_SSL": "False",
        "MAIL_USERNAME": netid,  # Just the NetID, not full email
        "MAIL_PASSWORD": password,
        "MAIL_DEFAULT_SENDER": email,
        "MAIL_RECIPIENT": recipient,
        "MAIL_DEBUG": "True",
    }

    # Create .env file content
    env_content = "# Email Configuration for CaseStrainer - UW SMTP\n"
    env_content += "# This file contains sensitive information - DO NOT commit to version control!\n\n"
    env_content += "\n".join([f"{key}={value}" for key, value in env_vars.items()])

    # Write to .env file
    try:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        with open(env_path, "w") as f:
            f.write(env_content)

        print(f"\n✅ Configuration saved to {env_path}")
        print("\nTesting the configuration...")

        # Test the configuration
        from test_email_config import test_email

        if test_email():
            print("\n🎉 Email configuration is working correctly!")
        else:
            print(
                "\n❌ Email configuration test failed. Please check the error messages above."
            )
            print("\nTroubleshooting tips:")
            print("1. Verify your UW NetID and password are correct")
            print("2. Make sure you're connected to the UW network or using the UW VPN")
            print("3. Check if your account has SMTP access enabled")
            print("4. Contact UW IT if you continue to have issues")

    except Exception as e:
        print(f"\n❌ Failed to save configuration: {e}")
        print("\nHere's your configuration. Please add it to your .env file manually:")
        print("\n" + env_content)


if __name__ == "__main__":
    main()
