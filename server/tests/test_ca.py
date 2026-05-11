"""Testes do servico de PKI: idempotencia e validacao de assinatura."""

from cryptography import x509
from cryptography.hazmat.primitives import hashes

from app.services.ca import (
    get_ca_cert_pem,
    load_or_create_ca,
    load_or_create_server_cert,
    sign_client_cert,
)


def test_ca_is_idempotent():
    ca1, _ = load_or_create_ca()
    ca2, _ = load_or_create_ca()
    assert ca1.serial_number == ca2.serial_number


def test_server_cert_is_signed_by_ca():
    ca_cert, ca_key = load_or_create_ca()
    bundle = load_or_create_server_cert()

    server_cert = x509.load_pem_x509_certificate(bundle.cert_pem)

    ca_key.public_key().verify(
        server_cert.signature,
        server_cert.tbs_certificate_bytes,
        __import__("cryptography").hazmat.primitives.asymmetric.padding.PKCS1v15(),
        server_cert.signature_hash_algorithm or hashes.SHA256(),
    )
    assert server_cert.issuer == ca_cert.subject


def test_client_cert_has_host_id_in_cn():
    bundle = sign_client_cert("11111111-2222-3333-4444-555555555555")
    cert = x509.load_pem_x509_certificate(bundle.cert_pem)
    cn = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value
    assert cn == "11111111-2222-3333-4444-555555555555"


def test_get_ca_cert_pem_starts_with_pem_marker():
    pem = get_ca_cert_pem()
    assert pem.startswith(b"-----BEGIN CERTIFICATE-----")
