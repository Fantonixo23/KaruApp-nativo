from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import datetime
import os

CERT_DIR = os.path.join(os.path.dirname(__file__), 'print_service', 'certs')
os.makedirs(CERT_DIR, exist_ok=True)

private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

now = datetime.datetime.utcnow()
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, 'PY'),
    x509.NameAttribute(NameOID.COMMON_NAME, 'Pipperfood POS Local'),
])

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(private_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(now)
    .not_valid_after(now + datetime.timedelta(days=3650))
    .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost')]), critical=False)
    .sign(private_key, hashes.SHA256())
)

with open(os.path.join(CERT_DIR, 'qz-private-key.pem'), 'wb') as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))

with open(os.path.join(CERT_DIR, 'qz-certificate.pem'), 'wb') as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print('Certificados generados en print_service/certs/')
print('  - qz-private-key.pem  (clave privada - NO compartir)')
print('  - qz-certificate.pem   (certificado publico - cargar en QZ Tray)')
