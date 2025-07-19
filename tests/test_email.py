"""
Test script to verify email functionality in CaseStrainer.
"""

import os
import sys
from flask import Flask
from flask_mail import Mail, Message
import pytest
pytest.skip("MAIL_SERVER is missing or deprecated", allow_module_level=True)

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import config
from src.config import (
    MAIL_SERVER,
    MAIL_PORT,
    MAIL_USE_TLS,
    MAIL_USE_SSL,
    MAIL_USERNAME,
    MAIL_PASSWORD,
    MAIL_DEFAULT_SENDER,
    MAIL_RECIPIENT,
    MAIL_DEBUG,
)


def test_email():
    """Test sending an email with the current configuration."""
    print("Testing email configuration...")
    print(f"Mail Server: {MAIL_SERVER}:{MAIL_PORT}")
    print(f"Use TLS: {MAIL_USE_TLS}, Use SSL: {MAIL_USE_SSL}")
    print(f"Username: {MAIL_USERNAME}")
    print(f"Default Sender: {MAIL_DEFAULT_SENDER}")
    print(f"Recipient: {MAIL_RECIPIENT}")

    # Create a test Flask app
    app = Flask(__name__)

    # Configure the app
    app.config["MAIL_SERVER"] = MAIL_SERVER
    app.config["MAIL_PORT"] = MAIL_PORT
    app.config["MAIL_USE_TLS"] = MAIL_USE_TLS
    app.config["MAIL_USE_SSL"] = MAIL_USE_SSL
    app.config["MAIL_USERNAME"] = MAIL_USERNAME
    app.config["MAIL_PASSWORD"] = MAIL_PASSWORD
    app.config["MAIL_DEFAULT_SENDER"] = MAIL_DEFAULT_SENDER
    app.config["MAIL_DEBUG"] = MAIL_DEBUG

    # Initialize Flask-Mail
    mail = Mail(app)

    # Create a test message
    with app.app_context():
        msg = Message(
            subject="Test Email from CaseStrainer",
            recipients=[MAIL_RECIPIENT],
            html="""
            <h2>This is a test email from CaseStrainer</h2>
            <p>If you're reading this, the email configuration is working correctly!</p>
            <p>This email was sent by the test script.</p>
            """,
        )

        try:
            mail.send(msg)
            print("✅ Test email sent successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to send test email: {e}")
            return False


if __name__ == "__main__":
    test_email()
