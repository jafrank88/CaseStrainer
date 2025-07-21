"""
Test Flask-Mail with UW SMTP configuration.
"""

from flask import Flask, jsonify
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Flask-Mail with direct settings that we know work
app.config.update(
    MAIL_SERVER="smtp.uw.edu",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME="jafrank",  # Just the NetID, not full email
    MAIL_PASSWORD="Race4theGa!axy!",
    MAIL_DEFAULT_SENDER="jafrank@uw.edu",
)

# Initialize Flask-Mail
mail = Mail(app)


@app.route("/test-email")
def test_email():
    """Test email endpoint with detailed logging."""
    print("\n--- Starting email test ---")
    print(f"Using SMTP server: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
    print(f"Username: {app.config['MAIL_USERNAME']}")
    print(f"Default sender: {app.config['MAIL_DEFAULT_SENDER']}")

    try:
        with app.app_context():
            # Create message
            recipient = "jafrank@uw.edu"
            print(f"Preparing email to: {recipient}")

            msg = Message(
                subject="Test Email from CaseStrainer (Flask-Mail)",
                recipients=[recipient],
                html="""
                <h2>This is a test email from CaseStrainer</h2>
                <p>If you're reading this, the Flask-Mail configuration is working correctly with UW SMTP!</p>
                """,
            )

            print("Sending email...")
            mail.send(msg)
            print("✅ Email sent successfully!")

            return jsonify(
                {
                    "status": "success",
                    "message": "Test email sent successfully!",
                    "details": {
                        "server": app.config["MAIL_SERVER"],
                        "port": app.config["MAIL_PORT"],
                        "username": app.config["MAIL_USERNAME"],
                        "sender": app.config["MAIL_DEFAULT_SENDER"],
                        "recipient": recipient,
                        "tls": app.config["MAIL_USE_TLS"],
                        "ssl": app.config["MAIL_USE_SSL"],
                    },
                }
            )

    except Exception as e:
        error_msg = f"❌ Failed to send email: {str(e)}"
        print(error_msg)
        import traceback

        traceback.print_exc()

        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to send test email",
                    "error": str(e),
                    "details": {
                        "server": app.config["MAIL_SERVER"],
                        "port": app.config["MAIL_PORT"],
                        "username": app.config["MAIL_USERNAME"],
                        "sender": app.config["MAIL_DEFAULT_SENDER"],
                        "tls": app.config["MAIL_USE_TLS"],
                        "ssl": app.config["MAIL_USE_SSL"],
                    },
                }
            ),
            500,
        )


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
