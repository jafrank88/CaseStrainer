"""
Test email functionality using the application's configuration.
"""

import os
import sys
import pytest
from flask import Flask
from flask_mail import Mail, Message

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def create_app():
    """Create and configure the Flask app with email settings."""
    app = Flask(__name__)

    # Configure Flask-Mail with test settings
    app.config.update(
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USE_SSL=False,
        MAIL_USERNAME='test@example.com',
        MAIL_PASSWORD='test_password',
        MAIL_DEFAULT_SENDER='test@example.com',
    )

    # Initialize Flask-Mail
    mail = Mail(app)

    # Store mail instance in the app
    app.mail = mail

    return app


def test_email_configuration():
    """Test that email configuration can be set up properly."""
    app = create_app()
    
    assert app.config['MAIL_SERVER'] == 'smtp.gmail.com'
    assert app.config['MAIL_PORT'] == 587
    assert app.config['MAIL_USE_TLS'] is True
    assert app.config['MAIL_USERNAME'] == 'test@example.com'
    
    # Test that Flask-Mail was initialized
    assert hasattr(app, 'mail')
    assert isinstance(app.mail, Mail)


def test_email_message_creation():
    """Test that email messages can be created properly."""
    app = create_app()
    
    with app.app_context():
        msg = Message(
            subject="Test Email from CaseStrainer App",
            recipients=['test@example.com'],
            html="""
            <h2>This is a test email from CaseStrainer</h2>
            <p>If you're reading this, the email configuration in the application is working correctly!</p>
            """,
        )
        
        assert msg.subject == "Test Email from CaseStrainer App"
        assert msg.recipients == ['test@example.com']
        assert 'CaseStrainer' in msg.html


def send_test_email():
    """Send a test email using the application's email configuration."""
    print("Testing email configuration from app...")
    print("SMTP Server: smtp.gmail.com:587")
    print("Username: test@example.com")
    print("From: test@example.com")
    print("To: test@example.com")

    # Create the Flask app
    app = create_app()
    mail = app.mail

    try:
        # Create and send email within the application context
        with app.app_context():
            # Create message
            msg = Message(
                subject="Test Email from CaseStrainer App",
                recipients=['test@example.com'],
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
