"""
Test script to verify email configuration in CaseStrainer.
"""

import os
import sys
from flask import Flask
from flask_mail import Mail, Message

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Initialize Flask app
app = Flask(__name__)

# Default configuration (will be overridden by environment variables)
app.config.update(
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_USE_TLS=os.getenv("MAIL_USE_TLS", "True").lower() in ("true", "1", "t"),
    MAIL_USE_SSL=os.getenv("MAIL_USE_SSL", "False").lower() in ("true", "1", "t"),
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER", "noreply@casestrainer.uw.edu"),
    MAIL_DEBUG=os.getenv("MAIL_DEBUG", "False").lower() in ("true", "1", "t"),
)

# Initialize Flask-Mail
mail = Mail(app)


def test_email():
    """Test sending an email with the current configuration."""
    print("Testing email configuration...")
    print(f"Mail Server: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
    print(
        f"Use TLS: {app.config['MAIL_USE_TLS']}, Use SSL: {app.config['MAIL_USE_SSL']}"
    )
    print(f"Username: {app.config['MAIL_USERNAME']}")
    print(f"Default Sender: {app.config['MAIL_DEFAULT_SENDER']}")

    recipient = os.getenv("MAIL_RECIPIENT", "jafrank@uw.edu")
    print(f"Recipient: {recipient}")

    # Create a test message
    with app.app_context():
        msg = Message(
            subject="Test Email from CaseStrainer",
            recipients=[recipient],
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
            print("\nTroubleshooting tips:")
            print("1. Check your SMTP server settings")
            print("2. Verify your username and password")
            print("3. If using Gmail, you may need to use an App Password")
            print(
                "4. Check if your email provider requires enabling 'Less secure app access'"
            )
            return False


if __name__ == "__main__":
    test_email()
