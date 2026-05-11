"""PKI: CA propria gerada na primeira execucao + assinatura de certs de cliente para mTLS gRPC.

Layout em disco (todos sob server/data/, gitignored):
    ca.crt / ca.key       — CA root self-signed, RSA 4096, 10 anos
    server.crt / server.key — cert do servidor gRPC (CN=sentinelbr-server, SAN configuravel)

SAN do server.crt vem de settings.server_cert_san (DNS) + server_cert_san_ips (IP),
ambas listas separadas por virgula. Default: localhost + sentinelbr-server + 127.0.0.1.
Em prod, configure via env pro FQDN publico:
    SENTINELBR_SERVER_CERT_SAN=server.empresa.com.br,sentinelbr-server
IMPORTANTE: mudar a SAN requer apagar server.crt + server.key e reiniciar o gRPC.

Carregamento eh idempotente: load_or_create_*() so gera se nao existir. Em prod, montar volume
persistente em server/data/ para nao perder a CA entre restarts.
"""

from __future__ import annotations

import datetime as dt
import ipaddress
from dataclasses import dataclass
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from app.config import get_settings

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CA_CERT_PATH = DATA_DIR / "ca.crt"
CA_KEY_PATH = DATA_DIR / "ca.key"
SERVER_CERT_PATH = DATA_DIR / "server.crt"
SERVER_KEY_PATH = DATA_DIR / "server.key"


@dataclass
class CertBundle:
    cert_pem: bytes
    key_pem: bytes


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _save_pem(path: Path, data: bytes, *, mode: int = 0o600) -> None:
    path.write_bytes(data)
    path.chmod(mode)


def _generate_key(bits: int = 4096) -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=bits)


def _key_to_pem(key: rsa.RSAPrivateKey) -> bytes:
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def _cert_to_pem(cert: x509.Certificate) -> bytes:
    return cert.public_bytes(serialization.Encoding.PEM)


def load_or_create_ca() -> tuple[x509.Certificate, rsa.RSAPrivateKey]:
    _ensure_data_dir()
    if CA_CERT_PATH.exists() and CA_KEY_PATH.exists():
        cert = x509.load_pem_x509_certificate(CA_CERT_PATH.read_bytes())
        key = serialization.load_pem_private_key(CA_KEY_PATH.read_bytes(), password=None)
        if isinstance(key, rsa.RSAPrivateKey):
            return cert, key

    key = _generate_key(4096)
    name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SentinelBR"),
        x509.NameAttribute(NameOID.COMMON_NAME, "SentinelBR Root CA"),
    ])
    now = dt.datetime.now(dt.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - dt.timedelta(minutes=5))
        .not_valid_after(now + dt.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=1), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
        .sign(private_key=key, algorithm=hashes.SHA256())
    )

    _save_pem(CA_CERT_PATH, _cert_to_pem(cert), mode=0o644)
    _save_pem(CA_KEY_PATH, _key_to_pem(key), mode=0o600)
    return cert, key


def load_or_create_server_cert() -> CertBundle:
    """Cert do servidor gRPC. Reusa CA, gera 1 vez."""
    _ensure_data_dir()
    if SERVER_CERT_PATH.exists() and SERVER_KEY_PATH.exists():
        return CertBundle(
            cert_pem=SERVER_CERT_PATH.read_bytes(),
            key_pem=SERVER_KEY_PATH.read_bytes(),
        )

    ca_cert, ca_key = load_or_create_ca()
    key = _generate_key(4096)
    name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SentinelBR"),
        x509.NameAttribute(NameOID.COMMON_NAME, "sentinelbr-server"),
    ])
    now = dt.datetime.now(dt.UTC)

    settings = get_settings()
    san_entries: list[x509.GeneralName] = []
    for dns in (d.strip() for d in settings.server_cert_san.split(",")):
        if dns:
            san_entries.append(x509.DNSName(dns))
    for ip_raw in (i.strip() for i in settings.server_cert_san_ips.split(",")):
        if ip_raw:
            san_entries.append(x509.IPAddress(ipaddress.ip_address(ip_raw)))
    if not san_entries:
        # Salvaguarda: sem SAN, mTLS quebra. Sempre garante localhost.
        san_entries = [x509.DNSName("localhost")]

    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - dt.timedelta(minutes=5))
        .not_valid_after(now + dt.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
        .add_extension(
            x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .sign(private_key=ca_key, algorithm=hashes.SHA256())
    )

    cert_pem = _cert_to_pem(cert)
    key_pem = _key_to_pem(key)
    _save_pem(SERVER_CERT_PATH, cert_pem, mode=0o644)
    _save_pem(SERVER_KEY_PATH, key_pem, mode=0o600)
    return CertBundle(cert_pem=cert_pem, key_pem=key_pem)


def sign_client_cert(host_id: str, validity_days: int = 90) -> CertBundle:
    """Gera cert client signado pela CA. CN = host_id (UUID).

    Agentes usam esse cert pra autenticar no gRPC via mTLS.
    Validade curta (90d) — agente renova proximo do vencimento.
    """
    ca_cert, ca_key = load_or_create_ca()
    key = _generate_key(2048)  # 2048 e suficiente pra cert curta, e mais rapido pra gerar
    name = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SentinelBR"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "agents"),
        x509.NameAttribute(NameOID.COMMON_NAME, host_id),
    ])
    now = dt.datetime.now(dt.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - dt.timedelta(minutes=5))
        .not_valid_after(now + dt.timedelta(days=validity_days))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH]),
            critical=False,
        )
        .sign(private_key=ca_key, algorithm=hashes.SHA256())
    )

    return CertBundle(cert_pem=_cert_to_pem(cert), key_pem=_key_to_pem(key))


def get_ca_cert_pem() -> bytes:
    cert, _ = load_or_create_ca()
    return _cert_to_pem(cert)
