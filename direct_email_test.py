"""
Direct email test script for UW SMTP.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_test_email():
    # SMTP server settings
    smtp_server = "smtp.uw.edu"
    smtp_port = 587

    # Email settings
    sender_email = "jafrank@uw.edu"
    recipient_email = "jafrank@uw.edu"

    # Create message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = "Direct Test Email from CaseStrainer"

    # Email body
    body = """
    <h2>This is a direct test email from CaseStrainer</h2>
    <p>If you're reading this, the direct SMTP connection is working!</p>
    """

    msg.attach(MIMEText(body, "html"))

    try:
        print(f"Connecting to {smtp_server}:{smtp_port}...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("Connected. Starting TLS...")
            server.starttls()
            print("TLS started. Authenticating...")
            server.login("jafrank", "Race4theGa!axy!")  # Using just the NetID
            print("Authentication successful. Sending email...")
            server.send_message(msg)
            print("✅ Test email sent successfully!")
            return True

    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you're connected to the UW network or using the UW VPN")
        print("2. Verify your NetID and password are correct")
        print("3. Try using your full UW email address as the username")
        print("4. Contact UW IT to verify SMTP access is enabled for your account")
        return False


if __name__ == "__main__":
    send_test_email()
