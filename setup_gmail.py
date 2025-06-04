"""
Helper script to set up Gmail SMTP configuration for CaseStrainer.
"""

import os
import sys
from getpass import getpass


def main():
    print("CaseStrainer Gmail SMTP Setup")
    print("-" * 40)
    print("This script will help you set up email functionality using Gmail SMTP.")
    print("\n⚠️  IMPORTANT: For Gmail, you'll need to use an App Password if you have")
    print("2-Step Verification enabled. You can generate one at:")
    print("https://myaccount.google.com/apppasswords")
    print("\nIf you don't have 2-Step Verification enabled, you may need to enable")
    print(
        """'Less secure app access' at:
https://myaccount.google.com/lesssecureapps (deprecated by Google but may still work)"""
    )

    # Get Gmail configuration from user
    email = input("\nEnter your Gmail address: ").strip()
    password = getpass("Enter your Gmail password or App Password: ")
    recipient = (
        input("Enter the recipient email address [jafrank@uw.edu]: ").strip()
        or "jafrank@uw.edu"
    )

    # Create environment variables
    env_vars = {
        "MAIL_SERVER": "smtp.gmail.com",
        "MAIL_PORT": "587",
        "MAIL_USE_TLS": "True",
        "MAIL_USE_SSL": "False",
        "MAIL_USERNAME": email,
        "MAIL_PASSWORD": password,
        "MAIL_DEFAULT_SENDER": email,
        "MAIL_RECIPIENT": recipient,
        "MAIL_DEBUG": "True",
    }

    # Create .env file content
    env_content = "# Email Configuration for CaseStrainer\n"
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
            print(
                "1. Make sure you're using an App Password if you have 2-Step Verification enabled"
            )
            print(
                "2. Check if 'Less secure app access' is enabled in your Google Account"
            )
            print(
                "3. You might need to allow access from less secure apps: https://myaccount.google.com/lesssecureapps"
            )
            print(
                "4. If you're using a work/school Google account, contact your administrator"
            )

    except Exception as e:
        print(f"\n❌ Failed to save configuration: {e}")
        print("\nHere's your configuration. Please add it to your .env file manually:")
        print("\n" + env_content)


if __name__ == "__main__":
    main()
