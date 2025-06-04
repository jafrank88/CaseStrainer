"""
Test email functionality using the application's configuration.
"""

import os
import sys
from flask import Flask, current_app
from flask_mail import Mail, Message

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import the app configuration
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


def create_app():
    """Create and configure the Flask app with email settings."""
    app = Flask(__name__)

    # Configure Flask-Mail
    app.config.update(
        MAIL_SERVER=MAIL_SERVER,
        MAIL_PORT=MAIL_PORT,
        MAIL_USE_TLS=MAIL_USE_TLS,
        MAIL_USE_SSL=MAIL_USE_SSL,
        MAIL_USERNAME=MAIL_USERNAME,
        MAIL_PASSWORD=MAIL_PASSWORD,
        MAIL_DEFAULT_SENDER=MAIL_DEFAULT_SENDER,
    )

    # Initialize Flask-Mail
    mail = Mail(app)

    # Store mail instance in the app
    app.mail = mail

    return app


def send_test_email():
    """Send a test email using the application's email configuration."""
    print("Testing email configuration from app...")
    print(f"SMTP Server: {MAIL_SERVER}:{MAIL_PORT}")
    print(f"Username: {MAIL_USERNAME}")
    print(f"From: {MAIL_DEFAULT_SENDER}")
    print(f"To: {MAIL_RECIPIENT}")

    # Create the Flask app
    app = create_app()
    mail = app.mail

    try:
        # Create and send email within the application context
        with app.app_context():
            # Create message
            msg = Message(
                subject="Test Email from CaseStrainer App",
                recipients=[MAIL_RECIPIENT],
                html="""
                <h2>This is a test email from CaseStrainer</h2>
                <p>If you're reading this, the email configuration in the application is working correctly!</p>
                """,
            )

            # Send email
            print("Sending email...")
            mail.send(msg)
            print("✅ Email sent successfully!")
            return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Starting application email test...")
    success = send_test_email()
    sys.exit(0 if success else 1)
