from cryptography import x509
from cryptography.hazmat.backends import default_backend

# Load the certificate
with open('ssl/cert.pem', 'rb') as f:
    cert_data = f.read()
    cert = x509.load_pem_x509_certificate(cert_data, default_backend())

# Print certificate information
print("Certificate Subject:", cert.subject)
print("Certificate Issuer:", cert.issuer)
print("Valid From:", cert.not_valid_before)
print("Valid Until:", cert.not_valid_after)

# Print Subject Alternative Names
try:
    san = cert.extensions.get_extension_for_oid(x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
    print("Subject Alternative Names:")
    for name in san.value:
        print(f"  {name}")
except x509.ExtensionNotFound:
    print("No Subject Alternative Name extension found")
