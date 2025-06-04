from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime
import ipaddress
import os

# Create output directory if it doesn't exist
os.makedirs("ssl", exist_ok=True)

# Generate a private key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# Write private key to file
with open("ssl/key.pem", "wb") as f:
    f.write(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

# Create a self-signed certificate
subject = issuer = x509.Name(
    [
        x509.NameAttribute(NameOID.COMMON_NAME, "wolf.law.uw.edu"),
    ]
)

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(private_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(
        # Certificate will be valid for 1 year
        datetime.datetime.utcnow()
        + datetime.timedelta(days=365)
    )
    .add_extension(
        x509.SubjectAlternativeName(
            [
                x509.DNSName("wolf.law.uw.edu"),
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.IPAddress(ipaddress.IPv4Address("0.0.0.0")),
                x509.IPAddress(ipaddress.IPv4Address("10.158.120.151")),
            ]
        ),
        critical=False,
    )
    .sign(private_key, hashes.SHA256())
)

# Write certificate to file
with open("ssl/cert.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print("Certificate and key generated successfully in the 'ssl' directory.")
