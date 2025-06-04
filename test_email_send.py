"""
Direct email test script for UW SMTP using Flask-Mail.
"""

from flask import Flask
from flask_mail import Mail, Message
import sys

# Create a simple Flask app
app = Flask(__name__)

# Configure Flask-Mail with UW SMTP settings
app.config.update(
    MAIL_SERVER="smtp.uw.edu",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME="jafrank",  # Just the NetID, not full email
    MAIL_PASSWORD="Race4theGa!axy!",
    MAIL_DEFAULT_SENDER="jafrank@uw.edu",
    MAIL_DEBUG=True,
)

# Initialize Flask-Mail
mail = Mail(app)


def send_test_email():
    """Send a test email using Flask-Mail."""
    print("Preparing to send test email...")
    print(f"SMTP Server: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
    print(f"Username: {app.config['MAIL_USERNAME']}")
    print(f"From: {app.config['MAIL_DEFAULT_SENDER']}")

    try:
        # Create and send email within the application context
        with app.app_context():
            try:
                # Create message
                recipient = "jafrank@uw.edu"
                print(f"Sending to: {recipient}")

                msg = Message(
                    subject="Direct Test Email from CaseStrainer",
                    recipients=[recipient],
                    html="""
                    <h2>This is a direct test email from CaseStrainer</h2>
                    <p>If you're reading this, the direct Flask-Mail configuration is working!</p>
                    """,
                )

                # Send email
                print("Sending email...")
                mail.send(msg)
                print("✅ Email sent successfully!")
                return True

            except Exception as e:
                print(f"❌ Error sending email: {e}")
                import traceback

                traceback.print_exc()
                return False

    except Exception as e:
        print(f"❌ Failed to prepare email: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Starting email test...")
    success = send_test_email()
    sys.exit(0 if success else 1)
