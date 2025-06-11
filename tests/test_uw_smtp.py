"""
Test script specifically for UW SMTP server.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def test_uw_smtp():
    print("UW SMTP Connection Test")
    print("=======================")

    # SMTP server settings
    smtp_server = "smtp.uw.edu"
    smtp_port = 587

    # Email settings
    sender_email = "jafrank@uw.edu"
    recipient_email = "jafrank@uw.edu"

    # Get password securely
    password = "Race4theGa!axy!"

    # Create message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = "Test Email from CaseStrainer (UW SMTP)"

    # Email body
    body = """
    <h2>This is a test email from CaseStrainer</h2>
    <p>If you're reading this, the UW SMTP configuration is working correctly!</p>
    <p>This email was sent using the UW SMTP server.</p>
    """

    msg.attach(MIMEText(body, "html"))

    try:
        print(f"Connecting to {smtp_server}:{smtp_port}...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("Connected. Starting TLS...")
            server.starttls()
            print("TLS started. Authenticating...")
            server.login("jafrank", password)  # Using just the NetID, not full email
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
    test_uw_smtp()
